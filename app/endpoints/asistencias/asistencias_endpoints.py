# app/endpoints/asistencias/asistencias_endpoints.py
from __future__ import annotations

from app.core.db import connect
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
# Helpers internos
# =========================================================
def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
    id_row_tabla: object | None = None,
) -> None:
    """
    Auditoría central del módulo de asistencias.

    Se registra sobre dbo.Asistencia_Lista, cuya PK es:
    - Asistencia_Lista_Id
    """
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
        # No romper flujo principal por fallo aislado de auditoría
        pass


# =========================================================
# Lookups base
# =========================================================
def get_periodos_activos(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
) -> list[dict]:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return listar_periodos_activos(conn)
    finally:
        conn.close()


def get_cursos_por_periodo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    codigo_usuario: int | None = None,
) -> list[dict]:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return listar_cursos_por_periodo(
            conn,
            periodo_id=int(periodo_id),
        )
    finally:
        conn.close()


def get_materias_por_periodo_curso(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    curso_cod: int,
    codigo_usuario: int | None = None,
) -> list[dict]:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return listar_materias_por_periodo_curso(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
        )
    finally:
        conn.close()


def get_docentes_por_periodo_curso_materia(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    codigo_usuario: int | None = None,
) -> list[dict]:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return listar_docentes_por_periodo_curso_materia(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
        )
    finally:
        conn.close()


def get_horario_principal_materia(
    db_user: str,
    db_pass: str,
    materia_cod: int,
    codigo_usuario: int | None = None,
) -> dict | None:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return obtener_horario_principal_materia(
            conn,
            materia_cod=int(materia_cod),
        )
    finally:
        conn.close()


def get_horarios_materia(
    db_user: str,
    db_pass: str,
    materia_cod: int,
    codigo_usuario: int | None = None,
) -> list[dict]:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return listar_horarios_materia(
            conn,
            materia_cod=int(materia_cod),
        )
    finally:
        conn.close()


def get_estudiantes_grupo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    codigo_usuario: int | None = None,
) -> list[dict]:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
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


def get_resumen_grupo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    codigo_usuario: int | None = None,
) -> dict:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return obtener_resumen_grupo(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
            docente_cod=int(docente_cod),
        )
    finally:
        conn.close()


# =========================================================
# Carga de asistencia existente por llave de negocio
# =========================================================
def get_asistencia_existente(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    fecha_clase: str,
    codigo_usuario: int | None = None,
) -> dict | None:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
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


# =========================================================
# Consulta por ID
# =========================================================
def get_asistencia_by_id(
    db_user: str,
    db_pass: str,
    asistencia_lista_id: int,
    codigo_usuario: int | None = None,
) -> dict | None:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return obtener_asistencia_por_id(
            conn,
            asistencia_lista_id=int(asistencia_lista_id),
        )
    finally:
        conn.close()


def get_resumen_lista_asistencia(
    db_user: str,
    db_pass: str,
    asistencia_lista_id: int,
    codigo_usuario: int | None = None,
) -> dict | None:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return obtener_resumen_lista_asistencia(
            conn,
            asistencia_lista_id=int(asistencia_lista_id),
        )
    finally:
        conn.close()


# =========================================================
# Consulta de listas existentes con filtros
# =========================================================
def search_listas_asistencia(
    db_user: str,
    db_pass: str,
    *,
    periodo_id: int | None = None,
    curso_cod: int | None = None,
    materia_cod: int | None = None,
    docente_cod: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    solo_activas: bool = True,
    codigo_usuario: int | None = None,
) -> list[dict]:
    require_asistencias_action("consultar")

    conn = connect(db_user, db_pass)
    try:
        return consultar_listas_asistencia(
            conn,
            periodo_id=None if periodo_id in (None, "", 0) else int(periodo_id),
            curso_cod=None if curso_cod in (None, "", 0) else int(curso_cod),
            materia_cod=None if materia_cod in (None, "", 0) else int(materia_cod),
            docente_cod=None if docente_cod in (None, "", 0) else int(docente_cod),
            fecha_desde=None if not fecha_desde else str(fecha_desde).strip(),
            fecha_hasta=None if not fecha_hasta else str(fecha_hasta).strip(),
            solo_activas=bool(solo_activas),
        )
    finally:
        conn.close()


# =========================================================
# Guardado
# =========================================================
def save_asistencia(
    db_user: str,
    db_pass: str,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    fecha_clase: str,
    asistentes: list[str] | tuple[str, ...] | None,
    ausentes: list[str] | tuple[str, ...] | None,
    codigo_usuario: int | None,
) -> dict:
    conn = connect(db_user, db_pass)
    try:
        asistencia_existente = cargar_asistencia_existente(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
            docente_cod=int(docente_cod),
            fecha_clase=str(fecha_clase).strip(),
        )

        if asistencia_existente:
            require_asistencias_action("actualizar")
        else:
            require_asistencias_action("crear")

        result = guardar_asistencia(
            conn,
            periodo_id=int(periodo_id),
            curso_cod=int(curso_cod),
            materia_cod=int(materia_cod),
            docente_cod=int(docente_cod),
            fecha_clase=str(fecha_clase).strip(),
            asistentes=list(asistentes or []),
            ausentes=list(ausentes or []),
            codigo_usuario=None if codigo_usuario is None else int(codigo_usuario),
        )

        if codigo_usuario is not None and isinstance(result, dict):
            accion = str(result.get("accion", "")).strip().lower()
            asistencia_lista_id = result.get("asistencia_lista_id")

            if accion == "creada":
                _registrar_auditoria(
                    conn,
                    codigo_usuario,
                    Mov.ASISTENCIA_LISTA_CREADA,
                    id_row_tabla=asistencia_lista_id,
                )
            elif accion == "actualizada":
                _registrar_auditoria(
                    conn,
                    codigo_usuario,
                    Mov.ASISTENCIA_LISTA_ACTUALIZADA,
                    id_row_tabla=asistencia_lista_id,
                )

        return result
    finally:
        conn.close()