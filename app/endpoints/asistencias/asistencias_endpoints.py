from __future__ import annotations

from app.core.db import connect_app
from app.core.auditoria import Mov, Tab
from app.repositories.auditoria_repo import insert_auditoria
from app.services.security.permission_service import require_asistencias_action
from app.services.asistencias.asistencias_service import (
    cargar_asistencia_existente,
    consultar_listas_asistencia,
    guardar_asistencia,
    listar_cursos_por_periodo,
    listar_docentes_por_periodo_curso_materia,
    listar_estudiantes_grupo,
    listar_horarios_materia,
    listar_materias_por_periodo_curso,
    listar_periodos_activos,
    obtener_asistencia_por_id,
    obtener_horario_principal_materia,
    obtener_resumen_grupo,
    obtener_resumen_lista_asistencia,
)


# =========================================================
# Helper conexión (ESTÁNDAR PROYECTO)
# =========================================================
def _get_conn():
    return connect_app()


# =========================================================
# Auditoría
# =========================================================
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
            id_tabla=Tab.ASISTENCIA_LISTA,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


# =========================================================
# LOOKUPS
# =========================================================
def get_periodos_activos(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return listar_periodos_activos(conn)
    finally:
        conn.close()


def get_cursos_por_periodo(db_user, db_pass, periodo_id, codigo_usuario=None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return listar_cursos_por_periodo(conn, periodo_id=int(periodo_id))
    finally:
        conn.close()


def get_materias_por_periodo_curso(db_user, db_pass, periodo_id, curso_cod, codigo_usuario=None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return listar_materias_por_periodo_curso(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
        )
    finally:
        conn.close()


def get_docentes_por_periodo_curso_materia(db_user, db_pass, periodo_id, curso_cod, materia_cod, codigo_usuario=None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return listar_docentes_por_periodo_curso_materia(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
        )
    finally:
        conn.close()


def get_estudiantes_grupo(db_user, db_pass, periodo_id, curso_cod, materia_cod, docente_cod, codigo_usuario=None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return listar_estudiantes_grupo(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
            docente_cod=int(docente_cod),
        )
    finally:
        conn.close()


# =========================================================
# CONSULTAS
# =========================================================
def get_asistencia_existente(db_user, db_pass, periodo_id, curso_cod, materia_cod, docente_cod, fecha_clase, codigo_usuario=None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return cargar_asistencia_existente(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
            docente_cod=int(docente_cod),
            fecha_clase=str(fecha_clase).strip(),
        )
    finally:
        conn.close()


def get_asistencia_by_id(db_user, db_pass, asistencia_lista_id, codigo_usuario=None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return obtener_asistencia_por_id(
            conn,
            asistencia_lista_id=int(asistencia_lista_id),
        )
    finally:
        conn.close()


def get_resumen_lista_asistencia(db_user, db_pass, asistencia_lista_id, codigo_usuario=None):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return obtener_resumen_lista_asistencia(
            conn,
            asistencia_lista_id=int(asistencia_lista_id),
        )
    finally:
        conn.close()


def search_listas_asistencia(db_user, db_pass, **kwargs):
    require_asistencias_action("consultar")

    conn = _get_conn()
    try:
        return consultar_listas_asistencia(conn, **kwargs)
    finally:
        conn.close()


# =========================================================
# GUARDADO
# =========================================================
def save_asistencia(db_user, db_pass, *, periodo_id, curso_cod, materia_cod, docente_cod, fecha_clase, asistentes, ausentes, codigo_usuario):

    conn = _get_conn()
    try:
        existente = cargar_asistencia_existente(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
            docente_cod=int(docente_cod),
            fecha_clase=str(fecha_clase).strip(),
        )

        require_asistencias_action("actualizar" if existente else "crear")

        result = guardar_asistencia(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
            docente_cod=int(docente_cod),
            fecha_clase=str(fecha_clase).strip(),
            asistentes=list(asistentes or []),
            ausentes=list(ausentes or []),
            codigo_usuario=codigo_usuario,
        )

        if codigo_usuario and isinstance(result, dict):
            accion = str(result.get("accion", "")).lower()

            if accion == "creada":
                _registrar_auditoria(conn, codigo_usuario, Mov.ASISTENCIA_LISTA_CREADA, result.get("asistencia_lista_id"))

            elif accion == "actualizada":
                _registrar_auditoria(conn, codigo_usuario, Mov.ASISTENCIA_LISTA_ACTUALIZADA, result.get("asistencia_lista_id"))

        return result

    finally:
        conn.close()