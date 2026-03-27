from __future__ import annotations

from app.repositories.auditoria_consulta_repo import (
    list_auditoria,
    get_distinct_tablas_auditoria,
    get_distinct_movimientos_auditoria,
    get_distinct_usuarios_auditoria,
    list_movimientos_catalogo,
)


# =========================================================
# Catálogos legibles
# =========================================================
TABLA_LABELS = {
    "U01": "Usuarios",
    "D01": "Docentes",
    "ES01": "Estudiantes",
    "P01": "Programas",
    "C01": "Cursos",
    "CD01": "Curso-Docente",
    "MC01": "Matrículas",
    "DM01": "Detalle Matrícula",
    "MH01": "Matrícula Materias",
    "AL01": "Asistencias / Lista",
    "MM01": "Movimientos Mantenimiento",
    "MF01": "Movimientos Flujo",
    "LEGACY": "Registro legado",
    "N/A": "No aplica",
}

MOVIMIENTO_LABELS = {
    1: "Insertado",
    2: "Actualizado",
    3: "Eliminado lógico",
    4: "Eliminado",
    5: "Consulta",
    6: "Login",
    7: "Logout",
    8: "Acción administrativa",
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
    code = str(id_tabla or "").strip()
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