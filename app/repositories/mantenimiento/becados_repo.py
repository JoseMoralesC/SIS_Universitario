from __future__ import annotations

import pyodbc

ACTIVO = 1
INACTIVO = 2


# ==========================
# Lookups
# ==========================

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


def fetch_becas(conn: pyodbc.Connection) -> list[tuple[int, str, int]]:
    """
    Becas activas para combo:
    (id_beca, nombre_beca, porcentaje_descuento)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id_beca, nombre_beca, porcentaje_descuento
        FROM dbo.Becas
        WHERE Estado_Codigo = ?
        ORDER BY nombre_beca ASC;
        """,
        ACTIVO,
    )
    return [(int(r[0]), str(r[1]), int(r[2])) for r in cur.fetchall()]


def fetch_estudiantes_disponibles_lookup(conn: pyodbc.Connection) -> list[tuple[str, str]]:
    """
    Estudiantes activos NO becados (con beca activa) para combo:
    (carnet, nombre_completo)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT e.Carnet, e.Nombre_Completo
        FROM dbo.Estudiantes e
        INNER JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = e.Estado_Codigo
        WHERE eg.Estado_Desc <> 'Inactivo'
          AND NOT EXISTS (
              SELECT 1
              FROM dbo.Becados bd
              WHERE bd.carnet = e.Carnet
                AND bd.Estado_Codigo = ?
          )
        ORDER BY e.Nombre_Completo ASC;
        """,
        ACTIVO,
    )
    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]


def list_becados_join(conn: pyodbc.Connection, *, only_active: bool = True) -> list[tuple]:
    """
    Grid de becados:
    (id_becado, carnet, nombre_estudiante, id_beca, nombre_beca, porcentaje_descuento, fecha_aplicacion, estado_codigo)
    """
    cur = conn.cursor()

    if only_active:
        cur.execute(
            """
            SELECT
                bd.id_becado,
                bd.carnet,
                e.Nombre_Completo AS nombre_estudiante,
                bd.id_beca,
                b.nombre_beca,
                b.porcentaje_descuento,
                bd.fecha_aplicacion,
                bd.Estado_Codigo
            FROM dbo.Becados bd
            INNER JOIN dbo.Estudiantes e ON e.Carnet = bd.carnet
            INNER JOIN dbo.Becas b ON b.id_beca = bd.id_beca
            WHERE bd.Estado_Codigo = ?
            ORDER BY bd.id_becado DESC;
            """,
            ACTIVO,
        )
    else:
        cur.execute(
            """
            SELECT
                bd.id_becado,
                bd.carnet,
                e.Nombre_Completo AS nombre_estudiante,
                bd.id_beca,
                b.nombre_beca,
                b.porcentaje_descuento,
                bd.fecha_aplicacion,
                bd.Estado_Codigo
            FROM dbo.Becados bd
            INNER JOIN dbo.Estudiantes e ON e.Carnet = bd.carnet
            INNER JOIN dbo.Becas b ON b.id_beca = bd.id_beca
            ORDER BY bd.id_becado DESC;
            """
        )

    return [tuple(r) for r in cur.fetchall()]


def list_becados_join_activos(conn: pyodbc.Connection) -> list[tuple]:
    return list_becados_join(conn, only_active=True)


# ==========================
# Util
# ==========================

def next_id_becado(conn: pyodbc.Connection) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            CAST(IDENT_CURRENT('dbo.Becados') AS INT)
            + CAST(IDENT_INCR('dbo.Becados') AS INT);
        """
    )
    val = cur.fetchone()[0]
    return 1 if val is None else int(val)


def exists_id_becado(conn: pyodbc.Connection, id_becado: int) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dbo.Becados WHERE id_becado = ?;", int(id_becado))
    return cur.fetchone() is not None


def exists_carnet(conn: pyodbc.Connection, carnet: str) -> bool:
    carnet = (carnet or "").strip()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dbo.Estudiantes WHERE Carnet = ?;", carnet)
    return cur.fetchone() is not None


def exists_becado_activo_by_carnet(
    conn: pyodbc.Connection,
    carnet: str,
    exclude_id: int | None = None,
) -> bool:
    carnet = (carnet or "").strip()
    cur = conn.cursor()

    if exclude_id is None:
        cur.execute(
            """
            SELECT 1
            FROM dbo.Becados
            WHERE carnet = ?
              AND Estado_Codigo = ?;
            """,
            carnet,
            ACTIVO,
        )
    else:
        cur.execute(
            """
            SELECT 1
            FROM dbo.Becados
            WHERE carnet = ?
              AND Estado_Codigo = ?
              AND id_becado <> ?;
            """,
            carnet,
            ACTIVO,
            int(exclude_id),
        )

    return cur.fetchone() is not None


# ==========================
# CRUD
# ==========================

def insert_becado(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Becados (carnet, id_beca, fecha_aplicacion, Estado_Codigo)
        OUTPUT INSERTED.id_becado
        VALUES (?, ?, ?, ?);
        """,
        (
            (carnet or "").strip(),
            int(id_beca),
            fecha_aplicacion,
            ACTIVO,
        ),
    )
    row = cur.fetchone()
    conn.commit()
    return int(row[0]) if row and row[0] is not None else 0


def update_becado(
    conn: pyodbc.Connection,
    *,
    id_becado: int,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Becados
        SET carnet = ?, id_beca = ?, fecha_aplicacion = ?
        WHERE id_becado = ?;
        """,
        (
            (carnet or "").strip(),
            int(id_beca),
            fecha_aplicacion,
            int(id_becado),
        ),
    )
    conn.commit()


def soft_delete_becado(conn: pyodbc.Connection, *, id_becado: int) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Becados
        SET Estado_Codigo = ?
        WHERE id_becado = ?;
        """,
        INACTIVO,
        int(id_becado),
    )
    conn.commit()