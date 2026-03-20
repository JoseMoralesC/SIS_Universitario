from __future__ import annotations

import pyodbc

from app.core.exceptions import ValidationError
from app.repositories.matriculas_materia.facturacion_matricula_repo import (
    build_referencia_pago,
    get_forma_pago_desc_by_cod,
)


# =========================================================
# Validaciones base
# =========================================================
def validar_forma_pago(forma_pago_cod: int) -> int:
    try:
        forma_pago_cod = int(forma_pago_cod)
    except Exception:
        raise ValidationError("Forma de pago inválida.")

    if forma_pago_cod <= 0:
        raise ValidationError("Forma de pago inválida.")

    return forma_pago_cod


# =========================================================
# Generación de referencia (preview UI)
# =========================================================
def generar_referencia_preview(
    conn: pyodbc.Connection,
    *,
    forma_pago_cod: int,
) -> str:
    """
    Genera la referencia de pago para mostrar en pantalla (preview).
    IMPORTANTE:
    - Esta referencia es informativa
    - La definitiva se vuelve a generar en el repository al guardar
    """

    forma_pago_cod = validar_forma_pago(forma_pago_cod)

    try:
        # Validamos que exista la forma de pago
        _ = get_forma_pago_desc_by_cod(conn, forma_pago_cod)

        referencia = build_referencia_pago(conn, forma_pago_cod)

        return referencia

    except Exception as e:
        raise ValidationError(str(e))


# =========================================================
# Validación antes de facturar
# =========================================================
def validar_facturacion_request(
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    forma_pago_cod: int,
) -> dict:
    """
    Validaciones básicas antes de enviar a facturación
    """

    if not carnet or not str(carnet).strip():
        raise ValidationError("El carnet es requerido.")

    try:
        curso_cod = int(curso_cod)
    except Exception:
        raise ValidationError("Curso inválido.")

    if curso_cod <= 0:
        raise ValidationError("Curso inválido.")

    try:
        periodo_id = int(periodo_id)
    except Exception:
        raise ValidationError("Período inválido.")

    if periodo_id <= 0:
        raise ValidationError("Período inválido.")

    forma_pago_cod = validar_forma_pago(forma_pago_cod)

    return {
        "carnet": str(carnet).strip(),
        "curso_cod": curso_cod,
        "periodo_id": periodo_id,
        "forma_pago_cod": forma_pago_cod,
    }