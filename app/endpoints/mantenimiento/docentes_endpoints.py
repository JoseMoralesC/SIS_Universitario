# app/endpoints/docentes_endpoints.py
from __future__ import annotations

from app.core.db import connect_app
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
            id_tabla=Tab.DOCENTES,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        # No romper el flujo principal por un fallo aislado de auditoría
        pass


def siguiente_docente_cod(db_user: str | None = None, db_pass: str | None = None) -> int:
    conn = _get_conn()
    try:
        return next_docente_cod(conn)
    finally:
        conn.close()


def get_lookups(db_user: str | None = None, db_pass: str | None = None):
    conn = _get_conn()
    try:
        estados = fetch_estados(conn)
        profesiones = fetch_profesiones(conn)
        return estados, profesiones
    finally:
        conn.close()


def listar_docentes(
    db_user: str | None = None,
    db_pass: str | None = None,
    codigo_usuario: int | None = None,
):
    """
    Lista docentes visibles en el grid:
    - NO incluye estado Inactivo
    - Sí incluye Activo y Suspendido (y cualquier otro excepto Inactivo)

    db_user y db_pass se conservan por compatibilidad temporal.
    codigo_usuario se acepta por consistencia y auditoría futura.
    """
    conn = _get_conn()
    try:
        return list_docentes_join_activos(conn)
    finally:
        conn.close()


def crear_docente(
    db_user: str | None,
    db_pass: str | None,
    docente_cod: int,
    identificacion: str,
    usuario_docente: str,
    nombre_completo: str,
    estado_codigo: int,
    profesion_cod: int,
    codigo_usuario: int | None = None,
) -> bool:
    conn = _get_conn()
    try:
        data = validar_docente_data(
            identificacion=identificacion,
            usuario_docente=usuario_docente,
            nombre_completo=nombre_completo,
            estado_codigo=estado_codigo,
            profesion_cod=profesion_cod,
        )

        docente_cod = int(docente_cod)

        validar_docente_unicidad(
            conn,
            docente_cod=None,
            identificacion=data["identificacion"],
            usuario_docente=data["usuario_docente"],
        )

        insert_docente(
            conn,
            docente_cod=docente_cod,
            **data,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.DOCENTE_CREADO,
            id_row_tabla=docente_cod,
        )

        return True
    finally:
        conn.close()


def actualizar_docente(
    db_user: str | None,
    db_pass: str | None,
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

    conn = _get_conn()
    try:
        data = validar_docente_data(
            identificacion=identificacion,
            usuario_docente=usuario_docente,
            nombre_completo=nombre_completo,
            estado_codigo=estado_codigo,
            profesion_cod=profesion_cod,
        )

        docente_cod = int(docente_cod)

        validar_docente_unicidad(
            conn,
            docente_cod=docente_cod,
            identificacion=data["identificacion"],
            usuario_docente=data["usuario_docente"],
        )

        update_docente(
            conn,
            docente_cod=docente_cod,
            **data,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.DOCENTE_ACTUALIZADO,
            id_row_tabla=docente_cod,
        )

        return True
    finally:
        conn.close()


def eliminar_docente(
    db_user: str | None,
    db_pass: str | None,
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

    conn = _get_conn()
    try:
        docente_cod = int(docente_cod)

        soft_delete_docente(conn, docente_cod)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.DOCENTE_ELIMINADO,
            id_row_tabla=docente_cod,
        )

        return True
    finally:
        conn.close()