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


# =========================================================
# Lookups - filtros de cabecera
# =========================================================
def fetch_periodos_con_matricula(conn: pyodbc.Connection) -> list[tuple[int, str, int]]:
    """
    Retorna períodos activos con matrícula de curso activa.

    Formato:
        (Periodo_Id, Periodo_Codigo, Anio)
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            p.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo
        FROM dbo.Periodos p
        INNER JOIN dbo.Matricula_Curso mc
            ON mc.Periodo_Id = p.Periodo_Id
        WHERE p.Estado_Codigo = ?
          AND mc.Estado_Codigo = ?
        ORDER BY p.Anio DESC, p.Numero_Periodo ASC;
        """,
        (int(activo), int(activo)),
    )

    return [
        (int(r[0]), str(r[1]), int(r[2]))
        for r in cur.fetchall()
    ]


def fetch_cursos_por_periodo(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    anio: int,
) -> list[tuple[int, str]]:
    """
    Cursos/carreras con matrícula activa en el período seleccionado.

    Compatibilidad:
    - si Matricula_Curso.Periodo_Id está poblado, filtra por Periodo_Id
    - si aún hay registros viejos sin Periodo_Id, usa el año lógico en mc.Periodo
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            cp.Curso_Cod,
            cp.Descripcion
        FROM dbo.Matricula_Curso mc
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = mc.Curso_Cod
        WHERE mc.Estado_Codigo = ?
          AND cp.Estado_Codigo = ?
          AND (
                mc.Periodo_Id = ?
                OR (mc.Periodo_Id IS NULL AND mc.Periodo = ?)
          )
        ORDER BY cp.Descripcion;
        """,
        (
            int(activo),
            int(activo),
            int(periodo_id),
            int(anio),
        ),
    )

    return [
        (int(r[0]), str(r[1]))
        for r in cur.fetchall()
    ]


def fetch_estudiantes_por_periodo_curso(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    anio: int,
    curso_cod: int,
) -> list[tuple[str, str]]:
    """
    Estudiantes activos matriculados en el curso y período seleccionados,
    PERO solo aquellos que ya tienen al menos una materia asignada
    en Matricula_Materia.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            e.Carnet,
            e.Nombre_Completo
        FROM dbo.Matricula_Curso mc
        INNER JOIN dbo.Estudiantes e
            ON e.Carnet = mc.Carnet
        WHERE mc.Curso_Cod = ?
          AND mc.Estado_Codigo = ?
          AND e.Estado_Codigo = ?
          AND (
                mc.Periodo_Id = ?
                OR (mc.Periodo_Id IS NULL AND mc.Periodo = ?)
          )
          AND EXISTS (
                SELECT 1
                FROM dbo.Matricula_Materia mm
                INNER JOIN dbo.Materias m
                    ON m.Materia_Cod = mm.Materia_Cod
                WHERE mm.Carnet = mc.Carnet
                  AND m.Curso_Cod = mc.Curso_Cod
                  AND mm.Estado_Codigo = ?
                  AND (
                        mm.Periodo_Id = ?
                        OR (mm.Periodo_Id IS NULL AND mm.Periodo = ?)
                  )
          )
        ORDER BY e.Nombre_Completo;
        """,
        (
            int(curso_cod),
            int(activo),
            int(activo),
            int(periodo_id),
            int(anio),
            int(activo),
            int(periodo_id),
            int(anio),
        ),
    )

    return [
        (str(r[0]), str(r[1]))
        for r in cur.fetchall()
    ]


# =========================================================
# Grid / Consulta detalle
# =========================================================
def list_matricula_detalle_estudiante(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    periodo_id: int,
    anio: int,
    curso_cod: int,
) -> list[tuple]:
    """
    Retorna el detalle de matrícula por materia del estudiante filtrado.

    Formato de salida:
    (
        Matricula_Materia_Id,
        Materia,
        Dias,
        Jornada,
        Horario_Detalle,
        Docente,
        Estado,
        Fecha_Matricula
    )

    Compatibilidad:
    - usa mm.Periodo_Id si existe
    - si no existe, cae a mm.Periodo = anio
    """
    cur = conn.cursor()
    cur.execute(
        """
        WITH HorariosMateria AS (
            SELECT
                mh.Materia_Cod,
                STRING_AGG(ds.Dia_Nombre, ', ') AS Dias,
                STRING_AGG(j.Jornada, ', ') AS Jornada,
                STRING_AGG(
                    CONCAT(ds.Dia_Nombre, ' - ', j.Jornada),
                    ' | '
                ) AS Horario_Detalle
            FROM dbo.Materia_Horario mh
            INNER JOIN dbo.Dias_Semana ds
                ON ds.Dia_Cod = mh.Dia_Cod
            INNER JOIN dbo.Jornadas j
                ON j.Jornada_Id = mh.Jornada_Id
            INNER JOIN dbo.Estado_General eg_h
                ON eg_h.Estado_Codigo = mh.Estado_Codigo
            WHERE eg_h.Estado_Desc = 'Activo'
            GROUP BY mh.Materia_Cod
        )
        SELECT
            mm.Matricula_Materia_Id,
            CONCAT(m.Materia_Cod, ' - ', m.Descripcion) AS Materia,
            ISNULL(hm.Dias, 'Sin días asignados') AS Dias,
            ISNULL(hm.Jornada, 'Sin jornada asignada') AS Jornada,
            ISNULL(hm.Horario_Detalle, 'Sin horario asignado') AS Horario_Detalle,
            CONCAT(d.Docente_Cod, ' - ', d.Nombre_Completo) AS Docente,
            eg.Estado_Desc,
            CONVERT(varchar(10), mm.Fecha_Matricula, 120) AS Fecha_Matricula
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = mm.Docente_Cod
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = mm.Estado_Codigo
        LEFT JOIN HorariosMateria hm
            ON hm.Materia_Cod = mm.Materia_Cod
        WHERE mm.Carnet = ?
          AND cp.Curso_Cod = ?
          AND (
                mm.Periodo_Id = ?
                OR (mm.Periodo_Id IS NULL AND mm.Periodo = ?)
          )
        ORDER BY m.Descripcion;
        """,
        (
            str(carnet).strip(),
            int(curso_cod),
            int(periodo_id),
            int(anio),
        ),
    )

    rows: list[tuple] = []
    for r in cur.fetchall():
        rows.append(
            (
                int(r[0]),
                str(r[1]),
                str(r[2]),
                str(r[3]),
                str(r[4]),
                str(r[5]),
                str(r[6]),
                str(r[7]),
            )
        )
    return rows