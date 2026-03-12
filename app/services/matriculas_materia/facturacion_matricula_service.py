from __future__ import annotations

from app.core.db import connect

from app.repositories.matriculas_materia.facturacion_matricula_repo import (
    fetch_formas_pago,
    build_resumen_facturacion,
    insert_facturacion_matricula,
)


# =========================================================
# Catálogos
# =========================================================
def listar_formas_pago(
    db_user: str,
    db_pass: str,
):
    """
    Retorna catálogo de formas de pago.
    """
    conn = connect(db_user, db_pass)

    try:
        return fetch_formas_pago(conn)
    finally:
        conn.close()


# =========================================================
# Resumen de facturación
# =========================================================
def obtener_resumen_facturacion(
    db_user: str,
    db_pass: str,
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    anio: int,
):
    """
    Calcula:
    - materias pendientes de facturar
    - beca vigente
    - subtotal
    - descuento
    - total
    """
    conn = connect(db_user, db_pass)

    try:
        return build_resumen_facturacion(
            conn,
            carnet=carnet,
            curso_cod=curso_cod,
            periodo_id=periodo_id,
            anio=anio,
        )
    finally:
        conn.close()


# =========================================================
# Procesar pago
# =========================================================
def procesar_pago_matricula(
    db_user: str,
    db_pass: str,
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    anio: int,
    forma_pago_cod: int,
    referencia_pago: str | None,
    observacion: str | None,
    codigo_usuario: int,
):
    """
    Inserta la facturación de materias pendientes.
    """
    conn = connect(db_user, db_pass)

    try:
        return insert_facturacion_matricula(
            conn,
            carnet=carnet,
            curso_cod=curso_cod,
            periodo_id=periodo_id,
            anio=anio,
            forma_pago_cod=forma_pago_cod,
            referencia_pago=referencia_pago,
            observacion=observacion,
            codigo_usuario=codigo_usuario,
        )
    finally:
        conn.close()