from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from app.core.config import USER_IMAGES_DIR, DEFAULT_USER_IMAGE
from app.core.exceptions import ValidationError
from app.repositories.security.perfil_usuario_repo import (
    get_perfil_usuario_by_usuario_seguridad_id,
    get_perfil_usuario_by_codigo_usuario,
    exists_usuario_login_excluding_current,
    exists_correo_excluding_current,
    update_perfil_usuario_no_sensible,
    get_perfil_actualizado,
)


# =========================================================
# Helpers internos
# =========================================================
_ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


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


def _to_optional_str(value, field_name: str, max_len: int | None = None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None

    if max_len is not None and len(text) > max_len:
        raise ValidationError(f"{field_name} no puede exceder {max_len} caracteres.")

    return text


def _validar_email(correo: str | None) -> str | None:
    correo = _to_optional_str(correo, "Correo", 120)
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


def _get_project_root() -> Path:
    """
    Resuelve la raíz del proyecto desde este archivo:
    app/services/security/perfil_usuario_service.py
    """
    return Path(__file__).resolve().parents[3]


def _get_user_images_dir() -> Path:
    """
    Retorna la carpeta absoluta de imágenes de usuario.
    """
    return _get_project_root() / USER_IMAGES_DIR


def _sanitize_filename_stem(value: str) -> str:
    """
    Limpia el nombre base del archivo para evitar caracteres no deseados.
    """
    text = str(value or "").strip()
    text = re.sub(r"[^\w\-\. ]+", "", text, flags=re.UNICODE)
    text = text.replace(" ", "_")
    return text or "usuario"


def _get_default_image_path() -> Path:
    return _get_user_images_dir() / DEFAULT_USER_IMAGE


def _find_existing_user_image(usuario: str | None) -> Path | None:
    """
    Busca una imagen existente para el usuario por nombre de login.
    """
    username = (usuario or "").strip()
    if not username:
        return None

    images_dir = _get_user_images_dir()
    if not images_dir.exists():
        return None

    username_lower = username.lower()

    for entry in images_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in _ALLOWED_IMAGE_EXTENSIONS:
            continue
        if entry.stem.strip().lower() == username_lower:
            return entry

    return None


def _build_foto_metadata(usuario: str | None) -> dict:
    """
    Retorna metadatos útiles para UI sobre la foto de perfil.
    """
    existing = _find_existing_user_image(usuario)
    default_path = _get_default_image_path()

    if existing and existing.exists():
        return {
            "foto_path": str(existing),
            "foto_filename": existing.name,
            "tiene_foto_personalizada": existing.name.lower() != DEFAULT_USER_IMAGE.lower(),
            "usa_foto_default": existing.name.lower() == DEFAULT_USER_IMAGE.lower(),
        }

    return {
        "foto_path": str(default_path),
        "foto_filename": default_path.name,
        "tiene_foto_personalizada": False,
        "usa_foto_default": True,
    }


def _normalizar_perfil_para_ui(perfil: dict | None) -> dict | None:
    """
    Enriquece el perfil con metadatos de foto y banderas de edición.
    """
    if not perfil:
        return None

    foto_meta = _build_foto_metadata(perfil.get("usuario"))

    return {
        **perfil,
        **foto_meta,
        "editable_fields": {
            "usuario": True,
            "nombre_usuario": True,
            "correo": True,
            "foto_perfil": True,
            "id_usuario": False,
            "codigo_usuario": False,
            "tipo_usuario": False,
            "descripcion_tipo": False,
            "estado_usuario": False,
            "descripcion_estado": False,
            "rol_id": False,
            "codigo_rol": False,
            "nombre_rol": False,
            "debe_cambiar_clave": False,
            "intentos_fallidos": False,
            "bloqueado_hasta": False,
            "ultimo_acceso": False,
            "ultimo_cambio_clave": False,
            "fecha_creacion": False,
            "fecha_modificacion": False,
        },
    }


# =========================================================
# Lectura de perfil
# =========================================================
def obtener_perfil_usuario_activo(
    conn,
    *,
    usuario_seguridad_id: int | None = None,
    codigo_usuario: int | None = None,
) -> dict:
    """
    Obtiene el perfil del usuario activo usando cualquiera de los dos identificadores.
    """
    if usuario_seguridad_id is None and codigo_usuario is None:
        raise ValidationError("No se recibió un identificador válido del usuario activo.")

    perfil = None

    if usuario_seguridad_id is not None:
        perfil = get_perfil_usuario_by_usuario_seguridad_id(
            conn,
            _to_int(usuario_seguridad_id, "Usuario de seguridad"),
        )

    if perfil is None and codigo_usuario is not None:
        perfil = get_perfil_usuario_by_codigo_usuario(
            conn,
            _to_int(codigo_usuario, "Código de usuario"),
        )

    if not perfil:
        raise ValidationError("No fue posible localizar el perfil del usuario activo.")

    return _normalizar_perfil_para_ui(perfil)


# =========================================================
# Validación de edición
# =========================================================
def validar_actualizacion_perfil_no_sensible(
    *,
    usuario_seguridad_id: int,
    usuario: str,
    nombre_usuario: str,
    correo: str | None = None,
) -> dict:
    """
    Valida y normaliza los datos que sí puede editar el usuario.
    """
    usuario_seguridad_id = _to_int(usuario_seguridad_id, "Usuario de seguridad")
    usuario = _validar_login(usuario)
    nombre_usuario = _validar_nombre(nombre_usuario)
    correo = _validar_email(correo)

    return {
        "usuario_seguridad_id": usuario_seguridad_id,
        "usuario": usuario,
        "nombre_usuario": nombre_usuario,
        "correo": correo,
    }


def validar_unicidad_actualizacion_perfil(
    conn,
    *,
    usuario_seguridad_id: int,
    usuario: str,
    correo: str | None,
) -> None:
    """
    Valida unicidad de usuario y correo excluyendo al mismo usuario actual.
    """
    if exists_usuario_login_excluding_current(conn, usuario, usuario_seguridad_id):
        raise ValidationError("Ya existe otro usuario con ese login.")

    if correo and exists_correo_excluding_current(conn, correo, usuario_seguridad_id):
        raise ValidationError("Ya existe otro usuario con ese correo.")


# =========================================================
# Actualización de datos editables
# =========================================================
def actualizar_perfil_usuario(
    conn,
    *,
    usuario_seguridad_id: int,
    usuario: str,
    nombre_usuario: str,
    correo: str | None = None,
) -> dict:
    """
    Actualiza datos no sensibles del perfil y devuelve el perfil recargado.
    """
    data = validar_actualizacion_perfil_no_sensible(
        usuario_seguridad_id=usuario_seguridad_id,
        usuario=usuario,
        nombre_usuario=nombre_usuario,
        correo=correo,
    )

    validar_unicidad_actualizacion_perfil(
        conn,
        usuario_seguridad_id=data["usuario_seguridad_id"],
        usuario=data["usuario"],
        correo=data["correo"],
    )

    perfil_actual = get_perfil_usuario_by_usuario_seguridad_id(
        conn,
        data["usuario_seguridad_id"],
    )
    if not perfil_actual:
        raise ValidationError("El usuario indicado no existe.")

    usuario_anterior = perfil_actual.get("usuario")

    update_perfil_usuario_no_sensible(
        conn,
        usuario_seguridad_id=data["usuario_seguridad_id"],
        usuario=data["usuario"],
        nombre_usuario=data["nombre_usuario"],
        correo=data["correo"],
    )

    perfil_actualizado = get_perfil_actualizado(
        conn,
        data["usuario_seguridad_id"],
    )
    if not perfil_actualizado:
        raise ValidationError("No fue posible recargar el perfil actualizado.")

    _renombrar_foto_si_cambio_usuario(
        usuario_anterior=usuario_anterior,
        usuario_nuevo=perfil_actualizado.get("usuario"),
    )

    perfil_actualizado = get_perfil_actualizado(
        conn,
        data["usuario_seguridad_id"],
    )

    return _normalizar_perfil_para_ui(perfil_actualizado)


# =========================================================
# Gestión de foto de perfil
# =========================================================
def validar_archivo_foto_perfil(file_path: str) -> Path:
    """
    Valida ruta física y extensión permitida del archivo de imagen.
    """
    path = Path(str(file_path or "").strip())
    if not path.exists() or not path.is_file():
        raise ValidationError("El archivo de imagen indicado no existe.")

    if path.suffix.lower() not in _ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            "Formato de imagen no permitido. Usa PNG, JPG, JPEG, GIF o WEBP."
        )

    return path


