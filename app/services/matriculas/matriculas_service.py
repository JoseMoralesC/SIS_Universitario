# app/services/matriculas/matriculas_service.py
from __future__ import annotations

import datetime as _dt
import pyodbc

from app.core.exceptions import ValidationError
from app.repositories.matriculas.matriculas_repo import (
    assert_matricula_schema_ready,
    get_estado_codigo_by_desc,
    exists_estudiante,
    estudiante_activo,
    exists_curso,
    curso_activo,
    exists_docente,
    docente_activo,
    docente_imparte_curso,
    exists_matricula,
)


def validar_matricula_data(
    *,
    carnet: str,
    curso_cod: int,
    docente_cod: int,
    fecha: str,
    periodo: int,
) -> dict:
    carnet = (carnet or "").strip()
    if not carnet:
        raise ValidationError("Carnet requerido.")

    try:
        curso_cod = int(curso_cod)
    except Exception:
        raise ValidationError("Curso inválido.")

    try:
        docente_cod = int(docente_cod)
    except Exception:
        raise ValidationError("Docente inválido.")

    try:
        periodo = int(periodo)
    except Exception:
        raise ValidationError("Periodo inválido.")

    fecha = (fecha or "").strip()
    if not fecha:
        raise ValidationError("Fecha requerida (usa el calendario).")

    # Esperamos YYYY-MM-DD (como la UI)
    try:
        y, m, d = [int(x) for x in fecha.split("-")]
        fecha_dt = _dt.date(y, m, d)
    except Exception:
        raise ValidationError("Formato de fecha inválido. Usa YYYY-MM-DD.")

    if fecha_dt < _dt.date.today():
        raise ValidationError("La fecha no puede ser menor a hoy.")

    return {
        "carnet": carnet,
        "curso_cod": curso_cod,
        "docente_cod": docente_cod,
        "periodo": periodo,
        "fecha_dt": fecha_dt,
    }


def validar_matricula_reglas(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    curso_cod: int,
    docente_cod: int,
    periodo: int,
) -> dict:
    # tabla preparada
    assert_matricula_schema_ready(conn)

    # existencia y estado
    if not exists_estudiante(conn, carnet):
        raise ValidationError("El estudiante no existe.")
    if not estudiante_activo(conn, carnet):
        raise ValidationError("El estudiante no está Activo.")

    if not exists_curso(conn, curso_cod):
        raise ValidationError("El curso no existe.")
    if not curso_activo(conn, curso_cod):
        raise ValidationError("El curso no está Activo.")

    if not exists_docente(conn, docente_cod):
        raise ValidationError("El docente no existe.")
    if not docente_activo(conn, docente_cod):
        raise ValidationError("El docente no está Activo.")

    # docente asignado a curso
    if not docente_imparte_curso(conn, curso_cod, docente_cod):
        raise ValidationError("El docente seleccionado no está asignado a ese curso.")

    # unicidad
    if exists_matricula(conn, carnet, curso_cod, periodo):
        raise ValidationError("Ya existe una matrícula para ese estudiante, curso y periodo.")

    estado_activo = get_estado_codigo_by_desc(conn, "Activo")
    return {"estado_codigo": estado_activo}


def validar_cambio_estado(conn: pyodbc.Connection, *, nuevo_estado: str) -> int:
    nuevo_estado = (nuevo_estado or "").strip()
    if not nuevo_estado:
        raise ValidationError("Estado requerido.")

    # La UI manda "Activo"/"Inactivo"
    try:
        return get_estado_codigo_by_desc(conn, nuevo_estado)
    except Exception:
        raise ValidationError(f"Estado inválido: {nuevo_estado}")