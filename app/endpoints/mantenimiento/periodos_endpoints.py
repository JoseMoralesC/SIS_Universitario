# app/endpoints/mantenimientos/periodos_endpoints.py
from __future__ import annotations

from app.core.db import connect
from app.core.auditoria import Mov
from app.repositories.auditoria_repo import insert_auditoria
from app.services.mantenimiento.periodos_service import PeriodosService


def _open_conn(db_user: str, db_pass: str):
    return connect(db_user, db_pass)


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


# =========================================================
# Lookups
# =========================================================
def fetch_estados_periodos(
    db_user: str,
    db_pass: str,
) -> list[tuple[int, str]]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = PeriodosService(conn)
        return service.obtener_estados()
    finally:
        conn.close()


# =========================================================
# Grid
# =========================================================
def list_periodos_rows(
    db_user: str,
    db_pass: str,
) -> list[tuple]:
    conn = _open_conn(db_user, db_pass)
    try:
        service = PeriodosService(conn)
        return service.listar_periodos()
    finally:
        conn.close()


# =========================================================
# Commands
# =========================================================
def create_periodo(
    *,
    db_user: str,
    db_pass: str,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)
    try:
        service = PeriodosService(conn)

        msg = service.crear_periodo(
            anio=anio,
            numero_periodo=numero_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado_codigo=estado_codigo,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_CREADO,
        )

        return msg
    finally:
        conn.close()


def update_periodo_endpoint(
    *,
    db_user: str,
    db_pass: str,
    periodo_id: int,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)
    try:
        service = PeriodosService(conn)

        msg = service.actualizar_periodo(
            periodo_id=periodo_id,
            anio=anio,
            numero_periodo=numero_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado_codigo=estado_codigo,
        )

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_ACTUALIZADO,
        )

        return msg
    finally:
        conn.close()


def delete_periodo_endpoint(
    *,
    db_user: str,
    db_pass: str,
    periodo_id: int,
    codigo_usuario: int | None = None,
) -> str:
    conn = _open_conn(db_user, db_pass)
    try:
        service = PeriodosService(conn)

        msg = service.eliminar_periodo(periodo_id=periodo_id)

        _registrar_auditoria(
            conn,
            codigo_usuario,
            Mov.PERIODO_ELIMINADO,
        )

        return msg
    finally:
        conn.close()