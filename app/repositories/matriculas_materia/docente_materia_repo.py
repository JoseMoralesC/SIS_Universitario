# app/repositories/matriculas_materia/docente_materia_repo.py
from __future__ import annotations

import pyodbc


# =========================================================
# Helpers
# =========================================================
def get_estado_codigo_by_desc(conn: pyodbc.Connection, estado_desc: str) -> int:
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


def exists_docente(conn: pyodbc.Connection, docente_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT TOP 1 1 FROM dbo.Docentes WHERE Docente_Cod = ?;",
        (int(docente_cod),),
    )
    return cur.fetchone() is not None


def exists_materia(conn: pyodbc.Connection, materia_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT TOP 1 1 FROM dbo.Materias WHERE Materia_Cod = ?;",
        (int(materia_cod),),
    )
    return cur.fetchone() is not None


def docente_activo(conn: pyodbc.Connection, docente_cod: int) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Docentes
        WHERE Docente_Cod = ?
          AND Estado_Codigo = ?;
        """,
        (int(docente_cod), int(activo)),
    )
    return cur.fetchone() is not None


def materia_activa(conn: pyodbc.Connection, materia_cod: int) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Materias
        WHERE Materia_Cod = ?
          AND Estado_Codigo = ?;
        """,
        (int(materia_cod), int(activo)),
    )
    return cur.fetchone() is not None


def docente_y_materia_mismo_curso(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    materia_cod: int,
) -> bool:
    """
    Regla clave:
    Un docente solo puede asignarse a materias del curso/carrera
    al que ya está asociado en dbo.Curso_Docente.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Materias m
        INNER JOIN dbo.Curso_Docente cd
            ON cd.Curso_Cod = m.Curso_Cod
        WHERE m.Materia_Cod = ?
          AND cd.Docente_Cod = ?;
        """,
        (int(materia_cod), int(docente_cod)),
    )
    return cur.fetchone() is not None


def exists_docente_materia(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    materia_cod: int,
) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Docente_Materia
        WHERE Docente_Cod = ?
          AND Materia_Cod = ?;
        """,
        (int(docente_cod), int(materia_cod)),
    )
    return cur.fetchone() is not None


def docente_materia_activa(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    materia_cod: int,
) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Docente_Materia
        WHERE Docente_Cod = ?
          AND Materia_Cod = ?
          AND Estado_Codigo = ?;
        """,
        (int(docente_cod), int(materia_cod), int(activo)),
    )
    return cur.fetchone() is not None


