from __future__ import annotations

from typing import List, Dict, Any

from app.services.matriculas_materia.facturacion_matricula_service import (
    listar_formas_pago,
    obtener_resumen_facturacion,
    procesar_pago_matricula,
)


# =========================================================
# Helpers
# =========================================================
def _forma_pago_to_dict(row: tuple) -> Dict[str, Any]:
    forma_pago_cod, descripcion = row

    return {
        "forma_pago_cod": int(forma_pago_cod),
        "descripcion": str(descripcion),
        "label": f"{descripcion}",
    }


# =========================================================
# Catálogo formas de pago
# =========================================================
def obtener_formas_pago(
    db_user: str,
    db_pass: str,
) -> List[Dict[str, Any]]:

    rows = listar_formas_pago(
        db_user,
        db_pass,
    )

    return [_forma_pago_to_dict(r) for r in rows]


# =========================================================
# Resumen de facturación
# =========================================================
def obtener_resumen_facturacion_estudiante(
    db_user: str,
    db_pass: str,
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    anio: int,
) -> Dict[str, Any]:

    data = obtener_resumen_facturacion(
        db_user,
        db_pass,
        carnet=carnet,
        curso_cod=curso_cod,
        periodo_id=periodo_id,
        anio=anio,
    )

    beca = data["beca"]

    materias = []
    for m in data["materias"]:
        materias.append(
            {
                "matricula_materia_id": m["matricula_materia_id"],
                "materia_cod": m["materia_cod"],
                "materia": m["materia"],
                "docente": m["docente"],
                "precio_base": float(m["precio_base"]),
                "porcentaje_beca": int(m["porcentaje_beca"]),
                "monto_descuento": float(m["monto_descuento"]),
                "monto_final": float(m["monto_final"]),
            }
        )

    return {
        "beca": {
            "tiene_beca": bool(beca["tiene_beca"]),
            "id_beca": beca["id_beca"],
            "nombre_beca": beca["nombre_beca"],
            "porcentaje_beca": int(beca["porcentaje_beca"]),
        },
        "materias": materias,
        "subtotal": float(data["subtotal"]),
        "descuento": float(data["descuento"]),
        "total": float(data["total"]),
        "cantidad_materias": int(data["cantidad_materias"]),
    }


# =========================================================
# Procesar pago
# =========================================================
def completar_pago_matricula(
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
) -> Dict[str, Any]:

    result = procesar_pago_matricula(
        db_user,
        db_pass,
        carnet=carnet,
        curso_cod=curso_cod,
        periodo_id=periodo_id,
        anio=anio,
        forma_pago_cod=forma_pago_cod,
        referencia_pago=referencia_pago,
        observacion=observacion,
        codigo_usuario=codigo_usuario,
    )

    return {
        "materias_facturadas": int(result["insertados"]),
        "subtotal": float(result["subtotal"]),
        "descuento": float(result["descuento"]),
        "total": float(result["total"]),
    }