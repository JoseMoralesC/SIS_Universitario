# app/endpoints/mantenimiento/estudiantes_endpoints.py
from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.repositories.mantenimiento.estudiantes_repo import (
    fetch_estados,
    list_estudiantes_join_activos,
    next_carnet,
    insert_estudiante,
    update_estudiante,
    soft_delete_estudiante,
)
from app.services.mantenimiento.estudiantes_service import (
    validar_estudiante_data,
    validar_estudiante_unicidad,
)
from app.services.security.permission_service import (
    require_maintenance_access,
    require_maintenance_action,
)


RESOURCE_KEY = "estudiantes"


def _get_conn():
    """
    Obtiene la conexión técnica de la aplicación.
    """
    return connect_app()


def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
    id_row_tabla: object | None = None,
) -> None:
    if codigo_usuario is None:
        return

    try:
        insert_auditoria(
            conn,
            codigo_usuario=int(codigo_usuario),
            movimiento_cod=int(movimiento_cod),
            id_tabla=Tab.ESTUDIANTES,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        # No romper el flujo principal por un fallo aislado de auditoría
        pass


def get_lookups(
    db_user: str | None = None,
    db_pass: str | None = None,
):
    """
    Devuelve estados de estudiante.
    """
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return fetch_estados(conn)
    finally:
        conn.close()


def listar_estudiantes(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
):
    """
    Lista estudiantes visibles en el grid.
    db_user y db_pass se conservan por compatibilidad temporal.
    codigo_usuario se acepta por consistencia.
    """
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return list_estudiantes_join_activos(conn)
    finally:
        conn.close()


def siguiente_carnet(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
) -> str:
    """
    Siguiente carnet para estudiantes.
    db_user y db_pass se conservan por compatibilidad temporal.
    codigo_usuario se acepta por uniformidad.
    """
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return next_carnet(conn)
    finally:
        conn.close()


def crear_estudiante(
    db_user: str | None,
    db_pass: str | None,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str,
    telefono: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "create")

    conn = _get_conn()
    try:
        data = validar_estudiante_data(
            identificacion=identificacion,
            nombre_completo=nombre_completo,
            direccion=direccion,
            telefono=telefono,
            estado_codigo=estado_codigo,
        )

        carnet = str(carnet).strip()
        if not carnet:
            raise ValidationError("Debe indicar un carnet válido.")

        validar_estudiante_unicidad(
            conn,
            carnet=None,
            identificacion=data["identificacion"],
        )

        insert_estudiante(
            conn,
            carnet=carnet,
            identificacion=data["identificacion"],
            nombre_completo=data["nombre_completo"],
            direccion=data["direccion"],
            telefono=data["telefono"],
            estado_codigo=data["estado_codigo"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.ESTUDIANTE_CREADO,
            id_row_tabla=carnet,
        )

        return True
    finally:
        conn.close()


def actualizar_estudiante(
    db_user: str | None,
    db_pass: str | None,
    carnet: str,
    identificacion: str,
    nombre_completo: str,
    direccion: str,
    telefono: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "update")

    carnet = str(carnet).strip()
    if not carnet:
        raise ValidationError("Debe seleccionar un estudiante para actualizar.")

    conn = _get_conn()
    try:
        data = validar_estudiante_data(
            identificacion=identificacion,
            nombre_completo=nombre_completo,
            direccion=direccion,
            telefono=telefono,
            estado_codigo=estado_codigo,
        )

        validar_estudiante_unicidad(
            conn,
            carnet=carnet,
            identificacion=data["identificacion"],
        )

        update_estudiante(
            conn,
            carnet=carnet,
            identificacion=data["identificacion"],
            nombre_completo=data["nombre_completo"],
            direccion=data["direccion"],
            telefono=data["telefono"],
            estado_codigo=data["estado_codigo"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.ESTUDIANTE_ACTUALIZADO,
            id_row_tabla=carnet,
        )

        return True
    finally:
        conn.close()


def eliminar_estudiante(
    db_user: str | None,
    db_pass: str | None,
    carnet: str,
    codigo_usuario: int | None = None,
) -> bool:
    """
    Borrado lógico:
    - Cambia Estado_Codigo al estado "Inactivo"
    - No hace DELETE físico
    """
    require_maintenance_action(RESOURCE_KEY, "delete")

    carnet = str(carnet).strip()
    if not carnet:
        raise ValidationError("Debe seleccionar un estudiante para eliminar.")

    conn = _get_conn()
    try:
        soft_delete_estudiante(conn, carnet)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.ESTUDIANTE_ELIMINADO,
            id_row_tabla=carnet,
        )

        return True
    finally:
        conn.close()