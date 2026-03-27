from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.session import (
    get_codigo_usuario,
    get_rol_codigo,
    get_session,
)
from app.services.auditoria_consulta_service import (
    listar_auditoria_legible,
    get_filtros_auditoria,
    get_diccionario_movimientos,
)


RESOURCE_KEY = "auditoria"


def _get_conn():
    return connect_app()


def _get_tipo_usuario_from_session() -> int | None:
    session_data = get_session() or {}
    value = session_data.get("tipo_usuario")

    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _is_auditor_allowed() -> bool:
    """
    Acceso permitido si el usuario activo cumple al menos una de estas reglas:
    - Rol CONSULTA
    - Tipo de usuario 2 (Auditor)
    """
    codigo_rol = str(get_rol_codigo() or "").strip().upper()
    tipo_usuario = _get_tipo_usuario_from_session()

    return codigo_rol == "CONSULTA" or tipo_usuario == 2


def _require_auditor_access() -> None:
    if not _is_auditor_allowed():
        raise ValidationError(
            "Acceso denegado. Solo el usuario auditor puede consultar este módulo."
        )


# =========================================================
# LOOKUPS / FILTROS
# =========================================================
def get_auditoria_filtros_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
):
    """
    Retorna catálogos base para poblar filtros del módulo Auditor.
    """
    _require_auditor_access()

    conn = _get_conn()
    try:
        filtros = get_filtros_auditoria(conn)
        return {
            "ok": True,
            "message": "Filtros de auditoría cargados correctamente.",
            "data": filtros,
        }
    finally:
        conn.close()


# =========================================================
# LISTADO PRINCIPAL
# =========================================================
def listar_auditoria_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
    *,
    codigo_usuario: int | None = None,
    movimiento_cod: int | None = None,
    id_tabla: str | None = None,
    texto: str | None = None,
    top: int = 300,
):
    """
    Lista registros de auditoría en formato legible para la UI.
    Solo accesible por el auditor.
    """
    _require_auditor_access()

    conn = _get_conn()
    try:
        rows = listar_auditoria_legible(
            conn,
            codigo_usuario=codigo_usuario,
            movimiento_cod=movimiento_cod,
            id_tabla=id_tabla,
            texto=texto,
            top=top,
        )

        return {
            "ok": True,
            "message": "Auditoría cargada correctamente.",
            "data": rows,
        }
    finally:
        conn.close()


# =========================================================
# RESUMEN SIMPLE
# =========================================================
def get_auditoria_resumen_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
    *,
    top: int = 300,
):
    """
    Retorna un resumen simple basado en el listado visible actual.
    Útil para tarjetas o labels de conteo en la UI.
    """
    _require_auditor_access()

    conn = _get_conn()
    try:
        rows = listar_auditoria_legible(
            conn,
            top=top,
        )

        total = len(rows)
        total_insertados = 0
        total_actualizados = 0
        total_eliminados = 0
        total_consultas = 0
        total_logins = 0

        for r in rows:
            mov = int(r.get("movimiento_cod") or 0)
            if mov == 1:
                total_insertados += 1
            elif mov == 2:
                total_actualizados += 1
            elif mov in (3, 4):
                total_eliminados += 1
            elif mov == 5:
                total_consultas += 1
            elif mov == 6:
                total_logins += 1

        return {
            "ok": True,
            "message": "Resumen de auditoría cargado correctamente.",
            "data": {
                "total_registros": total,
                "insertados": total_insertados,
                "actualizados": total_actualizados,
                "eliminados": total_eliminados,
                "consultas": total_consultas,
                "logins": total_logins,
                "codigo_usuario_sesion": get_codigo_usuario(),
            },
        }
    finally:
        conn.close()


# =========================================================
# DICCIONARIO DE MOVIMIENTOS
# =========================================================
def get_diccionario_movimientos_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
):
    """
    Retorna el catálogo oficial de movimientos para el popup
    de apoyo al auditor.
    """
    _require_auditor_access()

    conn = _get_conn()
    try:
        rows = get_diccionario_movimientos(conn)
        return {
            "ok": True,
            "message": "Diccionario de movimientos cargado correctamente.",
            "data": rows,
        }
    finally:
        conn.close()