# =========================================================
# Lookups
# =========================================================
def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        "SELECT Estado_Codigo, Estado_Desc FROM dbo.Estado_General ORDER BY Estado_Codigo;"
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_cursos_activos(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Curso_Cod, Descripcion
        FROM dbo.Cursos_Programas
        WHERE Estado_Codigo = ?
        ORDER BY Curso_Cod;
        """,
        (int(activo),),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_docentes_por_curso(conn: pyodbc.Connection, *, curso_cod: int) -> list[tuple[int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Curso_Docente cd
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = cd.Docente_Cod
        WHERE cd.Curso_Cod = ?
          AND d.Estado_Codigo = ?
        ORDER BY d.Nombre_Completo;
        """,
        (int(curso_cod), int(activo)),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_materias_por_curso(conn: pyodbc.Connection, *, curso_cod: int) -> list[tuple[int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            m.Materia_Cod,
            m.Descripcion
        FROM dbo.Materias m
        WHERE m.Curso_Cod = ?
          AND m.Estado_Codigo = ?
        ORDER BY m.Materia_Cod;
        """,
        (int(curso_cod), int(activo)),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_materias_disponibles_para_docente(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    curso_cod: int,
) -> list[tuple[int, str]]:
    """
    Devuelve materias activas del curso que aún NO están asignadas
    activamente al docente.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            m.Materia_Cod,
            m.Descripcion
        FROM dbo.Materias m
        WHERE m.Curso_Cod = ?
          AND m.Estado_Codigo = ?
          AND NOT EXISTS (
                SELECT 1
                FROM dbo.Docente_Materia dm
                WHERE dm.Docente_Cod = ?
                  AND dm.Materia_Cod = m.Materia_Cod
                  AND dm.Estado_Codigo = ?
          )
        ORDER BY m.Materia_Cod;
        """,
        (int(curso_cod), int(activo), int(docente_cod), int(activo)),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_docentes_disponibles_para_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
) -> list[tuple[int, str]]:
    """
    Docentes activos que pertenecen al mismo curso de la materia
    y que aún no la tienen activa en Docente_Materia.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Materias m
        INNER JOIN dbo.Curso_Docente cd
            ON cd.Curso_Cod = m.Curso_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = cd.Docente_Cod
        WHERE m.Materia_Cod = ?
          AND d.Estado_Codigo = ?
          AND NOT EXISTS (
                SELECT 1
                FROM dbo.Docente_Materia dm
                WHERE dm.Docente_Cod = d.Docente_Cod
                  AND dm.Materia_Cod = m.Materia_Cod
                  AND dm.Estado_Codigo = ?
          )
        ORDER BY d.Nombre_Completo;
        """,
        (int(materia_cod), int(activo), int(activo)),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


# =========================================================
# Grid / Listados
# =========================================================
def list_docente_materia(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid principal:
    (IdLogico, Curso, Materia, Docente, Estado, Fecha_Registro)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            cp.Curso_Cod,
            cp.Descripcion AS Curso_Desc,
            m.Materia_Cod,
            m.Descripcion AS Materia_Desc,
            d.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            eg.Estado_Desc,
            CONVERT(varchar(19), dm.Fecha_Registro, 120) AS Fecha_Registro
        FROM dbo.Docente_Materia dm
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = dm.Docente_Cod
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = dm.Materia_Cod
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = dm.Estado_Codigo
        ORDER BY cp.Curso_Cod, m.Materia_Cod, d.Nombre_Completo;
        """
    )

    rows: list[tuple] = []
    for curso_cod, curso_desc, materia_cod, materia_desc, docente_cod, docente_nombre, estado_desc, fecha_registro in cur.fetchall():
        id_logico = f"{int(docente_cod)}|{int(materia_cod)}"
        rows.append(
            (
                id_logico,
                f"{int(curso_cod)} - {str(curso_desc)}",
                f"{int(materia_cod)} - {str(materia_desc)}",
                f"{int(docente_cod)} - {str(docente_nombre)}",
                str(estado_desc or ""),
                str(fecha_registro or ""),
            )
        )
    return rows


def list_docente_materia_activos(conn: pyodbc.Connection) -> list[tuple]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            cp.Curso_Cod,
            cp.Descripcion AS Curso_Desc,
            m.Materia_Cod,
            m.Descripcion AS Materia_Desc,
            d.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            eg.Estado_Desc,
            CONVERT(varchar(19), dm.Fecha_Registro, 120) AS Fecha_Registro
        FROM dbo.Docente_Materia dm
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = dm.Docente_Cod
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = dm.Materia_Cod
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = dm.Estado_Codigo
        WHERE dm.Estado_Codigo = ?
        ORDER BY cp.Curso_Cod, m.Materia_Cod, d.Nombre_Completo;
        """,
        (int(activo),),
    )

    rows: list[tuple] = []
    for curso_cod, curso_desc, materia_cod, materia_desc, docente_cod, docente_nombre, estado_desc, fecha_registro in cur.fetchall():
        id_logico = f"{int(docente_cod)}|{int(materia_cod)}"
        rows.append(
            (
                id_logico,
                f"{int(curso_cod)} - {str(curso_desc)}",
                f"{int(materia_cod)} - {str(materia_desc)}",
                f"{int(docente_cod)} - {str(docente_nombre)}",
                str(estado_desc or ""),
                str(fecha_registro or ""),
            )
        )
    return rows


def list_docente_materia_por_curso(conn: pyodbc.Connection, *, curso_cod: int) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            cp.Curso_Cod,
            cp.Descripcion AS Curso_Desc,
            m.Materia_Cod,
            m.Descripcion AS Materia_Desc,
            d.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            eg.Estado_Desc,
            CONVERT(varchar(19), dm.Fecha_Registro, 120) AS Fecha_Registro
        FROM dbo.Docente_Materia dm
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = dm.Docente_Cod
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = dm.Materia_Cod
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = dm.Estado_Codigo
        WHERE cp.Curso_Cod = ?
        ORDER BY m.Materia_Cod, d.Nombre_Completo;
        """,
        (int(curso_cod),),
    )

    rows: list[tuple] = []
    for curso_cod_db, curso_desc, materia_cod, materia_desc, docente_cod, docente_nombre, estado_desc, fecha_registro in cur.fetchall():
        id_logico = f"{int(docente_cod)}|{int(materia_cod)}"
        rows.append(
            (
                id_logico,
                f"{int(curso_cod_db)} - {str(curso_desc)}",
                f"{int(materia_cod)} - {str(materia_desc)}",
                f"{int(docente_cod)} - {str(docente_nombre)}",
                str(estado_desc or ""),
                str(fecha_registro or ""),
            )
        )
    return rows


def list_materias_de_docente(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    solo_activas: bool = True,
) -> list[tuple]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()

    sql = """
        SELECT
            m.Materia_Cod,
            m.Descripcion,
            cp.Curso_Cod,
            cp.Descripcion AS Curso_Desc,
            eg.Estado_Desc
        FROM dbo.Docente_Materia dm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = dm.Materia_Cod
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = dm.Estado_Codigo
        WHERE dm.Docente_Cod = ?
    """
    params: list[int] = [int(docente_cod)]

    if solo_activas:
        sql += " AND dm.Estado_Codigo = ?"
        params.append(int(activo))

    sql += " ORDER BY cp.Curso_Cod, m.Materia_Cod;"

    cur.execute(sql, tuple(params))
    return [
        (int(r[0]), str(r[1]), int(r[2]), str(r[3]), str(r[4]))
        for r in cur.fetchall()
    ]


def list_docentes_de_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
    solo_activas: bool = True,
) -> list[tuple]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()

    sql = """
        SELECT
            d.Docente_Cod,
            d.Nombre_Completo,
            eg.Estado_Desc
        FROM dbo.Docente_Materia dm
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = dm.Docente_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = dm.Estado_Codigo
        WHERE dm.Materia_Cod = ?
    """
    params: list[int] = [int(materia_cod)]

    if solo_activas:
        sql += " AND dm.Estado_Codigo = ?"
        params.append(int(activo))

    sql += " ORDER BY d.Nombre_Completo;"

    cur.execute(sql, tuple(params))
    return [(int(r[0]), str(r[1]), str(r[2])) for r in cur.fetchall()]


