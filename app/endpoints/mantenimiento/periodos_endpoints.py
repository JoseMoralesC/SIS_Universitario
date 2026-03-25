# app/endpoints/mantenimiento/periodos_endpoints.py
from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.repositories.mantenimiento.periodos_repo import (
    fetch_estados,
    list_periodos_join_activos,
    insert_periodo,
    update_periodo,
    soft_delete_periodo,
)

from app.services.mantenimiento.periodos_service import (
    validar_periodo_data,
    validar_periodo_unicidad,
)
from app.services.security.permission_service import (
    require_maintenance_access,
    require_maintenance_action,
)


RESOURCE_KEY = "periodos"


def _get_conn():
    return connect_app()


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
# LOOKUPS
# =========================================================
def fetch_estados_periodos(
    db_user: str | None = None,
    db_pass: str | None = None,
):
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return fetch_estados(conn)
    finally:
        conn.close()


# =========================================================
# GRID
# =========================================================
def list_periodos_rows(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
):
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return list_periodos_join_activos(conn)
    finally:
        conn.close()


# =========================================================
# CREATE
# =========================================================
def create_periodo_endpoint(
    db_user: str | None,
    db_pass: str | None,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
):
    require_maintenance_action(RESOURCE_KEY, "create")

    conn = _get_conn()
    try:
        data = validar_periodo_data(
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
            periodo_id,
        )

        return "Período creado correctamente."
    finally:
        conn.close()


# =========================================================
# UPDATE
# =========================================================
def update_periodo_endpoint(
    db_user: str | None,
    db_pass: str | None,
    periodo_id: int,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
):
    require_maintenance_action(RESOURCE_KEY, "update")

    if not periodo_id:
        raise ValidationError("Debe seleccionar un período para actualizar.")

    conn = _get_conn()
    try:
        periodo_id = int(periodo_id)

        data = validar_periodo_data(
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
            periodo_id,
        )

        return "Período actualizado correctamente."
    finally:
        conn.close()


# =========================================================
# DELETE
# =========================================================
def delete_periodo_endpoint(
    db_user: str | None,
    db_pass: str | None,
    periodo_id: int,
    codigo_usuario: int | None = None,
):
    require_maintenance_action(RESOURCE_KEY, "delete")

    if not periodo_id:
        raise ValidationError("Debe seleccionar un período para eliminar.")

    conn = _get_conn()
    try:
        periodo_id = int(periodo_id)

        soft_delete_periodo(conn, periodo_id=periodo_id)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_ELIMINADO,
            periodo_id,
        )

        return "Período desactivado correctamente."
    finally:
        conn.close()