# app/endpoints/mantenimiento/becados_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.services.mantenimiento.becados_service import (
    validar_becado_data,
    validar_becado_unicidad,
)

from app.repositories.mantenimiento.becados_repo import (
    fetch_estados,
    fetch_becas,
    list_becados_join_activos,
    insert_becado,
    update_becado,
    soft_delete_becado,
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
            id_tabla=Tab.BECADOS,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        # No romper el flujo principal por fallo de auditoría
        pass


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        estados = fetch_estados(conn)
        becas = fetch_becas(conn)
        return estados, becas
    finally:
        conn.close()


def listar_becados(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
):
    """
    Lista becados visibles en el grid.
    """
    conn = connect(db_user, db_pass)
    try:
        return list_becados_join_activos(conn)
    finally:
        conn.close()


def crear_becado(
    db_user: str,
    db_pass: str,
    carnet: str,
    id_beca: int,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_becado_data(
            carnet=carnet,
            id_beca=id_beca,
            estado_codigo=estado_codigo,
        )

        validar_becado_unicidad(
            conn,
            id_becado=None,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
        )

        id_becado = insert_becado(
            conn,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
            estado_codigo=data["estado_codigo"],
        )

        # fallback seguro
        row_id = id_becado if id_becado is not None else f"{data['carnet']}|{data['id_beca']}"

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.BECADO_CREADO,
            id_row_tabla=row_id,
        )

        return True
    finally:
        conn.close()


def actualizar_becado(
    db_user: str,
    db_pass: str,
    id_becado: int,
    carnet: str,
    id_beca: int,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not id_becado:
        raise ValidationError("Debe seleccionar un becado para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        id_becado = int(id_becado)

        data = validar_becado_data(
            carnet=carnet,
            id_beca=id_beca,
            estado_codigo=estado_codigo,
        )

        validar_becado_unicidad(
            conn,
            id_becado=id_becado,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
        )

        update_becado(
            conn,
            id_becado=id_becado,
            carnet=data["carnet"],
            id_beca=data["id_beca"],
            estado_codigo=data["estado_codigo"],
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
    db_user: str,
    db_pass: str,
    id_becado: int,
    codigo_usuario: int | None = None,
) -> bool:
    """
    Borrado lógico
    """
    if not id_becado:
        raise ValidationError("Debe seleccionar un becado para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        id_becado = int(id_becado)

        soft_delete_becado(conn, id_becado)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.BECADO_ELIMINADO,
            id_row_tabla=id_becado,
        )

        return True
    finally:
        conn.close()