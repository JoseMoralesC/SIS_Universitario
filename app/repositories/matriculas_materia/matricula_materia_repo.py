# app/repositories/matriculas_materia/matricula_materia_repo.py
from __future__ import annotations

import pyodbc


# =========================================================
# Helpers
# =========================================================
def get_estado_codigo_by_desc(conn: pyodbc.Connection, estado_desc: str) -> int:
    estado_desc = (estado_desc or "").strip()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Estado_Codigo
        FROM dbo.Estado_General
        WHERE Estado_Desc = ?;
        """,
        (estado_desc,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Estado no encontrado: {estado_desc}")
    return int(row[0])


def exists_estudiante(conn: pyodbc.Connection, carnet: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Estudiantes
        WHERE Carnet = ?;
        """,
        (str(carnet).strip(),),
    )
    return cur.fetchone() is not None


def estudiante_activo(conn: pyodbc.Connection, carnet: str) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Estudiantes
        WHERE Carnet = ?
          AND Estado_Codigo = ?;
        """,
        (str(carnet).strip(), int(activo)),
    )
    return cur.fetchone() is not None


def exists_materia(conn: pyodbc.Connection, materia_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Materias
        WHERE Materia_Cod = ?;
        """,
        (int(materia_cod),),
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


def exists_docente(conn: pyodbc.Connection, docente_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Docentes
        WHERE Docente_Cod = ?;
        """,
        (int(docente_cod),),
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


def docente_asignado_a_materia(
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


def estudiante_matriculado_en_curso_de_materia(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    materia_cod: int,
    periodo: int,
) -> bool:
    """
    Verifica que el estudiante esté matriculado en el curso/carrera
    al que pertenece la materia, dentro del mismo periodo.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Materias m
        INNER JOIN dbo.Matricula_Curso mc
            ON mc.Curso_Cod = m.Curso_Cod
        WHERE m.Materia_Cod = ?
          AND mc.Carnet = ?
          AND mc.Periodo = ?
          AND mc.Estado_Codigo = ?;
        """,
        (int(materia_cod), str(carnet).strip(), int(periodo), int(activo)),
    )
    return cur.fetchone() is not None


def exists_matricula_materia(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    materia_cod: int,
    periodo: int,
) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Matricula_Materia
        WHERE Carnet = ?
          AND Materia_Cod = ?
          AND Periodo = ?;
        """,
        (str(carnet).strip(), int(materia_cod), int(periodo)),
    )
    return cur.fetchone() is not None


def matricula_materia_activa(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    materia_cod: int,
    periodo: int,
) -> bool:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Matricula_Materia
        WHERE Carnet = ?
          AND Materia_Cod = ?
          AND Periodo = ?
          AND Estado_Codigo = ?;
        """,
        (str(carnet).strip(), int(materia_cod), int(periodo), int(activo)),
    )
    return cur.fetchone() is not None


def count_materias_activas_estudiante_periodo(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    periodo: int,
) -> int:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*)
        FROM dbo.Matricula_Materia
        WHERE Carnet = ?
          AND Periodo = ?
          AND Estado_Codigo = ?;
        """,
        (str(carnet).strip(), int(periodo), int(activo)),
    )
    row = cur.fetchone()
    return int(row[0] or 0)


def fetch_beca_estudiante(conn: pyodbc.Connection, *, carnet: str) -> tuple | None:
    """
    Retorna la beca activa del estudiante si existe:
    (id_beca, nombre_beca, porcentaje_descuento)
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1
            b.id_beca,
            b.nombre_beca,
            b.porcentaje_descuento
        FROM dbo.Becados be
        INNER JOIN dbo.Becas b
            ON b.id_beca = be.id_beca
        WHERE be.carnet = ?
          AND be.Estado_Codigo = ?
          AND b.Estado_Codigo = ?
        ORDER BY be.fecha_aplicacion DESC, be.id_becado DESC;
        """,
        (str(carnet).strip(), int(activo), int(activo)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return (int(row[0]), str(row[1]), int(row[2]))


# =========================================================
# Lookups
# =========================================================
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
        (int(activo),),
    )
    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_periodos_matricula_curso_activos(conn: pyodbc.Connection) -> list[int]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT Periodo
        FROM dbo.Matricula_Curso
        WHERE Estado_Codigo = ?
        ORDER BY Periodo DESC;
        """,
        (int(activo),),
    )
    return [int(r[0]) for r in cur.fetchall()]


def fetch_materias_disponibles_estudiante(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    periodo: int,
) -> list[tuple[int, str, int, str]]:
    """
    Materias activas del curso donde el estudiante está matriculado
    en ese periodo y que aún no tiene activas en Matricula_Materia.
    Retorna:
    (Materia_Cod, Materia_Desc, Curso_Cod, Curso_Desc)
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            m.Materia_Cod,
            m.Descripcion,
            cp.Curso_Cod,
            cp.Descripcion AS Curso_Desc
        FROM dbo.Matricula_Curso mc
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = mc.Curso_Cod
        INNER JOIN dbo.Materias m
            ON m.Curso_Cod = mc.Curso_Cod
        WHERE mc.Carnet = ?
          AND mc.Periodo = ?
          AND mc.Estado_Codigo = ?
          AND m.Estado_Codigo = ?
          AND NOT EXISTS (
                SELECT 1
                FROM dbo.Matricula_Materia mm
                WHERE mm.Carnet = mc.Carnet
                  AND mm.Materia_Cod = m.Materia_Cod
                  AND mm.Periodo = mc.Periodo
                  AND mm.Estado_Codigo = ?
          )
        ORDER BY m.Materia_Cod;
        """,
        (
            str(carnet).strip(),
            int(periodo),
            int(activo),
            int(activo),
            int(activo),
        ),
    )
    return [
        (int(r[0]), str(r[1]), int(r[2]), str(r[3]))
        for r in cur.fetchall()
    ]


def fetch_docentes_disponibles_para_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
) -> list[tuple[int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Docente_Materia dm
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = dm.Docente_Cod
        WHERE dm.Materia_Cod = ?
          AND dm.Estado_Codigo = ?
          AND d.Estado_Codigo = ?
        ORDER BY d.Nombre_Completo;
        """,
        (int(materia_cod), int(activo), int(activo)),
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_matricula_curso_activa_estudiante(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    periodo: int,
) -> tuple | None:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1
            mc.Curso_Cod,
            cp.Descripcion
        FROM dbo.Matricula_Curso mc
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = mc.Curso_Cod
        WHERE mc.Carnet = ?
          AND mc.Periodo = ?
          AND mc.Estado_Codigo = ?;
        """,
        (str(carnet).strip(), int(periodo), int(activo)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return (int(row[0]), str(row[1]))


def fetch_estados(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Estado_Codigo, Estado_Desc
        FROM dbo.Estado_General
        ORDER BY Estado_Codigo;
        """
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


