# app/services/estudiantes_service.py
from __future__ import annotations


class ValidationError(Exception):
    pass


def validar_estudiante_data(
    *,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str | None,
    telefono: str | None,
    estado_codigo: int,
) -> dict:
    carnet = (carnet or "").strip()
    identificacion = (identificacion or "").strip()
    nombre_completo = (nombre_completo or "").strip()

    direccion = (direccion or "").strip() if direccion is not None else None
    telefono = (telefono or "").strip() if telefono is not None else None

    if not carnet:
        raise ValidationError("El Carnet es requerido.")
    if len(carnet) > 15:
        raise ValidationError("Carnet demasiado largo (máximo 15 caracteres).")

    if not identificacion:
        raise ValidationError("La identificación es requerida.")
    if len(identificacion) > 20:
        raise ValidationError("Identificación demasiado larga (máximo 20 caracteres).")

    if not nombre_completo:
        raise ValidationError("El nombre completo es requerido.")
    if len(nombre_completo) > 120:
        raise ValidationError("Nombre completo demasiado largo (máximo 120 caracteres).")

    # NULLables
    if direccion == "":
        direccion = None
    if telefono == "":
        telefono = None

    if direccion is not None and len(direccion) > 200:
        raise ValidationError("Dirección demasiado larga (máximo 200 caracteres).")
    if telefono is not None and len(telefono) > 20:
        raise ValidationError("Teléfono demasiado largo (máximo 20 caracteres).")

    try:
        estado_codigo = int(estado_codigo)
    except Exception:
        raise ValidationError("Estado inválido.")

    return {
        "carnet": carnet,
        "identificacion": identificacion,
        "nombre_completo": nombre_completo,
        "direccion": direccion,
        "telefono": telefono,
        "estado_codigo": estado_codigo,
    }