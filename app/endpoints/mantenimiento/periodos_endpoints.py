from __future__ import annotations

from app.core.db import connect
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.services.mantenimiento.periodos_service import (
    validar_periodo_data,
    validar_periodo_unicidad,
)

from app.repositories.mantenimiento.periodos_repo import (
    fetch_estados,
    list_periodos_join_activos,
    insert_periodo,
    update_periodo,
    soft_delete_periodo,
)


def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
    id_row_tabla: object | None = None,
) -> None:
    if codigo_usuario is None:
        return

    try:
        insert_auditoria(
            conn,
            codigo_usuario=int(codigo_usuario),
            movimiento_cod=int(movimiento_cod),
            id_tabla=Tab.PERIODOS,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


# =========================================================
# API interna alineada con la UI actual
# =========================================================
def fetch_estados_periodos(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return fetch_estados(conn)
    finally:
        conn.close()


def list_periodos_rows(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
):
    conn = connect(db_user, db_pass)
    try:
        return list_periodos_join_activos(conn)
    finally:
        conn.close()


def create_periodo(
    db_user: str,
    db_pass: str,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> str:
    conn = connect(db_user, db_pass)
    try:
        data = validar_periodo_data(
            periodo_codigo=None,
            anio=anio,
            numero_periodo=numero_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado_codigo=estado_codigo,
        )

        validar_periodo_unicidad(
            conn,
            periodo_id=None,
            periodo_codigo=data["periodo_codigo"],
            anio=data["anio"],
            numero_periodo=data["numero_periodo"],
        )

        periodo_id = insert_periodo(
            conn,
            periodo_codigo=data["periodo_codigo"],
            anio=data["anio"],
            numero_periodo=data["numero_periodo"],
            fecha_inicio=data["fecha_inicio"],
            fecha_fin=data["fecha_fin"],
            estado_codigo=data["estado_codigo"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_CREADO,
            id_row_tabla=periodo_id if periodo_id else data["periodo_codigo"],
        )

        return "Período creado correctamente."
    finally:
        conn.close()


def update_periodo_endpoint(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> str:
    if not periodo_id:
        raise ValidationError("Debe seleccionar un período para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        periodo_id = int(periodo_id)

        data = validar_periodo_data(
            periodo_codigo=None,
            anio=anio,
            numero_periodo=numero_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado_codigo=estado_codigo,
        )

        validar_periodo_unicidad(
            conn,
            periodo_id=periodo_id,
            periodo_codigo=data["periodo_codigo"],
            anio=data["anio"],
            numero_periodo=data["numero_periodo"],
        )

        update_periodo(
            conn,
            periodo_id=periodo_id,
            periodo_codigo=data["periodo_codigo"],
            anio=data["anio"],
            numero_periodo=data["numero_periodo"],
            fecha_inicio=data["fecha_inicio"],
            fecha_fin=data["fecha_fin"],
            estado_codigo=data["estado_codigo"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_ACTUALIZADO,
            id_row_tabla=periodo_id,
        )

        return "Período actualizado correctamente."
    finally:
        conn.close()


def delete_periodo_endpoint(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    codigo_usuario: int | None = None,
) -> str:
    if not periodo_id:
        raise ValidationError("Debe seleccionar un período para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        periodo_id = int(periodo_id)
        soft_delete_periodo(conn, periodo_id=periodo_id)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_ELIMINADO,
            id_row_tabla=periodo_id,
        )

        return "Período desactivado correctamente."
    finally:
        conn.close()


# =========================================================
# Alias de compatibilidad
# =========================================================
def get_lookups(db_user: str, db_pass: str):
    return fetch_estados_periodos(db_user, db_pass)


def listar_periodos(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    return list_periodos_rows(db_user, db_pass, codigo_usuario=codigo_usuario)


def crear_periodo(
    db_user: str,
    db_pass: str,
    periodo_codigo: str | None = None,
    anio: int = 0,
    numero_periodo: int = 0,
    fecha_inicio: str = "",
    fecha_fin: str = "",
    estado_codigo: int = 0,
    codigo_usuario: int | None = None,
) -> bool:
    create_periodo(
        db_user=db_user,
        db_pass=db_pass,
        anio=anio,
        numero_periodo=numero_periodo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado_codigo=estado_codigo,
        codigo_usuario=codigo_usuario,
    )
    return True


def actualizar_periodo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    periodo_codigo: str | None = None,
    anio: int = 0,
    numero_periodo: int = 0,
    fecha_inicio: str = "",
    fecha_fin: str = "",
    estado_codigo: int = 0,
    codigo_usuario: int | None = None,
) -> bool:
    update_periodo_endpoint(
        db_user=db_user,
        db_pass=db_pass,
        periodo_id=periodo_id,
        anio=anio,
        numero_periodo=numero_periodo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado_codigo=estado_codigo,
        codigo_usuario=codigo_usuario,
    )
    return True


def eliminar_periodo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    codigo_usuario: int | None = None,
) -> bool:
    delete_periodo_endpoint(
        db_user=db_user,
        db_pass=db_pass,
        periodo_id=periodo_id,
        codigo_usuario=codigo_usuario,
    )
    return True