# =========================================================
# Grid / Listados
# =========================================================
def list_matricula_materia(conn: pyodbc.Connection) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            mm.Matricula_Materia_Id,
            mm.Carnet,
            e.Nombre_Completo AS Estudiante,
            mm.Materia_Cod,
            m.Descripcion AS Materia,
            cp.Curso_Cod,
            cp.Descripcion AS Curso,
            mm.Periodo,
            mm.Docente_Cod,
            d.Nombre_Completo AS Docente,
            eg.Estado_Desc,
            CONVERT(varchar(10), mm.Fecha_Matricula, 120) AS Fecha_Matricula
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Estudiantes e
            ON e.Carnet = mm.Carnet
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = mm.Docente_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = mm.Estado_Codigo
        ORDER BY mm.Periodo DESC, e.Nombre_Completo, m.Materia_Cod;
        """
    )

    rows: list[tuple] = []
    for r in cur.fetchall():
        (
            matricula_materia_id,
            carnet,
            estudiante,
            materia_cod,
            materia_desc,
            curso_cod,
            curso_desc,
            periodo,
            docente_cod,
            docente_nombre,
            estado_desc,
            fecha_matricula,
        ) = r

        rows.append(
            (
                int(matricula_materia_id),
                str(carnet),
                str(estudiante),
                f"{int(curso_cod)} - {str(curso_desc)}",
                f"{int(materia_cod)} - {str(materia_desc)}",
                int(periodo),
                f"{int(docente_cod)} - {str(docente_nombre)}",
                str(estado_desc),
                str(fecha_matricula),
            )
        )
    return rows


def list_matricula_materia_por_estudiante_periodo(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    periodo: int,
) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            mm.Matricula_Materia_Id,
            mm.Materia_Cod,
            m.Descripcion AS Materia,
            mm.Docente_Cod,
            d.Nombre_Completo AS Docente,
            eg.Estado_Desc,
            CONVERT(varchar(10), mm.Fecha_Matricula, 120) AS Fecha_Matricula
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = mm.Docente_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = mm.Estado_Codigo
        WHERE mm.Carnet = ?
          AND mm.Periodo = ?
        ORDER BY mm.Materia_Cod;
        """,
        (str(carnet).strip(), int(periodo)),
    )
    return [
        (
            int(r[0]),
            f"{int(r[1])} - {str(r[2])}",
            f"{int(r[3])} - {str(r[4])}",
            str(r[5]),
            str(r[6]),
        )
        for r in cur.fetchall()
    ]


# =========================================================
# Commands
# =========================================================
def insert_matricula_materia(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    materia_cod: int,
    periodo: int,
    docente_cod: int,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Matricula_Materia
            (Carnet, Materia_Cod, Periodo, Docente_Cod, Estado_Codigo, Fecha_Matricula)
        VALUES (?, ?, ?, ?, ?, GETDATE());
        """,
        (
            str(carnet).strip(),
            int(materia_cod),
            int(periodo),
            int(docente_cod),
            int(estado_codigo),
        ),
    )
    conn.commit()


def reactivar_matricula_materia(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    materia_cod: int,
    periodo: int,
    docente_cod: int,
) -> None:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Matricula_Materia
        SET Docente_Cod = ?,
            Estado_Codigo = ?
        WHERE Carnet = ?
          AND Materia_Cod = ?
          AND Periodo = ?;
        """,
        (
            int(docente_cod),
            int(activo),
            str(carnet).strip(),
            int(materia_cod),
            int(periodo),
        ),
    )
    conn.commit()


def update_estado_matricula_materia(
    conn: pyodbc.Connection,
    *,
    matricula_materia_id: int,
    nuevo_estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Matricula_Materia
        SET Estado_Codigo = ?
        WHERE Matricula_Materia_Id = ?;
        """,
        (int(nuevo_estado_codigo), int(matricula_materia_id)),
    )
    conn.commit()


def delete_matricula_materia(
    conn: pyodbc.Connection,
    *,
    matricula_materia_id: int,
) -> None:
    inactivo = get_estado_codigo_by_desc(conn, "Inactivo")
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Matricula_Materia
        SET Estado_Codigo = ?
        WHERE Matricula_Materia_Id = ?;
        """,
        (int(inactivo), int(matricula_materia_id)),
    )
    conn.commit()