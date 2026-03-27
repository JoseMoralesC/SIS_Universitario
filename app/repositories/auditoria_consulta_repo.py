from __future__ import annotations

import pyodbc


def _row_to_dict(row) -> dict:
    return {
        "auditoria_id": int(row[0]) if row[0] is not None else None,
        "codigo_usuario": int(row[1]) if row[1] is not None else None,
        "fecha_movimiento": row[2],
        "movimiento_cod": int(row[3]) if row[3] is not None else None,
        "id_tabla": str(row[4]) if row[4] is not None else "",
        "id_row_tabla": str(row[5]) if row[5] is not None else "",
        "usuario_login": str(row[6]) if row[6] is not None else "",
        "nombre_usuario": str(row[7]) if row[7] is not None else "",
    }


def list_auditoria(
    conn: pyodbc.Connection,
    *,
    codigo_usuario: int | None = None,
    movimiento_cod: int | None = None,
    id_tabla: str | None = None,
    texto: str | None = None,
    top: int = 300,
) -> list[dict]:
    """
    Lista registros de auditoría con filtros opcionales.

    Incluye join a dbo.Usuarios para mostrar datos más legibles
    del usuario que ejecutó el movimiento.
    """
    top = int(top) if top else 300
    if top <= 0:
        top = 300

    sql = """
    SELECT TOP (?)
        a.Auditoria_Id,
        a.Codigo_Usuario,
        a.Fecha_Movimiento,
        a.Movimiento_Cod,
        a.Id_Tabla,
        a.Id_Row_Tabla,
        ISNULL(u.Usuario, '') AS Usuario_Login,
        ISNULL(u.Nombre_Usuario, '') AS Nombre_Usuario
    FROM dbo.Auditoria a
    LEFT JOIN dbo.Usuarios u
        ON u.Codigo_Usuario = a.Codigo_Usuario
    WHERE 1 = 1
    """

    params: list = [top]

    if codigo_usuario is not None:
        sql += " AND a.Codigo_Usuario = ?"
        params.append(int(codigo_usuario))

    if movimiento_cod is not None:
        sql += " AND a.Movimiento_Cod = ?"
        params.append(int(movimiento_cod))

    if id_tabla:
        sql += " AND a.Id_Tabla = ?"
        params.append(str(id_tabla).strip())

    if texto:
        sql += """
        AND (
            CAST(a.Codigo_Usuario AS VARCHAR(20)) LIKE ?
            OR CAST(a.Movimiento_Cod AS VARCHAR(20)) LIKE ?
            OR a.Id_Tabla LIKE ?
            OR a.Id_Row_Tabla LIKE ?
            OR ISNULL(u.Usuario, '') LIKE ?
            OR ISNULL(u.Nombre_Usuario, '') LIKE ?
        )
        """
        like_value = f"%{str(texto).strip()}%"
        params.extend([like_value] * 6)

    sql += " ORDER BY a.Fecha_Movimiento DESC, a.Auditoria_Id DESC;"

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    return [_row_to_dict(row) for row in rows]


def get_distinct_tablas_auditoria(conn: pyodbc.Connection) -> list[str]:
    """
    Retorna las tablas/códigos de tabla distintos existentes en auditoría.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT Id_Tabla
        FROM dbo.Auditoria
        WHERE Id_Tabla IS NOT NULL
          AND LTRIM(RTRIM(Id_Tabla)) <> ''
        ORDER BY Id_Tabla;
        """
    )
    rows = cur.fetchall()
    return [str(r[0]) for r in rows if r and r[0] is not None]


def get_distinct_movimientos_auditoria(conn: pyodbc.Connection) -> list[int]:
    """
    Retorna los códigos de movimiento distintos existentes en auditoría.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT Movimiento_Cod
        FROM dbo.Auditoria
        WHERE Movimiento_Cod IS NOT NULL
        ORDER BY Movimiento_Cod;
        """
    )
    rows = cur.fetchall()
    return [int(r[0]) for r in rows if r and r[0] is not None]


def get_distinct_usuarios_auditoria(conn: pyodbc.Connection) -> list[dict]:
    """
    Retorna usuarios presentes en auditoría para poblar filtros.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT
            a.Codigo_Usuario,
            ISNULL(u.Usuario, '') AS Usuario_Login,
            ISNULL(u.Nombre_Usuario, '') AS Nombre_Usuario
        FROM dbo.Auditoria a
        LEFT JOIN dbo.Usuarios u
            ON u.Codigo_Usuario = a.Codigo_Usuario
        ORDER BY a.Codigo_Usuario;
        """
    )
    rows = cur.fetchall()

    result: list[dict] = []
    for row in rows:
        result.append(
            {
                "codigo_usuario": int(row[0]) if row[0] is not None else None,
                "usuario_login": str(row[1]) if row[1] is not None else "",
                "nombre_usuario": str(row[2]) if row[2] is not None else "",
            }
        )
    return result


def list_movimientos_catalogo(conn: pyodbc.Connection) -> list[dict]:
    """
    Consulta el catálogo oficial de movimientos desde dbo.Movimiento_Auditoria.
    Retorna únicamente los campos relevantes para el diccionario del auditor.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            Movimiento_Cod,
            Descripcion,
            Estado_Codigo
        FROM dbo.Movimiento_Auditoria
        ORDER BY Movimiento_Cod;
        """
    )
    rows = cur.fetchall()

    result: list[dict] = []
    for row in rows:
        result.append(
            {
                "movimiento_cod": int(row[0]) if row[0] is not None else None,
                "descripcion": str(row[1]) if row[1] is not None else "",
                "estado_codigo": int(row[2]) if row[2] is not None else None,
            }
        )
    return result