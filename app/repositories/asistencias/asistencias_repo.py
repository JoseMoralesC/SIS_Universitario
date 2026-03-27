# app/repositories/asistencias/asistencias_repo.py
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
        estado_desc,
    )
    row = cur.fetchone()

    if not row:
        raise ValueError(f"Estado no encontrado: {estado_desc}")

    return int(row[0])


def _normalizar_lista_carnets(items: list[str] | tuple[str, ...] | None) -> list[str]:
    if not items:
        return []

    vistos: set[str] = set()
    salida: list[str] = []

    for item in items:
        carnet = str(item or "").strip()
        if not carnet:
            continue
        if carnet in vistos:
            continue
        vistos.add(carnet)
        salida.append(carnet)

    return salida


def _normalizar_usuario_docente(usuario_docente: str | None) -> str | None:
    valor = str(usuario_docente or "").strip()
    return valor or None


def get_docente_cod_by_usuario_docente(
    conn: pyodbc.Connection,
    usuario_docente: str,
) -> int | None:
    usuario_docente = _normalizar_usuario_docente(usuario_docente)
    if not usuario_docente:
        return None

    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 d.Docente_Cod
        FROM dbo.Docentes d
        WHERE UPPER(LTRIM(RTRIM(ISNULL(d.Usuario_Docente, '')))) = UPPER(LTRIM(RTRIM(?)));
        """,
        usuario_docente,
    )
    row = cur.fetchone()
    return int(row[0]) if row else None


def _get_periodo_academico_from_id(conn: pyodbc.Connection, periodo_id: int) -> int | None:
    """
    En este modelo, el campo Periodo de tablas como:
    - Matricula_Curso
    - Matricula_Materia
    representa el AÑO académico (ej. 2026).
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 Anio
        FROM dbo.Periodos
        WHERE Periodo_Id = ?;
        """,
        int(periodo_id),
    )
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else None


# =========================================================
# Exists / validaciones básicas
# =========================================================
def exists_periodo(conn: pyodbc.Connection, periodo_id: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Periodos
        WHERE Periodo_Id = ?;
        """,
        int(periodo_id),
    )
    return cur.fetchone() is not None


def exists_curso(conn: pyodbc.Connection, curso_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Cursos_Programas
        WHERE Curso_Cod = ?;
        """,
        int(curso_cod),
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
        int(materia_cod),
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
        int(docente_cod),
    )
    return cur.fetchone() is not None


def exists_estudiante(conn: pyodbc.Connection, carnet: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Estudiantes
        WHERE Carnet = ?;
        """,
        str(carnet).strip(),
    )
    return cur.fetchone() is not None


def exists_asistencia_lista(conn: pyodbc.Connection, asistencia_lista_id: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Asistencia_Lista
        WHERE Asistencia_Lista_Id = ?;
        """,
        int(asistencia_lista_id),
    )
    return cur.fetchone() is not None


# =========================================================
# Lookups
# =========================================================
def fetch_periodos_activos(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            p.Periodo_Id,
            p.Anio,
            p.Numero_Periodo,
            p.Periodo_Codigo
        FROM dbo.Periodos p
        WHERE p.Estado_Codigo = ?
        ORDER BY p.Anio DESC, p.Numero_Periodo DESC, p.Periodo_Id DESC;
        """,
        int(activo),
    )

    rows: list[tuple[int, str]] = []
    for row in cur.fetchall():
        periodo_id = int(row[0])
        anio = int(row[1])
        numero_periodo = int(row[2])
        periodo_codigo = str(row[3])

        label = f"{periodo_codigo} | {anio} - P{numero_periodo}"
        rows.append((periodo_id, label))

    return rows


