# app/repositories/mantenimientos/periodos_repo.py
from __future__ import annotations

import pyodbc
from datetime import date


# =========================================================
# Helpers
# =========================================================
def get_estado_codigo_by_desc(conn: pyodbc.Connection, estado_desc: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Estado_Codigo
        FROM dbo.Estado_General
        WHERE Estado_Desc = ?;
        """,
        ((estado_desc or "").strip(),),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"No se encontró el estado: {estado_desc}")
    return int(row[0])


# =========================================================
# Lookups
# =========================================================
def fetch_estados_generales(conn: pyodbc.Connection) -> list[tuple[int, str]]:
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
# Grid
# =========================================================
def list_periodos(conn: pyodbc.Connection) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            p.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo,
            p.Fecha_Inicio,
            p.Fecha_Fin,
            eg.Estado_Desc
        FROM dbo.Periodos p
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = p.Estado_Codigo
        ORDER BY p.Anio DESC, p.Numero_Periodo ASC;
        """
    )

    rows: list[tuple] = []
    for r in cur.fetchall():
        rows.append(
            (
                int(r[0]),
                str(r[1]),
                int(r[2]),
                int(r[3]),
                str(r[4]),
                str(r[5]),
                str(r[6]),
            )
        )
    return rows


# =========================================================
# Queries específicas
# =========================================================
def exists_periodo_id(conn: pyodbc.Connection, periodo_id: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Periodos
        WHERE Periodo_Id = ?;
        """,
        (int(periodo_id),),
    )
    return cur.fetchone() is not None


def exists_periodo_anio_numero(
    conn: pyodbc.Connection,
    *,
    anio: int,
    numero_periodo: int,
    exclude_periodo_id: int | None = None,
) -> bool:
    cur = conn.cursor()

    if exclude_periodo_id is None:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Periodos
            WHERE Anio = ?
              AND Numero_Periodo = ?;
            """,
            (int(anio), int(numero_periodo)),
        )
    else:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Periodos
            WHERE Anio = ?
              AND Numero_Periodo = ?
              AND Periodo_Id <> ?;
            """,
            (int(anio), int(numero_periodo), int(exclude_periodo_id)),
        )

    return cur.fetchone() is not None


def exists_periodo_codigo(
    conn: pyodbc.Connection,
    *,
    periodo_codigo: str,
    exclude_periodo_id: int | None = None,
) -> bool:
    cur = conn.cursor()

    if exclude_periodo_id is None:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Periodos
            WHERE Periodo_Codigo = ?;
            """,
            ((periodo_codigo or "").strip(),),
        )
    else:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Periodos
            WHERE Periodo_Codigo = ?
              AND Periodo_Id <> ?;
            """,
            ((periodo_codigo or "").strip(), int(exclude_periodo_id)),
        )

    return cur.fetchone() is not None


# =========================================================
# Commands
# =========================================================
def insert_periodo(
    conn: pyodbc.Connection,
    *,
    periodo_codigo: str,
    anio: int,
    numero_periodo: int,
    fecha_inicio: date,
    fecha_fin: date,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Periodos
        (
            Periodo_Codigo,
            Anio,
            Numero_Periodo,
            Fecha_Inicio,
            Fecha_Fin,
            Estado_Codigo
        )
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            (periodo_codigo or "").strip(),
            int(anio),
            int(numero_periodo),
            fecha_inicio,
            fecha_fin,
            int(estado_codigo),
        ),
    )
    conn.commit()


def update_periodo(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    periodo_codigo: str,
    anio: int,
    numero_periodo: int,
    fecha_inicio: date,
    fecha_fin: date,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Periodos
        SET
            Periodo_Codigo = ?,
            Anio = ?,
            Numero_Periodo = ?,
            Fecha_Inicio = ?,
            Fecha_Fin = ?,
            Estado_Codigo = ?
        WHERE Periodo_Id = ?;
        """,
        (
            (periodo_codigo or "").strip(),
            int(anio),
            int(numero_periodo),
            fecha_inicio,
            fecha_fin,
            int(estado_codigo),
            int(periodo_id),
        ),
    )
    conn.commit()


def soft_delete_periodo(conn: pyodbc.Connection, *, periodo_id: int) -> None:
    inactivo = get_estado_codigo_by_desc(conn, "Inactivo")

    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Periodos
        SET Estado_Codigo = ?
        WHERE Periodo_Id = ?;
        """,
        (int(inactivo), int(periodo_id)),
    )
    conn.commit()