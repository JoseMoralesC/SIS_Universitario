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


def list_becas(conn: pyodbc.Connection) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id_beca, nombre_beca, porcentaje_descuento, Estado_Codigo
        FROM dbo.Becas
        ORDER BY id_beca DESC;
        """
    )
    return [tuple(r) for r in cur.fetchall()]


def list_becas_join_activos(conn: pyodbc.Connection) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            b.id_beca,
            b.nombre_beca,
            b.porcentaje_descuento
        FROM dbo.Becas b
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = b.Estado_Codigo
        WHERE ISNULL(eg.Estado_Desc, '') <> 'Inactivo'
        ORDER BY b.id_beca DESC;
        """
    )
    return [tuple(r) for r in cur.fetchall()]


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

def insert_beca(
    conn: pyodbc.Connection,
    *,
    nombre_beca: str,
    porcentaje_descuento: int,
    estado_codigo: int = 1,
) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Becas (nombre_beca, porcentaje_descuento, Estado_Codigo)
        OUTPUT INSERTED.id_beca
        VALUES (?, ?, ?);
        """,
        (
            (nombre_beca or "").strip(),
            int(porcentaje_descuento),
            int(estado_codigo),
        ),
    )
    row = cur.fetchone()
    conn.commit()

    if not row or row[0] is None:
        raise RuntimeError("No se pudo obtener el id_beca generado.")

    return int(row[0])


def update_beca(
    conn: pyodbc.Connection,
    *,
    id_beca: int,
    nombre_beca: str,
    porcentaje_descuento: int,
    estado_codigo: int = 1,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Becas
        SET nombre_beca = ?,
            porcentaje_descuento = ?,
            Estado_Codigo = ?
        WHERE id_beca = ?;
        """,
        (
            (nombre_beca or "").strip(),
            int(porcentaje_descuento),
            int(estado_codigo),
            int(id_beca),
        ),
    )
    conn.commit()


def soft_delete_beca(conn: pyodbc.Connection, id_beca: int) -> None:
    try:
        inactivo_cod = get_estado_codigo_by_desc(conn, "Inactivo")
    except Exception:
        inactivo_cod = 0

    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.Becas SET Estado_Codigo = ? WHERE id_beca = ?;",
        (int(inactivo_cod), int(id_beca)),
    )
    conn.commit()