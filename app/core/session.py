from __future__ import annotations

from copy import deepcopy


_current_session: dict | None = None


def _normalize_token(value: object) -> str:
    """
    Normaliza valores de sesión, roles y permisos para comparaciones seguras.
    """
    if value is None:
        return ""
    return str(value).strip().upper().replace(" ", "_").replace("-", "_")


# =========================================================
# Gestión de sesión
# =========================================================
def set_session(session_data: dict) -> None:
    """
    Establece la sesión activa del sistema.
    """
    global _current_session

    if not isinstance(session_data, dict):
        raise ValueError("session_data debe ser un diccionario.")

    _current_session = deepcopy(session_data)


def clear_session() -> None:
    """
    Limpia la sesión activa.
    """
    global _current_session
    _current_session = None


def has_active_session() -> bool:
    """
    Indica si existe una sesión activa.
    """
    return _current_session is not None


def get_session() -> dict | None:
    """
    Retorna una copia de la sesión activa.
    """
    if _current_session is None:
        return None
    return deepcopy(_current_session)


def require_session() -> dict:
    """
    Retorna la sesión activa o levanta error si no existe.
    """
    session_data = get_session()
    if session_data is None:
        raise RuntimeError("No hay una sesión activa.")
    return session_data


# =========================================================
# Helpers de lectura
# =========================================================
def get_usuario() -> str | None:
    session_data = get_session()
    return session_data.get("usuario") if session_data else None


def get_nombre_usuario() -> str | None:
    session_data = get_session()
    return session_data.get("nombre_usuario") if session_data else None


def get_codigo_usuario() -> int | None:
    session_data = get_session()
    return session_data.get("codigo_usuario") if session_data else None


def get_usuario_seguridad_id() -> int | None:
    session_data = get_session()
    return session_data.get("usuario_seguridad_id") if session_data else None


def get_rol_codigo() -> str | None:
    session_data = get_session()
    return session_data.get("codigo_rol") if session_data else None


def get_rol_nombre() -> str | None:
    session_data = get_session()
    return session_data.get("nombre_rol") if session_data else None


def get_permisos() -> list[str]:
    session_data = get_session()
    if not session_data:
        return []
    return list(session_data.get("permisos", []))


def get_roles() -> list[dict]:
    session_data = get_session()
    if not session_data:
        return []
    return list(session_data.get("roles", []))


# =========================================================
# Validación de permisos / roles
# =========================================================
def has_permission(codigo_permiso: str) -> bool:
    """
    Valida si la sesión activa posee un permiso específico.
    La comparación se hace normalizada para tolerar variantes
    de formato en los códigos.
    """
    normalized = _normalize_token(codigo_permiso)
    if not normalized:
        return False

    permisos = {_normalize_token(code) for code in get_permisos() if _normalize_token(code)}
    return normalized in permisos


def has_any_permission(*codigos_permiso: str) -> bool:
    """
    Valida si la sesión activa tiene al menos uno de los permisos indicados.
    """
    permisos = {_normalize_token(code) for code in get_permisos() if _normalize_token(code)}
    valid_codes = [_normalize_token(code) for code in codigos_permiso if _normalize_token(code)]
    return any(code in permisos for code in valid_codes)


def has_all_permissions(*codigos_permiso: str) -> bool:
    """
    Valida si la sesión activa tiene todos los permisos indicados.
    """
    permisos = {_normalize_token(code) for code in get_permisos() if _normalize_token(code)}
    valid_codes = [_normalize_token(code) for code in codigos_permiso if _normalize_token(code)]
    if not valid_codes:
        return False
    return all(code in permisos for code in valid_codes)


def has_role(codigo_rol: str) -> bool:
    """
    Valida si el rol principal de la sesión coincide con el indicado
    o si el usuario lo tiene dentro de su lista de roles.
    """
    normalized_role = _normalize_token(codigo_rol)
    if not normalized_role:
        return False

    rol_principal = _normalize_token(get_rol_codigo())
    if rol_principal == normalized_role:
        return True

    for rol in get_roles():
        current = _normalize_token(rol.get("codigo_rol"))
        if current == normalized_role:
            return True

    return False


def is_admin() -> bool:
    """
    Atajo para validar si el usuario actual es Administrador.
    """
    return has_role("ADMIN")


def is_docente() -> bool:
    """
    Atajo para validar si el usuario actual es Docente.
    """
    return has_role("DOCENTE")


def is_auditor() -> bool:
    """
    Atajo para validar si el usuario actual es Auditor.
    """
    return has_role("AUDITOR")


def is_operador() -> bool:
    """
    Atajo para validar si el usuario actual es Operador.
    """
    return has_role("OPERADOR")


# =========================================================
# Resumen de sesión
# =========================================================
def get_session_summary() -> dict:
    """
    Retorna un resumen útil para UI y depuración controlada.
    """
    session_data = get_session()
    if not session_data:
        return {
            "activa": False,
            "usuario": None,
            "nombre_usuario": None,
            "codigo_rol": None,
            "nombre_rol": None,
            "permisos_count": 0,
        }

    return {
        "activa": True,
        "usuario": session_data.get("usuario"),
        "nombre_usuario": session_data.get("nombre_usuario"),
        "codigo_rol": session_data.get("codigo_rol"),
        "nombre_rol": session_data.get("nombre_rol"),
        "permisos_count": len(session_data.get("permisos", [])),
    }