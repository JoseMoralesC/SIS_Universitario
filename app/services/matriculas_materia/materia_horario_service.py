from __future__ import annotations

import pyodbc

from app.repositories.matriculas_materia.materia_horario_repo import (
    exists_horario,
    exists_materia,
    fetch_cursos_activos,
    fetch_dias_semana,
    fetch_jornadas,
    fetch_materias_activas,
    fetch_materias_por_curso_con_docente,
    get_estado_codigo_by_desc,
    insert_materia_horario,
    list_materia_horarios,
    update_estado_materia_horario,
)


class MateriaHorarioService:
    """
    Servicio de negocio para la Tab:
    Asignar jornadas/horarios a materias.
    """

    DIAS_VALIDOS = {"L", "K", "M", "J", "V", "S"}
    JORNADAS_VALIDAS = {1, 2, 3}

    def __init__(self, conn: pyodbc.Connection):
        self.conn = conn

    # =====================================================
    # Helpers internos
    # =====================================================
    def _normalizar_int(self, valor, nombre: str) -> int:
        try:
            return int(valor)
        except (TypeError, ValueError):
            raise ValueError(f"{nombre} inválido.")

    def _normalizar_dia(self, dia_cod: str) -> str:
        dia = str(dia_cod or "").strip().upper()
        if dia not in self.DIAS_VALIDOS:
            raise ValueError("Día inválido.")
        return dia

    def _asegurar_materia_valida(self, materia_cod: int) -> None:
        if not exists_materia(self.conn, materia_cod):
            raise ValueError("La materia indicada no existe.")

        materias_activas = {codigo for codigo, _ in fetch_materias_activas(self.conn)}
        if materia_cod not in materias_activas:
            raise ValueError("La materia indicada no está activa.")

    def _asegurar_jornada_valida(self, jornada_id: int) -> None:
        if jornada_id not in self.JORNADAS_VALIDAS:
            raise ValueError("Jornada inválida.")

    def _validar_regla_sabado(self, dia_cod: str, jornada_id: int) -> None:
        if dia_cod == "S" and jornada_id == 3:
            raise ValueError(
                "El sábado únicamente permite las jornadas 1 y 2."
            )

    def _asegurar_curso_valido(self, curso_cod: int) -> int:
        curso_cod = self._normalizar_int(curso_cod, "Curso")
        cursos_activos = {codigo for codigo, _ in fetch_cursos_activos(self.conn)}
        if curso_cod not in cursos_activos:
            raise ValueError("El curso indicado no existe o no está activo.")
        return curso_cod

    # =====================================================
    # Lookups
    # =====================================================
    def obtener_dias_semana(self) -> list[tuple[str, str]]:
        return fetch_dias_semana(self.conn)

    def obtener_jornadas(self) -> list[tuple[int, str]]:
        return fetch_jornadas(self.conn)

    def obtener_materias_activas(self) -> list[tuple[int, str]]:
        return fetch_materias_activas(self.conn)

    def obtener_cursos_activos(self) -> list[tuple[int, str]]:
        return fetch_cursos_activos(self.conn)

    def obtener_materias_por_curso_con_docente(self, curso_cod: int) -> list[tuple[int, str]]:
        curso_cod = self._asegurar_curso_valido(curso_cod)
        return fetch_materias_por_curso_con_docente(self.conn, curso_cod)

    # =====================================================
    # Grid
    # =====================================================
    def listar_horarios(self) -> list[tuple]:
        return list_materia_horarios(self.conn)

    # =====================================================
    # Commands
    # =====================================================
    def crear_horario_materia(
        self,
        *,
        materia_cod: int,
        dia_cod: str,
        jornada_id: int,
        estado_codigo: int = 1,
    ) -> str:
        materia_cod = self._normalizar_int(materia_cod, "Materia")
        jornada_id = self._normalizar_int(jornada_id, "Jornada")
        estado_codigo = self._normalizar_int(estado_codigo, "Estado")
        dia_cod = self._normalizar_dia(dia_cod)

        self._asegurar_materia_valida(materia_cod)
        self._asegurar_jornada_valida(jornada_id)
        self._validar_regla_sabado(dia_cod, jornada_id)

        if exists_horario(
            self.conn,
            materia_cod=materia_cod,
            dia_cod=dia_cod,
            jornada_id=jornada_id,
        ):
            raise ValueError("Ese horario ya existe para la materia seleccionada.")

        insert_materia_horario(
            self.conn,
            materia_cod=materia_cod,
            dia_cod=dia_cod,
            jornada_id=jornada_id,
            estado_codigo=estado_codigo,
        )
        return "Horario asignado correctamente."

    def cambiar_estado_horario(
        self,
        *,
        horario_id: int,
        nuevo_estado: int,
    ) -> str:
        horario_id = self._normalizar_int(horario_id, "Horario")
        nuevo_estado = self._normalizar_int(nuevo_estado, "Estado")

        update_estado_materia_horario(
            self.conn,
            horario_id=horario_id,
            nuevo_estado=nuevo_estado,
        )
        return "Estado del horario actualizado correctamente."

    def desactivar_horario(
        self,
        *,
        horario_id: int,
    ) -> str:
        horario_id = self._normalizar_int(horario_id, "Horario")
        inactivo = get_estado_codigo_by_desc(self.conn, "Inactivo")

        update_estado_materia_horario(
            self.conn,
            horario_id=horario_id,
            nuevo_estado=inactivo,
        )
        return "Horario desactivado correctamente."