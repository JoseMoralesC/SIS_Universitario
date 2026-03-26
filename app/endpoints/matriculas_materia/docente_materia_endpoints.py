from __future__ import annotations

from app.core.db import connect_app
from app.core.auditoria import (
    Mov,
    Tab,
    compose_named_row_id,
)
from app.repositories.auditoria_repo import insert_auditoria
from app.services.security.permission_service import require_matricula_materias_action
from app.services.matriculas_materia.docente_materia_service import DocenteMateriaService


# =========================================================
# Helpers internos
# =========================================================
def _to_int(value, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} inválido.")


def _build_row_id(
    docente_cod: int,
    materia_cod: int,
) -> str:
    """
    Identificador compuesto para auditoría de asignación docente-materia.
    """
    return compose_named_row_id(
        Docente_Cod=int(docente_cod),
        Materia_Cod=int(materia_cod),
    )


def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
    id_row_tabla: object | None = None,
) -> None:
    """
    Mantiene el mismo patrón de auditoría del proyecto,
    pero ahora registrando también tabla e id de fila afectada.
    """
    if codigo_usuario is None:
        return

    try:
        insert_auditoria(
            conn,
            codigo_usuario=int(codigo_usuario),
            movimiento_cod=int(movimiento_cod),
            id_tabla=Tab.DOCENTE_MATERIA,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


def _resolver_movimiento(default_value: int | str | None) -> int:
    if isinstance(default_value, int):
        return default_value

    if isinstance(default_value, str) and hasattr(Mov, default_value):
        return int(getattr(Mov, default_value))

    return 0


def _open_conn(db_user: str | None = None, db_pass: str | None = None):
    return connect_app()


# =========================================================
# Lookups
# =========================================================
def fetch_estados_docente_materia(
    db_user: str,
    db_pass: str,
) -> list[tuple[int, str]]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        return service.obtener_estados()
    finally:
        conn.close()


def fetch_cursos_activos_docente_materia(
    db_user: str,
    db_pass: str,
) -> list[tuple[int, str]]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        return service.obtener_cursos_activos()
    finally:
        conn.close()


def fetch_docentes_por_curso_docente_materia(
    db_user: str,
    db_pass: str,
    curso_cod: int,
) -> list[tuple[int, str]]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        curso_cod = _to_int(curso_cod, "Curso")
        return service.obtener_docentes_por_curso(curso_cod)
    finally:
        conn.close()


def fetch_materias_por_curso_docente_materia(
    db_user: str,
    db_pass: str,
    curso_cod: int,
) -> list[tuple[int, str]]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        curso_cod = _to_int(curso_cod, "Curso")
        return service.obtener_materias_por_curso(curso_cod)
    finally:
        conn.close()


def fetch_materias_disponibles_para_docente(
    db_user: str,
    db_pass: str,
    docente_cod: int,
    curso_cod: int,
) -> list[tuple[int, str]]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)

        docente_cod = _to_int(docente_cod, "Docente")
        curso_cod = _to_int(curso_cod, "Curso")

        return service.obtener_materias_disponibles_para_docente(
            docente_cod=docente_cod,
            curso_cod=curso_cod,
        )
    finally:
        conn.close()


def fetch_docentes_disponibles_para_materia(
    db_user: str,
    db_pass: str,
    materia_cod: int,
) -> list[tuple[int, str]]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        materia_cod = _to_int(materia_cod, "Materia")
        return service.obtener_docentes_disponibles_para_materia(
            materia_cod=materia_cod,
        )
    finally:
        conn.close()


# =========================================================
# Grid / Listados
# =========================================================
def list_docente_materia_rows(
    db_user: str,
    db_pass: str,
) -> list[tuple]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        return service.listar_asignaciones()
    finally:
        conn.close()


def list_docente_materia_rows_activos(
    db_user: str,
    db_pass: str,
) -> list[tuple]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        return service.listar_asignaciones_activas()
    finally:
        conn.close()


def list_docente_materia_rows_por_curso(
    db_user: str,
    db_pass: str,
    curso_cod: int,
) -> list[tuple]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)
        curso_cod = _to_int(curso_cod, "Curso")
        return service.listar_asignaciones_por_curso(curso_cod)
    finally:
        conn.close()


