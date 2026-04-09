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


# =========================================================
# Nuevo bloque: resolución de dato/registro afectado
# =========================================================
def _safe_text(value) -> str:
    return str(value or "").strip()


def _safe_upper(value) -> str:
    return _safe_text(value).upper()


def _row_to_columns_dict(cursor, row) -> dict:
    columns = [col[0] for col in cursor.description]
    result: dict = {}
    for idx, col_name in enumerate(columns):
        result[str(col_name)] = row[idx]
    return result


def _format_scalar(value) -> str:
    if value is None:
        return ""
    return str(value)


def _parse_compound_key(raw_value: str) -> dict[str, str]:
    """
    Convierte formatos como:
    - 'curso_cod=507;docente_cod=169'
    - 'Carnet=CUC-0097|Curso_Cod=504|Periodo=2026'
    - 'Materia_Cod=9065|Dia_Cod=K|Jornada_Id=1'
    en un diccionario case-insensitive a nivel de consumo.
    """
    text = _safe_text(raw_value)
    if not text:
        return {}

    normalized = text.replace(";", "|")
    parts = [p.strip() for p in normalized.split("|") if p.strip()]

    result: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[_safe_upper(key)] = _safe_text(value)
    return result


def _is_simple_pk_value(raw_value: str) -> bool:
    text = _safe_text(raw_value)
    if not text:
        return False
    return "=" not in text and "|" not in text and ";" not in text


def _build_detail_payload(
    *,
    ok: bool,
    id_tabla: str,
    id_row_tabla: str,
    tabla_fisica: str | None = None,
    descripcion: str | None = None,
    pk_values: dict | None = None,
    registro: dict | None = None,
    mensaje: str = "",
) -> dict:
    return {
        "ok": bool(ok),
        "id_tabla": _safe_text(id_tabla),
        "id_row_tabla": _safe_text(id_row_tabla),
        "tabla_fisica": _safe_text(tabla_fisica),
        "descripcion": _safe_text(descripcion),
        "pk_values": pk_values or {},
        "registro": registro or {},
        "mensaje": _safe_text(mensaje),
    }


def _query_single_row(
    conn: pyodbc.Connection,
    *,
    sql: str,
    params: list,
) -> dict | None:
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    if not row:
        return None
    return _row_to_columns_dict(cur, row)


