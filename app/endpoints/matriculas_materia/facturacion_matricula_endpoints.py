from __future__ import annotations

from app.core.db import connect
from app.core.auditoria import (
    Mov,
    Tab,
    compose_named_row_id,
)
from app.repositories.auditoria_repo import insert_auditoria
from app.services.security.permission_service import require_matricula_materias_action
from app.services.matriculas_materia.facturacion_matricula_service import (
    generar_referencia_preview,
    validar_facturacion_request,
)
from app.repositories.matriculas_materia.facturacion_matricula_repo import (
    build_resumen_facturacion,
    fetch_formas_pago,
    insert_facturacion_matricula,
)


# =========================================================
# Helpers internos
# =========================================================
def _build_row_id_fallback(
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    referencia_pago: str | None = None,
) -> str:
    """
    Fallback contextual para auditoría mientras el repository
    no devuelva explícitamente los Factura_Id insertados.
    """
    return compose_named_row_id(
        Carnet=(carnet or "").strip(),
        Curso_Cod=int(curso_cod),
        Periodo_Id=int(periodo_id),
        Referencia_Pago=(referencia_pago or "").strip() or None,
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
            id_tabla=Tab.MATRICULA_MATERIA_FACTURACION,
            id_row_tabla=id_row_tabla,
        )
    except Exception:
        # No romper flujo principal por fallo aislado de auditoría
        pass


# =========================================================
# Catálogos
# =========================================================
def get_formas_pago(
    db_user: str,
    db_pass: str,
    codigo_usuario: int | None = None,
) -> list[tuple[int, str]]:
    require_matricula_materias_action("consultar", resource_key="facturacion_matricula")

    conn = connect(db_user, db_pass)
    try:
        return fetch_formas_pago(conn)
    finally:
        conn.close()


# =========================================================
# Preview referencia automática
# =========================================================
def get_referencia_pago_preview(
    db_user: str,
    db_pass: str,
    *,
    forma_pago_cod: int,
    codigo_usuario: int | None = None,
) -> str:
    require_matricula_materias_action("consultar", resource_key="facturacion_matricula")

    conn = connect(db_user, db_pass)
    try:
        return generar_referencia_preview(
            conn,
            forma_pago_cod=int(forma_pago_cod),
        )
    finally:
        conn.close()


# =========================================================
# Resumen antes de facturar
# =========================================================
def get_resumen_facturacion(
    db_user: str,
    db_pass: str,
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    anio: int,
    forma_pago_cod: int,
    codigo_usuario: int | None = None,
) -> dict:
    """
    Retorna el resumen de materias pendientes, beca y totales.
    """
    require_matricula_materias_action("consultar", resource_key="facturacion_matricula")

    data = validar_facturacion_request(
        carnet=carnet,
        curso_cod=curso_cod,
        periodo_id=periodo_id,
        forma_pago_cod=forma_pago_cod,
    )

    conn = connect(db_user, db_pass)
    try:
        return build_resumen_facturacion(
            conn,
            carnet=data["carnet"],
            curso_cod=data["curso_cod"],
            periodo_id=data["periodo_id"],
            anio=int(anio),
        )
    finally:
        conn.close()


# =========================================================
# Confirmar facturación / pago
# =========================================================
def save_facturacion_matricula(
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
) -> dict:
    """
    Procesa la facturación final.
    La referencia manual ya no gobierna el guardado;
    el repository genera la definitiva automáticamente.
    """
    require_matricula_materias_action("crear", resource_key="facturacion_matricula")

    data = validar_facturacion_request(
        carnet=carnet,
        curso_cod=curso_cod,
        periodo_id=periodo_id,
        forma_pago_cod=forma_pago_cod,
    )

    conn = connect(db_user, db_pass)
    try:
        result = insert_facturacion_matricula(
            conn,
            carnet=data["carnet"],
            curso_cod=data["curso_cod"],
            periodo_id=data["periodo_id"],
            anio=int(anio),
            forma_pago_cod=data["forma_pago_cod"],
            referencia_pago=referencia_pago,
            observacion=observacion,
            codigo_usuario=int(codigo_usuario),
        )

        if codigo_usuario is not None and isinstance(result, dict):
            insertados = int(result.get("insertados", 0) or 0)

            if insertados > 0:
                row_id = _build_row_id_fallback(
                    carnet=data["carnet"],
                    curso_cod=data["curso_cod"],
                    periodo_id=data["periodo_id"],
                    referencia_pago=result.get("referencia_pago"),
                )

                _registrar_auditoria(
                    conn,
                    codigo_usuario,
                    Mov.FACTURA_MATRICULA_CREADA,
                    id_row_tabla=row_id,
                )

        return result
    finally:
        conn.close()