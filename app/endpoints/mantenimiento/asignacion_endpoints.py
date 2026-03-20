from __future__ import annotations

from app.core.db import connect
from app.core.exceptions import ValidationError
from app.core.auditoria import Mov, Tab, compose_named_row_id
from app.repositories.auditoria_repo import insert_auditoria

from app.repositories.mantenimiento.asignacion_repo import (
    fetch_programas_activos,
    fetch_docentes_activos,
    list_asignaciones,
    insert_asignacion,
    update_asignacion,
    delete_asignacion,
)

from app.services.mantenimiento.asignacion_service import (
    validar_asignacion_data,
    validar_asignacion_creacion,
    validar_asignacion_actualizacion,
)


def _build_row_id(curso_cod: int, docente_cod: int) -> str:
    """
    Identificador compuesto para dbo.Curso_Docente.
    """
    return compose_named_row_id(
        Curso_Cod=int(curso_cod),
        Docente_Cod=int(docente_cod),
    )


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
        # No romper flujo principal por fallo aislado de auditoría
        pass


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        programas = fetch_programas_activos(conn)
        docentes = fetch_docentes_activos(conn)
        return programas, docentes
    finally:
        conn.close()


def listar_asignaciones(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
):
    conn = connect(db_user, db_pass)
    try:
        return list_asignaciones(conn)
    finally:
        conn.close()


def crear_asignacion(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    docente_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_asignacion_data(
            curso_cod=curso_cod,
            docente_cod=docente_cod,
        )

        validar_asignacion_creacion(conn, **data)

        insert_asignacion(conn, **data)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_DOCENTE_CREADO,
            id_row_tabla=_build_row_id(
                data["curso_cod"],
                data["docente_cod"],
            ),
        )

        return True
    finally:
        conn.close()


def actualizar_asignacion(
    db_user: str,
    db_pass: str,
    curso_cod_original: int,
    docente_cod_original: int,
    curso_cod_nuevo: int,
    docente_cod_nuevo: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not curso_cod_original or not docente_cod_original:
        raise ValidationError("Debe seleccionar una asignación para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        data_nueva = validar_asignacion_data(
            curso_cod=curso_cod_nuevo,
            docente_cod=docente_cod_nuevo,
        )

        validar_asignacion_actualizacion(
            conn,
            curso_cod_original=int(curso_cod_original),
            docente_cod_original=int(docente_cod_original),
            curso_cod_nuevo=data_nueva["curso_cod"],
            docente_cod_nuevo=data_nueva["docente_cod"],
        )

        update_asignacion(
            conn,
            curso_cod_original=int(curso_cod_original),
            docente_cod_original=int(docente_cod_original),
            curso_cod_nuevo=data_nueva["curso_cod"],
            docente_cod_nuevo=data_nueva["docente_cod"],
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_DOCENTE_ACTUALIZADO,
            id_row_tabla=_build_row_id(
                data_nueva["curso_cod"],
                data_nueva["docente_cod"],
            ),
        )

        return True
    finally:
        conn.close()


def eliminar_asignacion(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    docente_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not curso_cod or not docente_cod:
        raise ValidationError("Debe seleccionar una asignación para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        curso_cod = int(curso_cod)
        docente_cod = int(docente_cod)

        delete_asignacion(
            conn,
            curso_cod=curso_cod,
            docente_cod=docente_cod,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.CURSO_DOCENTE_ELIMINADO,
            id_row_tabla=_build_row_id(curso_cod, docente_cod),
        )

        return True
    finally:
        conn.close()