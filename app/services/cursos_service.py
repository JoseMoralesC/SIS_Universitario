# app/services/cursos_service.py
from __future__ import annotations


class ValidationError(Exception):
    pass


def validar_curso_data(
    *,
    descripcion: str,
    curso_cod: int,
    estado_codigo: int,
) -> dict:
    descripcion = (descripcion or "").strip()
    if not descripcion:
        raise ValidationError("La descripción del curso (materia) es requerida.")

    try:
        curso_cod = int(curso_cod)
    except Exception:
        raise ValidationError("Programa inválido (Curso_Cod).")

    try:
        estado_codigo = int(estado_codigo)
    except Exception:
        raise ValidationError("Estado inválido.")

    return {
        "descripcion": descripcion,
        "curso_cod": curso_cod,
        "estado_codigo": estado_codigo,
    }