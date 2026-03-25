# app/endpoints/matriculas/matriculas_endpoints.py
from __future__ import annotations

from app.core.db import connect_app
from app.core.auditoria import Mov, Tab, compose_named_row_id
from app.repositories.auditoria_repo import insert_auditoria
from app.services.security.permission_service import require_matriculas_action

from app.repositories.matriculas.matriculas_repo import (
    fetch_estudiantes_activos,
    fetch_cursos_activos,
    fetch_docentes_activos,
    fetch_docentes_por_curso,
    fetch_estudiantes_elegibles_para_curso,
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


def _build_row_id(carnet: str, curso_cod: int, periodo: int) -> str:
    return compose_named_row_id(
        Carnet=(carnet or "").strip(),
        Curso_Cod=int(curso_cod),
        Periodo=int(periodo),
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
            id_tabla=Tab.MATRICULA_CURSO,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        pass


def get_lookups(db_user: str, db_pass: str, codigo_usuario: int | None = None) -> dict:
    require_matriculas_action("consultar")

    conn = connect_app()
    try:
        return {
            "estados": fetch_estados(conn),
            "estudiantes": fetch_estudiantes_activos(conn),
            "cursos": fetch_cursos_activos(conn),
            "docentes": fetch_docentes_activos(conn),
        }
    finally:
        conn.close()


def get_docentes_por_curso(db_user: str, db_pass: str, curso_cod: int, codigo_usuario: int | None = None):
    require_matriculas_action("consultar")

    conn = connect_app()
    try:
        return fetch_docentes_por_curso(conn, int(curso_cod))
    finally:
        conn.close()


def listar_matriculas(db_user: str, db_pass: str, codigo_usuario: int | None = None):
    require_matriculas_action("consultar")

    conn = connect_app()
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
    require_matriculas_action("crear")

    conn = connect_app()
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

        row_id = _build_row_id(
            carnet=data["carnet"],
            curso_cod=data["curso_cod"],
            periodo=data["periodo"],
        )

        _registrar_auditoria(conn, codigo_usuario, Mov.MATRICULA_CREADA, row_id)

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
    require_matriculas_action("actualizar")

    conn = connect_app()
    try:
        carnet_limpio = (carnet or "").strip()

        nuevo_estado_cod = validar_cambio_estado(conn, nuevo_estado=nuevo_estado)

        update_estado_matricula(
            conn,
            carnet=carnet_limpio,
            curso_cod=int(curso_cod),
            periodo=int(periodo),
            nuevo_estado_codigo=int(nuevo_estado_cod),
        )

        row_id = _build_row_id(carnet_limpio, curso_cod, periodo)

        _registrar_auditoria(conn, codigo_usuario, Mov.MATRICULA_ESTADO_CAMBIADO, row_id)

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
    require_matriculas_action("eliminar")

    conn = connect_app()
    try:
        carnet_limpio = (carnet or "").strip()

        delete_matricula(
            conn,
            carnet=carnet_limpio,
            curso_cod=int(curso_cod),
            periodo=int(periodo),
        )

        row_id = _build_row_id(carnet_limpio, curso_cod, periodo)

        _registrar_auditoria(conn, codigo_usuario, Mov.MATRICULA_ELIMINADA, row_id)

        return True
    finally:
        conn.close()


def listar_matriculas_por_curso(db_user: str, db_pass: str, curso_cod: int, codigo_usuario: int | None = None):
    require_matriculas_action("consultar")

    conn = connect_app()
    try:
        return list_matriculas_por_curso(conn, curso_cod=int(curso_cod))
    finally:
        conn.close()


def reporte_estudiantes_por_curso(
    *,
    db_user: str,
    db_pass: str,
    curso_cod: int,
    codigo_usuario: int,
):
    require_matriculas_action("report")

    conn = connect_app()
    try:
        data = reporte_estudiantes_por_curso_repo(conn, curso_cod=int(curso_cod))

        row_id = compose_named_row_id(Curso_Cod=curso_cod)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.REPORTE_ESTUDIANTES_POR_CURSO,
            row_id,
        )

        return data
    finally:
        conn.close()


def get_estudiantes_elegibles(
    db_user: str,
    db_pass: str,
    curso_cod: int,
    periodo: int,
    codigo_usuario: int | None = None,
):
    require_matriculas_action("consultar")

    conn = connect_app()
    try:
        return fetch_estudiantes_elegibles_para_curso(
            conn,
            curso_cod=int(curso_cod),
            periodo=int(periodo),
        )
    finally:
        conn.close()