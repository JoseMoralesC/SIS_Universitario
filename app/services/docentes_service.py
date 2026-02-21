# app/services/docentes_service.py
from __future__ import annotations


class ValidationError(Exception):
    pass


def validar_docente_data(
    *,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
) -> dict:
    identificacion = (identificacion or "").strip()
    usuario_docente = (usuario_docente or "").strip()
    nombre_completo = (nombre_completo or "").strip()

    if not identificacion:
        raise ValidationError("La identificación es requerida.")
    if not usuario_docente:
        raise ValidationError("El usuario docente es requerido.")
    if not nombre_completo:
        raise ValidationError("El nombre completo es requerido.")

    try:
        estado_codigo = int(estado_codigo)
    except Exception:
        raise ValidationError("Estado inválido.")

    try:
        profesion_cod = int(profesion_cod)
    except Exception:
        raise ValidationError("Profesión inválida.")

    return {
        "identificacion": identificacion,
        "usuario_docente": usuario_docente,
        "nombre_completo": nombre_completo,
        "estado_codigo": estado_codigo,
        "profesion_cod": profesion_cod,
    }