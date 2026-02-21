# app/services/programas_service.py
from __future__ import annotations


class ValidationError(Exception):
    pass


def validar_programa_data(
    *,
    descripcion: str,
    horario: str | None,
    precio_matricula: str,
    estado_codigo: int,
) -> dict:
    descripcion = (descripcion or "").strip()
    horario = (horario or "").strip() if horario is not None else None
    precio_txt = (precio_matricula or "").strip()

    if not descripcion:
        raise ValidationError("La descripción es requerida.")

    # Horario puede ser NULL en DB
    if horario == "":
        horario = None

    try:
        precio = float(precio_txt)
    except Exception:
        raise ValidationError("Precio Matrícula inválido (use número, ejemplo 12500 o 12500.50).")

    if precio < 0:
        raise ValidationError("Precio Matrícula no puede ser negativo.")

    try:
        estado_codigo = int(estado_codigo)
    except Exception:
        raise ValidationError("Estado inválido.")

    return {
        "descripcion": descripcion,
        "horario": horario,
        "precio_matricula": precio,
        "estado_codigo": estado_codigo,
    }