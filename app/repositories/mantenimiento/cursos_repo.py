# app/repositories/cursos_repo.py
from __future__ import annotations

import pyodbc


# ==========================
# Lookups
# ==========================

def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        "SELECT Estado_Codigo, Estado_Desc FROM dbo.Estado_General ORDER BY Estado_Codigo;"
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_programas(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    """
    Programas = dbo.Cursos_Programas (Curso_Cod, Descripcion)
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT Curso_Cod, Descripcion FROM dbo.Cursos_Programas ORDER BY Curso_Cod;"
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def get_estado_codigo_by_desc(conn: pyodbc.Connection, estado_desc: str) -> int:
    """
    Obtiene el Estado_Codigo según Estado_Desc (ej: 'Inactivo').
    """
    estado_desc = (estado_desc or "").strip()
    cur = conn.cursor()
    cur.execute(
        "SELECT Estado_Codigo FROM dbo.Estado_General WHERE Estado_Desc = ?;",
        (estado_desc,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Estado no encontrado: {estado_desc}")
    return int(row[0])


# ==========================
# Listado (Grid)
# ==========================

def list_cursos_join(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid:
    (Materia_Cod, Materia_Desc, Curso_Cod, Programa_Desc, Precio, Estado_Desc)
    Incluye todos los estados.
    """
    sql = """
    SELECT
        m.Materia_Cod,
        m.Descripcion AS Materia_Desc,
        m.Curso_Cod,
        cp.Descripcion AS Programa_Desc,
        m.Precio,
        eg.Estado_Desc AS Estado_Desc
    FROM dbo.Materias m
    LEFT JOIN dbo.Cursos_Programas cp ON cp.Curso_Cod = m.Curso_Cod
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = m.Estado_Codigo
    ORDER BY m.Materia_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def list_cursos_join_activos(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid: NO mostrar registros Inactivos.
    """
    sql = """
    SELECT
        m.Materia_Cod,
        m.Descripcion AS Materia_Desc,
        m.Curso_Cod,
        cp.Descripcion AS Programa_Desc,
        m.Precio,
        eg.Estado_Desc AS Estado_Desc
    FROM dbo.Materias m
    LEFT JOIN dbo.Cursos_Programas cp ON cp.Curso_Cod = m.Curso_Cod
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = m.Estado_Codigo
    WHERE eg.Estado_Desc <> 'Inactivo'
    ORDER BY m.Materia_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


# ==========================
# Util
# ==========================

def next_materia_cod(conn: pyodbc.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT ISNULL(MAX(Materia_Cod), 0) + 1 FROM dbo.Materias;")
    return int(cur.fetchone()[0])


# ==========================
# CRUD
# ==========================

def insert_curso(
    conn: pyodbc.Connection,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    precio: float,          # NUEVO
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Materias (Materia_Cod, Descripcion, Curso_Cod, Precio, Estado_Codigo)
        VALUES (?, ?, ?, ?, ?);
        """,
        (int(materia_cod), descripcion, int(curso_cod), float(precio), int(estado_codigo)),
    )
    conn.commit()


def update_curso(
    conn: pyodbc.Connection,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    precio: float,          # NUEVO
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Materias
        SET Descripcion = ?,
            Curso_Cod = ?,
            Precio = ?,
            Estado_Codigo = ?
        WHERE Materia_Cod = ?;
        """,
        (descripcion, int(curso_cod), float(precio), int(estado_codigo), int(materia_cod)),
    )
    conn.commit()


def delete_curso(conn: pyodbc.Connection, materia_cod: int) -> None:
    """
    LEGACY: borrado físico. No debería usarse en UI.
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.Materias WHERE Materia_Cod = ?;", (int(materia_cod),))
    conn.commit()


def soft_delete_curso(conn: pyodbc.Connection, materia_cod: int) -> None:
    """
    Borrado lógico: asigna Estado_Codigo correspondiente a 'Inactivo'.
    """
    inactivo_cod = get_estado_codigo_by_desc(conn, "Inactivo")

    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.Materias SET Estado_Codigo = ? WHERE Materia_Cod = ?;",
        (int(inactivo_cod), int(materia_cod)),
    )
    if cur.rowcount == 0:
        raise ValueError("No existe el curso seleccionado para eliminar.")
    conn.commit()


# ==========================
# Unicidad (anti-duplicados)
# ==========================

def exists_materia_descripcion(
    conn: pyodbc.Connection,
    descripcion: str,
    exclude_materia_cod: int | None = None,
) -> bool:
    """
    True si ya existe otra Materia con la misma Descripcion.
    """
    descripcion = (descripcion or "").strip()
    cur = conn.cursor()

    if exclude_materia_cod is None:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Materias WHERE Descripcion = ?;",
            (descripcion,),
        )
    else:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Materias WHERE Descripcion = ? AND Materia_Cod <> ?;",
            (descripcion, int(exclude_materia_cod)),
        )
    return cur.fetchone() is not None


def exists_materia_descripcion_programa(
    conn: pyodbc.Connection,
    descripcion: str,
    curso_cod: int,
    exclude_materia_cod: int | None = None,
) -> bool:
    """
    True si ya existe otra Materia con misma (Descripcion + Curso_Cod).
    """
    descripcion = (descripcion or "").strip()
    cur = conn.cursor()

    if exclude_materia_cod is None:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Materias WHERE Descripcion = ? AND Curso_Cod = ?;",
            (descripcion, int(curso_cod)),
        )
    else:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Materias
            WHERE Descripcion = ? AND Curso_Cod = ? AND Materia_Cod <> ?;
            """,
            (descripcion, int(curso_cod), int(exclude_materia_cod)),
        )
    return cur.fetchone() is not None