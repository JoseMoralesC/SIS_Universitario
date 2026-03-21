from __future__ import annotations

from app.core.db import connect
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.services.mantenimiento.becas_service import (
    validar_beca_data,
    validar_beca_unicidad,
    validar_beca_puede_eliminarse,
)

from app.repositories.mantenimiento.becas_repo import (
    fetch_estados,
    list_becas_join_activos,
    next_id_beca,
    insert_beca,
    update_beca,
    soft_delete_beca,
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
            id_tabla=Tab.BECAS,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return fetch_estados(conn)
    finally:
        conn.close()


def listar_becas(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
):
    conn = connect(db_user, db_pass)
    try:
        return list_becas_join_activos(conn)
    finally:
        conn.close()


def siguiente_id_beca(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_id_beca(conn)
    finally:
        conn.close()


def crear_beca(
    db_user: str,
    db_pass: str,
    nombre_beca: str,
    porcentaje_descuento: int,
    estado_codigo: int = 1,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_beca_data(
            nombre_beca=nombre_beca,
            porcentaje_descuento=porcentaje_descuento,
            estado_codigo=estado_codigo,
        )

        validar_beca_unicidad(
            conn,
            id_beca=None,
            nombre_beca=data["nombre_beca"],
        )

        id_beca = insert_beca(
            conn,
            nombre_beca=data["nombre_beca"],
            porcentaje_descuento=data["porcentaje_descuento"],
            estado_codigo=data["estado_codigo"],
        )

        _registrar_auditoria(conn, codigo_usuario, Mov.BECA_CREADA, id_row_tabla=id_beca)
        return True
    finally:
        conn.close()


def actualizar_beca(
    db_user: str,
    db_pass: str,
    id_beca: int,
    nombre_beca: str,
    porcentaje_descuento: int,
    estado_codigo: int = 1,
    codigo_usuario: int | None = None,
) -> bool:
    if not id_beca:
        raise ValidationError("Debe seleccionar una beca para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        id_beca = int(id_beca)

        data = validar_beca_data(
            id_beca=id_beca,
            nombre_beca=nombre_beca,
            porcentaje_descuento=porcentaje_descuento,
            estado_codigo=estado_codigo,
        )

        validar_beca_unicidad(
            conn,
            id_beca=id_beca,
            nombre_beca=data["nombre_beca"],
        )

        update_beca(
            conn,
            id_beca=id_beca,
            nombre_beca=data["nombre_beca"],
            porcentaje_descuento=data["porcentaje_descuento"],
            estado_codigo=data["estado_codigo"],
        )

        _registrar_auditoria(conn, codigo_usuario, Mov.BECA_ACTUALIZADA, id_row_tabla=id_beca)
        return True
    finally:
        conn.close()


def eliminar_beca(
    db_user: str,
    db_pass: str,
    id_beca: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not id_beca:
        raise ValidationError("Debe seleccionar una beca para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        id_beca = int(id_beca)
        validar_beca_puede_eliminarse(conn, id_beca=id_beca)
        soft_delete_beca(conn, id_beca)
        _registrar_auditoria(conn, codigo_usuario, Mov.BECA_ELIMINADA, id_row_tabla=id_beca)
        return True
    finally:
        conn.close()