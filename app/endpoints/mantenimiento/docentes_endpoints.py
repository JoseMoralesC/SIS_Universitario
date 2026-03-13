# app/endpoints/docentes_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.mantenimiento.docentes_service import (
    validar_docente_data,
    validar_docente_unicidad,
)
from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.docentes_repo import (
    fetch_estados,
    fetch_profesiones,
    list_docentes_join_activos,
    insert_docente,
    update_docente,
    soft_delete_docente,
    next_docente_cod,
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


def siguiente_docente_cod(db_user: str, db_pass: str) -> int:
    conn = connect(db_user, db_pass)
    try:
        return next_docente_cod(conn)
    finally:
        conn.close()


def get_lookups(db_user: str, db_pass: str):
    conn = connect(db_user, db_pass)
    try:
        estados = fetch_estados(conn)
        profesiones = fetch_profesiones(conn)
        return estados, profesiones
    finally:
        conn.close()


def listar_docentes(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
):
    """
    Lista docentes visibles en el grid:
    - NO incluye estado Inactivo
    - Sí incluye Activo y Suspendido (y cualquier otro excepto Inactivo)

    codigo_usuario se acepta por consistencia
    (y futuras auditorías de listado).
    """
    conn = connect(db_user, db_pass)
    try:
        return list_docentes_join_activos(conn)
    finally:
        conn.close()


def crear_docente(
    db_user: str,
    db_pass: str,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_docente_data(
            identificacion=identificacion,
            usuario_docente=usuario_docente,
            nombre_completo=nombre_completo,
            estado_codigo=estado_codigo,
            profesion_cod=profesion_cod,
        )

        validar_docente_unicidad(
            conn,
            docente_cod=None,
            identificacion=data["identificacion"],
            usuario_docente=data["usuario_docente"],
        )

        insert_docente(
            conn,
            docente_cod=int(docente_cod),
            **data,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.DOCENTE_CREADO,
        )

        return True
    finally:
        conn.close()


def actualizar_docente(
    db_user: str,
    db_pass: str,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    if not docente_cod:
        raise ValidationError("Debe seleccionar un docente para actualizar.")

    conn = connect(db_user, db_pass)
    try:
        data = validar_docente_data(
            identificacion=identificacion,
            usuario_docente=usuario_docente,
            nombre_completo=nombre_completo,
            estado_codigo=estado_codigo,
            profesion_cod=profesion_cod,
        )

        validar_docente_unicidad(
            conn,
            docente_cod=int(docente_cod),
            identificacion=data["identificacion"],
            usuario_docente=data["usuario_docente"],
        )

        update_docente(
            conn,
            docente_cod=int(docente_cod),
            **data,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.DOCENTE_ACTUALIZADO,
        )

        return True
    finally:
        conn.close()


def eliminar_docente(
    db_user: str,
    db_pass: str,
    docente_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    """
    Borrado lógico:
    - Cambia Estado_Codigo al estado "Inactivo"
    - No hace DELETE físico
    """
    if not docente_cod:
        raise ValidationError("Debe seleccionar un docente para eliminar.")

    conn = connect(db_user, db_pass)
    try:
        soft_delete_docente(conn, int(docente_cod))

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.DOCENTE_ELIMINADO,
        )

        return True
    finally:
        conn.close()