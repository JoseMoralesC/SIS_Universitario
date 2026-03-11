# app/endpoints/matriculas_materia/matricula_materia_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria
from app.services.matriculas_materia.matricula_materia_service import (
    MatriculaMateriaService,
)


# =========================================================
# Helpers internos
# =========================================================
def _to_int(value, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} inválido.")


def _registrar_auditoria(conn, codigo_usuario: int, movimiento_cod: int) -> None:
    try:
        insert_auditoria(conn, int(codigo_usuario), int(movimiento_cod))
    except Exception:
        # No romper flujo principal por fallo aislado de auditoría
        pass


def _resolver_movimiento(default_value: int | str | None) -> int:
    if isinstance(default_value, int):
        return default_value

    if isinstance(default_value, str) and hasattr(Mov, default_value):
        return int(getattr(Mov, default_value))

    return 0


def _open_conn(db_user: str, db_pass: str):
    return connect(db_user, db_pass)


# =========================================================
# Lookups
# =========================================================
def fetch_estudiantes_activos_matricula_materia(
    db_user: str,
    db_pass: str,
) -> list[tuple[str, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.obtener_estudiantes_activos()
    finally:
        conn.close()


def fetch_periodos_activos_matricula_materia(
    db_user: str,
    db_pass: str,
) -> list:
    """
    Compatibilidad temporal:

    Puede devolver cualquiera de estas formas, según lo que implemente el service:
    - [2026, 2027]
    - [("2026-I", 2026), ("2026-II", 2026)]
    - [(1, "2026-I", 2026), (2, "2026-II", 2026)]

    El tab ya está preparado para interpretar cualquiera de esas variantes.
    """
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.obtener_periodos_activos()
    finally:
        conn.close()


def fetch_estados_matricula_materia(
    db_user: str,
    db_pass: str,
) -> list[tuple[int, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.obtener_estados()
    finally:
        conn.close()


def fetch_matricula_curso_estudiante(
    db_user: str,
    db_pass: str,
    carnet: str,
    periodo: int,
) -> tuple | None:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.obtener_matricula_curso_estudiante(
            carnet=carnet,
            periodo=periodo,
        )
    finally:
        conn.close()


def fetch_materias_disponibles_estudiante(
    db_user: str,
    db_pass: str,
    carnet: str,
    periodo: int,
) -> list[tuple]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.obtener_materias_disponibles_estudiante(
            carnet=carnet,
            periodo=periodo,
        )
    finally:
        conn.close()


def fetch_docentes_disponibles_para_materia(
    db_user: str,
    db_pass: str,
    materia_cod: int,
) -> list[tuple[int, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        materia_cod = _to_int(materia_cod, "Materia")
        return service.obtener_docentes_disponibles_para_materia(
            materia_cod=materia_cod,
        )
    finally:
        conn.close()


def fetch_beca_estudiante(
    db_user: str,
    db_pass: str,
    carnet: str,
) -> tuple | None:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.obtener_beca_estudiante(carnet)
    finally:
        conn.close()


def fetch_restricciones_beca(
    db_user: str,
    db_pass: str,
    carnet: str,
) -> dict:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.obtener_restricciones_beca(carnet)
    finally:
        conn.close()


# =========================================================
# Grid / Listados
# =========================================================
def list_matricula_materia_rows(
    db_user: str,
    db_pass: str,
) -> list[tuple]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        return service.listar_matriculas()
    finally:
        conn.close()


def list_matricula_materia_rows_por_estudiante_periodo(
    db_user: str,
    db_pass: str,
    carnet: str,
    periodo: int,
) -> list[tuple]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MatriculaMateriaService(conn)
        periodo = _to_int(periodo, "Periodo")
        return service.listar_matriculas_por_estudiante_periodo(
            carnet=carnet,
            periodo=periodo,
        )
    finally:
        conn.close()


# =========================================================
# Commands
# =========================================================
def assign_matricula_materia(
    *,
    db_user: str,
    db_pass: str,
    carnet: str,
    materia_cod: int,
    periodo: int,
    docente_cod: int,
    estado_codigo: int = 1,
    codigo_usuario: int | None = None,
) -> str:
    """
    Crear matrícula por materia.
    Compatibilidad temporal: 'periodo' sigue llegando como AÑO lógico.
    """
    conn = _open_conn(db_user, db_pass)

    try:
        service = MatriculaMateriaService(conn)

        materia_cod = _to_int(materia_cod, "Materia")
        periodo = _to_int(periodo, "Periodo")
        docente_cod = _to_int(docente_cod, "Docente")
        estado_codigo = _to_int(estado_codigo, "Estado")

        msg = service.matricular_estudiante_en_materia(
            carnet=carnet,
            materia_cod=materia_cod,
            periodo=periodo,
            docente_cod=docente_cod,
            estado_codigo=estado_codigo,
        )

        if codigo_usuario is not None:
            mov = _resolver_movimiento("MATRICULA_MATERIA_CREAR")

            if mov > 0:
                _registrar_auditoria(
                    conn,
                    int(codigo_usuario),
                    mov,
                )

        return msg

    finally:
        conn.close()


def update_estado_matricula_materia_endpoint(
    *,
    db_user: str,
    db_pass: str,
    matricula_materia_id: int,
    nuevo_estado_codigo: int,
    codigo_usuario: int | None = None,
) -> str:
    """
    Actualizar estado de matrícula por materia.
    """
    conn = _open_conn(db_user, db_pass)

    try:
        service = MatriculaMateriaService(conn)

        matricula_materia_id = _to_int(
            matricula_materia_id,
            "Matrícula",
        )

        nuevo_estado_codigo = _to_int(
            nuevo_estado_codigo,
            "Estado",
        )

        msg = service.cambiar_estado_matricula(
            matricula_materia_id=matricula_materia_id,
            nuevo_estado_codigo=nuevo_estado_codigo,
        )

        if codigo_usuario is not None:
            mov = _resolver_movimiento("MATRICULA_MATERIA_ESTADO")

            if mov > 0:
                _registrar_auditoria(
                    conn,
                    int(codigo_usuario),
                    mov,
                )

        return msg

    finally:
        conn.close()


def delete_matricula_materia_endpoint(
    *,
    db_user: str,
    db_pass: str,
    matricula_materia_id: int,
    codigo_usuario: int | None = None,
) -> str:
    """
    Borrado lógico de matrícula por materia.
    """
    conn = _open_conn(db_user, db_pass)

    try:
        service = MatriculaMateriaService(conn)

        matricula_materia_id = _to_int(
            matricula_materia_id,
            "Matrícula",
        )

        msg = service.desactivar_matricula(
            matricula_materia_id=matricula_materia_id,
        )

        if codigo_usuario is not None:
            mov = _resolver_movimiento("MATRICULA_MATERIA_ELIMINAR")

            if mov > 0:
                _registrar_auditoria(
                    conn,
                    int(codigo_usuario),
                    mov,
                )

        return msg

    finally:
        conn.close()


# =========================================================
# Utilitarios
# =========================================================
def validar_rango_actual_beca(
    db_user: str,
    db_pass: str,
    carnet: str,
    periodo: int,
) -> dict:
    """
    Utilitario para UI.
    Permite saber si el estudiante ya cumple el mínimo
    requerido por la beca y cuántas materias puede agregar.

    Compatibilidad temporal: 'periodo' sigue llegando como AÑO lógico.
    """
    conn = _open_conn(db_user, db_pass)

    try:
        service = MatriculaMateriaService(conn)

        periodo = _to_int(periodo, "Periodo")

        return service.validar_rango_actual_beca(
            carnet=carnet,
            periodo=periodo,
        )

    finally:
        conn.close()