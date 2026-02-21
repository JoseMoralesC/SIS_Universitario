# app/repositories/docentes_repo.py
from __future__ import annotations
import pyodbc


def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute("SELECT Estado_Codigo, Estado_Desc FROM dbo.Estado_General ORDER BY Estado_Codigo;")
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_profesiones(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute("SELECT Profesion_Cod, Descripcion FROM dbo.Profesiones ORDER BY Profesion_Cod;")
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def list_docentes_join(conn: pyodbc.Connection) -> list[tuple]:
    """
    Devuelve filas para el grid con JOIN:
    (Docente_Cod, Identificacion, Usuario_Docente, Nombre_Completo, Estado_Desc, Profesion_Desc)
    """
    sql = """
    SELECT
        d.Docente_Cod,
        d.Identificacion,
        d.Usuario_Docente,
        d.Nombre_Completo,
        eg.Estado_Desc AS Estado,
        p.Descripcion AS Profesion
    FROM dbo.Docentes d
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = d.Estado_Codigo
    LEFT JOIN dbo.Profesiones p     ON p.Profesion_Cod  = d.Profesion_Cod
    ORDER BY d.Docente_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def insert_docente(
    conn,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Docentes
            (Docente_Cod, Identificacion, Usuario_Docente, Nombre_Completo, Estado_Codigo, Profesion_Cod)
        VALUES
            (?, ?, ?, ?, ?, ?);
        """,
        (docente_cod, identificacion, usuario_docente, nombre_completo, estado_codigo, profesion_cod),
    )
    conn.commit()


def update_docente(
    conn: pyodbc.Connection,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
) -> None:
    sql = """
    UPDATE dbo.Docentes
    SET Identificacion = ?,
        Usuario_Docente = ?,
        Nombre_Completo = ?,
        Estado_Codigo = ?,
        Profesion_Cod = ?
    WHERE Docente_Cod = ?;
    """
    cur = conn.cursor()
    cur.execute(sql, identificacion, usuario_docente, nombre_completo, int(estado_codigo), int(profesion_cod), int(docente_cod))
    conn.commit()


def delete_docente(conn: pyodbc.Connection, docente_cod: int) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.Docentes WHERE Docente_Cod = ?;", int(docente_cod))
    conn.commit()

def next_docente_cod(conn) -> int:
    cur = conn.cursor()
    cur.execute("SELECT ISNULL(MAX(Docente_Cod), 0) + 1 FROM dbo.Docentes;")
    return int(cur.fetchone()[0])    