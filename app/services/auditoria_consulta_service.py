from __future__ import annotations

from app.repositories.auditoria_consulta_repo import (
    list_auditoria,
    get_distinct_tablas_auditoria,
    get_distinct_movimientos_auditoria,
    get_distinct_usuarios_auditoria,
    list_movimientos_catalogo,
    get_registro_afectado_auditoria,
)


# =========================================================
# Catálogos legibles
# =========================================================
TABLA_LABELS = {
    "U01": "Usuarios",
    "D01": "Docentes",
    "E01": "Estudiantes",
    "CP01": "Cursos / Programas",
    "M01": "Materias",
    "P01": "Períodos",
    "BEC01": "Becas",
    "BECD01": "Becados",
    "AL01": "Asistencias / Lista",
    "CD01": "Asignación Curso-Docente",
    "DM01": "Asignación Docente-Materia",
    "MH01": "Horario de Materia",
    "MC01": "Matrícula de Curso",
    "MM01": "Matrícula por Materia",
    "LEGACY": "Registro legado",
    "N/A": "No aplica",
}

MOVIMIENTO_LABELS = {
    1: "Login exitoso",
    2: "Login fallido",
    3: "Matrícula creada",
    4: "Factura generada",
    5: "Cambio de estado de matrícula",
    6: "Matrícula eliminada",
    7: "Logout",
    10: "Docente creado",
    11: "Docente actualizado",
    12: "Docente eliminado",
    20: "Estudiante creado",
    21: "Estudiante actualizado",
    22: "Estudiante eliminado",
    30: "Programa/Curso creado",
    31: "Programa/Curso actualizado",
    32: "Programa/Curso eliminado",
    40: "Beca creada",
    41: "Beca actualizada",
    42: "Beca eliminada",
    50: "Becado creado",
    51: "Becado actualizado",
    52: "Becado eliminado",
    60: "Matrícula por materia creada",
    61: "Matrícula por materia actualizada",
    62: "Matrícula por materia eliminada",
    70: "Asignación docente-materia creada",
    71: "Asignación docente-materia actualizada",
    72: "Asignación docente-materia eliminada",
    80: "Horario de materia creado",
    81: "Horario de materia actualizado",
    82: "Horario de materia eliminado",
    90: "Período creado",
    91: "Período actualizado",
    92: "Período eliminado",
    100: "Restricción / validación aplicada",
}