def fetch_cursos_por_periodo(
    conn: pyodbc.Connection,
    periodo_id: int,
    usuario_docente: str | None = None,
) -> list[tuple[int, str]]:
    """
    Cursos válidos para asistencias.

    Regla corregida:
    - Curso activo
    - Con estudiantes matriculados en Matricula_Curso
    - Acepta cualquiera de estos escenarios:
        * mc.Periodo_Id = periodo_id
        * o mc.Periodo_Id IS NULL y mc.Periodo = anio_academico
    - Si viene usuario_docente, solo cursos de ese docente
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    usuario_docente = _normalizar_usuario_docente(usuario_docente)
    periodo_academico = _get_periodo_academico_from_id(conn, int(periodo_id))

    sql = """
        SELECT DISTINCT
            cp.Curso_Cod,
            cp.Descripcion
        FROM dbo.Cursos_Programas cp
        INNER JOIN dbo.Matricula_Curso mc
            ON mc.Curso_Cod = cp.Curso_Cod
           AND (
                mc.Periodo_Id = ?
                OR (mc.Periodo_Id IS NULL AND mc.Periodo = ?)
           )
           AND mc.Estado_Codigo = ?
        WHERE cp.Estado_Codigo = ?
    """
    params: list = [
        int(periodo_id),
        None if periodo_academico is None else int(periodo_academico),
        int(activo),
        int(activo),
    ]

    if usuario_docente:
        sql += """
          AND EXISTS (
                SELECT 1
                FROM dbo.Curso_Docente cd
                INNER JOIN dbo.Docentes d
                    ON d.Docente_Cod = cd.Docente_Cod
                   AND d.Estado_Codigo = ?
                WHERE cd.Curso_Cod = cp.Curso_Cod
                  AND UPPER(LTRIM(RTRIM(ISNULL(d.Usuario_Docente, ''))))
                      = UPPER(LTRIM(RTRIM(?)))
          )
        """
        params.extend([int(activo), usuario_docente])

    sql += """
        ORDER BY cp.Descripcion ASC;
    """

    cur = conn.cursor()
    cur.execute(sql, params)
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_materias_por_periodo_curso(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    usuario_docente: str | None = None,
) -> list[tuple[int, str]]:
    """
    Materias válidas para asistencias.

    Regla corregida:
    - Materia activa
    - Pertenece al curso
    - El curso tiene estudiantes matriculados en Matricula_Curso
    - Acepta cualquiera de estos escenarios:
        * mc.Periodo_Id = periodo_id
        * o mc.Periodo_Id IS NULL y mc.Periodo = anio_academico
    - Si viene usuario_docente, solo materias vinculadas a ese docente
      mediante Docente_Materia + Curso_Docente
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    usuario_docente = _normalizar_usuario_docente(usuario_docente)
    periodo_academico = _get_periodo_academico_from_id(conn, int(periodo_id))

    sql = """
        SELECT DISTINCT
            m.Materia_Cod,
            m.Descripcion
        FROM dbo.Materias m
        WHERE m.Curso_Cod = ?
          AND m.Estado_Codigo = ?
          AND EXISTS (
                SELECT 1
                FROM dbo.Matricula_Curso mc
                WHERE mc.Curso_Cod = m.Curso_Cod
                  AND (
                        mc.Periodo_Id = ?
                        OR (mc.Periodo_Id IS NULL AND mc.Periodo = ?)
                  )
                  AND mc.Estado_Codigo = ?
          )
    """
    params: list = [
        int(curso_cod),
        int(activo),
        int(periodo_id),
        None if periodo_academico is None else int(periodo_academico),
        int(activo),
    ]

    if usuario_docente:
        sql += """
          AND EXISTS (
                SELECT 1
                FROM dbo.Docente_Materia dm
                INNER JOIN dbo.Docentes d
                    ON d.Docente_Cod = dm.Docente_Cod
                   AND d.Estado_Codigo = ?
                INNER JOIN dbo.Curso_Docente cd
                    ON cd.Docente_Cod = dm.Docente_Cod
                   AND cd.Curso_Cod = m.Curso_Cod
                WHERE dm.Materia_Cod = m.Materia_Cod
                  AND dm.Estado_Codigo = ?
                  AND UPPER(LTRIM(RTRIM(ISNULL(d.Usuario_Docente, ''))))
                      = UPPER(LTRIM(RTRIM(?)))
          )
        """
        params.extend([int(activo), int(activo), usuario_docente])

    sql += """
        ORDER BY m.Descripcion ASC;
    """

    cur = conn.cursor()
    cur.execute(sql, params)
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_docentes_por_periodo_curso_materia(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    usuario_docente: str | None = None,
) -> list[tuple[int, str]]:
    """
    Docentes válidos para período + curso + materia.

    Regla corregida:
    - Docente activo
    - Asignado al curso en Curso_Docente
    - Asignado a la materia en Docente_Materia
    - El curso tiene matrícula en Matricula_Curso
    - Acepta cualquiera de estos escenarios:
        * mc.Periodo_Id = periodo_id
        * o mc.Periodo_Id IS NULL y mc.Periodo = anio_academico
    - Si viene usuario_docente, se restringe a ese login
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    usuario_docente = _normalizar_usuario_docente(usuario_docente)
    periodo_academico = _get_periodo_academico_from_id(conn, int(periodo_id))

    sql = """
        SELECT DISTINCT
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Docentes d
        INNER JOIN dbo.Curso_Docente cd
            ON cd.Docente_Cod = d.Docente_Cod
           AND cd.Curso_Cod = ?
        INNER JOIN dbo.Docente_Materia dm
            ON dm.Docente_Cod = d.Docente_Cod
           AND dm.Materia_Cod = ?
           AND dm.Estado_Codigo = ?
        INNER JOIN dbo.Matricula_Curso mc
            ON mc.Curso_Cod = cd.Curso_Cod
           AND (
                mc.Periodo_Id = ?
                OR (mc.Periodo_Id IS NULL AND mc.Periodo = ?)
           )
           AND mc.Estado_Codigo = ?
        WHERE d.Estado_Codigo = ?
    """
    params: list = [
        int(curso_cod),
        int(materia_cod),
        int(activo),
        int(periodo_id),
        None if periodo_academico is None else int(periodo_academico),
        int(activo),
        int(activo),
    ]

    if usuario_docente:
        sql += """
          AND UPPER(LTRIM(RTRIM(ISNULL(d.Usuario_Docente, ''))))
              = UPPER(LTRIM(RTRIM(?)))
        """
        params.append(usuario_docente)

    sql += """
        ORDER BY d.Nombre_Completo ASC;
    """

    cur = conn.cursor()
    cur.execute(sql, params)
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_horarios_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
) -> list[tuple[str, str, int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            mh.Dia_Cod,
            ds.Dia_Nombre,
            mh.Jornada_Id,
            j.Jornada
        FROM dbo.Materia_Horario mh
        INNER JOIN dbo.Dias_Semana ds
            ON ds.Dia_Cod = mh.Dia_Cod
        INNER JOIN dbo.Jornadas j
            ON j.Jornada_Id = mh.Jornada_Id
        WHERE mh.Materia_Cod = ?
          AND mh.Estado_Codigo = ?
        ORDER BY ds.Dia_Orden ASC, mh.Jornada_Id ASC;
        """,
        int(materia_cod),
        int(activo),
    )

    return [
        (str(r[0]), str(r[1]), int(r[2]), str(r[3]))
        for r in cur.fetchall()
    ]


