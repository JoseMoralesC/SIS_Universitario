from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.core.session import (
    get_session,
    get_usuario_seguridad_id,
    get_codigo_usuario,
    set_session,
)
from app.repositories.auditoria_repo import insert_auditoria
from app.services.security.perfil_usuario_service import (
    obtener_perfil_usuario_activo,
    actualizar_perfil_usuario,
    guardar_foto_perfil_usuario,
    quitar_foto_perfil_usuario,
)


MODULE_KEY = "seguridad"
RESOURCE_KEY = "usuarios"


def _get_conn():
    return connect_app()


def _get_active_ids(
    *,
    usuario_seguridad_id: int | None = None,
    codigo_usuario: int | None = None,
) -> tuple[int | None, int | None]:
    """
    Resuelve los ids del usuario activo:
    - si vienen por parámetro, los usa
    - si no, los toma de la sesión actual
    """
    usid = usuario_seguridad_id if usuario_seguridad_id is not None else get_usuario_seguridad_id()
    cuid = codigo_usuario if codigo_usuario is not None else get_codigo_usuario()
    return usid, cuid


def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
    id_row_tabla: object | None = None,
) -> None:
    """
    Registra auditoría del perfil.
    La auditoría no debe romper el flujo principal.
    """
    if codigo_usuario is None:
        return

    try:
        insert_auditoria(
            conn,
            codigo_usuario=int(codigo_usuario),
            movimiento_cod=int(movimiento_cod),
            id_tabla=Tab.USUARIOS,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


def _refresh_active_session_with_profile(perfil: dict | None) -> None:
    """
    Si existe una sesión activa, actualiza los campos de perfil
    que el usuario pudo modificar desde esta pantalla.
    """
    if not perfil:
        return

    session_data = get_session()
    if not session_data:
        return

    session_data["usuario_seguridad_id"] = perfil.get("usuario_seguridad_id")
    session_data["codigo_usuario"] = perfil.get("codigo_usuario")
    session_data["id_usuario"] = perfil.get("id_usuario")
    session_data["usuario"] = perfil.get("usuario")
    session_data["nombre_usuario"] = perfil.get("nombre_usuario")
    session_data["correo"] = perfil.get("correo")
    session_data["tipo_usuario"] = perfil.get("tipo_usuario")
    session_data["descripcion_tipo"] = perfil.get("descripcion_tipo")
    session_data["estado_usuario"] = perfil.get("estado_usuario")
    session_data["descripcion_estado"] = perfil.get("descripcion_estado")
    session_data["rol_id"] = perfil.get("rol_id")
    session_data["codigo_rol"] = perfil.get("codigo_rol")
    session_data["nombre_rol"] = perfil.get("nombre_rol")
    session_data["debe_cambiar_clave"] = perfil.get("debe_cambiar_clave", False)
    session_data["ultimo_acceso"] = perfil.get("ultimo_acceso")

    set_session(session_data)


# =========================================================
# READ / PERFIL ACTIVO
# =========================================================
def get_mi_perfil_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
    *,
    usuario_seguridad_id: int | None = None,
    codigo_usuario: int | None = None,
):
    """
    Obtiene el perfil del usuario con sesión activa.
    No depende de permisos finos del módulo de seguridad,
    ya que es consulta del propio perfil.
    """
    usid, cuid = _get_active_ids(
        usuario_seguridad_id=usuario_seguridad_id,
        codigo_usuario=codigo_usuario,
    )

    if usid is None and cuid is None:
        raise ValidationError("No se pudo determinar el usuario activo de la sesión.")

    conn = _get_conn()
    try:
        perfil = obtener_perfil_usuario_activo(
            conn,
            usuario_seguridad_id=usid,
            codigo_usuario=cuid,
        )

        return {
            "ok": True,
            "message": "Perfil cargado correctamente.",
            "data": perfil,
        }
    finally:
        conn.close()


