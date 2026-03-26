from __future__ import annotations

import re

from app.core.exceptions import ValidationError
from app.repositories.security.usuarios_repo import (
    fetch_roles_activos,
    fetch_tipos_usuario_activos,
    fetch_estados_usuario,
    exists_usuario_login,
    exists_id_usuario,
    exists_correo_usuario,
    exists_rol_activo,
    exists_tipo_usuario_activo,
    exists_estado_usuario,
    create_usuario_con_rol_principal,
)
from app.services.security.password_service import PasswordService


_password_service = PasswordService()


# =========================================================
# Helpers internos
# =========================================================
def _to_int(value, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} inválido.")


def _to_required_str(value, field_name: str, max_len: int | None = None) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"{field_name} es obligatorio.")

    if max_len is not None and len(text) > max_len:
        raise ValidationError(f"{field_name} no puede exceder {max_len} caracteres.")

    return text


def _to_optional_str(value, max_len: int | None = None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None

    if max_len is not None and len(text) > max_len:
        raise ValidationError(f"El valor no puede exceder {max_len} caracteres.")

    return text


def _validar_email(correo: str | None) -> str | None:
    correo = _to_optional_str(correo, 120)
    if not correo:
        return None

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(pattern, correo):
        raise ValidationError("El correo no tiene un formato válido.")

    return correo


def _validar_login(usuario: str) -> str:
    usuario = _to_required_str(usuario, "Usuario", 50)

    if " " in usuario:
        raise ValidationError("El usuario no puede contener espacios.")

    if len(usuario) < 3:
        raise ValidationError("El usuario debe tener al menos 3 caracteres.")

    return usuario


def _validar_nombre(nombre_usuario: str) -> str:
    return _to_required_str(nombre_usuario, "Nombre de usuario", 120)


def _validar_password(clave_plana: str, confirmar_clave: str | None = None) -> str:
    clave_plana = str(clave_plana or "")
    if not clave_plana.strip():
        raise ValidationError("La contraseña es obligatoria.")

    ok, msg = _password_service.validate_password_policy(clave_plana)
    if not ok:
        raise ValidationError(msg)

    if confirmar_clave is not None and clave_plana != str(confirmar_clave):
        raise ValidationError("La confirmación de contraseña no coincide.")

    return clave_plana


# =========================================================
# Lookups para UI
# =========================================================
def get_lookups_registro_usuario(conn) -> dict:
    """
    Retorna los lookups necesarios para el formulario de registro.
    """
    roles = fetch_roles_activos(conn)
    tipos_usuario = fetch_tipos_usuario_activos(conn)
    estados_usuario = fetch_estados_usuario(conn)

    return {
        "roles": [
            {
                "rol_id": int(rol_id),
                "codigo_rol": codigo_rol,
                "nombre_rol": nombre_rol,
            }
            for rol_id, codigo_rol, nombre_rol in roles
        ],
        "tipos_usuario": [
            {
                "tipo_usuario": int(tipo_usuario),
                "descripcion_tipo": descripcion_tipo,
            }
            for tipo_usuario, descripcion_tipo in tipos_usuario
        ],
        "estados_usuario": [
            {
                "estado_usuario": int(estado_usuario),
                "descripcion_estado": descripcion_estado,
            }
            for estado_usuario, descripcion_estado in estados_usuario
        ],
    }


# =========================================================
# Validación de datos de entrada
# =========================================================
def validar_usuario_seguridad_data(
    *,
    id_usuario: int,
    usuario: str,
    nombre_usuario: str,
    tipo_usuario: int,
    estado_usuario: int,
    rol_id: int,
    correo: str | None = None,
    clave_plana: str,
    confirmar_clave: str | None = None,
    debe_cambiar_clave: bool = True,
) -> dict:
    """
    Normaliza y valida los datos funcionales del formulario.
    """
    id_usuario = _to_int(id_usuario, "Identificación")
    if id_usuario < 0:
        raise ValidationError("La identificación no puede ser negativa.")

    usuario = _validar_login(usuario)
    nombre_usuario = _validar_nombre(nombre_usuario)
    tipo_usuario = _to_int(tipo_usuario, "Tipo de usuario")
    estado_usuario = _to_int(estado_usuario, "Estado de usuario")
    rol_id = _to_int(rol_id, "Rol")
    correo = _validar_email(correo)
    clave_plana = _validar_password(clave_plana, confirmar_clave)

    return {
        "id_usuario": id_usuario,
        "usuario": usuario,
        "nombre_usuario": nombre_usuario,
        "tipo_usuario": tipo_usuario,
        "estado_usuario": estado_usuario,
        "rol_id": rol_id,
        "correo": correo,
        "clave_plana": clave_plana,
        "debe_cambiar_clave": bool(debe_cambiar_clave),
    }


# =========================================================
# Validación de negocio / BD
# =========================================================
def validar_usuario_seguridad_unicidad_y_referencias(
    conn,
    *,
    id_usuario: int,
    usuario: str,
    correo: str | None,
    tipo_usuario: int,
    estado_usuario: int,
    rol_id: int,
) -> None:
    """
    Valida referencias activas y unicidad antes de registrar.
    """
    if exists_id_usuario(conn, id_usuario):
        raise ValidationError("Ya existe un usuario con esa identificación.")

    if exists_usuario_login(conn, usuario):
        raise ValidationError("Ya existe un usuario con ese login.")

    if correo and exists_correo_usuario(conn, correo):
        raise ValidationError("Ya existe un usuario con ese correo.")

    if not exists_tipo_usuario_activo(conn, tipo_usuario):
        raise ValidationError("El tipo de usuario indicado no existe o está inactivo.")

    if not exists_estado_usuario(conn, estado_usuario):
        raise ValidationError("El estado de usuario indicado no existe.")

    if not exists_rol_activo(conn, rol_id):
        raise ValidationError("El rol indicado no existe o está inactivo.")


# =========================================================
# Preparación de credenciales
# =========================================================
def preparar_credenciales_usuario(
    *,
    clave_plana: str,
) -> dict:
    """
    Genera salt y hash con la política vigente del sistema.
    """
    hashed = _password_service.hash_password(clave_plana)

    return {
        "clave_hash": hashed["clave_hash"],
        "clave_salt": hashed["clave_salt"],
        "clave_algoritmo": hashed["clave_algoritmo"],
        "clave_iteraciones": hashed["clave_iteraciones"],
    }


# =========================================================
# Caso de uso principal
# =========================================================
def registrar_usuario_seguridad(
    conn,
    *,
    id_usuario: int,
    usuario: str,
    nombre_usuario: str,
    tipo_usuario: int,
    estado_usuario: int,
    rol_id: int,
    clave_plana: str,
    confirmar_clave: str | None = None,
    correo: str | None = None,
    debe_cambiar_clave: bool = True,
) -> dict:
    """
    Caso de uso principal para registrar un usuario del sistema
    con un único rol principal.
    """
    data = validar_usuario_seguridad_data(
        id_usuario=id_usuario,
        usuario=usuario,
        nombre_usuario=nombre_usuario,
        tipo_usuario=tipo_usuario,
        estado_usuario=estado_usuario,
        rol_id=rol_id,
        correo=correo,
        clave_plana=clave_plana,
        confirmar_clave=confirmar_clave,
        debe_cambiar_clave=debe_cambiar_clave,
    )

    validar_usuario_seguridad_unicidad_y_referencias(
        conn,
        id_usuario=data["id_usuario"],
        usuario=data["usuario"],
        correo=data["correo"],
        tipo_usuario=data["tipo_usuario"],
        estado_usuario=data["estado_usuario"],
        rol_id=data["rol_id"],
    )

    credenciales = preparar_credenciales_usuario(
        clave_plana=data["clave_plana"],
    )

    usuario_creado = create_usuario_con_rol_principal(
        conn,
        id_usuario=data["id_usuario"],
        usuario=data["usuario"],
        nombre_usuario=data["nombre_usuario"],
        tipo_usuario=data["tipo_usuario"],
        estado_usuario=data["estado_usuario"],
        correo=data["correo"],
        clave_hash=credenciales["clave_hash"],
        clave_salt=credenciales["clave_salt"],
        clave_algoritmo=credenciales["clave_algoritmo"],
        clave_iteraciones=credenciales["clave_iteraciones"],
        debe_cambiar_clave=data["debe_cambiar_clave"],
        rol_id=data["rol_id"],
    )

    return usuario_creado
