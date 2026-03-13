# app/endpoints/mantenimiento/programas_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.mantenimiento.programas_service import (
    validar_programa_data,
    validar_programa_unicidad,
)
from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.programas_repo import (
    fetch_estados,
    list_programas_join_activos,
    next_curso_cod,
    insert_programa,
    update_programa,
    soft_delete_programa,
    set_curso_jornadas,
    get_curso_jornadas,
)

from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria


def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
) -> None:
    if codigo_usuario is None:
        return

    try:
        insert_auditoria(
            conn,
            codigo_usuario=int(codigo_usuario),
            movimiento_cod=int(movimiento_cod),
        )
    except Exception:
        # No romper el flujo principal por un fallo aislado de auditoría
        pass


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        estados = fetch_estados(conn)
        return estados
    finally:
        conn.close()


def listar_programas(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
):
    """
    Lista programas visibles en el grid:
    - NO incluye estado Inactivo
    - Sí incluye Activo y Suspendido
      (y cualquier otro excepto Inactivo)

    codigo_usuario se acepta por consistencia
    (y futuras auditorías de listado).
    """
    conn = connect(db_user, db_pass)
    try:
        return list_programas_join_activos(conn)
    finally:
        conn.close()


def siguiente_curso_cod(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
) -> int:
    """
    Siguiente ID para Cursos_Programas.
    codigo_usuario se acepta por consistencia.
    """
    conn = connect(db_user, db_pass)
    try:
        return next_curso_cod(conn)
    finally:
        conn.close()


def obtener_jornadas_programa(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    codigo_usuario: int | None = None,
) -> list[int]:
    """
    Devuelve las jornadas (1=Mañana, 2=Tarde, 3=Noche)
    asociadas al curso.
    codigo_usuario se acepta por consistencia.
    """
    if not curso_cod:
        return []

    conn = connect(db_user, db_pass)
    try:
        return get_curso_jornadas(conn, int(curso_cod))
    finally:
        conn.close()


def crear_programa(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    descripcion: str,
    horario_tipo_id: int | None,
    jornadas_ids: list[int] | None,
    precio_matricula: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_programa_data(
            descripcion=descripcion,
            horario_tipo_id=horario_tipo_id,
            jornadas_ids=jornadas_ids,
            precio_matricula=precio_matricula,
            estado_codigo=estado_codigo,
        )

        validar_programa_unicidad(
            conn,
            curso_cod=None,
            descripcion=data["descripcion"],
        )

        # Insert SOLO a Cursos_Programas (sin jornadas_ids)
        insert_programa(
            conn,
            curso_cod=int(curso_cod),
            descripcion=data["descripcion"],
            horario_tipo_id=data["horario_tipo_id"],
            precio_matricula=data["precio_matricula"],
            estado_codigo=data["estado_codigo"],
        )

        # Guardar jornadas en tabla puente
        set_curso_jornadas(
            conn,
            int(curso_cod),
            data["jornadas_ids"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PROGRAMA_CREADO,
        )

        return True
    finally:
        conn.close()


def actualizar_programa(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    descripcion: str,
    horario_tipo_id: int | None,
    jornadas_ids: list[int] | None,
    precio_matricula: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not curso_cod:
        raise ValidationError("Debe seleccionar un programa para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        data = validar_programa_data(
            descripcion=descripcion,
            horario_tipo_id=horario_tipo_id,
            jornadas_ids=jornadas_ids,
            precio_matricula=precio_matricula,
            estado_codigo=estado_codigo,
        )

        validar_programa_unicidad(
            conn,
            curso_cod=int(curso_cod),
            descripcion=data["descripcion"],
        )

        # Update SOLO a Cursos_Programas (sin jornadas_ids)
        update_programa(
            conn,
            curso_cod=int(curso_cod),
            descripcion=data["descripcion"],
            horario_tipo_id=data["horario_tipo_id"],
            precio_matricula=data["precio_matricula"],
            estado_codigo=data["estado_codigo"],
        )

        # Reemplazar jornadas
        set_curso_jornadas(
            conn,
            int(curso_cod),
            data["jornadas_ids"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PROGRAMA_ACTUALIZADO,
        )

        return True
    finally:
        conn.close()


def eliminar_programa(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    """
    Borrado lógico:
    - Cambia Estado_Codigo al estado "Inactivo"
    - No hace DELETE físico
    """
    if not curso_cod:
        raise ValidationError("Debe seleccionar un programa para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        soft_delete_programa(conn, int(curso_cod))

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PROGRAMA_ELIMINADO,
        )

        return True
    finally:
        conn.close()