def fetch_horario_principal_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
) -> tuple[str, str, int, str] | None:
    rows = fetch_horarios_materia(conn, materia_cod=materia_cod)
    return rows[0] if rows else None


def fetch_estudiantes_matriculados(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    usuario_docente: str | None = None,
) -> list[tuple[str, str]]:
    """
    Estudiantes del grupo final para asistencia.

    Acepta dos escenarios válidos en Matricula_Materia:
    - mm.Periodo_Id = periodo_id
    - o mm.Periodo = anio_academico cuando Periodo_Id venga NULL
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    usuario_docente = _normalizar_usuario_docente(usuario_docente)
    periodo_academico = _get_periodo_academico_from_id(conn, int(periodo_id))

    sql = """
        SELECT DISTINCT
            e.Carnet,
            e.Nombre_Completo
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Estudiantes e
            ON e.Carnet = mm.Carnet
           AND e.Estado_Codigo = ?
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
           AND m.Estado_Codigo = ?
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = mm.Docente_Cod
           AND d.Estado_Codigo = ?
        WHERE (
                mm.Periodo_Id = ?
                OR (mm.Periodo_Id IS NULL AND mm.Periodo = ?)
              )
          AND mm.Materia_Cod = ?
          AND mm.Docente_Cod = ?
          AND mm.Estado_Codigo = ?
          AND m.Curso_Cod = ?
    """
    params: list = [
        int(activo),
        int(activo),
        int(activo),
        int(periodo_id),
        None if periodo_academico is None else int(periodo_academico),
        int(materia_cod),
        int(docente_cod),
        int(activo),
        int(curso_cod),
    ]

    if usuario_docente:
        sql += """
          AND UPPER(LTRIM(RTRIM(ISNULL(d.Usuario_Docente, ''))))
              = UPPER(LTRIM(RTRIM(?)))
        """
        params.append(usuario_docente)

    sql += """
        ORDER BY e.Nombre_Completo ASC;
    """

    cur = conn.cursor()
    cur.execute(sql, params)
    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]


# =========================================================
# Cabecera / consulta de lista existente
# =========================================================
def find_asistencia_lista_by_unique(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    fecha_clase: str,
) -> tuple | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            al.Curso_Cod,
            al.Materia_Cod,
            al.Docente_Cod,
            al.Dia_Cod,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo
        FROM dbo.Asistencia_Lista al
        WHERE al.Periodo_Id = ?
          AND al.Curso_Cod = ?
          AND al.Materia_Cod = ?
          AND al.Docente_Cod = ?
          AND al.Fecha_Clase = ?
        ORDER BY al.Asistencia_Lista_Id DESC;
        """,
        int(periodo_id),
        int(curso_cod),
        int(materia_cod),
        int(docente_cod),
        fecha_clase,
    )

    row = cur.fetchone()
    return tuple(row) if row else None


