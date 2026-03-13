# app/endpoints/asistencias/asistencias_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.services.asistencias.asistencias_service import (
    cargar_asistencia_existente,
    guardar_asistencia,
    listar_cursos_por_periodo,
    listar_docentes_por_periodo_curso_materia,
    listar_estudiantes_grupo,
    listar_materias_por_periodo_curso,
    listar_periodos_activos,
    obtener_horario_principal_materia,
    obtener_resumen_grupo,
)


def get_periodos_activos(db_user: str, db_pass: str) -> list[dict]:
    conn = connect(db_user, db_pass)
    try:
        return listar_periodos_activos(conn)
    finally:
        conn.close()


def get_cursos_por_periodo(
    db_user: str,
    db_pass: str,
    periodo_id: int,
) -> list[dict]:
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
) -> list[dict]:
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
) -> list[dict]:
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
) -> dict | None:
    conn = connect(db_user, db_pass)
    try:
        return obtener_horario_principal_materia(
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
) -> list[dict]:
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
) -> dict:
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


def get_asistencia_existente(
    db_user: str,
    db_pass: str,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    fecha_clase: str,
) -> dict | None:
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
        return guardar_asistencia(
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
    finally:
        conn.close()