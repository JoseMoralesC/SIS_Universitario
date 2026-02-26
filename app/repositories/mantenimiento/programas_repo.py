# app/repositories/programas_repo.py
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


def get_estado_codigo_by_desc(conn: pyodbc.Connection, estado_desc: str) -> int:
    """
    Obtiene el Estado_Codigo según Estado_Desc (ej: 'Inactivo').
    """
    estado_desc = (estado_desc or "").strip()
    cur = conn.cursor()
    cur.execute(
        "SELECT Estado_Codigo FROM dbo.Estado_General WHERE Estado_Desc = ?;",
        estado_desc,
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Estado no encontrado: {estado_desc}")
    return int(row[0])


# ==========================
# Listado (Grid)
# ==========================

def list_programas_join(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid:
    (Curso_Cod, Descripcion, Horario (jornadas reales), Precio_Matricula, Estado_Desc)
    """
    sql = """
    SELECT
        cp.Curso_Cod,
        cp.Descripcion,
        ISNULL(j.HorarioReal, 'Sin horario') AS Horario,
        cp.Precio_Matricula,
        eg.Estado_Desc AS Estado
    FROM dbo.Cursos_Programas cp
    LEFT JOIN dbo.Estado_General eg
        ON eg.Estado_Codigo = cp.Estado_Codigo
    OUTER APPLY (
        SELECT STRING_AGG(j2.Jornada, ' + ') WITHIN GROUP (ORDER BY j2.Jornada_Id) AS HorarioReal
        FROM dbo.Curso_Jornadas cj
        INNER JOIN dbo.Jornadas j2 ON j2.Jornada_Id = cj.Jornada_Id
        WHERE cj.Curso_Cod = cp.Curso_Cod
    ) j
    ORDER BY cp.Curso_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def list_programas_join_activos(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid:
    - NO mostrar registros Inactivos
    - Horario muestra jornadas reales (Mañana + Tarde + Noche)
    """
    sql = """
    SELECT
        cp.Curso_Cod,
        cp.Descripcion,
        ISNULL(j.HorarioReal, 'Sin horario') AS Horario,
        cp.Precio_Matricula,
        eg.Estado_Desc AS Estado
    FROM dbo.Cursos_Programas cp
    LEFT JOIN dbo.Estado_General eg
        ON eg.Estado_Codigo = cp.Estado_Codigo
    OUTER APPLY (
        SELECT STRING_AGG(j2.Jornada, ' + ') WITHIN GROUP (ORDER BY j2.Jornada_Id) AS HorarioReal
        FROM dbo.Curso_Jornadas cj
        INNER JOIN dbo.Jornadas j2 ON j2.Jornada_Id = cj.Jornada_Id
        WHERE cj.Curso_Cod = cp.Curso_Cod
    ) j
    WHERE eg.Estado_Desc <> 'Inactivo'
    ORDER BY cp.Curso_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


# ==========================
# Util
# ==========================

def next_curso_cod(conn: pyodbc.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT ISNULL(MAX(Curso_Cod), 0) + 1 FROM dbo.Cursos_Programas;")
    return int(cur.fetchone()[0])


# ==========================
# CRUD (Cursos_Programas)
# ==========================

def insert_programa(
    conn: pyodbc.Connection,
    curso_cod: int,
    descripcion: str,
    horario_tipo_id: int | None,
    precio_matricula: float,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Cursos_Programas
            (Curso_Cod, Descripcion, Horario_TipoId, Precio_Matricula, Estado_Codigo)
        VALUES
            (?, ?, ?, ?, ?);
        """,
        (
            int(curso_cod),
            descripcion,
            None if horario_tipo_id is None else int(horario_tipo_id),
            float(precio_matricula),
            int(estado_codigo),
        ),
    )
    conn.commit()


def update_programa(
    conn: pyodbc.Connection,
    curso_cod: int,
    descripcion: str,
    horario_tipo_id: int | None,
    precio_matricula: float,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Cursos_Programas
        SET Descripcion = ?,
            Horario_TipoId = ?,
            Precio_Matricula = ?,
            Estado_Codigo = ?
        WHERE Curso_Cod = ?;
        """,
        (
            descripcion,
            None if horario_tipo_id is None else int(horario_tipo_id),
            float(precio_matricula),
            int(estado_codigo),
            int(curso_cod),
        ),
    )
    conn.commit()


def delete_programa(conn: pyodbc.Connection, curso_cod: int) -> None:
    """
    LEGACY: borrado físico. No debería usarse en UI.
    """
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM dbo.Cursos_Programas WHERE Curso_Cod = ?;",
        (int(curso_cod),),
    )
    conn.commit()


def soft_delete_programa(conn: pyodbc.Connection, curso_cod: int) -> None:
    """
    Borrado lógico:
    - Asigna Estado_Codigo correspondiente a 'Inactivo'
    """
    inactivo_cod = get_estado_codigo_by_desc(conn, "Inactivo")

    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.Cursos_Programas SET Estado_Codigo = ? WHERE Curso_Cod = ?;",
        (int(inactivo_cod), int(curso_cod)),
    )
    if cur.rowcount == 0:
        raise ValueError("No existe el programa seleccionado para eliminar.")
    conn.commit()


# ==========================
# Unicidad (anti-duplicados)
# ==========================

def exists_programa_descripcion(
    conn: pyodbc.Connection,
    descripcion: str,
    exclude_curso_cod: int | None = None,
) -> bool:
    """
    True si ya existe otro programa con esa Descripcion.
    En update, excluye el mismo Curso_Cod.
    """
    descripcion = (descripcion or "").strip()
    cur = conn.cursor()

    if exclude_curso_cod is None:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Cursos_Programas WHERE Descripcion = ?;",
            (descripcion,),
        )
    else:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Cursos_Programas
            WHERE Descripcion = ?
              AND Curso_Cod <> ?;
            """,
            (descripcion, int(exclude_curso_cod)),
        )

    return cur.fetchone() is not None


# ==========================
# Jornadas por Curso (Curso_Jornadas)
# ==========================

def get_curso_jornadas(conn: pyodbc.Connection, curso_cod: int) -> list[int]:
    """
    Devuelve lista de Jornada_Id asociadas al curso.
    1=Mañana, 2=Tarde, 3=Noche
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Jornada_Id
        FROM dbo.Curso_Jornadas
        WHERE Curso_Cod = ?
        ORDER BY Jornada_Id;
        """,
        (int(curso_cod),),
    )
    return [int(r[0]) for r in cur.fetchall()]


def set_curso_jornadas(conn: pyodbc.Connection, curso_cod: int, jornadas_ids: list[int] | None) -> None:
    """
    Reemplaza jornadas del curso (delete + insert).
    jornadas_ids: lista de ids (1,2,3). Se tolera [] o None.
    """
    jornadas_ids = jornadas_ids or []

    # Limpieza: solo {1,2,3}, sin duplicados
    clean: list[int] = []
    for x in jornadas_ids:
        try:
            jid = int(x)
        except Exception:
            continue
        if jid in (1, 2, 3) and jid not in clean:
            clean.append(jid)
    clean.sort()

    cur = conn.cursor()

    # Borra existentes
    cur.execute(
        "DELETE FROM dbo.Curso_Jornadas WHERE Curso_Cod = ?;",
        (int(curso_cod),),
    )

    # Inserta nuevas
    for jid in clean:
        cur.execute(
            "INSERT INTO dbo.Curso_Jornadas (Curso_Cod, Jornada_Id) VALUES (?, ?);",
            (int(curso_cod), int(jid)),
        )

    conn.commit()