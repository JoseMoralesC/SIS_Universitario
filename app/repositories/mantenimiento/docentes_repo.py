# app/repositories/docentes_repo.py
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


def fetch_profesiones(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        "SELECT Profesion_Cod, Descripcion FROM dbo.Profesiones ORDER BY Profesion_Cod;"
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def get_estado_codigo_by_desc(conn: pyodbc.Connection, estado_desc: str) -> int:
    """
    Obtiene el Estado_Codigo según Estado_Desc (ej: 'Inactivo').
    Lanza ValueError si no existe.
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

def list_docentes_join(conn: pyodbc.Connection) -> list[tuple]:
    """
    Devuelve filas para el grid con JOIN:
    (Docente_Cod, Identificacion, Usuario_Docente, Nombre_Completo, Estado_Desc, Profesion_Desc)
    Incluye todos los estados.
    """
    sql = """
    SELECT
        d.Docente_Cod,
        d.Identificacion,
        d.Usuario_Docente,
        d.Nombre_Completo,
        eg.Estado_Desc AS Estado,
        p.Descripcion AS Profesion
    FROM dbo.Docentes d
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = d.Estado_Codigo
    LEFT JOIN dbo.Profesiones p     ON p.Profesion_Cod  = d.Profesion_Cod
    ORDER BY d.Docente_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


def list_docentes_join_activos(conn: pyodbc.Connection) -> list[tuple]:
    """
    Grid: NO mostrar registros Inactivos.
    Muestra Activo + Suspendido (y cualquier otro excepto Inactivo).
    """
    sql = """
    SELECT
        d.Docente_Cod,
        d.Identificacion,
        d.Usuario_Docente,
        d.Nombre_Completo,
        eg.Estado_Desc AS Estado,
        p.Descripcion AS Profesion
    FROM dbo.Docentes d
    LEFT JOIN dbo.Estado_General eg ON eg.Estado_Codigo = d.Estado_Codigo
    LEFT JOIN dbo.Profesiones p     ON p.Profesion_Cod  = d.Profesion_Cod
    WHERE eg.Estado_Desc <> 'Inactivo'
    ORDER BY d.Docente_Cod DESC;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return [tuple(r) for r in cur.fetchall()]


# ==========================
# CRUD
# ==========================

def insert_docente(
    conn: pyodbc.Connection,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Docentes
            (Docente_Cod, Identificacion, Usuario_Docente, Nombre_Completo, Estado_Codigo, Profesion_Cod)
        VALUES
            (?, ?, ?, ?, ?, ?);
        """,
        (int(docente_cod), identificacion, usuario_docente, nombre_completo, int(estado_codigo), int(profesion_cod)),
    )
    conn.commit()


def update_docente(
    conn: pyodbc.Connection,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
) -> None:
    sql = """
    UPDATE dbo.Docentes
    SET Identificacion = ?,
        Usuario_Docente = ?,
        Nombre_Completo = ?,
        Estado_Codigo = ?,
        Profesion_Cod = ?
    WHERE Docente_Cod = ?;
    """
    cur = conn.cursor()
    cur.execute(
        sql,
        identificacion,
        usuario_docente,
        nombre_completo,
        int(estado_codigo),
        int(profesion_cod),
        int(docente_cod),
    )
    conn.commit()


def delete_docente(conn: pyodbc.Connection, docente_cod: int) -> None:
    """
    LEGACY: borrado físico.
    Mantengo la función por compatibilidad, pero NO debería usarse en UI.
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.Docentes WHERE Docente_Cod = ?;", int(docente_cod))
    conn.commit()


def soft_delete_docente(conn: pyodbc.Connection, docente_cod: int) -> None:
    """
    Borrado lógico: asigna Estado_Codigo correspondiente a 'Inactivo'.
    """
    inactivo_cod = get_estado_codigo_by_desc(conn, "Inactivo")

    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.Docentes SET Estado_Codigo = ? WHERE Docente_Cod = ?;",
        (int(inactivo_cod), int(docente_cod)),
    )
    if cur.rowcount == 0:
        raise ValueError("No existe el docente seleccionado para eliminar.")
    conn.commit()


# ==========================
# Unicidad (anti-duplicados)
# ==========================

def exists_identificacion(conn: pyodbc.Connection, identificacion: str, exclude_docente_cod: int | None = None) -> bool:
    identificacion = (identificacion or "").strip()
    cur = conn.cursor()

    if exclude_docente_cod is None:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Docentes WHERE Identificacion = ?;",
            identificacion,
        )
    else:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Docentes WHERE Identificacion = ? AND Docente_Cod <> ?;",
            (identificacion, int(exclude_docente_cod)),
        )
    return cur.fetchone() is not None


def exists_usuario_docente(conn: pyodbc.Connection, usuario_docente: str, exclude_docente_cod: int | None = None) -> bool:
    usuario_docente = (usuario_docente or "").strip()
    cur = conn.cursor()

    if exclude_docente_cod is None:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Docentes WHERE Usuario_Docente = ?;",
            usuario_docente,
        )
    else:
        cur.execute(
            "SELECT TOP 1 1 FROM dbo.Docentes WHERE Usuario_Docente = ? AND Docente_Cod <> ?;",
            (usuario_docente, int(exclude_docente_cod)),
        )
    return cur.fetchone() is not None


# ==========================
# Util
# ==========================

def next_docente_cod(conn: pyodbc.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT ISNULL(MAX(Docente_Cod), 0) + 1 FROM dbo.Docentes;")
    return int(cur.fetchone()[0])

def next_carnet(conn: pyodbc.Connection) -> int:
    """
    Devuelve el siguiente carnet numérico (MAX + 1).
    Si existen carnets no numéricos, se ignoran.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ISNULL(MAX(TRY_CONVERT(int, Carnet)), 0) + 1
        FROM dbo.Estudiantes;
        """
    )
    return int(cur.fetchone()[0])