def _renombrar_foto_si_cambio_usuario(
    *,
    usuario_anterior: str | None,
    usuario_nuevo: str | None,
) -> None:
    """
    Si el usuario cambió su login y ya tenía foto personalizada,
    renombra el archivo para mantener el enlace automático por username.
    """
    anterior = (usuario_anterior or "").strip()
    nuevo = (usuario_nuevo or "").strip()

    if not anterior or not nuevo or anterior.lower() == nuevo.lower():
        return

    foto_actual = _find_existing_user_image(anterior)
    if not foto_actual or not foto_actual.exists():
        return

    if foto_actual.name.lower() == DEFAULT_USER_IMAGE.lower():
        return

    destino = foto_actual.with_name(f"{_sanitize_filename_stem(nuevo)}{foto_actual.suffix.lower()}")

    if destino.exists():
        # Si ya existe un archivo con el nuevo nombre, se reemplaza.
        try:
            destino.unlink()
        except Exception:
            pass

    try:
        foto_actual.rename(destino)
    except Exception:
        # La foto no debe romper el update funcional del perfil.
        pass


def guardar_foto_perfil_usuario(
    conn,
    *,
    usuario_seguridad_id: int,
    origen_file_path: str,
) -> dict:
    """
    Copia la foto seleccionada al directorio oficial del sistema usando
    el login actual del usuario como nombre base del archivo.
    """
    usuario_seguridad_id = _to_int(usuario_seguridad_id, "Usuario de seguridad")
    source_path = validar_archivo_foto_perfil(origen_file_path)

    perfil = get_perfil_usuario_by_usuario_seguridad_id(conn, usuario_seguridad_id)
    if not perfil:
        raise ValidationError("No fue posible localizar el usuario para asignar la foto.")

    usuario = perfil.get("usuario")
    usuario = _validar_login(usuario)

    images_dir = _get_user_images_dir()
    images_dir.mkdir(parents=True, exist_ok=True)

    # Elimina imágenes previas personalizadas con el mismo username en otra extensión.
    for entry in images_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in _ALLOWED_IMAGE_EXTENSIONS:
            continue
        if entry.stem.strip().lower() == usuario.strip().lower():
            if entry.name.lower() != DEFAULT_USER_IMAGE.lower():
                try:
                    entry.unlink()
                except Exception:
                    pass

    destino = images_dir / f"{_sanitize_filename_stem(usuario)}{source_path.suffix.lower()}"

    try:
        shutil.copy2(source_path, destino)
    except Exception as ex:
        raise ValidationError(f"No fue posible guardar la foto de perfil. Detalle: {ex}")

    perfil_actualizado = get_perfil_actualizado(conn, usuario_seguridad_id)
    if not perfil_actualizado:
        raise ValidationError("La foto fue cargada, pero no se pudo recargar el perfil.")

    return _normalizar_perfil_para_ui(perfil_actualizado)


def quitar_foto_perfil_usuario(
    conn,
    *,
    usuario_seguridad_id: int,
) -> dict:
    """
    Elimina la foto personalizada del usuario si existe.
    El sistema volverá a usar la imagen default.
    """
    usuario_seguridad_id = _to_int(usuario_seguridad_id, "Usuario de seguridad")

    perfil = get_perfil_usuario_by_usuario_seguridad_id(conn, usuario_seguridad_id)
    if not perfil:
        raise ValidationError("No fue posible localizar el usuario.")

    foto_actual = _find_existing_user_image(perfil.get("usuario"))
    if foto_actual and foto_actual.exists():
        if foto_actual.name.lower() != DEFAULT_USER_IMAGE.lower():
            try:
                foto_actual.unlink()
            except Exception as ex:
                raise ValidationError(f"No fue posible eliminar la foto actual. Detalle: {ex}")

    perfil_actualizado = get_perfil_actualizado(conn, usuario_seguridad_id)
    if not perfil_actualizado:
        raise ValidationError("No fue posible recargar el perfil luego de quitar la foto.")

    return _normalizar_perfil_para_ui(perfil_actualizado)