# app/endpoints/matriculas/matriculas_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria

from app.repositories.matriculas.matriculas_repo import (
    fetch_estudiantes_activos,
    fetch_cursos_activos,
    fetch_docentes_activos,
    fetch_docentes_por_curso,
    list_matriculas,
    insert_matricula,
    update_estado_matricula,
    delete_matricula,
    list_matriculas_por_curso,
    reporte_estudiantes_por_curso as reporte_estudiantes_por_curso_repo,
    fetch_estados,
)

from app.services.matriculas.matriculas_service import (
    validar_matricula_data,
    validar_matricula_reglas,
    validar_cambio_estado,
)


def get_lookups(db_user: str, db_pass: str, codigo_usuario: int | None = None) -> dict:
    conn = connect(db_user, db_pass)
    try:
        return {
            "estados": fetch_estados(conn),
            "estudiantes": fetch_estudiantes_activos(conn),
            "cursos": fetch_cursos_activos(conn),
            # NOTA: docentes generales se pueden dejar si querés para otras pantallas,
            # pero en Matrículas el combo se carga por curso.
            "docentes": fetch_docentes_activos(conn),
        }
    finally:
        conn.close()


def get_docentes_por_curso(db_user: str, db_pass: str, curso_cod: int, codigo_usuario: int | None = None) -> list:
    conn = connect(db_user, db_pass)
    try:
        return fetch_docentes_por_curso(conn, int(curso_cod))
    finally:
        conn.close()


def listar_matriculas(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    conn = connect(db_user, db_pass)
    try:
        return list_matriculas(conn)
    finally:
        conn.close()


def matricular(
    *,
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None,
    carnet: str,
    curso_cod: int,
    docente_cod: int,
    fecha: str,
    periodo: int,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        data = validar_matricula_data(
            carnet=carnet,
            curso_cod=curso_cod,
            docente_cod=docente_cod,
            fecha=fecha,
            periodo=periodo,
        )

        reglas = validar_matricula_reglas(
            conn,
            carnet=data["carnet"],
            curso_cod=data["curso_cod"],
            docente_cod=data["docente_cod"],
            periodo=data["periodo"],
        )

        insert_matricula(
            conn,
            carnet=data["carnet"],
            curso_cod=data["curso_cod"],
            periodo=data["periodo"],
            docente_cod=data["docente_cod"],
            fecha=data["fecha_dt"],
            estado_codigo=int(reglas["estado_codigo"]),
        )

        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.MATRICULA_CREADA)
            except Exception:
                pass

        return True
    finally:
        conn.close()


def cambiar_estado(
    *,
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None,
    carnet: str,
    curso_cod: int,
    periodo: int,
    nuevo_estado: str,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        nuevo_estado_cod = validar_cambio_estado(conn, nuevo_estado=nuevo_estado)

        update_estado_matricula(
            conn,
            carnet=(carnet or "").strip(),
            curso_cod=int(curso_cod),
            periodo=int(periodo),
            nuevo_estado_codigo=int(nuevo_estado_cod),
        )

        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.MATRICULA_ESTADO_CAMBIADO)
            except Exception:
                pass

        return True
    finally:
        conn.close()


def eliminar_matricula(
    *,
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None,
    carnet: str,
    curso_cod: int,
    periodo: int,
) -> bool:
    conn = connect(db_user, db_pass)
    try:
        delete_matricula(
            conn,
            carnet=(carnet or "").strip(),
            curso_cod=int(curso_cod),
            periodo=int(periodo),
        )

        if codigo_usuario is not None:
            try:
                insert_auditoria(conn, codigo_usuario=int(codigo_usuario), movimiento_cod=Mov.MATRICULA_ELIMINADA)
            except Exception:
                pass

        return True
    finally:
        conn.close()


def listar_matriculas_por_curso(db_user: str, db_pass: str, curso_cod: int, codigo_usuario: int | None = None):
    conn = connect(db_user, db_pass)
    try:
        return list_matriculas_por_curso(conn, curso_cod=int(curso_cod))
    finally:
        conn.close()


def reporte_estudiantes_por_curso(*, db_user: str, db_pass: str, curso_cod: int, codigo_usuario: int):
    """
    Reporte: estudiantes matriculados por curso.
    Devuelve lista de tuplas: (Periodo, Carnet, Estudiante, Estado)
    """
    conn = connect(db_user, db_pass)
    try:
        data = reporte_estudiantes_por_curso_repo(conn, curso_cod=int(curso_cod))

        # Auditoría (opcional, no revienta si falla)
        try:
            insert_auditoria(
                conn,
                codigo_usuario=int(codigo_usuario),
                movimiento_cod=Mov.REPORTE_ESTUDIANTES_POR_CURSO,
            )
        except Exception:
            pass

        return data
    finally:
        conn.close()

from app.repositories.matriculas.matriculas_repo import fetch_estudiantes_elegibles_para_curso
# (agregalo en el bloque de imports donde están los otros fetch/list)

def get_estudiantes_elegibles(db_user: str, db_pass: str, curso_cod: int, periodo: int, codigo_usuario: int | None = None) -> list:
    conn = connect(db_user, db_pass)
    try:
        return fetch_estudiantes_elegibles_para_curso(conn, curso_cod=int(curso_cod), periodo=int(periodo))
    finally:
        conn.close()        