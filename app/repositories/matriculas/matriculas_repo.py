# app/repositories/matriculas/matriculas_repo.py
from __future__ import annotations

import datetime as _dt
import pyodbc


# -----------------------------
# Helpers
# -----------------------------
def _has_column(conn: pyodbc.Connection, table: str, col: str) -> bool:
    sql = """
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ? AND COLUMN_NAME = ?;
    """
    cur = conn.cursor()
    cur.execute(sql, (table, col))
    return cur.fetchone() is not None


def assert_matricula_schema_ready(conn: pyodbc.Connection) -> None:
    """
    Asegura que Matricula_Curso tenga columnas necesarias para Entregable #3:
    - Fecha_Matricula
    - Docente_Cod
    """
    missing: list[str] = []
    if not _has_column(conn, "Matricula_Curso", "Fecha_Matricula"):
        missing.append("Fecha_Matricula")
    if not _has_column(conn, "Matricula_Curso", "Docente_Cod"):
        missing.append("Docente_Cod")

    if missing:
        raise RuntimeError(
            "La tabla dbo.Matricula_Curso no tiene columnas requeridas para Entregable #3: "
            + ", ".join(missing)
            + ". Ejecuta el script/ALTER correspondiente en tu BD."
        )


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


def exists_estudiante(conn: pyodbc.Connection, carnet: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dbo.Estudiantes WHERE Carnet = ?;", (carnet,))
    return cur.fetchone() is not None


def estudiante_activo(conn: pyodbc.Connection, carnet: str) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM dbo.Estudiantes WHERE Carnet = ? AND Estado_Codigo = ?;",
        (carnet, activo),
    )
    return cur.fetchone() is not None


def exists_curso(conn: pyodbc.Connection, curso_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dbo.Cursos_Programas WHERE Curso_Cod = ?;", (curso_cod,))
    return cur.fetchone() is not None


def curso_activo(conn: pyodbc.Connection, curso_cod: int) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM dbo.Cursos_Programas WHERE Curso_Cod = ? AND Estado_Codigo = ?;",
        (curso_cod, activo),
    )
    return cur.fetchone() is not None


def exists_docente(conn: pyodbc.Connection, docente_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dbo.Docentes WHERE Docente_Cod = ?;", (docente_cod,))
    return cur.fetchone() is not None


def docente_activo(conn: pyodbc.Connection, docente_cod: int) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM dbo.Docentes WHERE Docente_Cod = ? AND Estado_Codigo = ?;",
        (docente_cod, activo),
    )
    return cur.fetchone() is not None


def docente_imparte_curso(conn: pyodbc.Connection, curso_cod: int, docente_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM dbo.Curso_Docente WHERE Curso_Cod = ? AND Docente_Cod = ?;",
        (curso_cod, docente_cod),
    )
    return cur.fetchone() is not None


def exists_matricula(conn: pyodbc.Connection, carnet: str, curso_cod: int, periodo: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM dbo.Matricula_Curso WHERE Carnet = ? AND Curso_Cod = ? AND Periodo = ?;",
        (carnet, curso_cod, periodo),
    )
    return cur.fetchone() is not None