# =========================================================
# UPDATE / DATOS NO SENSIBLES
# =========================================================
def update_mi_perfil_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
    *,
    usuario_seguridad_id: int | None = None,
    codigo_usuario: int | None = None,
    usuario: str,
    nombre_usuario: str,
    correo: str | None = None,
):
    """
    Actualiza datos no sensibles del perfil del usuario activo:
    - usuario
    - nombre_usuario
    - correo
    """
    usid, cuid = _get_active_ids(
        usuario_seguridad_id=usuario_seguridad_id,
        codigo_usuario=codigo_usuario,
    )

    if usid is None:
        raise ValidationError(
            "No se pudo determinar el Usuario_Seguridad_Id del usuario activo."
        )

    conn = _get_conn()
    try:
        perfil_actualizado = actualizar_perfil_usuario(
            conn,
            usuario_seguridad_id=usid,
            usuario=usuario,
            nombre_usuario=nombre_usuario,
            correo=correo,
        )

        _refresh_active_session_with_profile(perfil_actualizado)

        _registrar_auditoria(
            conn,
            codigo_usuario=perfil_actualizado.get("codigo_usuario") or cuid,
            movimiento_cod=Mov.USUARIO_ACTUALIZADO,
            id_row_tabla=perfil_actualizado.get("usuario_seguridad_id"),
        )

        return {
            "ok": True,
            "message": "Perfil actualizado correctamente.",
            "data": perfil_actualizado,
        }
    finally:
        conn.close()


# =========================================================
# UPDATE / FOTO DE PERFIL
# =========================================================
def upload_mi_foto_perfil_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
    *,
    origen_file_path: str,
    usuario_seguridad_id: int | None = None,
    codigo_usuario: int | None = None,
):
    """
    Carga o reemplaza la foto de perfil del usuario activo.
    """
    usid, cuid = _get_active_ids(
        usuario_seguridad_id=usuario_seguridad_id,
        codigo_usuario=codigo_usuario,
    )

    if usid is None:
        raise ValidationError(
            "No se pudo determinar el Usuario_Seguridad_Id del usuario activo."
        )

    conn = _get_conn()
    try:
        perfil_actualizado = guardar_foto_perfil_usuario(
            conn,
            usuario_seguridad_id=usid,
            origen_file_path=origen_file_path,
        )

        _refresh_active_session_with_profile(perfil_actualizado)

        _registrar_auditoria(
            conn,
            codigo_usuario=perfil_actualizado.get("codigo_usuario") or cuid,
            movimiento_cod=Mov.USUARIO_ACTUALIZADO,
            id_row_tabla=perfil_actualizado.get("usuario_seguridad_id"),
        )

        return {
            "ok": True,
            "message": "Foto de perfil actualizada correctamente.",
            "data": perfil_actualizado,
        }
    finally:
        conn.close()


def remove_mi_foto_perfil_endpoint(
    db_user: str | None = None,
    db_pass: str | None = None,
    *,
    usuario_seguridad_id: int | None = None,
    codigo_usuario: int | None = None,
):
    """
    Elimina la foto personalizada del usuario activo y vuelve a la imagen default.
    """
    usid, cuid = _get_active_ids(
        usuario_seguridad_id=usuario_seguridad_id,
        codigo_usuario=codigo_usuario,
    )

    if usid is None:
        raise ValidationError(
            "No se pudo determinar el Usuario_Seguridad_Id del usuario activo."
        )

    conn = _get_conn()
    try:
        perfil_actualizado = quitar_foto_perfil_usuario(
            conn,
            usuario_seguridad_id=usid,
        )

        _refresh_active_session_with_profile(perfil_actualizado)

        _registrar_auditoria(
            conn,
            codigo_usuario=perfil_actualizado.get("codigo_usuario") or cuid,
            movimiento_cod=Mov.USUARIO_ACTUALIZADO,
            id_row_tabla=perfil_actualizado.get("usuario_seguridad_id"),
        )

        return {
            "ok": True,
            "message": "Foto de perfil eliminada correctamente.",
            "data": perfil_actualizado,
        }
    finally:
        conn.close()