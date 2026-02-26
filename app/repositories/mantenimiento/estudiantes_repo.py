# app/repositories/estudiantes_repo.py
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
        (estado_desc,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Estado no encontrado: {estado_desc}")
    return int(row[0])


# ==========================
# Listado (Grid)
# ==========================

def list_estudiantes_join(conn: pyodbc.Connection) -> list[tuple]:
    sql = """
    SELECT
        e.Carnet,
        e.Identificacion,
        e.Nombre_Completo,
        e.Direccion,
        e.Telefono,
        eg.Estado_Desc AS Estado
    FROM dbo.Estudiantes e
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = e.Estado_Codigo
    ORDER BY e.Carnet DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def list_estudiantes_join_activos(conn: pyodbc.Connection) -> list[tuple]:
    sql = """
    SELECT
        e.Carnet,
        e.Identificacion,
        e.Nombre_Completo,
        e.Direccion,
        e.Telefono,
        eg.Estado_Desc AS Estado
    FROM dbo.Estudiantes e
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = e.Estado_Codigo
    WHERE eg.Estado_Desc <> 'Inactivo'
    ORDER BY e.Carnet DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


# ==========================
# Util
# ==========================

def next_carnet(conn: pyodbc.Connection) -> str:
    """
    Genera el siguiente Carnet con formato: CUC-0001, CUC-0002, ...
    Lee el máximo número a la derecha del prefijo CUC-.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ISNULL(
            MAX(TRY_CONVERT(int, SUBSTRING(Carnet, 5, 20))), 0
        ) + 1
        FROM dbo.Estudiantes
        WHERE Carnet LIKE 'CUC-%'
          AND TRY_CONVERT(int, SUBSTRING(Carnet, 5, 20)) IS NOT NULL;
        """
    )
    n = int(cur.fetchone()[0])

    # mínimo 4 dígitos, pero si pasa de 9999, crece natural
    num_txt = str(n).zfill(4)
    return f"CUC-{num_txt}"


# ==========================
# CRUD
# ==========================

def insert_estudiante(
    conn: pyodbc.Connection,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str | None,
    telefono: str | None,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Estudiantes
            (Carnet, Identificacion, Nombre_Completo, Direccion, Telefono, Estado_Codigo)
        VALUES
            (?, ?, ?, ?, ?, ?);
        """,
        (carnet, identificacion, nombre_completo, direccion, telefono, int(estado_codigo)),
    )
    conn.commit()


def update_estudiante(
    conn: pyodbc.Connection,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str | None,
    telefono: str | None,
    estado_codigo: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Estudiantes
        SET Identificacion = ?,
            Nombre_Completo = ?,
            Direccion = ?,
            Telefono = ?,
            Estado_Codigo = ?
        WHERE Carnet = ?;
        """,
        (identificacion, nombre_completo, direccion, telefono, int(estado_codigo), carnet),
    )
    conn.commit()


def delete_estudiante(conn: pyodbc.Connection, carnet: str) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.Estudiantes WHERE Carnet = ?;", (carnet,))
    conn.commit()


def soft_delete_estudiante(conn: pyodbc.Connection, carnet: str) -> None:
    inactivo_cod = get_estado_codigo_by_desc(conn, "Inactivo")

    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.Estudiantes SET Estado_Codigo = ? WHERE Carnet = ?;",
        (int(inactivo_cod), carnet),
    )
    if cur.rowcount == 0:
        raise ValueError("No existe el estudiante seleccionado para eliminar.")
    conn.commit()


# ==========================
# Unicidad (anti-duplicados)
# ==========================

def exists_carnet(conn: pyodbc.Connection, carnet: str, exclude_carnet: str | None = None) -> bool:
    carnet = (carnet or "").strip()
    cur = conn.cursor()

    if not exclude_carnet:
        cur.execute("SELECT TOP 1 1 FROM dbo.Estudiantes WHERE Carnet = ?;", (carnet,))
    else:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Estudiantes WHERE Carnet = ? AND Carnet <> ?;",
            (carnet, exclude_carnet.strip()),
        )
    return cur.fetchone() is not None


def exists_identificacion(conn: pyodbc.Connection, identificacion: str, exclude_carnet: str | None = None) -> bool:
    identificacion = (identificacion or "").strip()
    cur = conn.cursor()

    if not exclude_carnet:
        cur.execute("SELECT TOP 1 1 FROM dbo.Estudiantes WHERE Identificacion = ?;", (identificacion,))
    else:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Estudiantes WHERE Identificacion = ? AND Carnet <> ?;",
            (identificacion, exclude_carnet.strip()),
        )
    return cur.fetchone() is not None