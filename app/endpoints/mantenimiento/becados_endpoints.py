from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.services.mantenimiento.becados_service import (
    validar_becado_create_data,
    validar_becado_update_data,
    validar_becado_refs,
    validar_becado_unicidad_activa,
    validar_becado_existente,
)

from app.repositories.mantenimiento.becados_repo import (
    fetch_estudiantes_disponibles_lookup,
    fetch_becas,
    list_becados_join_activos,
    next_id_becado,
    insert_becado,
    update_becado,
    soft_delete_becado,
)


def _get_conn():
    """
    Obtiene la conexión técnica de la aplicación.
    """
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


def get_lookups(db_user: str | None = None, db_pass: str | None = None):
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


def listar_becados(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
):
    conn = _get_conn()
    try:
        return list_becados_join_activos(conn)
    finally:
        conn.close()


def siguiente_id_becado(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
) -> int:
    conn = _get_conn()
    try:
        return next_id_becado(conn)
    finally:
        conn.close()


def crear_becado(
    db_user: str | None,
    db_pass: str | None,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
    codigo_usuario: int | None = None,
) -> bool:
    conn = _get_conn()
    try:
        data = validar_becado_create_data(
            carnet=carnet,
            id_beca=id_beca,
            fecha_aplicacion=fecha_aplicacion,
        )

        validar_becado_refs(
            conn,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
        )

        validar_becado_unicidad_activa(
            conn,
            carnet=data["carnet"],
            exclude_id=None,
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


def actualizar_becado(
    db_user: str | None,
    db_pass: str | None,
    id_becado: int,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
    codigo_usuario: int | None = None,
) -> bool:
    if not id_becado:
        raise ValidationError("Debe seleccionar un becado para actualizar.")

    conn = _get_conn()
    try:
        id_becado = int(id_becado)

        validar_becado_existente(conn, id_becado=id_becado)

        data = validar_becado_update_data(
            id_becado=id_becado,
            carnet=carnet,
            id_beca=id_beca,
            fecha_aplicacion=fecha_aplicacion,
        )

        validar_becado_refs(
            conn,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
        )

        validar_becado_unicidad_activa(
            conn,
            carnet=data["carnet"],
            exclude_id=id_becado,
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


def eliminar_becado(
    db_user: str | None,
    db_pass: str | None,
    id_becado: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not id_becado:
        raise ValidationError("Debe seleccionar un becado para eliminar.")

    conn = _get_conn()
    try:
        id_becado = int(id_becado)

        validar_becado_existente(conn, id_becado=id_becado)

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