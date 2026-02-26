# app/repositories/auditoria_repo.py
# Repositorio: inserta y consulta eventos en dbo.Auditoria

from __future__ import annotations

import pyodbc


def insert_auditoria(
    conn: pyodbc.Connection,
    *,
    codigo_usuario: int,
    movimiento_cod: int,
) -> None:
    """Inserta un registro en dbo.Auditoria."""
    sql = (
        "INSERT INTO dbo.Auditoria (Codigo_Usuario, Fecha_Movimiento, Movimiento_Cod) "
        "VALUES (?, SYSDATETIME(), ?);"
    )
    cur = conn.cursor()
    cur.execute(sql, (codigo_usuario, int(movimiento_cod)))
    conn.commit()


def list_auditoria_top(conn: pyodbc.Connection, top: int = 100):
    """Devuelve los últimos N movimientos (más recientes primero)."""
    sql = (
        "SELECT TOP (?) Auditoria_Id, Codigo_Usuario, Fecha_Movimiento, Movimiento_Cod "
        "FROM dbo.Auditoria ORDER BY Auditoria_Id DESC;"
    )
    cur = conn.cursor()
    cur.execute(sql, (int(top),))
    return cur.fetchall()
