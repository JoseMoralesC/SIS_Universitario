# app/core/db.py
# Modulo para manejar la conexión a la base de datos SQL Server usando pyodbc


import pyodbc
from app.core.config import DB_SERVER, DB_NAME, DB_DRIVER

def build_conn_str(usuario: str, contra: str) -> str:
    return (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={usuario};"
        f"PWD={contra};"
        "TrustServerCertificate=yes;"
    )

def connect(usuario: str, contra: str, timeout: int = 5):
    conn_str = build_conn_str(usuario, contra)
    return pyodbc.connect(conn_str, timeout=timeout)

