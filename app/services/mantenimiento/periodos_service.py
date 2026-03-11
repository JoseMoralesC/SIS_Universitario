# app/services/mantenimientos/periodos_service.py
from __future__ import annotations

from datetime import date, datetime
import pyodbc

from app.repositories.mantenimiento.periodos_repo import (
    exists_periodo_anio_numero,
    exists_periodo_codigo,
    exists_periodo_id,
    fetch_estados_generales,
    insert_periodo,
    list_periodos,
    soft_delete_periodo,
    update_periodo,
)


class PeriodosService:
    ROMANOS = {
        1: "I",
        2: "II",
        3: "III",
    }

    def __init__(self, conn: pyodbc.Connection):
        self.conn = conn

    # =====================================================
    # Helpers internos
    # =====================================================
    def _to_int(self, value, field_name: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} inválido.")

    def _to_date(self, value, field_name: str) -> date:
        if isinstance(value, date):
            return value
        try:
            return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
        except Exception:
            raise ValueError(f"{field_name} inválida. Use formato YYYY-MM-DD.")

    def _validar_numero_periodo(self, numero_periodo: int) -> int:
        numero_periodo = self._to_int(numero_periodo, "Número de período")
        if numero_periodo not in (1, 2, 3):
            raise ValueError("El número de período debe ser 1, 2 o 3.")
        return numero_periodo

    def _generar_codigo_periodo(self, anio: int, numero_periodo: int) -> str:
        romano = self.ROMANOS.get(numero_periodo)
        if not romano:
            raise ValueError("Número de período inválido.")
        return f"{anio}-{romano}"

    def _validar_fechas(self, fecha_inicio: date, fecha_fin: date) -> None:
        if fecha_inicio > fecha_fin:
            raise ValueError("La fecha de inicio no puede ser mayor que la fecha final.")

    # =====================================================
    # Lookups
    # =====================================================
    def obtener_estados(self) -> list[tuple[int, str]]:
        return fetch_estados_generales(self.conn)

    # =====================================================
    # Grid
    # =====================================================
    def listar_periodos(self) -> list[tuple]:
        return list_periodos(self.conn)

    # =====================================================
    # Commands
    # =====================================================
    def crear_periodo(
        self,
        *,
        anio: int,
        numero_periodo: int,
        fecha_inicio,
        fecha_fin,
        estado_codigo: int,
    ) -> str:
        anio = self._to_int(anio, "Año")
        numero_periodo = self._validar_numero_periodo(numero_periodo)
        fecha_inicio = self._to_date(fecha_inicio, "Fecha inicio")
        fecha_fin = self._to_date(fecha_fin, "Fecha fin")
        estado_codigo = self._to_int(estado_codigo, "Estado")

        self._validar_fechas(fecha_inicio, fecha_fin)

        periodo_codigo = self._generar_codigo_periodo(anio, numero_periodo)

        if exists_periodo_anio_numero(
            self.conn,
            anio=anio,
            numero_periodo=numero_periodo,
        ):
            raise ValueError("Ya existe un período con ese año y número.")

        if exists_periodo_codigo(
            self.conn,
            periodo_codigo=periodo_codigo,
        ):
            raise ValueError("Ya existe un período con ese código.")

        insert_periodo(
            self.conn,
            periodo_codigo=periodo_codigo,
            anio=anio,
            numero_periodo=numero_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado_codigo=estado_codigo,
        )

        return "Período creado correctamente."

    def actualizar_periodo(
        self,
        *,
        periodo_id: int,
        anio: int,
        numero_periodo: int,
        fecha_inicio,
        fecha_fin,
        estado_codigo: int,
    ) -> str:
        periodo_id = self._to_int(periodo_id, "Período")
        anio = self._to_int(anio, "Año")
        numero_periodo = self._validar_numero_periodo(numero_periodo)
        fecha_inicio = self._to_date(fecha_inicio, "Fecha inicio")
        fecha_fin = self._to_date(fecha_fin, "Fecha fin")
        estado_codigo = self._to_int(estado_codigo, "Estado")

        self._validar_fechas(fecha_inicio, fecha_fin)

        if not exists_periodo_id(self.conn, periodo_id):
            raise ValueError("El período indicado no existe.")

        periodo_codigo = self._generar_codigo_periodo(anio, numero_periodo)

        if exists_periodo_anio_numero(
            self.conn,
            anio=anio,
            numero_periodo=numero_periodo,
            exclude_periodo_id=periodo_id,
        ):
            raise ValueError("Ya existe otro período con ese año y número.")

        if exists_periodo_codigo(
            self.conn,
            periodo_codigo=periodo_codigo,
            exclude_periodo_id=periodo_id,
        ):
            raise ValueError("Ya existe otro período con ese código.")

        update_periodo(
            self.conn,
            periodo_id=periodo_id,
            periodo_codigo=periodo_codigo,
            anio=anio,
            numero_periodo=numero_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado_codigo=estado_codigo,
        )

        return "Período actualizado correctamente."

    def eliminar_periodo(self, *, periodo_id: int) -> str:
        periodo_id = self._to_int(periodo_id, "Período")

        if not exists_periodo_id(self.conn, periodo_id):
            raise ValueError("El período indicado no existe.")

        soft_delete_periodo(self.conn, periodo_id=periodo_id)
        return "Período desactivado correctamente."