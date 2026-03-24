# app/endpoints/cursos_endpoints.py
from __future__ import annotations

from app.core.db import connect_app
from app.services.mantenimiento.cursos_service import (
    validar_curso_data,
    validar_curso_unicidad,
)
from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.cursos_repo import (
    fetch_estados,
    fetch_programas,
    list_cursos_join_activos,
    next_materia_cod,
    insert_curso,
    update_curso,
    soft_delete_curso,
)

from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria


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
            id_tabla=Tab.MATERIAS,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        # No romper el flujo principal por un fallo aislado de auditoría
        pass


def get_lookups(db_user: str | None = None, db_pass: str | None = None):
    conn = _get_conn()
    try:
        estados = fetch_estados(conn)
        programas = fetch_programas(conn)
        return estados, programas
    finally:
        conn.close()


def listar_cursos(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
):
    """
    Lista cursos visibles en el grid:
    - NO incluye estado Inactivo
    - Sí incluye Activo y Suspendido (y cualquier otro excepto Inactivo)

    db_user y db_pass se conservan por compatibilidad temporal.
    codigo_usuario se acepta por consistencia
    (y futuras auditorías de listado).
    """
    conn = _get_conn()
    try:
        return list_cursos_join_activos(conn)
    finally:
        conn.close()


def siguiente_materia_cod(db_user: str | None = None, db_pass: str | None = None) -> int:
    conn = _get_conn()
    try:
        return next_materia_cod(conn)
    finally:
        conn.close()


def crear_curso(
    db_user: str | None,
    db_pass: str | None,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    precio: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = _get_conn()
    try:
        data = validar_curso_data(
            descripcion=descripcion,
            curso_cod=curso_cod,
            precio=precio,
            estado_codigo=estado_codigo,
        )

        materia_cod = int(materia_cod)

        validar_curso_unicidad(
            conn,
            materia_cod=None,
            descripcion=data["descripcion"],
            curso_cod=data["curso_cod"],
        )

        insert_curso(
            conn,
            materia_cod=materia_cod,
            **data,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_CREADO,
            id_row_tabla=materia_cod,
        )

        return True
    finally:
        conn.close()


def actualizar_curso(
    db_user: str | None,
    db_pass: str | None,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    precio: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not materia_cod:
        raise ValidationError("Debe seleccionar un curso para actualizar.")

    conn = _get_conn()
    try:
        materia_cod = int(materia_cod)

        data = validar_curso_data(
            descripcion=descripcion,
            curso_cod=curso_cod,
            precio=precio,
            estado_codigo=estado_codigo,
        )

        validar_curso_unicidad(
            conn,
            materia_cod=materia_cod,
            descripcion=data["descripcion"],
            curso_cod=data["curso_cod"],
        )

        update_curso(
            conn,
            materia_cod=materia_cod,
            **data,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_ACTUALIZADO,
            id_row_tabla=materia_cod,
        )

        return True
    finally:
        conn.close()


def eliminar_curso(
    db_user: str | None,
    db_pass: str | None,
    materia_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    """
    Borrado lógico:
    - Cambia Estado_Codigo al estado "Inactivo"
    - No hace DELETE físico
    """
    if not materia_cod:
        raise ValidationError("Debe seleccionar un curso para eliminar.")

    conn = _get_conn()
    try:
        materia_cod = int(materia_cod)

        soft_delete_curso(conn, materia_cod)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_ELIMINADO,
            id_row_tabla=materia_cod,
        )

        return True
    finally:
        conn.close()