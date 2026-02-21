# app/repositories/estudiantes_repo.py
from __future__ import annotations
import pyodbc


def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute("SELECT Estado_Codigo, Estado_Desc FROM dbo.Estado_General ORDER BY Estado_Codigo;")
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def list_estudiantes_join(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid:
    (Carnet, Identificacion, Nombre_Completo, Direccion, Telefono, Estado_Desc)
    """
    sql = """
    SELECT
        e.Carnet,
        e.Identificacion,
        e.Nombre_Completo,
        e.Direccion,
        e.Telefono,
        eg.Estado_Desc AS Estado
    FROM dbo.Estudiantes e
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = e.Estado_Codigo
    ORDER BY e.Carnet DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def insert_estudiante(
    conn: pyodbc.Connection,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str | None,
    telefono: str | None,
    estado_codigo: int,
):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Estudiantes
            (Carnet, Identificacion, Nombre_Completo, Direccion, Telefono, Estado_Codigo)
        VALUES
            (?, ?, ?, ?, ?, ?);
        """,
        (carnet, identificacion, nombre_completo, direccion, telefono, estado_codigo),
    )
    conn.commit()


def update_estudiante(
    conn: pyodbc.Connection,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str | None,
    telefono: str | None,
    estado_codigo: int,
):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Estudiantes
        SET Identificacion = ?,
            Nombre_Completo = ?,
            Direccion = ?,
            Telefono = ?,
            Estado_Codigo = ?
        WHERE Carnet = ?;
        """,
        (identificacion, nombre_completo, direccion, telefono, estado_codigo, carnet),
    )
    conn.commit()


def delete_estudiante(conn: pyodbc.Connection, carnet: str):
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.Estudiantes WHERE Carnet = ?;", (carnet,))
    conn.commit()