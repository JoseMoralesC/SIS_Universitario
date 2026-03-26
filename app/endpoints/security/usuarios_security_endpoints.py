from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria
from app.services.security.permission_service import (
    require_module_action,
)
from app.services.security.usuarios_service import (
    get_lookups_registro_usuario,
    registrar_usuario_seguridad,
)


MODULE_KEY = "seguridad"
RESOURCE_KEY = "usuarios"


def _get_conn():
    return connect_app()


def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
    id_row_tabla: object | None = None,
) -> None:
    """
    Registra auditoría del módulo de usuarios.
    La auditoría no debe romper el flujo principal del caso de uso.
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
        # No romper registro de usuario por un fallo de auditoría.
        pass


# =========================================================
# LOOKUPS
# =========================================================
def get_lookups_usuarios_security(
    db_user: str | None = None,
    db_pass: str | None = None,
):
    """
    Devuelve roles, tipos de usuario y estados para el formulario.
    """
    require_module_action(
        MODULE_KEY,
        "view",
        resource_key=RESOURCE_KEY,
    )

    conn = _get_conn()
    try:
        return get_lookups_registro_usuario(conn)
    finally:
        conn.close()


# =========================================================
# CREATE
# =========================================================
def create_usuario_security_endpoint(
    db_user: str | None,
    db_pass: str | None,
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
    codigo_usuario: int | None = None,
):
    """
    Registra un nuevo usuario del sistema con un único rol principal.
    """
    require_module_action(
        MODULE_KEY,
        "create",
        resource_key=RESOURCE_KEY,
    )

    conn = _get_conn()
    try:
        data = registrar_usuario_seguridad(
            conn,
            id_usuario=id_usuario,
            usuario=usuario,
            nombre_usuario=nombre_usuario,
            tipo_usuario=tipo_usuario,
            estado_usuario=estado_usuario,
            rol_id=rol_id,
            clave_plana=clave_plana,
            confirmar_clave=confirmar_clave,
            correo=correo,
            debe_cambiar_clave=debe_cambiar_clave,
        )

        usuario_seguridad_id = data.get("usuario_seguridad_id")
        if not usuario_seguridad_id:
            raise ValidationError(
                "No fue posible obtener el identificador del usuario creado."
            )

        _registrar_auditoria(
            conn,
            codigo_usuario=codigo_usuario,
            movimiento_cod=Mov.USUARIO_CREADO,
            id_row_tabla=usuario_seguridad_id,
        )

        return {
            "ok": True,
            "message": "Usuario registrado correctamente.",
            "data": data,
        }
    finally:
        conn.close()