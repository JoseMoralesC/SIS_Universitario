from __future__ import annotations

from typing import List, Dict, Any

from app.services.security.permission_service import require_matricula_materias_action
from app.services.matriculas_materia.consulta_matricula_estudiante_service import (
    listar_periodos_con_matricula,
    listar_cursos_por_periodo,
    listar_estudiantes_por_periodo_curso,
    listar_matricula_detalle_estudiante,
)


# =========================================================
# Helpers de formato para UI
# =========================================================
def _periodo_to_dict(row: tuple) -> Dict[str, Any]:
    periodo_id, periodo_codigo, anio = row
    return {
        "periodo_id": int(periodo_id),
        "periodo_codigo": str(periodo_codigo),
        "anio": int(anio),
        "label": f"{periodo_codigo} - {anio}",
    }


def _curso_to_dict(row: tuple) -> Dict[str, Any]:
    curso_cod, descripcion = row
    return {
        "curso_cod": int(curso_cod),
        "descripcion": str(descripcion),
        "label": f"{curso_cod} - {descripcion}",
    }


def _estudiante_to_dict(row: tuple) -> Dict[str, Any]:
    carnet, nombre_completo = row
    return {
        "carnet": str(carnet),
        "nombre_completo": str(nombre_completo),
        "label": f"{carnet} - {nombre_completo}",
    }


def _detalle_to_dict(row: tuple) -> Dict[str, Any]:
    (
        matricula_materia_id,
        materia,
        dias,
        jornada,
        horario_detalle,
        docente,
        estado,
        fecha_matricula,
    ) = row

    return {
        "matricula_materia_id": int(matricula_materia_id),
        "materia": str(materia),
        "dias": str(dias),
        "jornada": str(jornada),
        "horario_detalle": str(horario_detalle),
        "docente": str(docente),
        "estado": str(estado),
        "fecha_matricula": str(fecha_matricula),
    }


# =========================================================
# Endpoints - Comboboxes
# =========================================================
def obtener_periodos_con_matricula(
    db_user: str,
    db_pass: str,
) -> List[Dict[str, Any]]:
    require_matricula_materias_action("consultar", resource_key="consulta_matricula_estudiante")

    rows = listar_periodos_con_matricula(db_user, db_pass)
    return [_periodo_to_dict(r) for r in rows]


def obtener_cursos_por_periodo(
    db_user: str,
    db_pass: str,
    *,
    periodo_id: int,
    anio: int,
) -> List[Dict[str, Any]]:
    require_matricula_materias_action("consultar", resource_key="consulta_matricula_estudiante")

    rows = listar_cursos_por_periodo(
        db_user,
        db_pass,
        periodo_id=periodo_id,
        anio=anio,
    )
    return [_curso_to_dict(r) for r in rows]


def obtener_estudiantes_por_periodo_curso(
    db_user: str,
    db_pass: str,
    *,
    periodo_id: int,
    anio: int,
    curso_cod: int,
) -> List[Dict[str, Any]]:
    require_matricula_materias_action("consultar", resource_key="consulta_matricula_estudiante")

    rows = listar_estudiantes_por_periodo_curso(
        db_user,
        db_pass,
        periodo_id=periodo_id,
        anio=anio,
        curso_cod=curso_cod,
    )
    return [_estudiante_to_dict(r) for r in rows]


# =========================================================
# Endpoint - Grid consulta
# =========================================================
def consultar_matricula_estudiante(
    db_user: str,
    db_pass: str,
    *,
    carnet: str,
    periodo_id: int,
    anio: int,
    curso_cod: int,
) -> List[Dict[str, Any]]:
    require_matricula_materias_action("consultar", resource_key="consulta_matricula_estudiante")

    rows = listar_matricula_detalle_estudiante(
        db_user,
        db_pass,
        carnet=carnet,
        periodo_id=periodo_id,
        anio=anio,
        curso_cod=curso_cod,
    )
    return [_detalle_to_dict(r) for r in rows]