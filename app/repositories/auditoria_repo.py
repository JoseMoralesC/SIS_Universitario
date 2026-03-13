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
    """
    Inserta un registro en dbo.Auditoria.

    Parámetros
    ----------
    conn : pyodbc.Connection
        Conexión activa a SQL Server
    codigo_usuario : int
        Usuario que ejecuta el movimiento
    movimiento_cod : int
        Código del movimiento definido en core.auditoria.Mov
    """
    try:
        sql = """
        INSERT INTO dbo.Auditoria
        (
            Codigo_Usuario,
            Fecha_Movimiento,
            Movimiento_Cod
        )
        VALUES
        (
            ?,
            SYSDATETIME(),
            ?
        );
        """

        cur = conn.cursor()
        cur.execute(sql, (codigo_usuario, int(movimiento_cod)))
        conn.commit()

    except pyodbc.Error as e:
        # No detenemos el sistema por fallos de auditoría
        print("Error registrando auditoría:", e)


def list_auditoria_top(
    conn: pyodbc.Connection,
    top: int = 100
):
    """
    Devuelve los últimos N movimientos registrados.
    """

    sql = """
    SELECT TOP (?)
        Auditoria_Id,
        Codigo_Usuario,
        Fecha_Movimiento,
        Movimiento_Cod
    FROM dbo.Auditoria
    ORDER BY Auditoria_Id DESC;
    """

    cur = conn.cursor()
    cur.execute(sql, (int(top),))

    return cur.fetchall()