# app/services/cursos_service.py
from __future__ import annotations

import pyodbc

from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.cursos_repo import (
    exists_materia_descripcion,
    exists_materia_descripcion_programa,
)


def validar_curso_data(
    *,
    descripcion: str,
    curso_cod: int,
    precio: str,              # NUEVO
    estado_codigo: int,
) -> dict:
    descripcion = (descripcion or "").strip()
    if not descripcion:
        raise ValidationError("La descripción del curso (materia) es requerida.")

    try:
        curso_cod = int(curso_cod)
    except Exception:
        raise ValidationError("Programa inválido (Curso_Cod).")

    # NUEVO: validar precio
    precio_txt = (precio or "").strip()
    try:
        precio_val = float(precio_txt.replace(",", ""))
    except Exception:
        raise ValidationError("Precio inválido (use número, ejemplo 23500 o 23500.00).")

    if precio_val < 0:
        raise ValidationError("El precio no puede ser negativo.")

    try:
        estado_codigo = int(estado_codigo)
    except Exception:
        raise ValidationError("Estado inválido.")

    return {
        "descripcion": descripcion,
        "curso_cod": curso_cod,
        "precio": precio_val,          # NUEVO
        "estado_codigo": estado_codigo,
    }


def validar_curso_unicidad(
    conn: pyodbc.Connection,
    *,
    materia_cod: int | None,
    descripcion: str,
    curso_cod: int,
) -> None:
    """
    Anti-duplicados (Cursos/Materias).

    Reglas aplicadas:
    1) Descripción NO debe repetirse en Materias
    2) y/o (Descripción + Programa) tampoco debe repetirse

    En UPDATE excluye el mismo Materia_Cod.
    """
    exclude = int(materia_cod) if materia_cod is not None else None

    # Regla 1 (más estricta)
    if exists_materia_descripcion(conn, descripcion, exclude_materia_cod=exclude):
        raise ValidationError("Ya existe una materia con esa descripción.")

    # Regla 2 (extra seguridad)
    if exists_materia_descripcion_programa(
        conn,
        descripcion,
        int(curso_cod),
        exclude_materia_cod=exclude,
    ):
        raise ValidationError("Ya existe esa materia asociada a ese programa.")