def get_asistencia_lista_detalle_cabecera(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
) -> tuple | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            CONCAT(p.Periodo_Codigo, ' | ', p.Anio, ' - P', p.Numero_Periodo) AS Periodo_Label,
            al.Curso_Cod,
            cp.Descripcion AS Curso_Desc,
            al.Materia_Cod,
            m.Descripcion AS Materia_Desc,
            al.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            al.Dia_Cod,
            ds.Dia_Nombre,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo
        FROM dbo.Asistencia_Lista al
        INNER JOIN dbo.Periodos p
            ON p.Periodo_Id = al.Periodo_Id
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = al.Curso_Cod
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = al.Materia_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = al.Docente_Cod
        INNER JOIN dbo.Dias_Semana ds
            ON ds.Dia_Cod = al.Dia_Cod
        WHERE al.Asistencia_Lista_Id = ?;
        """,
        int(asistencia_lista_id),
    )

    row = cur.fetchone()
    return tuple(row) if row else None


def fetch_asistencia_detalle(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            ad.Asistencia_Detalle_Id,
            ad.Carnet,
            e.Nombre_Completo,
            ad.Estado_Asistencia,
            ad.Observacion,
            ad.Estado_Codigo
        FROM dbo.Asistencia_Detalle ad
        INNER JOIN dbo.Estudiantes e
            ON e.Carnet = ad.Carnet
        WHERE ad.Asistencia_Lista_Id = ?
        ORDER BY e.Nombre_Completo ASC;
        """,
        int(asistencia_lista_id),
    )

    return [tuple(r) for r in cur.fetchall()]


