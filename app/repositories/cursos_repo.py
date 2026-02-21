# app/repositories/cursos_repo.py
from __future__ import annotations
import pyodbc


def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute("SELECT Estado_Codigo, Estado_Desc FROM dbo.Estado_General ORDER BY Estado_Codigo;")
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_programas(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    """
    Programas = dbo.Cursos_Programas (Curso_Cod, Descripcion)
    """
    cur = conn.cursor()
    cur.execute("SELECT Curso_Cod, Descripcion FROM dbo.Cursos_Programas ORDER BY Curso_Cod;")
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def list_cursos_join(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid:
    (Materia_Cod, Materia_Desc, Curso_Cod, Programa_Desc, Estado_Desc)
    """
    sql = """
    SELECT
        m.Materia_Cod,
        m.Descripcion AS Materia_Desc,
        m.Curso_Cod,
        cp.Descripcion AS Programa_Desc,
        eg.Estado_Desc AS Estado_Desc
    FROM dbo.Materias m
    LEFT JOIN dbo.Cursos_Programas cp ON cp.Curso_Cod = m.Curso_Cod
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = m.Estado_Codigo
    ORDER BY m.Materia_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def next_materia_cod(conn: pyodbc.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT ISNULL(MAX(Materia_Cod), 0) + 1 FROM dbo.Materias;")
    return int(cur.fetchone()[0])


def insert_curso(
    conn: pyodbc.Connection,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    estado_codigo: int,
):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Materias (Materia_Cod, Descripcion, Curso_Cod, Estado_Codigo)
        VALUES (?, ?, ?, ?);
        """,
        (materia_cod, descripcion, curso_cod, estado_codigo),
    )
    conn.commit()


def update_curso(
    conn: pyodbc.Connection,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    estado_codigo: int,
):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Materias
        SET Descripcion = ?,
            Curso_Cod = ?,
            Estado_Codigo = ?
        WHERE Materia_Cod = ?;
        """,
        (descripcion, curso_cod, estado_codigo, materia_cod),
    )
    conn.commit()


def delete_curso(conn: pyodbc.Connection, materia_cod: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.Materias WHERE Materia_Cod = ?;", (materia_cod,))
    conn.commit()