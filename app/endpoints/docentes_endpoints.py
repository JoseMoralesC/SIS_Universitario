# app/endpoints/docentes_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.docentes_service import (
    validar_docente_data,
    ValidationError,
)
from app.repositories.docentes_repo import (
    fetch_estados,
    fetch_profesiones,
    list_docentes_join,
    insert_docente,
    update_docente,
    delete_docente,
    next_docente_cod,
)
def siguiente_docente_cod(db_user: str, db_pass: str) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_docente_cod(conn)
    finally:
        conn.close()


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        estados = fetch_estados(conn)
        profesiones = fetch_profesiones(conn)
        return estados, profesiones
    finally:
        conn.close()


def listar_docentes(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        return list_docentes_join(conn)
    finally:
        conn.close()


def crear_docente(
    db_user: str,
    db_pass: str,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
):
    data = validar_docente_data(
        identificacion=identificacion,
        usuario_docente=usuario_docente,
        nombre_completo=nombre_completo,
        estado_codigo=estado_codigo,
        profesion_cod=profesion_cod,
    )

    conn = connect(db_user, db_pass)
    try:
        insert_docente(conn, docente_cod=int(docente_cod), **data)
    finally:
        conn.close()


def actualizar_docente(
    db_user: str,
    db_pass: str,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
):
    if not docente_cod:
        raise ValidationError("Debe seleccionar un docente para actualizar.")

    data = validar_docente_data(
        identificacion=identificacion,
        usuario_docente=usuario_docente,
        nombre_completo=nombre_completo,
        estado_codigo=estado_codigo,
        profesion_cod=profesion_cod,
    )

    conn = connect(db_user, db_pass)
    try:
        update_docente(conn, docente_cod=int(docente_cod), **data)
    finally:
        conn.close()


def eliminar_docente(db_user: str, db_pass: str, docente_cod: int):
    if not docente_cod:
        raise ValidationError("Debe seleccionar un docente para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        delete_docente(conn, int(docente_cod))
    finally:
        conn.close()