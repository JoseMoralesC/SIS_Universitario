# app/endpoints/matriculas_materia/materia_horario_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.core.auditoria import (
    Mov,
    Tab,
    compose_named_row_id,
)
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


def _build_row_id(
    materia_cod: int,
    dia: str,
    hora_inicio: str,
) -> str:
    """
    Identificador compuesto para horarios de materia.
    """
    return compose_named_row_id(
        Materia_Cod=int(materia_cod),
        Dia=(dia or "").strip(),
        Hora_Inicio=(hora_inicio or "").strip(),
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
            id_tabla=Tab.MATERIA_HORARIO,
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


def _open_conn(db_user: str, db_pass: str):
    return connect(db_user, db_pass)


# =========================================================
# Lookups
# =========================================================
def fetch_materias_activos_horario(
    db_user: str,
    db_pass: str,
):
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        return service.obtener_materias_activas()
    finally:
        conn.close()


def fetch_dias_semana():
    """
    Puede ser fijo o venir del service.
    """
    return [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
    ]


# =========================================================
# Grid / Listados
# =========================================================
def list_materia_horario_rows(
    db_user: str,
    db_pass: str,
):
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        return service.listar_horarios()
    finally:
        conn.close()


def list_materia_horario_por_materia(
    db_user: str,
    db_pass: str,
    materia_cod: int,
):
    conn = _open_conn(db_user, db_pass)
    try:
        service = MateriaHorarioService(conn)
        materia_cod = _to_int(materia_cod, "Materia")
        return service.listar_horarios_por_materia(materia_cod)
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
    dia: str,
    hora_inicio: str,
    hora_fin: str,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)

    try:
        service = MateriaHorarioService(conn)

        materia_cod = _to_int(materia_cod, "Materia")

        msg = service.asignar_horario(
            materia_cod=materia_cod,
            dia=dia,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )

        mov = _resolver_movimiento("MATERIA_HORARIO_CREADO")
        if mov > 0:
            _registrar_auditoria(
                conn,
                codigo_usuario,
                mov,
                id_row_tabla=_build_row_id(
                    materia_cod,
                    dia,
                    hora_inicio,
                ),
            )

        return msg

    finally:
        conn.close()


def update_materia_horario(
    *,
    db_user: str,
    db_pass: str,
    materia_cod: int,
    dia: str,
    hora_inicio: str,
    hora_fin: str,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)

    try:
        service = MateriaHorarioService(conn)

        materia_cod = _to_int(materia_cod, "Materia")

        msg = service.actualizar_horario(
            materia_cod=materia_cod,
            dia=dia,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )

        mov = _resolver_movimiento("MATERIA_HORARIO_ACTUALIZADO")
        if mov > 0:
            _registrar_auditoria(
                conn,
                codigo_usuario,
                mov,
                id_row_tabla=_build_row_id(
                    materia_cod,
                    dia,
                    hora_inicio,
                ),
            )

        return msg

    finally:
        conn.close()


def delete_materia_horario(
    *,
    db_user: str,
    db_pass: str,
    materia_cod: int,
    dia: str,
    hora_inicio: str,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)

    try:
        service = MateriaHorarioService(conn)

        materia_cod = _to_int(materia_cod, "Materia")

        msg = service.eliminar_horario(
            materia_cod=materia_cod,
            dia=dia,
            hora_inicio=hora_inicio,
        )

        mov = _resolver_movimiento("MATERIA_HORARIO_ELIMINADO")
        if mov > 0:
            _registrar_auditoria(
                conn,
                codigo_usuario,
                mov,
                id_row_tabla=_build_row_id(
                    materia_cod,
                    dia,
                    hora_inicio,
                ),
            )

        return msg

    finally:
        conn.close()