from __future__ import annotations

from app.core.db import connect
from app.repositories.mantenimiento.becados_repo import (
    fetch_estudiantes_disponibles_lookup,
    list_becados_join,
    next_id_becado,
    insert_becado,
    update_becado,
    soft_delete_becado,
    exists_becado_activo_by_carnet,
)

from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria
from app.repositories.mantenimiento.becas_repo import fetch_becas_lookup
from app.services.mantenimiento.becados_service import (
    validar_becado_create_data,
    validar_becado_update_data,
    validar_becado_refs,
    validar_becado_existente,
)
from app.core.exceptions import ValidationError


def get_lookups(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    conn = connect(db_user, db_pass)
    try:
        estudiantes = fetch_estudiantes_disponibles_lookup(conn)   # solo no becados (activos)
        becas = fetch_becas_lookup(conn)
        return {"estudiantes": estudiantes, "becas": becas}
    finally:
        conn.close()


def listar_becados(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    """
    IMPORTANTE: solo muestra becados ACTIVOS
    """
    conn = connect(db_user, db_pass)
    try:
        return list_becados_join(conn, only_active=True)
    finally:
        conn.close()


def siguiente_id_becado(db_user: str, db_pass: str, codigo_usuario: int | None = None) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_id_becado(conn)
    finally:
        conn.close()


def crear_becado(
    db_user: str,
    db_pass: str,
    id_becado: int,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_becado_create_data(
            carnet=carnet,
            id_beca=id_beca,
            fecha_aplicacion=fecha_aplicacion,
        )
        validar_becado_refs(conn, carnet=data["carnet"], id_beca=data["id_beca"])

        if exists_becado_activo_by_carnet(conn, data["carnet"]):
            raise ValidationError("El estudiante ya tiene una beca activa.")

        insert_becado(conn, id_becado=int(id_becado), **data)

        # Auditoría
        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.BECADO_CREADO)
            except Exception:
                pass

        return True
    finally:
        conn.close()


def actualizar_becado(
    db_user: str,
    db_pass: str,
    id_becado: int,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_becado_update_data(
            id_becado=int(id_becado),
            carnet=carnet,
            id_beca=id_beca,
            fecha_aplicacion=fecha_aplicacion,
        )
        validar_becado_existente(conn, id_becado=data["id_becado"])
        validar_becado_refs(conn, carnet=data["carnet"], id_beca=data["id_beca"])

        if exists_becado_activo_by_carnet(conn, data["carnet"], exclude_id=data["id_becado"]):
            raise ValidationError("El estudiante ya tiene una beca activa.")

        update_becado(conn, **data)

        # Auditoría
        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.BECADO_ACTUALIZADO)
            except Exception:
                pass

        return True
    finally:
        conn.close()


def eliminar_becado(db_user: str, db_pass: str, id_becado: int, codigo_usuario: int | None = None) -> bool:
    """
    DELETE lógico
    """
    conn = connect(db_user, db_pass)
    try:
        validar_becado_existente(conn, id_becado=int(id_becado))
        soft_delete_becado(conn, id_becado=int(id_becado))

        # Auditoría
        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.BECADO_ELIMINADO)
            except Exception:
                pass

        return True
    finally:
        conn.close()