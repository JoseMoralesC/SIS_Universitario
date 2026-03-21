from __future__ import annotations

from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.becas_repo import (
    exists_nombre_beca,
    exists_id_beca,
    is_beca_in_use,
)


def validar_beca_data(
    *,
    id_beca: int | None = None,
    nombre_beca: str,
    porcentaje_descuento: int,
    estado_codigo: int = 1,
) -> dict:
    if id_beca is not None:
        try:
            id_beca = int(id_beca)
        except Exception:
            raise ValidationError("El ID de la beca debe ser numérico.")
        if id_beca <= 0:
            raise ValidationError("El ID de la beca debe ser mayor a 0.")

    nombre_beca = (nombre_beca or "").strip()

    try:
        porcentaje_descuento = int(porcentaje_descuento)
    except Exception:
        raise ValidationError("El porcentaje de descuento debe ser numérico.")

    try:
        estado_codigo = int(estado_codigo)
    except Exception:
        raise ValidationError("El estado es inválido.")

    if not nombre_beca:
        raise ValidationError("El nombre de la beca es requerido.")
    if len(nombre_beca) > 50:
        raise ValidationError("Nombre de beca demasiado largo (máximo 50).")
    if porcentaje_descuento < 0 or porcentaje_descuento > 100:
        raise ValidationError("El porcentaje debe estar entre 0 y 100.")

    return {
        "id_beca": id_beca,
        "nombre_beca": nombre_beca,
        "porcentaje_descuento": porcentaje_descuento,
        "estado_codigo": estado_codigo,
    }


def validar_beca_unicidad(
    conn,
    *,
    id_beca: int | None = None,
    nombre_beca: str,
    exclude_id: int | None = None,
) -> None:
    # Compatibilidad con llamadas viejas y nuevas
    exclude = exclude_id if exclude_id is not None else id_beca
    if exists_nombre_beca(conn, nombre_beca, exclude_id=exclude):
        raise ValidationError("Ya existe una beca con ese nombre.")


def validar_beca_existente(conn, *, id_beca: int) -> None:
    if not exists_id_beca(conn, int(id_beca)):
        raise ValidationError("La beca indicada no existe.")


def validar_beca_puede_eliminarse(conn, *, id_beca: int) -> None:
    if is_beca_in_use(conn, int(id_beca)):
        raise ValidationError("No se puede eliminar: la beca está asignada a estudiantes (tabla Becados).")