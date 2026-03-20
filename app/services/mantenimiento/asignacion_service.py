from __future__ import annotations

import pyodbc

from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.asignacion_repo import (
    exists_programa,
    exists_docente,
    exists_asignacion,
)


def validar_asignacion_data(
    *,
    curso_cod: int,
    docente_cod: int,
) -> dict:
    try:
        curso_cod = int(curso_cod)
    except Exception:
        raise ValidationError("Programa/Carrera inválido.")

    try:
        docente_cod = int(docente_cod)
    except Exception:
        raise ValidationError("Docente inválido.")

    if curso_cod <= 0:
        raise ValidationError("Programa/Carrera inválido.")
    if docente_cod <= 0:
        raise ValidationError("Docente inválido.")

    return {
        "curso_cod": curso_cod,
        "docente_cod": docente_cod,
    }


def validar_asignacion_creacion(
    conn: pyodbc.Connection,
    *,
    curso_cod: int,
    docente_cod: int,
) -> None:
    if not exists_programa(conn, curso_cod):
        raise ValidationError("El programa/carrera seleccionado no existe.")

    if not exists_docente(conn, docente_cod):
        raise ValidationError("El docente seleccionado no existe.")

    if exists_asignacion(conn, curso_cod, docente_cod):
        raise ValidationError("Ese docente ya está asignado a esa carrera/programa.")


def validar_asignacion_actualizacion(
    conn: pyodbc.Connection,
    *,
    curso_cod_original: int,
    docente_cod_original: int,
    curso_cod_nuevo: int,
    docente_cod_nuevo: int,
) -> None:
    if not exists_asignacion(conn, curso_cod_original, docente_cod_original):
        raise ValidationError("La asignación original no existe.")

    if not exists_programa(conn, curso_cod_nuevo):
        raise ValidationError("El programa/carrera nuevo no existe.")

    if not exists_docente(conn, docente_cod_nuevo):
        raise ValidationError("El docente nuevo no existe.")

    # Si realmente está cambiando la PK compuesta, validamos que no duplique
    cambio_real = (
        int(curso_cod_original) != int(curso_cod_nuevo)
        or int(docente_cod_original) != int(docente_cod_nuevo)
    )

    if cambio_real and exists_asignacion(conn, curso_cod_nuevo, docente_cod_nuevo):
        raise ValidationError("Ya existe una asignación con ese programa/carrera y docente.")