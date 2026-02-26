# app/core/error_handler.py
from __future__ import annotations

import traceback
import pyodbc
import tkinter as tk

from app.core.exceptions import ValidationError
from app.ui.components.error_dialog import ErrorDialog


def _format_details(exc: Exception) -> str:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return tb.strip()


def _friendly_db_message(exc: Exception) -> tuple[str, str]:
    """
    Devuelve (mensaje_usuario, detalles).
    - No mostramos crudo el error SQL al usuario por defecto.
    - Detalles quedan para el panel "Ver detalles".
    """
    details = _format_details(exc)

    # Integridad / duplicados
    if isinstance(exc, pyodbc.IntegrityError):
        # Mensaje genérico (no dependemos del texto exacto del driver)
        return (
            "No se pudo completar la operación por una restricción de integridad.\n"
            "Revise que no existan valores duplicados y que los datos sean válidos.",
            details,
        )

    if isinstance(exc, pyodbc.Error):
        return (
            "No se pudo completar la operación por un problema de base de datos.\n"
            "Verifique su conexión e intente nuevamente.",
            details,
        )

    return ("Ocurrió un error inesperado. Intente nuevamente.", details)


def show_info(parent: tk.Misc, title: str, message: str):
    ErrorDialog(parent, title=title, message=message, details=None, level="info").wait_window()


def show_warning(parent: tk.Misc, title: str, message: str):
    ErrorDialog(parent, title=title, message=message, details=None, level="warning").wait_window()


def show_error(parent: tk.Misc, title: str, message: str, *, details: str | None = None):
    ErrorDialog(parent, title=title, message=message, details=details, level="error").wait_window()


def handle_exception(parent: tk.Misc, exc: Exception, *, context: str = "Operación"):
    """
    Capa protectora UI:
    - ValidationError => warning limpio
    - pyodbc => error DB amigable
    - otros => error genérico + detalles
    """
    if isinstance(exc, ValidationError):
        show_warning(parent, "Validación", str(exc))
        return

    msg, details = _friendly_db_message(exc)
    show_error(parent, f"{context} - Error", msg, details=details)
# al final de app/core/error_handler.py
from app.ui.components.confirm_dialog import show_confirm  # noqa: F401    