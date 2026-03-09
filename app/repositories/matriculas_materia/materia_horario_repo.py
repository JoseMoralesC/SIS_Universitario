# app/repositories/matriculas_materia/materia_horario_repo.py
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


def exists_materia(conn: pyodbc.Connection, materia_cod: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT TOP 1 1 FROM dbo.Materias WHERE Materia_Cod = ?;",
        (int(materia_cod),),
    )
    return cur.fetchone() is not None


def exists_horario(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
    dia_cod: str,
    jornada_id: int,
) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Materia_Horario
        WHERE Materia_Cod = ?
          AND Dia_Cod = ?
          AND Jornada_Id = ?;
        """,
        (int(materia_cod), dia_cod, int(jornada_id)),
    )
    return cur.fetchone() is not None


# =========================================================
# Lookups
# =========================================================
def fetch_dias_semana(conn: pyodbc.Connection) -> list[tuple[str, str]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Dia_Cod, Dia_Nombre
        FROM dbo.Dias_Semana
        ORDER BY Dia_Orden;
        """
    )
    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_jornadas(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Jornada_Id, Jornada
        FROM dbo.Jornadas
        ORDER BY Jornada_Id;
        """
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def fetch_materias_activas(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT Materia_Cod, Descripcion
        FROM dbo.Materias
        WHERE Estado_Codigo = ?
        ORDER BY Materia_Cod;
        """,
        (int(activo),),
    )

    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


# =========================================================
# Grid
# =========================================================
def list_materia_horarios(conn: pyodbc.Connection) -> list[tuple]:

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            mh.MateriaHorario_Id,
            m.Materia_Cod,
            m.Descripcion,
            mh.Dia_Cod,
            ds.Dia_Nombre,
            mh.Jornada_Id,
            j.Jornada,
            eg.Estado_Desc
        FROM dbo.Materia_Horario mh
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mh.Materia_Cod
        INNER JOIN dbo.Dias_Semana ds
            ON ds.Dia_Cod = mh.Dia_Cod
        INNER JOIN dbo.Jornadas j
            ON j.Jornada_Id = mh.Jornada_Id
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = mh.Estado_Codigo
        ORDER BY m.Materia_Cod, ds.Dia_Orden, j.Jornada_Id;
        """
    )

    rows: list[tuple] = []

    for row in cur.fetchall():

        (
            horario_id,
            materia_cod,
            materia_desc,
            dia_cod,
            dia_nombre,
            jornada_id,
            jornada,
            estado_desc,
        ) = row

        rows.append(
            (
                int(horario_id),
                f"{int(materia_cod)} - {materia_desc}",
                f"{dia_cod} - {dia_nombre}",
                f"{int(jornada_id)} - {jornada}",
                estado_desc,
            )
        )

    return rows


# =========================================================
# Commands
# =========================================================
def insert_materia_horario(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
    dia_cod: str,
    jornada_id: int,
    estado_codigo: int,
):

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO dbo.Materia_Horario
        (
            Materia_Cod,
            Dia_Cod,
            Jornada_Id,
            Estado_Codigo,
            Fecha_Registro
        )
        VALUES (?, ?, ?, ?, SYSDATETIME());
        """,
        (
            int(materia_cod),
            dia_cod,
            int(jornada_id),
            int(estado_codigo),
        ),
    )

    conn.commit()


def update_estado_materia_horario(
    conn: pyodbc.Connection,
    *,
    horario_id: int,
    nuevo_estado: int,
):

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE dbo.Materia_Horario
        SET Estado_Codigo = ?
        WHERE MateriaHorario_Id = ?;
        """,
        (int(nuevo_estado), int(horario_id)),
    )

    conn.commit()


def delete_materia_horario(
    conn: pyodbc.Connection,
    *,
    horario_id: int,
):

    inactivo = get_estado_codigo_by_desc(conn, "Inactivo")

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE dbo.Materia_Horario
        SET Estado_Codigo = ?
        WHERE MateriaHorario_Id = ?;
        """,
        (int(inactivo), int(horario_id)),
    )

    conn.commit()