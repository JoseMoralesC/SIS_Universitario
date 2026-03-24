# app/core/db.py
# Módulo para manejar la conexión a la base de datos SQL Server usando pyodbc

from __future__ import annotations

import pyodbc

from app.core.config import (
    DB_SERVER,
    DB_NAME,
    DB_DRIVER,
    DB_APP_USER,
    DB_APP_PASS,
)


# =========================================================
# Construcción de connection string
# =========================================================
def build_conn_str(usuario: str, contra: str) -> str:
    return (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={usuario};"
        f"PWD={contra};"
        "TrustServerCertificate=yes;"
    )


# =========================================================
# Conexión genérica (legacy)
# =========================================================
def connect(usuario: str, contra: str, timeout: int = 15):
    """
    Conexión directa usando credenciales proporcionadas.

    Este método se mantiene por compatibilidad,
    pero ya no se usará para autenticación del sistema.
    """
    conn_str = build_conn_str(usuario, contra)
    return pyodbc.connect(conn_str, timeout=timeout)


# =========================================================
# Conexión técnica de la aplicación (NUEVO)
# =========================================================
def connect_app(timeout: int = 15):
    """
    Conexión usando la cuenta técnica definida en config.py.

    Este es el método que debe usar todo el sistema
    para consultas de negocio y seguridad.
    """
    if not DB_APP_USER or not DB_APP_PASS:
        raise ValueError(
            "Las credenciales de la cuenta técnica (DB_APP_USER / DB_APP_PASS) "
            "no están configuradas en app/core/config.py"
        )

    conn_str = build_conn_str(DB_APP_USER, DB_APP_PASS)
    return pyodbc.connect(conn_str, timeout=timeout)


# =========================================================
# Helper opcional para uso seguro
# =========================================================
def get_connection(use_app: bool = True, usuario: str | None = None, contra: str | None = None):
    """
    Helper flexible para obtener conexión.

    - use_app=True  -> usa conexión técnica (recomendado)
    - use_app=False -> usa credenciales explícitas
    """
    if use_app:
        return connect_app()

    if not usuario or not contra:
        raise ValueError("Debe proporcionar usuario y contraseña para conexión directa.")

    return connect(usuario, contra)