# app/core/exceptions.py
from __future__ import annotations


class ValidationError(Exception):
    """Error de validación (reglas de negocio / datos de entrada)."""
    pass