# =========================================================
# Commands
# =========================================================
def insert_docente_materia(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    materia_cod: int,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Docente_Materia
            (Docente_Cod, Materia_Cod, Estado_Codigo, Fecha_Registro)
        VALUES (?, ?, ?, SYSDATETIME());
        """,
        (int(docente_cod), int(materia_cod), int(estado_codigo)),
    )
    conn.commit()


def reactivar_docente_materia(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    materia_cod: int,
) -> None:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Docente_Materia
        SET Estado_Codigo = ?
        WHERE Docente_Cod = ?
          AND Materia_Cod = ?;
        """,
        (int(activo), int(docente_cod), int(materia_cod)),
    )
    conn.commit()


def update_estado_docente_materia(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    materia_cod: int,
    nuevo_estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Docente_Materia
        SET Estado_Codigo = ?
        WHERE Docente_Cod = ?
          AND Materia_Cod = ?;
        """,
        (int(nuevo_estado_codigo), int(docente_cod), int(materia_cod)),
    )
    conn.commit()


def delete_docente_materia(
    conn: pyodbc.Connection,
    *,
    docente_cod: int,
    materia_cod: int,
) -> None:
    """
    Borrado lógico.
    """
    inactivo = get_estado_codigo_by_desc(conn, "Inactivo")
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Docente_Materia
        SET Estado_Codigo = ?
        WHERE Docente_Cod = ?
          AND Materia_Cod = ?;
        """,
        (int(inactivo), int(docente_cod), int(materia_cod)),
    )
    conn.commit()