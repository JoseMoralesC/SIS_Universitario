# app/endpoints/cursos_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.cursos_service import validar_curso_data, ValidationError
from app.repositories.cursos_repo import (
    fetch_estados,
    fetch_programas,
    list_cursos_join,
    next_materia_cod,
    insert_curso,
    update_curso,
    delete_curso,
)


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        estados = fetch_estados(conn)
        programas = fetch_programas(conn)
        return estados, programas
    finally:
        conn.close()


def listar_cursos(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return list_cursos_join(conn)
    finally:
        conn.close()


def siguiente_materia_cod(db_user: str, db_pass: str) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_materia_cod(conn)
    finally:
        conn.close()


def crear_curso(
    db_user: str,
    db_pass: str,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    estado_codigo: int,
):
    data = validar_curso_data(descripcion=descripcion, curso_cod=curso_cod, estado_codigo=estado_codigo)

    conn = connect(db_user, db_pass)
    try:
        insert_curso(conn, materia_cod=int(materia_cod), **data)
    finally:
        conn.close()


def actualizar_curso(
    db_user: str,
    db_pass: str,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    estado_codigo: int,
):
    if not materia_cod:
        raise ValidationError("Debe seleccionar un curso para actualizar.")

    data = validar_curso_data(descripcion=descripcion, curso_cod=curso_cod, estado_codigo=estado_codigo)

    conn = connect(db_user, db_pass)
    try:
        update_curso(conn, materia_cod=int(materia_cod), **data)
    finally:
        conn.close()


def eliminar_curso(db_user: str, db_pass: str, materia_cod: int):
    if not materia_cod:
        raise ValidationError("Debe seleccionar un curso para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        delete_curso(conn, int(materia_cod))
    finally:
        conn.close()