# =========================================================
# Helpers internos
# =========================================================
def _safe_int(value) -> int | None:
    if value in (None, "", "Todos", "TODOS"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def _tabla_legible(id_tabla: str | None) -> str:
    code = str(id_tabla or "").strip().upper()
    if not code:
        return ""
    return TABLA_LABELS.get(code, code)


def _movimiento_legible(movimiento_cod: int | None) -> str:
    if movimiento_cod is None:
        return ""
    return MOVIMIENTO_LABELS.get(int(movimiento_cod), f"Movimiento {movimiento_cod}")


def _usuario_legible(item: dict) -> str:
    codigo = item.get("codigo_usuario")
    login = str(item.get("usuario_login") or "").strip()
    nombre = str(item.get("nombre_usuario") or "").strip()

    if login and nombre:
        return f"{codigo} - {login} - {nombre}"
    if login:
        return f"{codigo} - {login}"
    if nombre:
        return f"{codigo} - {nombre}"
    return str(codigo or "")


def _enriquecer_registro(row: dict) -> dict:
    id_tabla = str(row.get("id_tabla") or "").strip()
    movimiento_cod = row.get("movimiento_cod")

    return {
        **row,
        "tabla_label": _tabla_legible(id_tabla),
        "movimiento_label": _movimiento_legible(movimiento_cod),
        "usuario_display": _usuario_legible(row),
        "row_display": str(row.get("id_row_tabla") or "").strip() or "N/A",
    }


def _estado_legible(estado_codigo: int | None) -> str:
    if estado_codigo is None:
        return ""
    if int(estado_codigo) == 1:
        return "Activo"
    if int(estado_codigo) == 0:
        return "Inactivo"
    return str(estado_codigo)


def _valor_legible(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _titulo_campo(field_name: str) -> str:
    text = str(field_name or "").strip().replace("_", " ")
    if not text:
        return ""
    return text


def _dict_to_lines(data: dict) -> list[str]:
    lines: list[str] = []
    for key, value in data.items():
        value_text = _valor_legible(value)
        if value_text == "":
            continue
        lines.append(f"{_titulo_campo(key)}: {value_text}")
    return lines


def _formatear_pk_values(pk_values: dict) -> str:
    if not pk_values:
        return ""

    parts: list[str] = []
    for key, value in pk_values.items():
        value_text = _valor_legible(value)
        if value_text == "":
            continue
        parts.append(f"{key}={value_text}")

    return " | ".join(parts)


def _formatear_registro_afectado_legible(payload: dict) -> dict:
    """
    Transforma el payload del repo a un formato muy fácil de consumir
    por la UI del auditor.
    """
    ok = bool(payload.get("ok"))
    id_tabla = str(payload.get("id_tabla") or "").strip().upper()
    id_row_tabla = str(payload.get("id_row_tabla") or "").strip()
    tabla_fisica = str(payload.get("tabla_fisica") or "").strip()
    descripcion = str(payload.get("descripcion") or "").strip()
    mensaje = str(payload.get("mensaje") or "").strip()

    pk_values = payload.get("pk_values") or {}
    registro = payload.get("registro") or {}

    tabla_label = _tabla_legible(id_tabla) or descripcion or id_tabla or "Registro"
    pk_values_text = _formatear_pk_values(pk_values)

    registro_lines = _dict_to_lines(registro)

    if ok and registro_lines:
        detalle_texto = "\n".join(registro_lines)
    elif ok:
        detalle_texto = "El registro fue resuelto, pero no contiene campos visibles para mostrar."
    else:
        detalle_texto = mensaje or "No fue posible reconstruir el dato afectado."

    encabezado_parts: list[str] = []
    if tabla_label:
        encabezado_parts.append(f"Tabla: {tabla_label}")
    if tabla_fisica:
        encabezado_parts.append(f"Origen: {tabla_fisica}")
    if pk_values_text:
        encabezado_parts.append(f"Llave: {pk_values_text}")
    elif id_row_tabla:
        encabezado_parts.append(f"Identificador auditoría: {id_row_tabla}")

    encabezado_texto = "\n".join(encabezado_parts).strip()

    return {
        "ok": ok,
        "id_tabla": id_tabla,
        "id_row_tabla": id_row_tabla,
        "tabla_label": tabla_label,
        "tabla_fisica": tabla_fisica,
        "descripcion": descripcion or tabla_label,
        "mensaje": mensaje,
        "pk_values": pk_values,
        "pk_values_text": pk_values_text,
        "registro": registro,
        "registro_lines": registro_lines,
        "encabezado_texto": encabezado_texto,
        "detalle_texto": detalle_texto,
        "texto_completo": (
            f"{encabezado_texto}\n\n{detalle_texto}".strip()
            if encabezado_texto
            else detalle_texto
        ),
    }


# =========================================================
# Consultas principales
# =========================================================
def listar_auditoria_legible(
    conn,
    *,
    codigo_usuario: int | None = None,
    movimiento_cod: int | None = None,
    id_tabla: str | None = None,
    texto: str | None = None,
    top: int = 300,
) -> list[dict]:
    """
    Retorna auditoría enriquecida y legible para la UI.
    """
    rows = list_auditoria(
        conn,
        codigo_usuario=_safe_int(codigo_usuario),
        movimiento_cod=_safe_int(movimiento_cod),
        id_tabla=_safe_str(id_tabla),
        texto=_safe_str(texto),
        top=top,
    )
    return [_enriquecer_registro(r) for r in rows]


def get_filtros_auditoria(conn) -> dict:
    """
    Retorna listas base para poblar filtros de UI.
    """
    tablas = get_distinct_tablas_auditoria(conn)
    movimientos = get_distinct_movimientos_auditoria(conn)
    usuarios = get_distinct_usuarios_auditoria(conn)

    tablas_data = [
        {
            "codigo": code,
            "label": _tabla_legible(code),
            "display": f"{code} - {_tabla_legible(code)}",
        }
        for code in tablas
    ]

    movimientos_data = [
        {
            "codigo": mov,
            "label": _movimiento_legible(mov),
            "display": f"{mov} - {_movimiento_legible(mov)}",
        }
        for mov in movimientos
    ]

    usuarios_data = []
    for u in usuarios:
        usuarios_data.append(
            {
                **u,
                "display": _usuario_legible(u),
            }
        )

    return {
        "tablas": tablas_data,
        "movimientos": movimientos_data,
        "usuarios": usuarios_data,
    }


def get_diccionario_movimientos(conn) -> list[dict]:
    """
    Retorna el catálogo oficial de movimientos para el popup
    de apoyo al auditor.
    """
    rows = list_movimientos_catalogo(conn)

    result: list[dict] = []
    for row in rows:
        codigo = row.get("movimiento_cod")
        descripcion = str(row.get("descripcion") or "").strip()
        estado_codigo = row.get("estado_codigo")

        result.append(
            {
                "movimiento_cod": codigo,
                "descripcion": descripcion,
                "estado_codigo": estado_codigo,
                "estado_label": _estado_legible(estado_codigo),
                "display": f"{codigo} - {descripcion}",
            }
        )

    return result


def get_registro_afectado_legible(
    conn,
    *,
    id_tabla: str | None,
    id_row_tabla: str | None,
) -> dict:
    """
    Retorna el dato/registro afectado en formato legible para la UI del auditor.
    """
    payload = get_registro_afectado_auditoria(
        conn,
        id_tabla=_safe_str(id_tabla),
        id_row_tabla=_safe_str(id_row_tabla),
    )
    return _formatear_registro_afectado_legible(payload)