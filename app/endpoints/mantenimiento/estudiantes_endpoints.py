# app/endpoints/estudiantes_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.mantenimiento.estudiantes_service import (
    validar_estudiante_data,
    validar_estudiante_unicidad,
)
from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.estudiantes_repo import (
    fetch_estados,
    list_estudiantes_join_activos,
    next_carnet,  # NUEVO
    insert_estudiante,
    update_estudiante,
    soft_delete_estudiante,
)

from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return fetch_estados(conn)
    finally:
        conn.close()


def listar_estudiantes(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    """
    Lista estudiantes visibles en el grid (según repo: normalmente excluye Inactivo).
    codigo_usuario se acepta por consistencia.
    """
    conn = connect(db_user, db_pass)
    try:
        return list_estudiantes_join_activos(conn)
    finally:
        conn.close()


def siguiente_carnet(db_user: str, db_pass: str) -> str:
    conn = connect(db_user, db_pass)
    try:
        return next_carnet(conn)
    finally:
        conn.close()


def crear_estudiante(
    db_user: str,
    db_pass: str,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str | None,
    telefono: str | None,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_estudiante_data(
            carnet=carnet,
            identificacion=identificacion,
            nombre_completo=nombre_completo,
            direccion=direccion,
            telefono=telefono,
            estado_codigo=estado_codigo,
        )

        validar_estudiante_unicidad(
            conn,
            carnet=data["carnet"],
            identificacion=data["identificacion"],
        )

        insert_estudiante(conn, **data)

        # Auditoría
        try:
            insert_auditoria(conn, codigo_usuario=codigo_usuario, movimiento_cod=Mov.ESTUDIANTE_CREADO)
        except Exception:
            pass

        return True
    finally:
        conn.close()


def actualizar_estudiante(
    db_user: str,
    db_pass: str,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str | None,
    telefono: str | None,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    carnet = (carnet or "").strip()
    if not carnet:
        raise ValidationError("Debe seleccionar un estudiante para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        data = validar_estudiante_data(
            carnet=carnet,
            identificacion=identificacion,
            nombre_completo=nombre_completo,
            direccion=direccion,
            telefono=telefono,
            estado_codigo=estado_codigo,
        )

        # OJO: la unicidad debe excluir el mismo carnet.
        # Tu service actual usa (carnet, identificacion). Mantenemos tu intención:
        validar_estudiante_unicidad(
            conn,
            carnet=carnet,
            identificacion=data["identificacion"],
        )

        update_estudiante(conn, **data)

        # Auditoría
        try:
            insert_auditoria(conn, codigo_usuario=codigo_usuario, movimiento_cod=Mov.ESTUDIANTE_ACTUALIZADO)
        except Exception:
            pass

        return True
    finally:
        conn.close()


def eliminar_estudiante(
    db_user: str,
    db_pass: str,
    carnet: str,
    codigo_usuario: int | None = None,
) -> bool:
    carnet = (carnet or "").strip()
    if not carnet:
        raise ValidationError("Debe seleccionar un estudiante para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        soft_delete_estudiante(conn, carnet)

        # Auditoría
        try:
            insert_auditoria(conn, codigo_usuario=codigo_usuario, movimiento_cod=Mov.ESTUDIANTE_ELIMINADO)
        except Exception:
            pass

        return True
    finally:
        conn.close()