# =========================================================
# Consultas de listas existentes
# =========================================================
def fetch_listas_asistencia(
    conn: pyodbc.Connection,
    *,
    periodo_id: int | None = None,
    curso_cod: int | None = None,
    materia_cod: int | None = None,
    docente_cod: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    estado_codigo: int | None = None,
    usuario_docente: str | None = None,
) -> list[tuple]:
    usuario_docente = _normalizar_usuario_docente(usuario_docente)

    cur = conn.cursor()

    sql = """
        SELECT
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            CONCAT(p.Periodo_Codigo, ' | ', p.Anio, ' - P', p.Numero_Periodo) AS Periodo_Label,
            al.Curso_Cod,
            cp.Descripcion AS Curso_Desc,
            al.Materia_Cod,
            m.Descripcion AS Materia_Desc,
            al.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            al.Dia_Cod,
            ds.Dia_Nombre,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo,
            SUM(CASE WHEN ad.Estado_Asistencia = 'A' THEN 1 ELSE 0 END) AS Total_Asistentes,
            SUM(CASE WHEN ad.Estado_Asistencia = 'F' THEN 1 ELSE 0 END) AS Total_Ausentes,
            COUNT(ad.Asistencia_Detalle_Id) AS Total_Registros
        FROM dbo.Asistencia_Lista al
        INNER JOIN dbo.Periodos p
            ON p.Periodo_Id = al.Periodo_Id
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = al.Curso_Cod
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = al.Materia_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = al.Docente_Cod
        INNER JOIN dbo.Dias_Semana ds
            ON ds.Dia_Cod = al.Dia_Cod
        LEFT JOIN dbo.Asistencia_Detalle ad
            ON ad.Asistencia_Lista_Id = al.Asistencia_Lista_Id
        WHERE 1 = 1
    """

    params: list = []

    if periodo_id is not None:
        sql += " AND al.Periodo_Id = ?"
        params.append(int(periodo_id))

    if curso_cod is not None:
        sql += " AND al.Curso_Cod = ?"
        params.append(int(curso_cod))

    if materia_cod is not None:
        sql += " AND al.Materia_Cod = ?"
        params.append(int(materia_cod))

    if docente_cod is not None:
        sql += " AND al.Docente_Cod = ?"
        params.append(int(docente_cod))

    if fecha_desde:
        sql += " AND al.Fecha_Clase >= ?"
        params.append(str(fecha_desde).strip())

    if fecha_hasta:
        sql += " AND al.Fecha_Clase <= ?"
        params.append(str(fecha_hasta).strip())

    if estado_codigo is not None:
        sql += " AND al.Estado_Codigo = ?"
        params.append(int(estado_codigo))

    if usuario_docente:
        sql += """
            AND UPPER(LTRIM(RTRIM(ISNULL(d.Usuario_Docente, ''))))
                = UPPER(LTRIM(RTRIM(?)))
        """
        params.append(usuario_docente)

    sql += """
        GROUP BY
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo,
            al.Curso_Cod,
            cp.Descripcion,
            al.Materia_Cod,
            m.Descripcion,
            al.Docente_Cod,
            d.Nombre_Completo,
            al.Dia_Cod,
            ds.Dia_Nombre,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo
        ORDER BY
            al.Fecha_Clase DESC,
            cp.Descripcion ASC,
            m.Descripcion ASC,
            d.Nombre_Completo ASC,
            al.Asistencia_Lista_Id DESC;
    """

    cur.execute(sql, params)
    return [tuple(r) for r in cur.fetchall()]


