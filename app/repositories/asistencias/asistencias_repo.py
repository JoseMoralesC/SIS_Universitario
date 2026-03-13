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
    """
    Limpia, quita vacíos y elimina duplicados preservando orden.
    """
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
        (str(carnet).strip(),),
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


def fetch_cursos_por_periodo(conn: pyodbc.Connection, periodo_id: int) -> list[tuple[int, str]]:
    """
    Cursos que realmente tienen matrícula por materia en el período indicado.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            cp.Curso_Cod,
            cp.Descripcion
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        WHERE mm.Periodo_Id = ?
          AND mm.Estado_Codigo = ?
          AND m.Estado_Codigo = ?
          AND cp.Estado_Codigo = ?
        ORDER BY cp.Descripcion ASC;
        """,
        int(periodo_id),
        int(activo),
        int(activo),
        int(activo),
    )

    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_materias_por_periodo_curso(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
) -> list[tuple[int, str]]:
    """
    Materias realmente matriculadas en el período/curso seleccionado.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            m.Materia_Cod,
            m.Descripcion
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        WHERE mm.Periodo_Id = ?
          AND m.Curso_Cod = ?
          AND mm.Estado_Codigo = ?
          AND m.Estado_Codigo = ?
        ORDER BY m.Descripcion ASC;
        """,
        int(periodo_id),
        int(curso_cod),
        int(activo),
        int(activo),
    )

    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_docentes_por_periodo_curso_materia(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
) -> list[tuple[int, str]]:
    """
    Docentes que realmente tienen estudiantes matriculados en esa materia.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = mm.Docente_Cod
        WHERE mm.Periodo_Id = ?
          AND m.Curso_Cod = ?
          AND mm.Materia_Cod = ?
          AND mm.Estado_Codigo = ?
          AND m.Estado_Codigo = ?
          AND d.Estado_Codigo = ?
        ORDER BY d.Nombre_Completo ASC;
        """,
        int(periodo_id),
        int(curso_cod),
        int(materia_cod),
        int(activo),
        int(activo),
        int(activo),
    )

    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_horarios_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
) -> list[tuple[str, str, int, str]]:
    """
    Retorna:
    (dia_cod, dia_nombre, jornada_id, jornada)
    """
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
    """
    Devuelve el primer horario activo de la materia:
    (dia_cod, dia_nombre, jornada_id, jornada)

    Nota:
    si la materia tiene más de un horario, toma el primero por orden de día/jornada.
    """
    rows = fetch_horarios_materia(conn, materia_cod=materia_cod)
    return rows[0] if rows else None


def fetch_estudiantes_matriculados(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
) -> list[tuple[str, str]]:
    """
    Estudiantes activos matriculados en la combinación exacta:
    período + curso + materia + docente
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            e.Carnet,
            e.Nombre_Completo
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Estudiantes e
            ON e.Carnet = mm.Carnet
        WHERE mm.Periodo_Id = ?
          AND m.Curso_Cod = ?
          AND mm.Materia_Cod = ?
          AND mm.Docente_Cod = ?
          AND mm.Estado_Codigo = ?
          AND m.Estado_Codigo = ?
          AND e.Estado_Codigo = ?
        ORDER BY e.Nombre_Completo ASC;
        """,
        int(periodo_id),
        int(curso_cod),
        int(materia_cod),
        int(docente_cod),
        int(activo),
        int(activo),
        int(activo),
    )

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
    """
    Busca una lista existente por la llave única del negocio.

    Retorna:
    (
        Asistencia_Lista_Id,
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
    """
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
    """
    Retorna cabecera enriquecida:
    (
        Asistencia_Lista_Id,
        Periodo_Id,
        Periodo_Label,
        Curso_Cod,
        Curso_Desc,
        Materia_Cod,
        Materia_Desc,
        Docente_Cod,
        Docente_Nombre,
        Dia_Cod,
        Dia_Nombre,
        Fecha_Clase,
        Fecha_Registro,
        Codigo_Usuario,
        Estado_Codigo
    )
    """
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
    """
    Retorna:
    (
        Asistencia_Detalle_Id,
        Carnet,
        Nombre_Completo,
        Estado_Asistencia,
        Observacion,
        Estado_Codigo
    )
    """
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

    # Evitar que un carnet quede en ambas listas
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
    """
    Reemplaza completamente el detalle de la lista.
    """
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
) -> int:
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(DISTINCT e.Carnet)
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Estudiantes e
            ON e.Carnet = mm.Carnet
        WHERE mm.Periodo_Id = ?
          AND m.Curso_Cod = ?
          AND mm.Materia_Cod = ?
          AND mm.Docente_Cod = ?
          AND mm.Estado_Codigo = ?
          AND m.Estado_Codigo = ?
          AND e.Estado_Codigo = ?;
        """,
        int(periodo_id),
        int(curso_cod),
        int(materia_cod),
        int(docente_cod),
        int(activo),
        int(activo),
        int(activo),
    )

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