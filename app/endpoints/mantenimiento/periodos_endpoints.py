# app/endpoints/mantenimiento/periodos_endpoints.py
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
        # No romper el flujo principal por un fallo aislado de auditoría
        pass


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return fetch_estados(conn)
    finally:
        conn.close()


def listar_periodos(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
):
    """
    Lista períodos visibles en el grid.
    codigo_usuario se acepta por consistencia.
    """
    conn = connect(db_user, db_pass)
    try:
        return list_periodos_join_activos(conn)
    finally:
        conn.close()


def crear_periodo(
    db_user: str,
    db_pass: str,
    periodo_codigo: str,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_periodo_data(
            periodo_codigo=periodo_codigo,
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

        # Si el repo no devuelve el ID, al menos dejamos el código como fallback
        row_id = periodo_id if periodo_id is not None else data["periodo_codigo"]

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_CREADO,
            id_row_tabla=row_id,
        )

        return True
    finally:
        conn.close()


def actualizar_periodo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    periodo_codigo: str,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not periodo_id:
        raise ValidationError("Debe seleccionar un período para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        periodo_id = int(periodo_id)

        data = validar_periodo_data(
            periodo_codigo=periodo_codigo,
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

        return True
    finally:
        conn.close()


def eliminar_periodo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    codigo_usuario: int | None = None,
) -> bool:
    """
    Borrado lógico:
    - Cambia Estado_Codigo al estado Inactivo
    - No hace DELETE físico
    """
    if not periodo_id:
        raise ValidationError("Debe seleccionar un período para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        periodo_id = int(periodo_id)

        soft_delete_periodo(conn, periodo_id)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_ELIMINADO,
            id_row_tabla=periodo_id,
        )

        return True
    finally:
        conn.close()