# -----------------------------
# Lookups
# -----------------------------
def fetch_estudiantes_activos(conn: pyodbc.Connection) -> list[tuple[str, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Carnet, Nombre_Completo
        FROM dbo.Estudiantes
        WHERE Estado_Codigo = ?
        ORDER BY Nombre_Completo;
        """,
        (activo,),
    )
    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]


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
        (activo,),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_docentes_activos(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Docente_Cod, Nombre_Completo
        FROM dbo.Docentes
        WHERE Estado_Codigo = ?
        ORDER BY Nombre_Completo;
        """,
        (activo,),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_docentes_por_curso(conn: pyodbc.Connection, curso_cod: int) -> list[tuple[int, str]]:
    # Docentes activos que imparten el curso (según Curso_Docente)
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.Docente_Cod, d.Nombre_Completo
        FROM dbo.Curso_Docente cd
        JOIN dbo.Docentes d ON d.Docente_Cod = cd.Docente_Cod
        WHERE cd.Curso_Cod = ? AND d.Estado_Codigo = ?
        ORDER BY d.Nombre_Completo;
        """,
        (int(curso_cod), activo),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        "SELECT Estado_Codigo, Estado_Desc FROM dbo.Estado_General ORDER BY Estado_Codigo;"
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]

def fetch_estudiantes_elegibles_para_curso(conn, *, curso_cod: int, periodo: int) -> list[tuple[str, str]]:
    """
    Devuelve estudiantes activos que NO tienen ninguna matrícula ACTIVA en el periodo dado.
    (Regla global: un estudiante no puede matricularse más de una vez por periodo, aunque sea otro curso)
    """
    cur = conn.cursor()
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur.execute(
        """
        SELECT e.Carnet, e.Nombre_Completo
        FROM dbo.Estudiantes e
        WHERE e.Estado_Codigo = ?
          AND NOT EXISTS (
              SELECT 1
              FROM dbo.Matricula_Curso mc
              WHERE mc.Carnet = e.Carnet
                AND mc.Periodo = ?
                AND mc.Estado_Codigo = ?
          )
        ORDER BY e.Carnet;
        """,
        (int(activo), int(periodo), int(activo)),
    )

    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]

# -----------------------------
# Queries (grids)
# -----------------------------
def list_matriculas(conn: pyodbc.Connection) -> list[tuple]:
    """
    Devuelve filas para el grid principal:
    (Matricula_ID, Estudiante, Curso, Docente, Fecha, Estado)
    """

    assert_matricula_schema_ready(conn)
    cur = conn.cursor()
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur.execute(
        """
        SELECT
            mc.Carnet,
            mc.Curso_Cod,
            mc.Periodo,
            e.Nombre_Completo,
            c.Descripcion,
            mc.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            CONVERT(varchar(10), mc.Fecha_Matricula, 23) AS Fecha_Matricula,
            eg.Estado_Desc
        FROM dbo.Matricula_Curso mc
        JOIN dbo.Estudiantes e ON e.Carnet = mc.Carnet
        JOIN dbo.Cursos_Programas c ON c.Curso_Cod = mc.Curso_Cod
        LEFT JOIN dbo.Docentes d ON d.Docente_Cod = mc.Docente_Cod
        JOIN dbo.Estado_General eg ON eg.Estado_Codigo = mc.Estado_Codigo
        WHERE mc.Estado_Codigo = ?
        ORDER BY mc.Periodo DESC, mc.Curso_Cod, e.Nombre_Completo;
        """,
        (int(activo),)   # <- ESTE ERA EL FALTANTE
    )

    rows: list[tuple] = []
    for carnet, curso_cod, periodo, est_nom, curso_desc, docente_cod, doc_nom, fecha_txt, estado_desc in cur.fetchall():
        matricula_id = f"{str(carnet)}|{int(curso_cod)}|{int(periodo)}"
        docente_txt = ""
        if docente_cod is not None:
            docente_txt = f"{int(docente_cod)} - {str(doc_nom or '')}".strip(" -")
        rows.append(
            (
                matricula_id,
                f"{str(carnet)} - {str(est_nom)}",
                f"{int(curso_cod)} - {str(curso_desc)}",
                docente_txt,
                str(fecha_txt or ""),
                str(estado_desc or ""),
            )
        )
    return rows


def list_matriculas_por_curso(conn: pyodbc.Connection, *, curso_cod: int) -> list[tuple]:
    """
    Misma estructura que list_matriculas, pero filtrado por curso_cod.
    (NO filtra por periodo porque el endpoint actual no lo pide)
    """
    assert_matricula_schema_ready(conn)
    cur = conn.cursor()
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur.execute(
        """
        SELECT
            mc.Carnet,
            mc.Curso_Cod,
            mc.Periodo,
            e.Nombre_Completo,
            c.Descripcion,
            mc.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            CONVERT(varchar(10), mc.Fecha_Matricula, 23) AS Fecha_Matricula,
            eg.Estado_Desc
        FROM dbo.Matricula_Curso mc
        JOIN dbo.Estudiantes e ON e.Carnet = mc.Carnet
        JOIN dbo.Cursos_Programas c ON c.Curso_Cod = mc.Curso_Cod
        LEFT JOIN dbo.Docentes d ON d.Docente_Cod = mc.Docente_Cod
        JOIN dbo.Estado_General eg ON eg.Estado_Codigo = mc.Estado_Codigo
        WHERE mc.Estado_Codigo = ?
          AND mc.Curso_Cod = ?
        ORDER BY mc.Periodo DESC, e.Nombre_Completo;
        """,
        (int(activo), int(curso_cod)),
    )

    rows: list[tuple] = []
    for carnet, curso_cod_db, periodo, est_nom, curso_desc, docente_cod, doc_nom, fecha_txt, estado_desc in cur.fetchall():
        matricula_id = f"{str(carnet)}|{int(curso_cod_db)}|{int(periodo)}"
        docente_txt = ""
        if docente_cod is not None:
            docente_txt = f"{int(docente_cod)} - {str(doc_nom or '')}".strip(" -")

        rows.append(
            (
                matricula_id,
                f"{str(carnet)} - {str(est_nom)}",
                f"{int(curso_cod_db)} - {str(curso_desc)}",
                docente_txt,
                str(fecha_txt or ""),
                str(estado_desc or ""),
            )
        )
    return rows


def reporte_estudiantes_por_curso(conn: pyodbc.Connection, *, curso_cod: int) -> list[tuple]:
    """
    Reporte: estudiantes matriculados en el curso (Periodo, Carnet, Estudiante, Estado).
    """
    assert_matricula_schema_ready(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            mc.Periodo,
            mc.Carnet,
            e.Nombre_Completo,
            eg.Estado_Desc
        FROM dbo.Matricula_Curso mc
        JOIN dbo.Estudiantes e ON e.Carnet = mc.Carnet
        JOIN dbo.Estado_General eg ON eg.Estado_Codigo = mc.Estado_Codigo
        WHERE mc.Curso_Cod = ?
        ORDER BY mc.Periodo DESC, e.Nombre_Completo;
        """,
        (int(curso_cod),),
    )
    return [(int(r[0]), str(r[1]), str(r[2]), str(r[3])) for r in cur.fetchall()]


# -----------------------------
# Commands
# -----------------------------
def insert_matricula(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    curso_cod: int,
    periodo: int,
    docente_cod: int,
    fecha: _dt.date,
    estado_codigo: int,
) -> None:
    assert_matricula_schema_ready(conn)
    sql = """
        INSERT INTO dbo.Matricula_Curso
            (Carnet, Curso_Cod, Periodo, Estado_Codigo, Docente_Cod, Fecha_Matricula)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    cur = conn.cursor()
    cur.execute(sql, (carnet, int(curso_cod), int(periodo), int(estado_codigo), int(docente_cod), fecha))
    conn.commit()


def update_estado_matricula(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    curso_cod: int,
    periodo: int,
    nuevo_estado_codigo: int,
) -> None:
    sql = """
        UPDATE dbo.Matricula_Curso
        SET Estado_Codigo = ?
        WHERE Carnet = ? AND Curso_Cod = ? AND Periodo = ?;
    """
    cur = conn.cursor()
    cur.execute(sql, (int(nuevo_estado_codigo), (carnet or "").strip(), int(curso_cod), int(periodo)))
    conn.commit()


def delete_matricula(conn: pyodbc.Connection, *, carnet: str, curso_cod: int, periodo: int) -> None:
    """
    Borrado lógico: cambia Estado_Codigo a 'Inactivo' (no elimina fila).
    """
    inactivo = get_estado_codigo_by_desc(conn, "Inactivo")
    sql = """
        UPDATE dbo.Matricula_Curso
        SET Estado_Codigo = ?
        WHERE Carnet = ? AND Curso_Cod = ? AND Periodo = ?;
    """
    cur = conn.cursor()
    cur.execute(sql, (int(inactivo), (carnet or "").strip(), int(curso_cod), int(periodo)))
    conn.commit()