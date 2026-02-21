# app/endpoints/programas_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.programas_service import validar_programa_data, ValidationError
from app.repositories.programas_repo import (
    fetch_estados,
    list_programas_join,
    next_curso_cod,
    insert_programa,
    update_programa,
    delete_programa,
)


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        estados = fetch_estados(conn)
        return estados
    finally:
        conn.close()


def listar_programas(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return list_programas_join(conn)
    finally:
        conn.close()


def siguiente_curso_cod(db_user: str, db_pass: str) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_curso_cod(conn)
    finally:
        conn.close()


def crear_programa(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    descripcion: str,
    horario: str | None,
    precio_matricula: str,
    estado_codigo: int,
):
    data = validar_programa_data(
        descripcion=descripcion,
        horario=horario,
        precio_matricula=precio_matricula,
        estado_codigo=estado_codigo,
    )

    conn = connect(db_user, db_pass)
    try:
        insert_programa(conn, curso_cod=int(curso_cod), **data)
    finally:
        conn.close()


def actualizar_programa(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    descripcion: str,
    horario: str | None,
    precio_matricula: str,
    estado_codigo: int,
):
    if not curso_cod:
        raise ValidationError("Debe seleccionar un programa para actualizar.")

    data = validar_programa_data(
        descripcion=descripcion,
        horario=horario,
        precio_matricula=precio_matricula,
        estado_codigo=estado_codigo,
    )

    conn = connect(db_user, db_pass)
    try:
        update_programa(conn, curso_cod=int(curso_cod), **data)
    finally:
        conn.close()


def eliminar_programa(db_user: str, db_pass: str, curso_cod: int):
    if not curso_cod:
        raise ValidationError("Debe seleccionar un programa para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        delete_programa(conn, int(curso_cod))
    finally:
        conn.close()