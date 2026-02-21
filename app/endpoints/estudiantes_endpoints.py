# app/endpoints/estudiantes_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.estudiantes_service import validar_estudiante_data, ValidationError
from app.repositories.estudiantes_repo import (
    fetch_estados,
    list_estudiantes_join,
    insert_estudiante,
    update_estudiante,
    delete_estudiante,
)


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return fetch_estados(conn)
    finally:
        conn.close()


def listar_estudiantes(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return list_estudiantes_join(conn)
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
):
    data = validar_estudiante_data(
        carnet=carnet,
        identificacion=identificacion,
        nombre_completo=nombre_completo,
        direccion=direccion,
        telefono=telefono,
        estado_codigo=estado_codigo,
    )

    conn = connect(db_user, db_pass)
    try:
        insert_estudiante(conn, **data)
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
):
    if not (carnet or "").strip():
        raise ValidationError("Debe seleccionar un estudiante para actualizar.")

    data = validar_estudiante_data(
        carnet=carnet,
        identificacion=identificacion,
        nombre_completo=nombre_completo,
        direccion=direccion,
        telefono=telefono,
        estado_codigo=estado_codigo,
    )

    conn = connect(db_user, db_pass)
    try:
        update_estudiante(conn, **data)
    finally:
        conn.close()


def eliminar_estudiante(db_user: str, db_pass: str, carnet: str):
    if not (carnet or "").strip():
        raise ValidationError("Debe seleccionar un estudiante para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        delete_estudiante(conn, carnet.strip())
    finally:
        conn.close()