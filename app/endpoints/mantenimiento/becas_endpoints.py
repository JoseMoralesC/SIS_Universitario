from __future__ import annotations

from app.core.db import connect
from app.repositories.mantenimiento.becas_repo import (
    list_becas,
    next_id_beca,
    insert_beca,
    update_beca,
    soft_delete_beca,
)

from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria
from app.services.mantenimiento.becas_service import (
    validar_beca_data,
    validar_beca_unicidad,
    validar_beca_existente,
    validar_beca_puede_eliminarse,
)


def listar_becas(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    conn = connect(db_user, db_pass)
    try:
        return list_becas(conn)
    finally:
        conn.close()


def siguiente_id_beca(db_user: str, db_pass: str, codigo_usuario: int | None = None) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_id_beca(conn)
    finally:
        conn.close()


def crear_beca(
    db_user: str,
    db_pass: str,
    nombre_beca: str,
    porcentaje_descuento: str,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        # Validaciones consistentes
        data = validar_beca_data(
            id_beca=None,
            nombre_beca=nombre_beca,
            porcentaje_descuento=int(porcentaje_descuento),
        )
        validar_beca_unicidad(conn, nombre_beca=data["nombre_beca"], exclude_id=None)

        insert_beca(conn, nombre_beca=data["nombre_beca"], porcentaje_descuento=int(data["porcentaje_descuento"]))

        # Auditoría
        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.BECA_CREADA)
            except Exception:
                pass

        return True
    finally:
        conn.close()


def actualizar_beca(
    db_user: str,
    db_pass: str,
    id_beca: int,
    nombre_beca: str,
    porcentaje_descuento: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_beca_data(
            id_beca=int(id_beca),
            nombre_beca=nombre_beca,
            porcentaje_descuento=int(porcentaje_descuento),
        )
        validar_beca_existente(conn, id_beca=data["id_beca"])
        validar_beca_unicidad(conn, nombre_beca=data["nombre_beca"], exclude_id=data["id_beca"])

        update_beca(conn, **data)

        # Auditoría
        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.BECA_ACTUALIZADA)
            except Exception:
                pass

        return True
    finally:
        conn.close()


def eliminar_beca(db_user: str, db_pass: str, id_beca: int, codigo_usuario: int | None = None) -> bool:
    conn = connect(db_user, db_pass)
    try:
        validar_beca_existente(conn, id_beca=int(id_beca))
        validar_beca_puede_eliminarse(conn, id_beca=int(id_beca))
        soft_delete_beca(conn, id_beca=int(id_beca))  # lógico

        # Auditoría
        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.BECA_ELIMINADA)
            except Exception:
                pass

        return True
    finally:
        conn.close()