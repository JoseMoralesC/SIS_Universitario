from __future__ import annotations

from datetime import date, datetime

from app.core.exceptions import ValidationError
from app.repositories.mantenimiento.periodos_repo import (
    exists_periodo_anio_numero,
    exists_periodo_codigo,
    exists_periodo_id,
)


ROMANOS = {
    1: "I",
    2: "II",
    3: "III",
}


def _to_int(value, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} inválido.")


def _to_date(value, field_name: str) -> str:
    if isinstance(value, date):
        return value.isoformat()

    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date().isoformat()
    except Exception:
        raise ValidationError(f"{field_name} inválida. Use formato YYYY-MM-DD.")


def _validar_numero_periodo(numero_periodo: int) -> int:
    numero_periodo = _to_int(numero_periodo, "Número de período")
    if numero_periodo not in (1, 2, 3):
        raise ValidationError("El número de período debe ser 1, 2 o 3.")
    return numero_periodo


def _generar_codigo_periodo(anio: int, numero_periodo: int) -> str:
    romano = ROMANOS.get(numero_periodo)
    if not romano:
        raise ValidationError("Número de período inválido.")
    return f"{anio}-{romano}"


def _validar_fechas(fecha_inicio: str, fecha_fin: str) -> None:
    fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    if fi > ff:
        raise ValidationError("La fecha de inicio no puede ser mayor que la fecha final.")


def validar_periodo_data(
    *,
    periodo_codigo: str | None = None,
    anio: int,
    numero_periodo: int,
    fecha_inicio: str,
    fecha_fin: str,
    estado_codigo: int,
) -> dict:
    anio = _to_int(anio, "Año")
    numero_periodo = _validar_numero_periodo(numero_periodo)
    fecha_inicio = _to_date(fecha_inicio, "Fecha inicio")
    fecha_fin = _to_date(fecha_fin, "Fecha fin")
    estado_codigo = _to_int(estado_codigo, "Estado")

    _validar_fechas(fecha_inicio, fecha_fin)

    codigo_generado = _generar_codigo_periodo(anio, numero_periodo)

    return {
        "periodo_codigo": codigo_generado if not periodo_codigo else str(periodo_codigo).strip(),
        "anio": anio,
        "numero_periodo": numero_periodo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "estado_codigo": estado_codigo,
    }


def validar_periodo_unicidad(
    conn,
    *,
    periodo_id: int | None,
    periodo_codigo: str,
    anio: int,
    numero_periodo: int,
) -> None:
    if periodo_id is None:
        if exists_periodo_anio_numero(
            conn,
            anio=anio,
            numero_periodo=numero_periodo,
        ):
            raise ValidationError("Ya existe un período con ese año y número.")

        if exists_periodo_codigo(
            conn,
            periodo_codigo=periodo_codigo,
        ):
            raise ValidationError("Ya existe un período con ese código.")
    else:
        if not exists_periodo_id(conn, int(periodo_id)):
            raise ValidationError("El período indicado no existe.")

        if exists_periodo_anio_numero(
            conn,
            anio=anio,
            numero_periodo=numero_periodo,
            exclude_periodo_id=int(periodo_id),
        ):
            raise ValidationError("Ya existe otro período con ese año y número.")

        if exists_periodo_codigo(
            conn,
            periodo_codigo=periodo_codigo,
            exclude_periodo_id=int(periodo_id),
        ):
            raise ValidationError("Ya existe otro período con ese código.")