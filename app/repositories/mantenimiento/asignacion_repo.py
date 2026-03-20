from __future__ import annotations

import pyodbc


# =========================================================
# LOOKUPS
# =========================================================

def fetch_programas_activos(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            cp.Curso_Cod,
            cp.Descripcion
        FROM dbo.Cursos_Programas cp
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = cp.Estado_Codigo
        WHERE eg.Estado_Desc <> 'Inactivo'
        ORDER BY cp.Curso_Cod;
        """
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_docentes_activos(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Docentes d
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = d.Estado_Codigo
        WHERE eg.Estado_Desc <> 'Inactivo'
        ORDER BY d.Nombre_Completo;
        """
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


# =========================================================
# VALIDACIONES DE EXISTENCIA
# =========================================================

def exists_programa(conn: pyodbc.Connection, curso_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT TOP 1 1 FROM dbo.Cursos_Programas WHERE Curso_Cod = ?;",
        (int(curso_cod),),
    )
    return cur.fetchone() is not None


def exists_docente(conn: pyodbc.Connection, docente_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT TOP 1 1 FROM dbo.Docentes WHERE Docente_Cod = ?;",
        (int(docente_cod),),
    )
    return cur.fetchone() is not None


# =========================================================
# LISTADO GRID
# =========================================================

def list_asignaciones(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid:
    (IdLogico, Curso_Cod, Programa, Docente_Cod, Docente)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            cd.Curso_Cod,
            cp.Descripcion AS Programa,
            cd.Docente_Cod,
            d.Nombre_Completo AS Docente
        FROM dbo.Curso_Docente cd
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = cd.Curso_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = cd.Docente_Cod
        ORDER BY cd.Curso_Cod, d.Nombre_Completo;
        """
    )

    rows: list[tuple] = []
    for curso_cod, programa_desc, docente_cod, docente_nombre in cur.fetchall():
        id_logico = f"{int(curso_cod)}|{int(docente_cod)}"
        rows.append(
            (
                id_logico,
                int(curso_cod),
                str(programa_desc),
                int(docente_cod),
                str(docente_nombre),
            )
        )
    return rows


def list_docentes_por_programa(
    conn: pyodbc.Connection,
    curso_cod: int,
) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Curso_Docente cd
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = cd.Docente_Cod
        WHERE cd.Curso_Cod = ?
        ORDER BY d.Nombre_Completo;
        """,
        (int(curso_cod),),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


# =========================================================
# DUPLICADOS
# =========================================================

def exists_asignacion(
    conn: pyodbc.Connection,
    curso_cod: int,
    docente_cod: int,
) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Curso_Docente
        WHERE Curso_Cod = ?
          AND Docente_Cod = ?;
        """,
        (int(curso_cod), int(docente_cod)),
    )
    return cur.fetchone() is not None


# =========================================================
# CRUD
# =========================================================

def insert_asignacion(
    conn: pyodbc.Connection,
    curso_cod: int,
    docente_cod: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Curso_Docente (Curso_Cod, Docente_Cod)
        VALUES (?, ?);
        """,
        (int(curso_cod), int(docente_cod)),
    )
    conn.commit()


def update_asignacion(
    conn: pyodbc.Connection,
    curso_cod_original: int,
    docente_cod_original: int,
    curso_cod_nuevo: int,
    docente_cod_nuevo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Curso_Docente
        SET Curso_Cod = ?,
            Docente_Cod = ?
        WHERE Curso_Cod = ?
          AND Docente_Cod = ?;
        """,
        (
            int(curso_cod_nuevo),
            int(docente_cod_nuevo),
            int(curso_cod_original),
            int(docente_cod_original),
        ),
    )

    if cur.rowcount == 0:
        raise ValueError("No existe la asignación seleccionada para actualizar.")

    conn.commit()


def delete_asignacion(
    conn: pyodbc.Connection,
    curso_cod: int,
    docente_cod: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM dbo.Curso_Docente
        WHERE Curso_Cod = ?
          AND Docente_Cod = ?;
        """,
        (int(curso_cod), int(docente_cod)),
    )

    if cur.rowcount == 0:
        raise ValueError("No existe la asignación seleccionada para eliminar.")

    conn.commit()