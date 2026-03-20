# app/repositories/auditoria_repo.py
# Repositorio: inserta y consulta eventos en dbo.Auditoria

from __future__ import annotations

import pyodbc

from app.core.auditoria import (
    Tab,
    get_tabla_codigo,
    stringify_row_id,
)


def _resolver_tabla_codigo(id_tabla: str | None) -> str:
    """
    Resuelve el código final de tabla para auditoría.

    Casos soportados:
    - None -> LEGACY
    - 'D01' -> 'D01'
    - 'Docentes' -> 'D01'
    - 'dbo.Docentes' -> 'D01'
    """
    if not id_tabla:
        return Tab.LEGACY

    valor = str(id_tabla).strip()
    if not valor:
        return Tab.LEGACY

    # Si ya parece un código de catálogo, se respeta.
    # Ej: D01, AL01, LEGACY, etc.
    if valor.upper() == valor and len(valor) <= 10 and " " not in valor:
        return valor

    return get_tabla_codigo(valor, default=Tab.LEGACY)


def insert_auditoria(
    conn: pyodbc.Connection,
    *,
    codigo_usuario: int,
    movimiento_cod: int,
    id_tabla: str | None = None,
    id_row_tabla: object | None = None,
) -> None:
    """
    Inserta un registro en dbo.Auditoria con la nueva estructura.

    Parámetros
    ----------
    conn : pyodbc.Connection
        Conexión activa a SQL Server
    codigo_usuario : int
        Usuario que ejecuta el movimiento
    movimiento_cod : int
        Código del movimiento definido en core.auditoria.Mov
    id_tabla : str | None
        Código de tabla (ej. 'D01') o nombre de tabla (ej. 'Docentes')
    id_row_tabla : object | None
        PK del registro afectado, simple o compuesta
    """
    try:
        tabla_codigo = _resolver_tabla_codigo(id_tabla)
        row_id = stringify_row_id(id_row_tabla)

        sql = """
        INSERT INTO dbo.Auditoria
        (
            Codigo_Usuario,
            Fecha_Movimiento,
            Movimiento_Cod,
            Id_Tabla,
            Id_Row_Tabla
        )
        VALUES
        (
            ?,
            SYSDATETIME(),
            ?,
            ?,
            ?
        );
        """

        cur = conn.cursor()
        cur.execute(
            sql,
            (
                int(codigo_usuario),
                int(movimiento_cod),
                tabla_codigo,
                row_id,
            ),
        )
        conn.commit()

    except pyodbc.Error as e:
        # No detenemos el sistema por fallos de auditoría
        print("Error registrando auditoría:", e)


def insert_auditoria_en_tabla(
    conn: pyodbc.Connection,
    *,
    codigo_usuario: int,
    movimiento_cod: int,
    nombre_tabla: str,
    id_row_tabla: object | None = None,
) -> None:
    """
    Variante práctica cuando el endpoint conoce el nombre de la tabla.
    """
    insert_auditoria(
        conn,
        codigo_usuario=codigo_usuario,
        movimiento_cod=movimiento_cod,
        id_tabla=nombre_tabla,
        id_row_tabla=id_row_tabla,
    )


def insert_auditoria_legacy(
    conn: pyodbc.Connection,
    *,
    codigo_usuario: int,
    movimiento_cod: int,
) -> None:
    """
    Compatibilidad temporal para flujos viejos que aún no envían
    tabla ni id de fila.
    """
    insert_auditoria(
        conn,
        codigo_usuario=codigo_usuario,
        movimiento_cod=movimiento_cod,
        id_tabla=Tab.LEGACY,
        id_row_tabla="N/A",
    )


def list_auditoria_top(
    conn: pyodbc.Connection,
    top: int = 100
):
    """
    Devuelve los últimos N movimientos registrados.
    """

    sql = """
    SELECT TOP (?)
        Auditoria_Id,
        Codigo_Usuario,
        Fecha_Movimiento,
        Movimiento_Cod,
        Id_Tabla,
        Id_Row_Tabla
    FROM dbo.Auditoria
    ORDER BY Auditoria_Id DESC;
    """

    cur = conn.cursor()
    cur.execute(sql, (int(top),))

    return cur.fetchall()