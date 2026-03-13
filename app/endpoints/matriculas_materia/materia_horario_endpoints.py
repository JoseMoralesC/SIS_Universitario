from __future__ import annotations

from app.core.db import connect
from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria
from app.services.matriculas_materia.materia_horario_service import MateriaHorarioService


# =========================================================
# Helpers internos
# =========================================================
def _to_int(value, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} inválido.")


def _registrar_auditoria(
    conn,
    codigo_usuario: int | None,
    movimiento_cod: int,
) -> None:
    if codigo_usuario is None:
        return

    try:
        insert_auditoria(
            conn,
            codigo_usuario=int(codigo_usuario),
            movimiento_cod=int(movimiento_cod),
        )
    except Exception:
        # No romper el flujo principal por un fallo aislado de auditoría
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
def fetch_dias_semana_materia_horario(
    db_user: str,
    db_pass: str,
) -> list[tuple[str, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        return service.obtener_dias_semana()
    finally:
        conn.close()


def fetch_jornadas_materia_horario(
    db_user: str,
    db_pass: str,
) -> list[tuple[int, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        return service.obtener_jornadas()
    finally:
        conn.close()


def fetch_materias_activas_materia_horario(
    db_user: str,
    db_pass: str,
) -> list[tuple[int, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        return service.obtener_materias_activas()
    finally:
        conn.close()


def fetch_cursos_activos_materia_horario(
    db_user: str,
    db_pass: str,
) -> list[tuple[int, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        return service.obtener_cursos_activos()
    finally:
        conn.close()


def fetch_materias_por_curso_con_docente_materia_horario(
    db_user: str,
    db_pass: str,
    curso_cod: int,
) -> list[tuple[int, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        curso_cod = _to_int(curso_cod, "Curso")
        return service.obtener_materias_por_curso_con_docente(curso_cod)
    finally:
        conn.close()


# =========================================================
# Grid / Listados
# =========================================================
def list_materia_horario_rows(
    db_user: str,
    db_pass: str,
) -> list[tuple]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        return service.listar_horarios()
    finally:
        conn.close()


# =========================================================
# Commands
# =========================================================
def assign_materia_horario(
    *,
    db_user: str,
    db_pass: str,
    materia_cod: int,
    dia_cod: str,
    jornada_id: int,
    estado_codigo: int = 1,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)

        materia_cod = _to_int(materia_cod, "Materia")
        jornada_id = _to_int(jornada_id, "Jornada")
        estado_codigo = _to_int(estado_codigo, "Estado")
        dia_cod = str(dia_cod or "").strip().upper()

        msg = service.crear_horario_materia(
            materia_cod=materia_cod,
            dia_cod=dia_cod,
            jornada_id=jornada_id,
            estado_codigo=estado_codigo,
        )

        mov = _resolver_movimiento("MATERIA_HORARIO_CREADO")
        if mov > 0:
            _registrar_auditoria(conn, codigo_usuario, mov)

        return msg
    finally:
        conn.close()


def update_estado_materia_horario_endpoint(
    *,
    db_user: str,
    db_pass: str,
    horario_id: int,
    nuevo_estado: int,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)

        horario_id = _to_int(horario_id, "Horario")
        nuevo_estado = _to_int(nuevo_estado, "Estado")

        msg = service.cambiar_estado_horario(
            horario_id=horario_id,
            nuevo_estado=nuevo_estado,
        )

        mov = _resolver_movimiento("MATERIA_HORARIO_ACTUALIZADO")
        if mov > 0:
            _registrar_auditoria(conn, codigo_usuario, mov)

        return msg
    finally:
        conn.close()


def delete_materia_horario_endpoint(
    *,
    db_user: str,
    db_pass: str,
    horario_id: int,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)

        horario_id = _to_int(horario_id, "Horario")

        msg = service.desactivar_horario(
            horario_id=horario_id,
        )

        mov = _resolver_movimiento("MATERIA_HORARIO_ELIMINADO")
        if mov > 0:
            _registrar_auditoria(conn, codigo_usuario, mov)

        return msg
    finally:
        conn.close()