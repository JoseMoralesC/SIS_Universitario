# app/endpoints/mantenimiento/becados_endpoints.py
from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.services.mantenimiento.becados_service import (
    validar_becado_data,
    validar_becado_unicidad,
)


from app.repositories.mantenimiento.becados_repo import (
    fetch_estudiantes_disponibles_lookup,  # <-- FIX
    fetch_becas,                           # <-- FIX
    list_becados_join_activos,
    next_id_becado,
    insert_becado,
    update_becado,
    soft_delete_becado,
)

from app.services.security.permission_service import (
    require_maintenance_access,
    require_maintenance_action,
)


RESOURCE_KEY = "becados"


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
            id_tabla=Tab.BECADOS,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


# =========================================================
# LOOKUPS
# =========================================================
def get_lookups(
    db_user: str | None = None,
    db_pass: str | None = None,
):
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
    
        estudiantes = fetch_estudiantes_disponibles_lookup(conn)
        becas = fetch_becas(conn)

        return {
            "estudiantes": estudiantes,
            "becas": becas,
        }
    finally:
        conn.close()


# =========================================================
# GRID
# =========================================================
def listar_becados(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
):
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return list_becados_join_activos(conn)
    finally:
        conn.close()


# =========================================================
# NEXT ID
# =========================================================
def siguiente_id_becado(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
) -> int:
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return next_id_becado(conn)
    finally:
        conn.close()


# =========================================================
# CREATE
# =========================================================
def crear_becado(
    db_user: str | None,
    db_pass: str | None,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "create")

    conn = _get_conn()
    try:
        data = validar_becado_data(
            carnet=carnet,
            id_beca=id_beca,
            fecha_aplicacion=fecha_aplicacion,
        )

        validar_becado_unicidad(
            conn,
            id_becado=None,
            carnet=data["carnet"],
        )

        id_becado = insert_becado(
            conn,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
            fecha_aplicacion=data["fecha_aplicacion"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.BECADO_CREADO,
            id_row_tabla=id_becado,
        )

        return True
    finally:
        conn.close()


# =========================================================
# UPDATE
# =========================================================
def actualizar_becado(
    db_user: str | None,
    db_pass: str | None,
    id_becado: int,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "update")

    if not id_becado:
        raise ValidationError("Debe seleccionar una asignación de beca para actualizar.")

    conn = _get_conn()
    try:
        id_becado = int(id_becado)

        data = validar_becado_data(
            id_becado=id_becado,
            carnet=carnet,
            id_beca=id_beca,
            fecha_aplicacion=fecha_aplicacion,
        )

        validar_becado_unicidad(
            conn,
            id_becado=id_becado,
            carnet=data["carnet"],
        )

        update_becado(
            conn,
            id_becado=id_becado,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
            fecha_aplicacion=data["fecha_aplicacion"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.BECADO_ACTUALIZADO,
            id_row_tabla=id_becado,
        )

        return True
    finally:
        conn.close()


# =========================================================
# DELETE
# =========================================================
def eliminar_becado(
    db_user: str | None,
    db_pass: str | None,
    id_becado: int,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "delete")

    if not id_becado:
        raise ValidationError("Debe seleccionar una asignación de beca para eliminar.")

    conn = _get_conn()
    try:
        id_becado = int(id_becado)

        soft_delete_becado(conn, id_becado=id_becado)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.BECADO_ELIMINADO,
            id_row_tabla=id_becado,
        )

        return True
    finally:
        conn.close()