def fetch_asistencia_lista_resumen_row(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
) -> tuple | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            CONCAT(p.Periodo_Codigo, ' | ', p.Anio, ' - P', p.Numero_Periodo) AS Periodo_Label,
            al.Curso_Cod,
            cp.Descripcion AS Curso_Desc,
            al.Materia_Cod,
            m.Descripcion AS Materia_Desc,
            al.Docente_Cod,
            d.Nombre_Completo AS Docente_Nombre,
            al.Dia_Cod,
            ds.Dia_Nombre,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo,
            SUM(CASE WHEN ad.Estado_Asistencia = 'A' THEN 1 ELSE 0 END) AS Total_Asistentes,
            SUM(CASE WHEN ad.Estado_Asistencia = 'F' THEN 1 ELSE 0 END) AS Total_Ausentes,
            COUNT(ad.Asistencia_Detalle_Id) AS Total_Registros
        FROM dbo.Asistencia_Lista al
        INNER JOIN dbo.Periodos p
            ON p.Periodo_Id = al.Periodo_Id
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = al.Curso_Cod
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = al.Materia_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = al.Docente_Cod
        INNER JOIN dbo.Dias_Semana ds
            ON ds.Dia_Cod = al.Dia_Cod
        LEFT JOIN dbo.Asistencia_Detalle ad
            ON ad.Asistencia_Lista_Id = al.Asistencia_Lista_Id
        WHERE al.Asistencia_Lista_Id = ?
        GROUP BY
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo,
            al.Curso_Cod,
            cp.Descripcion,
            al.Materia_Cod,
            m.Descripcion,
            al.Docente_Cod,
            d.Nombre_Completo,
            al.Dia_Cod,
            ds.Dia_Nombre,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo;
        """,
        int(asistencia_lista_id),
    )
    row = cur.fetchone()
    return tuple(row) if row else None


# =========================================================
# Commands
# =========================================================
def insert_asistencia_lista(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    dia_cod: str,
    fecha_clase: str,
    codigo_usuario: int | None,
    estado_codigo: int,
) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Asistencia_Lista
        (
            Periodo_Id,
            Curso_Cod,
            Materia_Cod,
            Docente_Cod,
            Dia_Cod,
            Fecha_Clase,
            Fecha_Registro,
            Codigo_Usuario,
            Estado_Codigo
        )
        OUTPUT INSERTED.Asistencia_Lista_Id
        VALUES (?, ?, ?, ?, ?, ?, SYSDATETIME(), ?, ?);
        """,
        int(periodo_id),
        int(curso_cod),
        int(materia_cod),
        int(docente_cod),
        (dia_cod or "").strip(),
        fecha_clase,
        None if codigo_usuario is None else int(codigo_usuario),
        int(estado_codigo),
    )

    row = cur.fetchone()
    conn.commit()

    return int(row[0]) if row and row[0] is not None else 0


def update_asistencia_lista_cabecera(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
    dia_cod: str,
    fecha_clase: str,
    codigo_usuario: int | None,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Asistencia_Lista
        SET Dia_Cod = ?,
            Fecha_Clase = ?,
            Codigo_Usuario = ?,
            Estado_Codigo = ?
        WHERE Asistencia_Lista_Id = ?;
        """,
        (dia_cod or "").strip(),
        fecha_clase,
        None if codigo_usuario is None else int(codigo_usuario),
        int(estado_codigo),
        int(asistencia_lista_id),
    )
    conn.commit()


def insert_asistencia_detalle_many(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
    asistentes: list[str] | tuple[str, ...] | None,
    ausentes: list[str] | tuple[str, ...] | None,
    estado_codigo: int,
) -> None:
    asistentes_norm = _normalizar_lista_carnets(asistentes)
    ausentes_norm = _normalizar_lista_carnets(ausentes)

    set_asistentes = set(asistentes_norm)
    ausentes_norm = [c for c in ausentes_norm if c not in set_asistentes]

    rows: list[tuple] = []

    for carnet in asistentes_norm:
        rows.append(
            (
                int(asistencia_lista_id),
                carnet,
                "A",
                None,
                int(estado_codigo),
            )
        )

    for carnet in ausentes_norm:
        rows.append(
            (
                int(asistencia_lista_id),
                carnet,
                "F",
                None,
                int(estado_codigo),
            )
        )

    if not rows:
        return

    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO dbo.Asistencia_Detalle
        (
            Asistencia_Lista_Id,
            Carnet,
            Estado_Asistencia,
            Observacion,
            Estado_Codigo
        )
        VALUES (?, ?, ?, ?, ?);
        """,
        rows,
    )
    conn.commit()


