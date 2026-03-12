from __future__ import annotations

from typing import List, Tuple

from app.core.db import connect

from app.repositories.matriculas_materia.consulta_matricula_estudiante_repo import (
    fetch_periodos_con_matricula,
    fetch_cursos_por_periodo,
    fetch_estudiantes_por_periodo_curso,
    list_matricula_detalle_estudiante,
)


# =========================================================
# Periodos
# =========================================================
def listar_periodos_con_matricula(
    db_user: str,
    db_pass: str,
) -> List[Tuple[int, str, int]]:
    """
    Retorna períodos disponibles para consulta de matrícula.

    Formato:
        (Periodo_Id, Periodo_Codigo, Anio)
    """
    conn = connect(db_user, db_pass)

    try:
        return fetch_periodos_con_matricula(conn)
    finally:
        conn.close()


# =========================================================
# Cursos
# =========================================================
def listar_cursos_por_periodo(
    db_user: str,
    db_pass: str,
    *,
    periodo_id: int,
    anio: int,
) -> List[Tuple[int, str]]:
    """
    Cursos con matrícula activa en el período seleccionado.

    Retorna:
        (Curso_Cod, Descripcion)
    """
    conn = connect(db_user, db_pass)

    try:
        return fetch_cursos_por_periodo(
            conn,
            periodo_id=periodo_id,
            anio=anio,
        )
    finally:
        conn.close()


# =========================================================
# Estudiantes
# =========================================================
def listar_estudiantes_por_periodo_curso(
    db_user: str,
    db_pass: str,
    *,
    periodo_id: int,
    anio: int,
    curso_cod: int,
) -> List[Tuple[str, str]]:
    """
    Estudiantes matriculados en el curso y período.

    Retorna:
        (Carnet, Nombre_Completo)
    """
    conn = connect(db_user, db_pass)

    try:
        return fetch_estudiantes_por_periodo_curso(
            conn,
            periodo_id=periodo_id,
            anio=anio,
            curso_cod=curso_cod,
        )
    finally:
        conn.close()


# =========================================================
# Grid consulta
# =========================================================
def listar_matricula_detalle_estudiante(
    db_user: str,
    db_pass: str,
    *,
    carnet: str,
    periodo_id: int,
    anio: int,
    curso_cod: int,
) -> List[Tuple]:
    """
    Retorna el detalle de matrícula del estudiante.

    Grid:
        Matricula_Materia_Id
        Materia
        Dias
        Jornada
        Horario_Detalle
        Docente
        Estado
        Fecha_Matricula
    """
    conn = connect(db_user, db_pass)

    try:
        return list_matricula_detalle_estudiante(
            conn,
            carnet=carnet,
            periodo_id=periodo_id,
            anio=anio,
            curso_cod=curso_cod,
        )
    finally:
        conn.close()