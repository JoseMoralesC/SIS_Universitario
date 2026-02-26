# app/endpoints/cursos_endpoints.py
from __future__ import annotations

from app.core.db import connect
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

from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        estados = fetch_estados(conn)
        programas = fetch_programas(conn)
        return estados, programas
    finally:
        conn.close()


def listar_cursos(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    """
    Lista cursos visibles en el grid:
    - NO incluye estado Inactivo
    - Sí incluye Activo y Suspendido (y cualquier otro excepto Inactivo)

    codigo_usuario se acepta por consistencia (y futuras auditorías de listado).
    """
    conn = connect(db_user, db_pass)
    try:
        return list_cursos_join_activos(conn)
    finally:
        conn.close()


def siguiente_materia_cod(db_user: str, db_pass: str) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_materia_cod(conn)
    finally:
        conn.close()


def crear_curso(
    db_user: str,
    db_pass: str,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    precio: str,  # NUEVO
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_curso_data(
            descripcion=descripcion,
            curso_cod=curso_cod,
            precio=precio,  # NUEVO
            estado_codigo=estado_codigo,
        )

        validar_curso_unicidad(
            conn,
            materia_cod=None,  # crear
            descripcion=data["descripcion"],
            curso_cod=data["curso_cod"],
        )

        insert_curso(conn, materia_cod=int(materia_cod), **data)

        # Auditoría
        try:
            insert_auditoria(conn, codigo_usuario=codigo_usuario, movimiento_cod=Mov.CURSO_CREADO)
        except Exception:
            pass

        return True
    finally:
        conn.close()


def actualizar_curso(
    db_user: str,
    db_pass: str,
    materia_cod: int,
    descripcion: str,
    curso_cod: int,
    precio: str,  # NUEVO
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not materia_cod:
        raise ValidationError("Debe seleccionar un curso para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        data = validar_curso_data(
            descripcion=descripcion,
            curso_cod=curso_cod,
            precio=precio,  # NUEVO
            estado_codigo=estado_codigo,
        )

        validar_curso_unicidad(
            conn,
            materia_cod=int(materia_cod),
            descripcion=data["descripcion"],
            curso_cod=data["curso_cod"],
        )

        update_curso(conn, materia_cod=int(materia_cod), **data)

        # Auditoría
        try:
            insert_auditoria(conn, codigo_usuario=codigo_usuario, movimiento_cod=Mov.CURSO_ACTUALIZADO)
        except Exception:
            pass

        return True
    finally:
        conn.close()


def eliminar_curso(
    db_user: str,
    db_pass: str,
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

    conn = connect(db_user, db_pass)
    try:
        soft_delete_curso(conn, int(materia_cod))

        # Auditoría
        try:
            insert_auditoria(conn, codigo_usuario=codigo_usuario, movimiento_cod=Mov.CURSO_ELIMINADO)
        except Exception:
            pass

        return True
    finally:
        conn.close()