# app/services/docentes_service.py
from __future__ import annotations

import pyodbc

from app.repositories.mantenimiento.docentes_repo import (
    exists_identificacion,
    exists_usuario_docente,
)


from app.core.exceptions import ValidationError


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

    # Validaciones básicas sugeridas (opcionales, pero útiles):
    # - identificación solo dígitos (si aplica a tu formato real)
    # if not identificacion.isdigit():
    #     raise ValidationError("La identificación debe contener solo números.")

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


def validar_docente_unicidad(
    conn: pyodbc.Connection,
    *,
    docente_cod: int | None,
    identificacion: str,
    usuario_docente: str,
) -> None:
    """
    Anti-duplicados:
    - Identificacion única
    - Usuario_Docente único

    En UPDATE excluye el mismo Docente_Cod.
    """
    exclude = int(docente_cod) if docente_cod is not None else None

    if exists_identificacion(conn, identificacion, exclude_docente_cod=exclude):
        raise ValidationError("Ya existe un docente con esa identificación.")

    if exists_usuario_docente(conn, usuario_docente, exclude_docente_cod=exclude):
        raise ValidationError("Ya existe un docente con ese usuario docente.")