def list_materias_de_docente_rows(
    db_user: str,
    db_pass: str,
    docente_cod: int,
    solo_activas: bool = True,
) -> list[tuple]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)

        docente_cod = _to_int(docente_cod, "Docente")

        return service.listar_materias_de_docente(
            docente_cod=docente_cod,
            solo_activas=solo_activas,
        )
    finally:
        conn.close()


def list_docentes_de_materia_rows(
    db_user: str,
    db_pass: str,
    materia_cod: int,
    solo_activas: bool = True,
) -> list[tuple]:
    require_matricula_materias_action("consultar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)
    try:
        service = DocenteMateriaService(conn)

        materia_cod = _to_int(materia_cod, "Materia")

        return service.listar_docentes_de_materia(
            materia_cod=materia_cod,
            solo_activas=solo_activas,
        )
    finally:
        conn.close()


# =========================================================
# Commands
# =========================================================
def assign_docente_materia(
    *,
    db_user: str,
    db_pass: str,
    docente_cod: int,
    materia_cod: int,
    estado_codigo: int = 1,
    codigo_usuario: int | None = None,
) -> str:
    require_matricula_materias_action("crear", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)

    try:
        service = DocenteMateriaService(conn)

        docente_cod = _to_int(docente_cod, "Docente")
        materia_cod = _to_int(materia_cod, "Materia")
        estado_codigo = _to_int(estado_codigo, "Estado")

        msg = service.asignar_docente_a_materia(
            docente_cod=docente_cod,
            materia_cod=materia_cod,
            estado_codigo=estado_codigo,
        )

        mov = _resolver_movimiento("DOCENTE_MATERIA_CREADA")
        if mov > 0:
            _registrar_auditoria(
                conn,
                codigo_usuario,
                mov,
                id_row_tabla=_build_row_id(
                    docente_cod=docente_cod,
                    materia_cod=materia_cod,
                ),
            )

        return msg

    finally:
        conn.close()


def update_estado_docente_materia(
    *,
    db_user: str,
    db_pass: str,
    docente_cod: int,
    materia_cod: int,
    nuevo_estado_codigo: int,
    codigo_usuario: int | None = None,
) -> str:
    require_matricula_materias_action("actualizar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)

    try:
        service = DocenteMateriaService(conn)

        docente_cod = _to_int(docente_cod, "Docente")
        materia_cod = _to_int(materia_cod, "Materia")
        nuevo_estado_codigo = _to_int(nuevo_estado_codigo, "Estado")

        msg = service.cambiar_estado_asignacion(
            docente_cod=docente_cod,
            materia_cod=materia_cod,
            nuevo_estado_codigo=nuevo_estado_codigo,
        )

        mov = _resolver_movimiento("DOCENTE_MATERIA_ACTUALIZADA")
        if mov > 0:
            _registrar_auditoria(
                conn,
                codigo_usuario,
                mov,
                id_row_tabla=_build_row_id(
                    docente_cod=docente_cod,
                    materia_cod=materia_cod,
                ),
            )

        return msg

    finally:
        conn.close()


def delete_docente_materia(
    *,
    db_user: str,
    db_pass: str,
    docente_cod: int,
    materia_cod: int,
    codigo_usuario: int | None = None,
) -> str:
    require_matricula_materias_action("eliminar", resource_key="docente_materia")

    conn = _open_conn(db_user, db_pass)

    try:
        service = DocenteMateriaService(conn)

        docente_cod = _to_int(docente_cod, "Docente")
        materia_cod = _to_int(materia_cod, "Materia")

        msg = service.desactivar_asignacion(
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        )

        mov = _resolver_movimiento("DOCENTE_MATERIA_ELIMINADA")
        if mov > 0:
            _registrar_auditoria(
                conn,
                codigo_usuario,
                mov,
                id_row_tabla=_build_row_id(
                    docente_cod=docente_cod,
                    materia_cod=materia_cod,
                ),
            )

        return msg

    finally:
        conn.close()