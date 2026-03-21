from __future__ import annotations

import datetime as _dt

from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.becados_repo import (
    exists_carnet,
    exists_id_becado,
    exists_becado_activo_by_carnet,
)
from app.repositories.mantenimiento.becas_repo import exists_id_beca


def _parse_date(value: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValidationError("La fecha de aplicación es requerida (YYYY-MM-DD).")

    if "/" in v:
        parts = v.split("/")
        if len(parts) == 3:
            dd, mm, yyyy = parts
            try:
                d = _dt.date(int(yyyy), int(mm), int(dd))
            except Exception:
                raise ValidationError("Fecha inválida. Use YYYY-MM-DD o DD/MM/YYYY.")
            return d.isoformat()

    try:
        d = _dt.date.fromisoformat(v)
        return d.isoformat()
    except Exception:
        raise ValidationError("Fecha inválida. Use formato YYYY-MM-DD.")


def validar_becado_create_data(
    *,
    id_becado: int | None = None,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
) -> dict:
    if id_becado is not None:
        try:
            id_becado = int(id_becado)
        except Exception:
            raise ValidationError("El ID del registro debe ser numérico.")

        if id_becado <= 0:
            raise ValidationError("El ID del registro debe ser mayor a 0.")

    carnet = (carnet or "").strip()

    try:
        id_beca = int(id_beca)
    except Exception:
        raise ValidationError("El tipo de beca debe ser numérico.")

    if not carnet:
        raise ValidationError("Debe seleccionar un estudiante.")
    if len(carnet) > 15:
        raise ValidationError("Carnet demasiado largo (máximo 15).")
    if id_beca <= 0:
        raise ValidationError("Debe seleccionar una beca válida.")

    fecha_norm = _parse_date(fecha_aplicacion)

    return {
        "id_becado": id_becado,
        "carnet": carnet,
        "id_beca": id_beca,
        "fecha_aplicacion": fecha_norm,
    }


def validar_becado_update_data(
    *,
    id_becado: int,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
) -> dict:
    return validar_becado_create_data(
        id_becado=id_becado,
        carnet=carnet,
        id_beca=id_beca,
        fecha_aplicacion=fecha_aplicacion,
    )


def validar_becado_refs(conn, *, carnet: str, id_beca: int) -> None:
    if not exists_carnet(conn, carnet):
        raise ValidationError("El estudiante (carnet) no existe.")
    if not exists_id_beca(conn, int(id_beca)):
        raise ValidationError("La beca indicada no existe.")


def validar_becado_unicidad_activa(
    conn,
    *,
    carnet: str,
    exclude_id: int | None = None,
) -> None:
    if exists_becado_activo_by_carnet(conn, carnet, exclude_id=exclude_id):
        raise ValidationError("El estudiante ya tiene una beca activa.")


def validar_becado_existente(conn, *, id_becado: int) -> None:
    if not exists_id_becado(conn, int(id_becado)):
        raise ValidationError("El registro de beca no existe.")


# =========================================================
# COMPATIBILIDAD CON VERSIONES VIEJAS DEL ENDPOINT
# =========================================================

def validar_becado_data(
    *,
    id_becado: int | None = None,
    carnet: str,
    id_beca: int,
    fecha_aplicacion: str,
) -> dict:
    return validar_becado_create_data(
        id_becado=id_becado,
        carnet=carnet,
        id_beca=id_beca,
        fecha_aplicacion=fecha_aplicacion,
    )


def validar_becado_unicidad(
    conn,
    *,
    id_becado: int | None = None,
    carnet: str,
    id_beca: int,
) -> None:
    validar_becado_refs(conn, carnet=carnet, id_beca=id_beca)
    validar_becado_unicidad_activa(conn, carnet=carnet, exclude_id=id_becado)