def delete_asistencia_detalle_by_lista(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM dbo.Asistencia_Detalle
        WHERE Asistencia_Lista_Id = ?;
        """,
        int(asistencia_lista_id),
    )
    conn.commit()


def replace_asistencia_detalle(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
    asistentes: list[str] | tuple[str, ...] | None,
    ausentes: list[str] | tuple[str, ...] | None,
    estado_codigo: int,
) -> None:
    asistentes_norm = _normalizar_lista_carnets(asistentes)
    ausentes_norm = _normalizar_lista_carnets(ausentes)

    set_asistentes = set(asistentes_norm)
    ausentes_norm = [c for c in ausentes_norm if c not in set_asistentes]

    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM dbo.Asistencia_Detalle
        WHERE Asistencia_Lista_Id = ?;
        """,
        int(asistencia_lista_id),
    )

    rows: list[tuple] = []

    for carnet in asistentes_norm:
        rows.append(
            (
                int(asistencia_lista_id),
                carnet,
                "A",
                None,
                int(estado_codigo),
            )
        )

    for carnet in ausentes_norm:
        rows.append(
            (
                int(asistencia_lista_id),
                carnet,
                "F",
                None,
                int(estado_codigo),
            )
        )

    if rows:
        cur.executemany(
            """
            INSERT INTO dbo.Asistencia_Detalle
            (
                Asistencia_Lista_Id,
                Carnet,
                Estado_Asistencia,
                Observacion,
                Estado_Codigo
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            rows,
        )

    conn.commit()


# =========================================================
# Resúmenes útiles
# =========================================================
def count_estudiantes_matriculados(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    usuario_docente: str | None = None,
) -> int:
    activo = get_estado_codigo_by_desc(conn, "Activo")
    usuario_docente = _normalizar_usuario_docente(usuario_docente)
    periodo_academico = _get_periodo_academico_from_id(conn, int(periodo_id))

    sql = """
        SELECT COUNT(DISTINCT e.Carnet)
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Estudiantes e
            ON e.Carnet = mm.Carnet
           AND e.Estado_Codigo = ?
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
           AND m.Estado_Codigo = ?
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = mm.Docente_Cod
           AND d.Estado_Codigo = ?
        WHERE (
                mm.Periodo_Id = ?
                OR (mm.Periodo_Id IS NULL AND mm.Periodo = ?)
              )
          AND mm.Materia_Cod = ?
          AND mm.Docente_Cod = ?
          AND mm.Estado_Codigo = ?
          AND m.Curso_Cod = ?
    """
    params: list = [
        int(activo),
        int(activo),
        int(activo),
        int(periodo_id),
        None if periodo_academico is None else int(periodo_academico),
        int(materia_cod),
        int(docente_cod),
        int(activo),
        int(curso_cod),
    ]

    if usuario_docente:
        sql += """
          AND UPPER(LTRIM(RTRIM(ISNULL(d.Usuario_Docente, ''))))
              = UPPER(LTRIM(RTRIM(?)))
        """
        params.append(usuario_docente)

    cur = conn.cursor()
    cur.execute(sql, params)

    row = cur.fetchone()
    return int(row[0] or 0)


def count_asistencia_resumen(
    conn: pyodbc.Connection,
    *,
    asistencia_lista_id: int,
) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            SUM(CASE WHEN Estado_Asistencia = 'A' THEN 1 ELSE 0 END) AS Total_Asistentes,
            SUM(CASE WHEN Estado_Asistencia = 'F' THEN 1 ELSE 0 END) AS Total_Ausentes
        FROM dbo.Asistencia_Detalle
        WHERE Asistencia_Lista_Id = ?;
        """,
        int(asistencia_lista_id),
    )

    row = cur.fetchone()

    asistentes = int((row[0] or 0) if row else 0)
    ausentes = int((row[1] or 0) if row else 0)

    return {
        "asistentes": asistentes,
        "ausentes": ausentes,
        "total_registrados": asistentes + ausentes,
    }