def _resolve_u01_usuarios(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["Codigo_Usuario"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            u.Codigo_Usuario,
            u.Id_Usuario,
            u.Usuario,
            u.Nombre_Usuario,
            u.Correo,
            u.Tipo_Usuario,
            tu.Descripcion_Tipo AS Tipo_Usuario_Desc,
            u.Estado_Usuario,
            eu.Descripcion_Estado AS Estado_Usuario_Desc,
            u.Debe_Cambiar_Clave,
            u.Intentos_Fallidos,
            u.Bloqueado_Hasta,
            u.Ultimo_Acceso,
            u.Ultimo_Cambio_Clave,
            u.Fecha_Creacion,
            u.Fecha_Modificacion,
            u.Usuario_Seguridad_Id
        FROM dbo.Usuarios u
        LEFT JOIN dbo.Tipo_Usuario tu
            ON tu.Tipo_Usuario = u.Tipo_Usuario
        LEFT JOIN dbo.Estado_Usuario eu
            ON eu.Estado_Usuario = u.Estado_Usuario
        WHERE u.Codigo_Usuario = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["Codigo_Usuario"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("CODIGO_USUARIO") or parsed.get("USUARIO_SEGURIDAD_ID")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="U01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Usuarios",
                descripcion="Usuarios",
                mensaje="No fue posible interpretar la llave del registro de usuario.",
            )

        if parsed.get("CODIGO_USUARIO"):
            pk_values["Codigo_Usuario"] = parsed["CODIGO_USUARIO"]
            where = "u.Codigo_Usuario = ?"
            param = parsed["CODIGO_USUARIO"]
        else:
            pk_values["Usuario_Seguridad_Id"] = parsed["USUARIO_SEGURIDAD_ID"]
            where = "u.Usuario_Seguridad_Id = ?"
            param = parsed["USUARIO_SEGURIDAD_ID"]

        sql = f"""
        SELECT TOP 1
            u.Codigo_Usuario,
            u.Id_Usuario,
            u.Usuario,
            u.Nombre_Usuario,
            u.Correo,
            u.Tipo_Usuario,
            tu.Descripcion_Tipo AS Tipo_Usuario_Desc,
            u.Estado_Usuario,
            eu.Descripcion_Estado AS Estado_Usuario_Desc,
            u.Debe_Cambiar_Clave,
            u.Intentos_Fallidos,
            u.Bloqueado_Hasta,
            u.Ultimo_Acceso,
            u.Ultimo_Cambio_Clave,
            u.Fecha_Creacion,
            u.Fecha_Modificacion,
            u.Usuario_Seguridad_Id
        FROM dbo.Usuarios u
        LEFT JOIN dbo.Tipo_Usuario tu
            ON tu.Tipo_Usuario = u.Tipo_Usuario
        LEFT JOIN dbo.Estado_Usuario eu
            ON eu.Estado_Usuario = u.Estado_Usuario
        WHERE {where};
        """
        registro = _query_single_row(conn, sql=sql, params=[param])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="U01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Usuarios",
            descripcion="Usuarios",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Usuarios.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="U01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Usuarios",
        descripcion="Usuarios",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_d01_docentes(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["Docente_Cod"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            d.Docente_Cod,
            d.Identificacion,
            d.Usuario_Docente,
            d.Nombre_Completo,
            d.Estado_Codigo,
            eg.Estado_Desc,
            d.Profesion_Cod,
            p.Descripcion AS Profesion
        FROM dbo.Docentes d
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = d.Estado_Codigo
        LEFT JOIN dbo.Profesiones p
            ON p.Profesion_Cod = d.Profesion_Cod
        WHERE d.Docente_Cod = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["Docente_Cod"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("DOCENTE_COD")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="D01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Docentes",
                descripcion="Docentes",
                mensaje="No fue posible interpretar la llave del docente.",
            )

        pk_values["Docente_Cod"] = pk
        sql = """
        SELECT TOP 1
            d.Docente_Cod,
            d.Identificacion,
            d.Usuario_Docente,
            d.Nombre_Completo,
            d.Estado_Codigo,
            eg.Estado_Desc,
            d.Profesion_Cod,
            p.Descripcion AS Profesion
        FROM dbo.Docentes d
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = d.Estado_Codigo
        LEFT JOIN dbo.Profesiones p
            ON p.Profesion_Cod = d.Profesion_Cod
        WHERE d.Docente_Cod = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="D01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Docentes",
            descripcion="Docentes",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Docentes.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="D01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Docentes",
        descripcion="Docentes",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_e01_estudiantes(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["Carnet"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            e.Carnet,
            e.Identificacion,
            e.Nombre_Completo,
            e.Direccion,
            e.Telefono,
            e.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Estudiantes e
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = e.Estado_Codigo
        WHERE e.Carnet = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["Carnet"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("CARNET")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="E01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Estudiantes",
                descripcion="Estudiantes",
                mensaje="No fue posible interpretar la llave del estudiante.",
            )

        pk_values["Carnet"] = pk
        sql = """
        SELECT TOP 1
            e.Carnet,
            e.Identificacion,
            e.Nombre_Completo,
            e.Direccion,
            e.Telefono,
            e.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Estudiantes e
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = e.Estado_Codigo
        WHERE e.Carnet = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="E01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Estudiantes",
            descripcion="Estudiantes",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Estudiantes.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="E01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Estudiantes",
        descripcion="Estudiantes",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_cp01_cursos_programas(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["Curso_Cod"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            cp.Curso_Cod,
            cp.Descripcion,
            cp.Precio_Matricula,
            cp.Estado_Codigo,
            eg.Estado_Desc,
            cp.Horario_TipoId,
            ht.Descripcion AS Horario_Tipo
        FROM dbo.Cursos_Programas cp
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = cp.Estado_Codigo
        LEFT JOIN dbo.Horario_Tipo ht
            ON ht.Horario_TipoId = cp.Horario_TipoId
        WHERE cp.Curso_Cod = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["Curso_Cod"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("CURSO_COD")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="CP01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Cursos_Programas",
                descripcion="Cursos / Programas",
                mensaje="No fue posible interpretar la llave del curso/programa.",
            )

        pk_values["Curso_Cod"] = pk
        sql = """
        SELECT TOP 1
            cp.Curso_Cod,
            cp.Descripcion,
            cp.Precio_Matricula,
            cp.Estado_Codigo,
            eg.Estado_Desc,
            cp.Horario_TipoId,
            ht.Descripcion AS Horario_Tipo
        FROM dbo.Cursos_Programas cp
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = cp.Estado_Codigo
        LEFT JOIN dbo.Horario_Tipo ht
            ON ht.Horario_TipoId = cp.Horario_TipoId
        WHERE cp.Curso_Cod = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="CP01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Cursos_Programas",
            descripcion="Cursos / Programas",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Cursos_Programas.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="CP01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Cursos_Programas",
        descripcion="Cursos / Programas",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_m01_materias(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["Materia_Cod"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            m.Materia_Cod,
            m.Descripcion,
            m.Curso_Cod,
            cp.Descripcion AS Curso,
            m.Estado_Codigo,
            eg.Estado_Desc,
            m.Precio
        FROM dbo.Materias m
        LEFT JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = m.Estado_Codigo
        WHERE m.Materia_Cod = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["Materia_Cod"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("MATERIA_COD")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="M01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Materias",
                descripcion="Materias",
                mensaje="No fue posible interpretar la llave de la materia.",
            )

        pk_values["Materia_Cod"] = pk
        sql = """
        SELECT TOP 1
            m.Materia_Cod,
            m.Descripcion,
            m.Curso_Cod,
            cp.Descripcion AS Curso,
            m.Estado_Codigo,
            eg.Estado_Desc,
            m.Precio
        FROM dbo.Materias m
        LEFT JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = m.Curso_Cod
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = m.Estado_Codigo
        WHERE m.Materia_Cod = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="M01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Materias",
            descripcion="Materias",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Materias.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="M01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Materias",
        descripcion="Materias",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_p01_periodos(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["Periodo_Id"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            p.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo,
            p.Fecha_Inicio,
            p.Fecha_Fin,
            p.Estado_Codigo,
            eg.Estado_Desc,
            p.Fecha_Registro
        FROM dbo.Periodos p
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = p.Estado_Codigo
        WHERE p.Periodo_Id = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["Periodo_Id"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("PERIODO_ID")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="P01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Periodos",
                descripcion="Periodos",
                mensaje="No fue posible interpretar la llave del período.",
            )

        pk_values["Periodo_Id"] = pk
        sql = """
        SELECT TOP 1
            p.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo,
            p.Fecha_Inicio,
            p.Fecha_Fin,
            p.Estado_Codigo,
            eg.Estado_Desc,
            p.Fecha_Registro
        FROM dbo.Periodos p
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = p.Estado_Codigo
        WHERE p.Periodo_Id = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="P01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Periodos",
            descripcion="Periodos",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Periodos.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="P01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Periodos",
        descripcion="Periodos",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_bec01_becas(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["id_beca"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            b.id_beca,
            b.nombre_beca,
            b.porcentaje_descuento,
            b.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Becas b
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = b.Estado_Codigo
        WHERE b.id_beca = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["id_beca"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("ID_BECA")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="BEC01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Becas",
                descripcion="Becas",
                mensaje="No fue posible interpretar la llave de la beca.",
            )

        pk_values["id_beca"] = pk
        sql = """
        SELECT TOP 1
            b.id_beca,
            b.nombre_beca,
            b.porcentaje_descuento,
            b.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Becas b
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = b.Estado_Codigo
        WHERE b.id_beca = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="BEC01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Becas",
            descripcion="Becas",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Becas.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="BEC01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Becas",
        descripcion="Becas",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_becd01_becados(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["id_becado"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            b.id_becado,
            b.carnet,
            e.Nombre_Completo AS Estudiante,
            b.id_beca,
            be.nombre_beca,
            be.porcentaje_descuento,
            b.fecha_aplicacion,
            b.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Becados b
        LEFT JOIN dbo.Estudiantes e
            ON e.Carnet = b.carnet
        LEFT JOIN dbo.Becas be
            ON be.id_beca = b.id_beca
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = b.Estado_Codigo
        WHERE b.id_becado = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["id_becado"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("ID_BECADO")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="BECD01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Becados",
                descripcion="Becados",
                mensaje="No fue posible interpretar la llave del becado.",
            )

        pk_values["id_becado"] = pk
        sql = """
        SELECT TOP 1
            b.id_becado,
            b.carnet,
            e.Nombre_Completo AS Estudiante,
            b.id_beca,
            be.nombre_beca,
            be.porcentaje_descuento,
            b.fecha_aplicacion,
            b.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Becados b
        LEFT JOIN dbo.Estudiantes e
            ON e.Carnet = b.carnet
        LEFT JOIN dbo.Becas be
            ON be.id_beca = b.id_beca
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = b.Estado_Codigo
        WHERE b.id_becado = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="BECD01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Becados",
            descripcion="Becados",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Becados.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="BECD01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Becados",
        descripcion="Becados",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_al01_asistencia_lista(conn: pyodbc.Connection, raw_id: str) -> dict:
    pk_values: dict[str, str] = {}

    if _is_simple_pk_value(raw_id):
        pk_values["Asistencia_Lista_Id"] = _safe_text(raw_id)
        sql = """
        SELECT TOP 1
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo,
            al.Curso_Cod,
            cp.Descripcion AS Curso,
            al.Materia_Cod,
            m.Descripcion AS Materia,
            al.Docente_Cod,
            d.Nombre_Completo AS Docente,
            al.Dia_Cod,
            ds.Dia_Nombre,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Asistencia_Lista al
        LEFT JOIN dbo.Periodos p
            ON p.Periodo_Id = al.Periodo_Id
        LEFT JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = al.Curso_Cod
        LEFT JOIN dbo.Materias m
            ON m.Materia_Cod = al.Materia_Cod
        LEFT JOIN dbo.Docentes d
            ON d.Docente_Cod = al.Docente_Cod
        LEFT JOIN dbo.Dias_Semana ds
            ON ds.Dia_Cod = al.Dia_Cod
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = al.Estado_Codigo
        WHERE al.Asistencia_Lista_Id = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk_values["Asistencia_Lista_Id"]])
    else:
        parsed = _parse_compound_key(raw_id)
        pk = parsed.get("ASISTENCIA_LISTA_ID")
        if not pk:
            return _build_detail_payload(
                ok=False,
                id_tabla="AL01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Asistencia_Lista",
                descripcion="Asistencia / Lista",
                mensaje="No fue posible interpretar la llave de la asistencia.",
            )

        pk_values["Asistencia_Lista_Id"] = pk
        sql = """
        SELECT TOP 1
            al.Asistencia_Lista_Id,
            al.Periodo_Id,
            p.Periodo_Codigo,
            p.Anio,
            p.Numero_Periodo,
            al.Curso_Cod,
            cp.Descripcion AS Curso,
            al.Materia_Cod,
            m.Descripcion AS Materia,
            al.Docente_Cod,
            d.Nombre_Completo AS Docente,
            al.Dia_Cod,
            ds.Dia_Nombre,
            al.Fecha_Clase,
            al.Fecha_Registro,
            al.Codigo_Usuario,
            al.Estado_Codigo,
            eg.Estado_Desc
        FROM dbo.Asistencia_Lista al
        LEFT JOIN dbo.Periodos p
            ON p.Periodo_Id = al.Periodo_Id
        LEFT JOIN dbo.Cursos_Programas cp
            ON cp.Curso_Cod = al.Curso_Cod
        LEFT JOIN dbo.Materias m
            ON m.Materia_Cod = al.Materia_Cod
        LEFT JOIN dbo.Docentes d
            ON d.Docente_Cod = al.Docente_Cod
        LEFT JOIN dbo.Dias_Semana ds
            ON ds.Dia_Cod = al.Dia_Cod
        LEFT JOIN dbo.Estado_General eg
            ON eg.Estado_Codigo = al.Estado_Codigo
        WHERE al.Asistencia_Lista_Id = ?;
        """
        registro = _query_single_row(conn, sql=sql, params=[pk])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="AL01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Asistencia_Lista",
            descripcion="Asistencia / Lista",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Asistencia_Lista.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="AL01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Asistencia_Lista",
        descripcion="Asistencia / Lista",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_cd01_curso_docente(conn: pyodbc.Connection, raw_id: str) -> dict:
    parsed = _parse_compound_key(raw_id)
    curso_cod = parsed.get("CURSO_COD")
    docente_cod = parsed.get("DOCENTE_COD")

    pk_values = {
        "Curso_Cod": _safe_text(curso_cod),
        "Docente_Cod": _safe_text(docente_cod),
    }

    if not curso_cod or not docente_cod:
        return _build_detail_payload(
            ok=False,
            id_tabla="CD01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Curso_Docente",
            descripcion="Asignación Curso-Docente",
            pk_values=pk_values,
            mensaje="No fue posible interpretar la llave compuesta de dbo.Curso_Docente.",
        )

    sql = """
    SELECT TOP 1
        cd.Curso_Cod,
        cp.Descripcion AS Curso,
        cd.Docente_Cod,
        d.Nombre_Completo AS Docente,
        d.Usuario_Docente,
        d.Identificacion
    FROM dbo.Curso_Docente cd
    LEFT JOIN dbo.Cursos_Programas cp
        ON cp.Curso_Cod = cd.Curso_Cod
    LEFT JOIN dbo.Docentes d
        ON d.Docente_Cod = cd.Docente_Cod
    WHERE cd.Curso_Cod = ?
      AND cd.Docente_Cod = ?;
    """
    registro = _query_single_row(conn, sql=sql, params=[curso_cod, docente_cod])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="CD01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Curso_Docente",
            descripcion="Asignación Curso-Docente",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Curso_Docente.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="CD01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Curso_Docente",
        descripcion="Asignación Curso-Docente",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_dm01_docente_materia(conn: pyodbc.Connection, raw_id: str) -> dict:
    parsed = _parse_compound_key(raw_id)
    docente_cod = parsed.get("DOCENTE_COD")
    materia_cod = parsed.get("MATERIA_COD")

    pk_values = {
        "Docente_Cod": _safe_text(docente_cod),
        "Materia_Cod": _safe_text(materia_cod),
    }

    if not docente_cod or not materia_cod:
        return _build_detail_payload(
            ok=False,
            id_tabla="DM01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Docente_Materia",
            descripcion="Asignación Docente-Materia",
            pk_values=pk_values,
            mensaje="No fue posible interpretar la llave compuesta de dbo.Docente_Materia.",
        )

    sql = """
    SELECT TOP 1
        dm.Docente_Cod,
        d.Nombre_Completo AS Docente,
        dm.Materia_Cod,
        m.Descripcion AS Materia,
        m.Curso_Cod,
        cp.Descripcion AS Curso,
        dm.Estado_Codigo,
        eg.Estado_Desc,
        dm.Fecha_Registro
    FROM dbo.Docente_Materia dm
    LEFT JOIN dbo.Docentes d
        ON d.Docente_Cod = dm.Docente_Cod
    LEFT JOIN dbo.Materias m
        ON m.Materia_Cod = dm.Materia_Cod
    LEFT JOIN dbo.Cursos_Programas cp
        ON cp.Curso_Cod = m.Curso_Cod
    LEFT JOIN dbo.Estado_General eg
        ON eg.Estado_Codigo = dm.Estado_Codigo
    WHERE dm.Docente_Cod = ?
      AND dm.Materia_Cod = ?;
    """
    registro = _query_single_row(conn, sql=sql, params=[docente_cod, materia_cod])

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="DM01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Docente_Materia",
            descripcion="Asignación Docente-Materia",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Docente_Materia.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="DM01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Docente_Materia",
        descripcion="Asignación Docente-Materia",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_mh01_materia_horario(conn: pyodbc.Connection, raw_id: str) -> dict:
    parsed = _parse_compound_key(raw_id)
    materia_cod = parsed.get("MATERIA_COD")
    dia_cod = parsed.get("DIA_COD")
    jornada_id = parsed.get("JORNADA_ID")

    pk_values = {
        "Materia_Cod": _safe_text(materia_cod),
        "Dia_Cod": _safe_text(dia_cod),
        "Jornada_Id": _safe_text(jornada_id),
    }

    if not materia_cod or not dia_cod or not jornada_id:
        return _build_detail_payload(
            ok=False,
            id_tabla="MH01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Materia_Horario",
            descripcion="Horario de Materia",
            pk_values=pk_values,
            mensaje="No fue posible interpretar la llave compuesta de dbo.Materia_Horario.",
        )

    sql = """
    SELECT TOP 1
        mh.MateriaHorario_Id,
        mh.Materia_Cod,
        m.Descripcion AS Materia,
        m.Curso_Cod,
        cp.Descripcion AS Curso,
        mh.Dia_Cod,
        ds.Dia_Nombre,
        mh.Jornada_Id,
        j.Jornada,
        mh.Estado_Codigo,
        eg.Estado_Desc,
        mh.Fecha_Registro
    FROM dbo.Materia_Horario mh
    LEFT JOIN dbo.Materias m
        ON m.Materia_Cod = mh.Materia_Cod
    LEFT JOIN dbo.Cursos_Programas cp
        ON cp.Curso_Cod = m.Curso_Cod
    LEFT JOIN dbo.Dias_Semana ds
        ON ds.Dia_Cod = mh.Dia_Cod
    LEFT JOIN dbo.Jornadas j
        ON j.Jornada_Id = mh.Jornada_Id
    LEFT JOIN dbo.Estado_General eg
        ON eg.Estado_Codigo = mh.Estado_Codigo
    WHERE mh.Materia_Cod = ?
      AND mh.Dia_Cod = ?
      AND mh.Jornada_Id = ?;
    """
    registro = _query_single_row(
        conn,
        sql=sql,
        params=[materia_cod, dia_cod, jornada_id],
    )

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="MH01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Materia_Horario",
            descripcion="Horario de Materia",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Materia_Horario.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="MH01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Materia_Horario",
        descripcion="Horario de Materia",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_mc01_matricula_curso(conn: pyodbc.Connection, raw_id: str) -> dict:
    parsed = _parse_compound_key(raw_id)

    carnet = parsed.get("CARNET")
    curso_cod = parsed.get("CURSO_COD")
    periodo = parsed.get("PERIODO")

    pk_values = {
        "Carnet": _safe_text(carnet),
        "Curso_Cod": _safe_text(curso_cod),
        "Periodo": _safe_text(periodo),
    }

    if not (carnet and curso_cod and periodo):
        if parsed.get("CURSO_COD") and len(parsed) == 1:
            return _build_detail_payload(
                ok=False,
                id_tabla="MC01",
                id_row_tabla=raw_id,
                tabla_fisica="dbo.Matricula_Curso",
                descripcion="Matrícula de Curso",
                pk_values=pk_values,
                mensaje=(
                    "El registro de auditoría solo contiene Curso_Cod. "
                    "No es suficiente para reconstruir una fila única de dbo.Matricula_Curso."
                ),
            )

        return _build_detail_payload(
            ok=False,
            id_tabla="MC01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Matricula_Curso",
            descripcion="Matrícula de Curso",
            pk_values=pk_values,
            mensaje="No fue posible interpretar la llave compuesta de dbo.Matricula_Curso.",
        )

    sql = """
    SELECT TOP 1
        mc.Carnet,
        e.Nombre_Completo AS Estudiante,
        mc.Curso_Cod,
        cp.Descripcion AS Curso,
        mc.Periodo,
        mc.Periodo_Id,
        p.Periodo_Codigo,
        p.Anio,
        p.Numero_Periodo,
        mc.Docente_Cod,
        d.Nombre_Completo AS Docente,
        mc.Estado_Codigo,
        eg.Estado_Desc,
        mc.Fecha_Matricula
    FROM dbo.Matricula_Curso mc
    LEFT JOIN dbo.Estudiantes e
        ON e.Carnet = mc.Carnet
    LEFT JOIN dbo.Cursos_Programas cp
        ON cp.Curso_Cod = mc.Curso_Cod
    LEFT JOIN dbo.Periodos p
        ON p.Periodo_Id = mc.Periodo_Id
    LEFT JOIN dbo.Docentes d
        ON d.Docente_Cod = mc.Docente_Cod
    LEFT JOIN dbo.Estado_General eg
        ON eg.Estado_Codigo = mc.Estado_Codigo
    WHERE mc.Carnet = ?
      AND mc.Curso_Cod = ?
      AND mc.Periodo = ?;
    """
    registro = _query_single_row(
        conn,
        sql=sql,
        params=[carnet, curso_cod, periodo],
    )

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="MC01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Matricula_Curso",
            descripcion="Matrícula de Curso",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Matricula_Curso.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="MC01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Matricula_Curso",
        descripcion="Matrícula de Curso",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


def _resolve_mm01_matricula_materia(conn: pyodbc.Connection, raw_id: str) -> dict:
    parsed = _parse_compound_key(raw_id)

    carnet = parsed.get("CARNET")
    materia_cod = parsed.get("MATERIA_COD")
    periodo = parsed.get("PERIODO")

    pk_values = {
        "Carnet": _safe_text(carnet),
        "Materia_Cod": _safe_text(materia_cod),
        "Periodo": _safe_text(periodo),
    }

    if not (carnet and materia_cod and periodo):
        return _build_detail_payload(
            ok=False,
            id_tabla="MM01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Matricula_Materia",
            descripcion="Matrícula por Materia",
            pk_values=pk_values,
            mensaje="No fue posible interpretar la llave compuesta de dbo.Matricula_Materia.",
        )

    sql = """
    SELECT TOP 1
        mm.Matricula_Materia_Id,
        mm.Carnet,
        e.Nombre_Completo AS Estudiante,
        mm.Materia_Cod,
        m.Descripcion AS Materia,
        m.Curso_Cod,
        cp.Descripcion AS Curso,
        mm.Periodo,
        mm.Periodo_Id,
        p.Periodo_Codigo,
        p.Anio,
        p.Numero_Periodo,
        mm.Docente_Cod,
        d.Nombre_Completo AS Docente,
        mm.Estado_Codigo,
        eg.Estado_Desc,
        mm.Fecha_Matricula
    FROM dbo.Matricula_Materia mm
    LEFT JOIN dbo.Estudiantes e
        ON e.Carnet = mm.Carnet
    LEFT JOIN dbo.Materias m
        ON m.Materia_Cod = mm.Materia_Cod
    LEFT JOIN dbo.Cursos_Programas cp
        ON cp.Curso_Cod = m.Curso_Cod
    LEFT JOIN dbo.Periodos p
        ON p.Periodo_Id = mm.Periodo_Id
    LEFT JOIN dbo.Docentes d
        ON d.Docente_Cod = mm.Docente_Cod
    LEFT JOIN dbo.Estado_General eg
        ON eg.Estado_Codigo = mm.Estado_Codigo
    WHERE mm.Carnet = ?
      AND mm.Materia_Cod = ?
      AND mm.Periodo = ?
    ORDER BY mm.Matricula_Materia_Id DESC;
    """
    registro = _query_single_row(
        conn,
        sql=sql,
        params=[carnet, materia_cod, periodo],
    )

    if not registro:
        return _build_detail_payload(
            ok=False,
            id_tabla="MM01",
            id_row_tabla=raw_id,
            tabla_fisica="dbo.Matricula_Materia",
            descripcion="Matrícula por Materia",
            pk_values=pk_values,
            mensaje="No se encontró el registro afectado en dbo.Matricula_Materia.",
        )

    return _build_detail_payload(
        ok=True,
        id_tabla="MM01",
        id_row_tabla=raw_id,
        tabla_fisica="dbo.Matricula_Materia",
        descripcion="Matrícula por Materia",
        pk_values=pk_values,
        registro=registro,
        mensaje="Registro afectado resuelto correctamente.",
    )


_RESOLVERS = {
    "U01": _resolve_u01_usuarios,
    "D01": _resolve_d01_docentes,
    "E01": _resolve_e01_estudiantes,
    "CP01": _resolve_cp01_cursos_programas,
    "M01": _resolve_m01_materias,
    "P01": _resolve_p01_periodos,
    "BEC01": _resolve_bec01_becas,
    "BECD01": _resolve_becd01_becados,
    "AL01": _resolve_al01_asistencia_lista,
    "CD01": _resolve_cd01_curso_docente,
    "DM01": _resolve_dm01_docente_materia,
    "MH01": _resolve_mh01_materia_horario,
    "MC01": _resolve_mc01_matricula_curso,
    "MM01": _resolve_mm01_matricula_materia,
}


def get_registro_afectado_auditoria(
    conn: pyodbc.Connection,
    *,
    id_tabla: str | None,
    id_row_tabla: str | None,
) -> dict:
    """
    Resuelve el dato/registro afectado real a partir de:
    - id_tabla
    - id_row_tabla

    Retorna un payload uniforme para que luego el service/UI
    lo transformen a una vista amigable para el auditor.
    """
    tabla_code = _safe_upper(id_tabla)
    raw_id = _safe_text(id_row_tabla)

    if not tabla_code:
        return _build_detail_payload(
            ok=False,
            id_tabla="",
            id_row_tabla=raw_id,
            mensaje="No se recibió el código de tabla de auditoría.",
        )

    if tabla_code in ("LEGACY", "N/A"):
        return _build_detail_payload(
            ok=False,
            id_tabla=tabla_code,
            id_row_tabla=raw_id,
            mensaje="Registro histórico/legado. No es posible reconstruir el dato afectado.",
        )

    if not raw_id:
        return _build_detail_payload(
            ok=False,
            id_tabla=tabla_code,
            id_row_tabla=raw_id,
            mensaje="No se recibió el identificador del registro afectado.",
        )

    resolver = _RESOLVERS.get(tabla_code)
    if resolver is None:
        return _build_detail_payload(
            ok=False,
            id_tabla=tabla_code,
            id_row_tabla=raw_id,
            mensaje=(
                "La tabla afectada aún no tiene resolvedor implementado "
                f"para el código {tabla_code}."
            ),
        )

    try:
        return resolver(conn, raw_id)
    except pyodbc.Error as e:
        return _build_detail_payload(
            ok=False,
            id_tabla=tabla_code,
            id_row_tabla=raw_id,
            mensaje=f"Error de base de datos al resolver el registro afectado: {e}",
        )
    except Exception as e:
        return _build_detail_payload(
            ok=False,
            id_tabla=tabla_code,
            id_row_tabla=raw_id,
            mensaje=f"Error inesperado al resolver el registro afectado: {e}",
        )