from __future__ import annotations

import pyodbc
import unicodedata

from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.asignacion_repo import (
    exists_programa,
    exists_docente,
    exists_asignacion,
    exists_docente_asignado,
    get_programa_descripcion,
    get_docente_profesion_descripcion,
    fetch_docentes_disponibles_con_profesion,
)


def _normalize(text: str | None) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def _extraer_tematica_programa(programa_desc: str) -> str:
    tema = _normalize(programa_desc)
    prefijos = [
        "diplomado en ",
        "diplomado de ",
        "bachillerato en ",
        "tecnico en ",
        "tecnico de ",
    ]
    for p in prefijos:
        if tema.startswith(p):
            tema = tema[len(p):]
            break
    return tema.strip()


def es_profesion_compatible_con_programa(programa_desc: str, profesion_desc: str) -> bool:
    programa_norm = _normalize(programa_desc)
    profesion_norm = _normalize(profesion_desc)
    tema = _extraer_tematica_programa(programa_desc)

    if not programa_norm or not profesion_norm:
        return False

    # Match directo por texto
    if tema and (tema in profesion_norm or profesion_norm in tema):
        return True

    # Reglas explícitas para el proyecto
    reglas = {
        "programacion": {"ingenieria en sistemas", "big data"},
        "big data": {"big data", "ingenieria en sistemas"},
        "administracion": {"administracion", "control de calidad"},
        "educacion": {"educacion"},
        "turismo": {"turismo"},
        "secretariado": {"secretariado"},
        "mecanica dental": {"mecanica dental"},
        "diseno grafico": {"diseno grafico"},
        "contabilidad": {"administracion", "control de calidad"},
    }

    for clave_programa, profesiones_validas in reglas.items():
        if clave_programa in programa_norm:
            return any(p in profesion_norm for p in profesiones_validas)

    return False


def obtener_docentes_disponibles_para_programa(
    conn: pyodbc.Connection,
    *,
    curso_cod: int,
    docente_cod_actual: int | None = None,
) -> list[tuple[int, str]]:
    programa_desc = get_programa_descripcion(conn, int(curso_cod))
    if not programa_desc:
        return []

    candidatos = fetch_docentes_disponibles_con_profesion(
        conn,
        docente_cod_actual=docente_cod_actual,
    )

    filtrados: list[tuple[int, str]] = []
    for docente_cod, nombre_completo, profesion_desc in candidatos:
        if es_profesion_compatible_con_programa(programa_desc, profesion_desc):
            filtrados.append((int(docente_cod), str(nombre_completo)))

    return filtrados


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

    if exists_docente_asignado(conn, docente_cod):
        raise ValidationError("Ese docente ya está asignado a otro programa/carrera.")

    programa_desc = get_programa_descripcion(conn, curso_cod)
    profesion_desc = get_docente_profesion_descripcion(conn, docente_cod)

    if not es_profesion_compatible_con_programa(programa_desc or "", profesion_desc or ""):
        raise ValidationError(
            "La profesión del docente no es compatible con la carrera/programa seleccionado."
        )


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

    cambio_real = (
        int(curso_cod_original) != int(curso_cod_nuevo)
        or int(docente_cod_original) != int(docente_cod_nuevo)
    )

    if cambio_real and exists_asignacion(conn, curso_cod_nuevo, docente_cod_nuevo):
        raise ValidationError("Ya existe una asignación con ese programa/carrera y docente.")

    # El docente nuevo no puede estar asignado a otro programa distinto
    if exists_docente_asignado(
        conn,
        docente_cod_nuevo,
        exclude_curso_cod=curso_cod_original if int(docente_cod_nuevo) == int(docente_cod_original) else None,
    ):
        raise ValidationError("Ese docente ya está asignado a otro programa/carrera.")

    programa_desc = get_programa_descripcion(conn, curso_cod_nuevo)
    profesion_desc = get_docente_profesion_descripcion(conn, docente_cod_nuevo)

    if not es_profesion_compatible_con_programa(programa_desc or "", profesion_desc or ""):
        raise ValidationError(
            "La profesión del docente no es compatible con la carrera/programa seleccionado."
        )