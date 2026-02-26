# app/repositories/mantenimiento/becas_repo.py
from __future__ import annotations

import pyodbc


# ==========================
# Lookups
# ==========================

def list_becas(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT id_beca, nombre_beca, porcentaje_descuento, Estado_Codigo
        FROM dbo.Becas
        WHERE Estado_Codigo = 1
        ORDER BY id_beca;
    """)
    return cur.fetchall()  # o dicts si ya lo haces así


def fetch_becas_lookup(conn: pyodbc.Connection) -> list[tuple[int, str, int]]:
    """Retorna becas para combo: (id_beca, nombre_beca, porcentaje_descuento)"""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id_beca, nombre_beca, porcentaje_descuento
        FROM dbo.Becas
        ORDER BY nombre_beca ASC;
        """
    )
    return [(int(r[0]), str(r[1]), int(r[2])) for r in cur.fetchall()]


# ==========================
# Util
# ==========================

def next_id_beca(conn: pyodbc.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT ISNULL(MAX(id_beca), 0) + 1 FROM dbo.Becas;")
    return int(cur.fetchone()[0])


def exists_id_beca(conn: pyodbc.Connection, id_beca: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dbo.Becas WHERE id_beca = ?;", int(id_beca))
    return cur.fetchone() is not None


def exists_nombre_beca(conn: pyodbc.Connection, nombre_beca: str, exclude_id: int | None = None) -> bool:
    nombre_beca = (nombre_beca or "").strip()
    cur = conn.cursor()
    if exclude_id is None:
        cur.execute("SELECT 1 FROM dbo.Becas WHERE nombre_beca = ?;", nombre_beca)
    else:
        cur.execute(
            "SELECT 1 FROM dbo.Becas WHERE nombre_beca = ? AND id_beca <> ?;",
            nombre_beca,
            int(exclude_id),
        )
    return cur.fetchone() is not None


def is_beca_in_use(conn: pyodbc.Connection, id_beca: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dbo.Becados WHERE id_beca = ?;", int(id_beca))
    return cur.fetchone() is not None


# ==========================
# CRUD
# ==========================

def insert_beca(conn, nombre_beca: str, porcentaje_descuento: int) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Becas (nombre_beca, porcentaje_descuento)
        OUTPUT INSERTED.id_beca
        VALUES (?, ?);
        """,
        (nombre_beca, int(porcentaje_descuento)),
    )
    row = cur.fetchone()
    conn.commit()

    if not row or row[0] is None:
        raise RuntimeError("No se pudo obtener el id_beca generado (OUTPUT INSERTED devolvió None).")

    return int(row[0])


def update_beca(conn: pyodbc.Connection, *, id_beca: int, nombre_beca: str, porcentaje_descuento: int) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Becas
        SET nombre_beca = ?, porcentaje_descuento = ?
        WHERE id_beca = ?;
        """,
        (nombre_beca or "").strip(),
        int(porcentaje_descuento),
        int(id_beca),
    )
    conn.commit()


def soft_delete_beca(conn, id_beca: int) -> None:
    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.Becas SET Estado_Codigo = 0 WHERE id_beca = ?;",
        int(id_beca),
    )
    conn.commit()
