from __future__ import annotations

from app.core.db import connect_app
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria

from app.repositories.mantenimiento.asignacion_repo import (
    fetch_programas_activos,
    list_asignaciones,
    insert_asignacion,
    update_asignacion,
    delete_asignacion,
)

from app.services.mantenimiento.asignacion_service import (
    validar_asignacion_data,
    validar_asignacion_creacion,
    validar_asignacion_actualizacion,
    obtener_docentes_disponibles_para_programa,
)
from app.services.security.permission_service import (
    require_maintenance_access,
    require_maintenance_action,
)


RESOURCE_KEY = "asignacion"


def _get_conn():
    return connect_app()


def _compose_named_row_id(curso_cod: int, docente_cod: int) -> str:
    return f"curso_cod={int(curso_cod)};docente_cod={int(docente_cod)}"


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
            id_tabla=Tab.CURSO_DOCENTE,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


def get_lookups(
    db_user: str | None = None,
    db_pass: str | None = None,
):
    """
    Devuelve programas activos.
    El combo de docentes se carga por programa seleccionado.
    """
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        programas = fetch_programas_activos(conn)
        return programas, []
    finally:
        conn.close()


def get_docentes_disponibles_para_programa(
    db_user: str | None,
    db_pass: str | None,
    curso_cod: int,
    docente_cod_actual: int | None = None,
):
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return obtener_docentes_disponibles_para_programa(
            conn,
            curso_cod=int(curso_cod),
            docente_cod_actual=docente_cod_actual,
        )
    finally:
        conn.close()


def listar_asignaciones(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
):
    require_maintenance_access(RESOURCE_KEY)

    conn = _get_conn()
    try:
        return list_asignaciones(conn)
    finally:
        conn.close()


def crear_asignacion(
    db_user: str | None,
    db_pass: str | None,
    curso_cod: int,
    docente_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "create")

    conn = _get_conn()
    try:
        data = validar_asignacion_data(
            curso_cod=curso_cod,
            docente_cod=docente_cod,
        )

        validar_asignacion_creacion(
            conn,
            curso_cod=data["curso_cod"],
            docente_cod=data["docente_cod"],
        )

        insert_asignacion(
            conn,
            curso_cod=data["curso_cod"],
            docente_cod=data["docente_cod"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_DOCENTE_CREADO,
            id_row_tabla=_compose_named_row_id(
                data["curso_cod"],
                data["docente_cod"],
            ),
        )

        return True
    finally:
        conn.close()


def actualizar_asignacion(
    db_user: str | None,
    db_pass: str | None,
    curso_cod_original: int,
    docente_cod_original: int,
    curso_cod_nuevo: int,
    docente_cod_nuevo: int,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "update")

    if not curso_cod_original or not docente_cod_original:
        raise ValidationError("Debe seleccionar una asignación para actualizar.")

    conn = _get_conn()
    try:
        original = validar_asignacion_data(
            curso_cod=curso_cod_original,
            docente_cod=docente_cod_original,
        )
        nuevo = validar_asignacion_data(
            curso_cod=curso_cod_nuevo,
            docente_cod=docente_cod_nuevo,
        )

        validar_asignacion_actualizacion(
            conn,
            curso_cod_original=original["curso_cod"],
            docente_cod_original=original["docente_cod"],
            curso_cod_nuevo=nuevo["curso_cod"],
            docente_cod_nuevo=nuevo["docente_cod"],
        )

        update_asignacion(
            conn,
            curso_cod_original=original["curso_cod"],
            docente_cod_original=original["docente_cod"],
            curso_cod_nuevo=nuevo["curso_cod"],
            docente_cod_nuevo=nuevo["docente_cod"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_DOCENTE_ACTUALIZADO,
            id_row_tabla=(
                f"{_compose_named_row_id(original['curso_cod'], original['docente_cod'])}"
                f" -> "
                f"{_compose_named_row_id(nuevo['curso_cod'], nuevo['docente_cod'])}"
            ),
        )

        return True
    finally:
        conn.close()


def eliminar_asignacion(
    db_user: str | None,
    db_pass: str | None,
    curso_cod: int,
    docente_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    require_maintenance_action(RESOURCE_KEY, "delete")

    data = validar_asignacion_data(
        curso_cod=curso_cod,
        docente_cod=docente_cod,
    )

    conn = _get_conn()
    try:
        delete_asignacion(
            conn,
            curso_cod=data["curso_cod"],
            docente_cod=data["docente_cod"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_DOCENTE_ELIMINADO,
            id_row_tabla=_compose_named_row_id(
                data["curso_cod"],
                data["docente_cod"],
            ),
        )

        return True
    finally:
        conn.close()