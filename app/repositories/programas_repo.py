# app/repositories/programas_repo.py
from __future__ import annotations
import pyodbc


def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute("SELECT Estado_Codigo, Estado_Desc FROM dbo.Estado_General ORDER BY Estado_Codigo;")
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def list_programas_join(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid:
    (Curso_Cod, Descripcion, Horario, Precio_Matricula, Estado_Desc)
    """
    sql = """
    SELECT
        cp.Curso_Cod,
        cp.Descripcion,
        cp.Horario,
        cp.Precio_Matricula,
        eg.Estado_Desc AS Estado
    FROM dbo.Cursos_Programas cp
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = cp.Estado_Codigo
    ORDER BY cp.Curso_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def next_curso_cod(conn: pyodbc.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT ISNULL(MAX(Curso_Cod), 0) + 1 FROM dbo.Cursos_Programas;")
    return int(cur.fetchone()[0])


def insert_programa(
    conn: pyodbc.Connection,
    curso_cod: int,
    descripcion: str,
    horario: str | None,
    precio_matricula: float,
    estado_codigo: int,
):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Cursos_Programas
            (Curso_Cod, Descripcion, Horario, Precio_Matricula, Estado_Codigo)
        VALUES
            (?, ?, ?, ?, ?);
        """,
        (curso_cod, descripcion, horario, precio_matricula, estado_codigo),
    )
    conn.commit()


def update_programa(
    conn: pyodbc.Connection,
    curso_cod: int,
    descripcion: str,
    horario: str | None,
    precio_matricula: float,
    estado_codigo: int,
):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Cursos_Programas
        SET Descripcion = ?,
            Horario = ?,
            Precio_Matricula = ?,
            Estado_Codigo = ?
        WHERE Curso_Cod = ?;
        """,
        (descripcion, horario, precio_matricula, estado_codigo, curso_cod),
    )
    conn.commit()


def delete_programa(conn: pyodbc.Connection, curso_cod: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.Cursos_Programas WHERE Curso_Cod = ?;", (curso_cod,))
    conn.commit()