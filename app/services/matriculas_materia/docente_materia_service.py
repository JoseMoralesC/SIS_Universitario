# app/services/matriculas_materia/docente_materia_service.py
from __future__ import annotations

import pyodbc

from app.repositories.matriculas_materia.docente_materia_repo import (
    docente_activo,
    docente_materia_activa,
    docente_y_materia_mismo_curso,
    exists_docente,
    exists_docente_materia,
    exists_materia,
    fetch_cursos_activos,
    fetch_docentes_disponibles_para_materia,
    fetch_docentes_por_curso,
    fetch_estados,
    fetch_materias_disponibles_para_docente,
    fetch_materias_por_curso,
    get_estado_codigo_by_desc,
    list_docente_materia,
    list_docente_materia_activos,
    list_docente_materia_por_curso,
    list_docentes_de_materia,
    list_materias_de_docente,
    materia_activa,
    reactivar_docente_materia,
    insert_docente_materia,
    update_estado_docente_materia,
)


class DocenteMateriaService:
    """
    Servicio de negocio para la Tab:
    Asignar docente a una o más materias.
    """

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

    def _asegurar_docente_valido(self, docente_cod: int) -> None:
        if not exists_docente(self.conn, docente_cod):
            raise ValueError("El docente indicado no existe.")

        if not docente_activo(self.conn, docente_cod):
            raise ValueError("El docente indicado no está activo.")

    def _asegurar_materia_valida(self, materia_cod: int) -> None:
        if not exists_materia(self.conn, materia_cod):
            raise ValueError("La materia indicada no existe.")

        if not materia_activa(self.conn, materia_cod):
            raise ValueError("La materia indicada no está activa.")

    def _asegurar_mismo_curso(self, docente_cod: int, materia_cod: int) -> None:
        if not docente_y_materia_mismo_curso(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        ):
            raise ValueError(
                "El docente no pertenece al curso/carrera asociado a la materia seleccionada."
            )

    # =====================================================
    # Lookups
    # =====================================================
    def obtener_estados(self) -> list[tuple[int, str]]:
        return fetch_estados(self.conn)

    def obtener_cursos_activos(self) -> list[tuple[int, str]]:
        return fetch_cursos_activos(self.conn)

    def obtener_docentes_por_curso(self, curso_cod: int) -> list[tuple[int, str]]:
        curso_cod = self._normalizar_int(curso_cod, "Curso")
        return fetch_docentes_por_curso(self.conn, curso_cod=curso_cod)

    def obtener_materias_por_curso(self, curso_cod: int) -> list[tuple[int, str]]:
        curso_cod = self._normalizar_int(curso_cod, "Curso")
        return fetch_materias_por_curso(self.conn, curso_cod=curso_cod)

    def obtener_materias_disponibles_para_docente(
        self,
        docente_cod: int,
        curso_cod: int,
    ) -> list[tuple[int, str]]:
        docente_cod = self._normalizar_int(docente_cod, "Docente")
        curso_cod = self._normalizar_int(curso_cod, "Curso")

        self._asegurar_docente_valido(docente_cod)

        return fetch_materias_disponibles_para_docente(
            self.conn,
            docente_cod=docente_cod,
            curso_cod=curso_cod,
        )

    def obtener_docentes_disponibles_para_materia(
        self,
        materia_cod: int,
    ) -> list[tuple[int, str]]:
        materia_cod = self._normalizar_int(materia_cod, "Materia")
        self._asegurar_materia_valida(materia_cod)

        return fetch_docentes_disponibles_para_materia(
            self.conn,
            materia_cod=materia_cod,
        )

    # =====================================================
    # Grid / Listados
    # =====================================================
    def listar_asignaciones(self) -> list[tuple]:
        return list_docente_materia(self.conn)

    def listar_asignaciones_activas(self) -> list[tuple]:
        return list_docente_materia_activos(self.conn)

    def listar_asignaciones_por_curso(self, curso_cod: int) -> list[tuple]:
        curso_cod = self._normalizar_int(curso_cod, "Curso")
        return list_docente_materia_por_curso(self.conn, curso_cod=curso_cod)

    def listar_materias_de_docente(
        self,
        docente_cod: int,
        solo_activas: bool = True,
    ) -> list[tuple]:
        docente_cod = self._normalizar_int(docente_cod, "Docente")
        self._asegurar_docente_valido(docente_cod)

        return list_materias_de_docente(
            self.conn,
            docente_cod=docente_cod,
            solo_activas=bool(solo_activas),
        )

    def listar_docentes_de_materia(
        self,
        materia_cod: int,
        solo_activas: bool = True,
    ) -> list[tuple]:
        materia_cod = self._normalizar_int(materia_cod, "Materia")
        self._asegurar_materia_valida(materia_cod)

        return list_docentes_de_materia(
            self.conn,
            materia_cod=materia_cod,
            solo_activas=bool(solo_activas),
        )

    # =====================================================
    # Commands
    # =====================================================
    def asignar_docente_a_materia(
        self,
        docente_cod: int,
        materia_cod: int,
        estado_codigo: int = 1,
    ) -> str:
        docente_cod = self._normalizar_int(docente_cod, "Docente")
        materia_cod = self._normalizar_int(materia_cod, "Materia")
        estado_codigo = self._normalizar_int(estado_codigo, "Estado")

        self._asegurar_docente_valido(docente_cod)
        self._asegurar_materia_valida(materia_cod)
        self._asegurar_mismo_curso(docente_cod, materia_cod)

        if docente_materia_activa(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        ):
            raise ValueError("Esa asignación ya se encuentra activa.")

        if exists_docente_materia(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        ):
            reactivar_docente_materia(
                self.conn,
                docente_cod=docente_cod,
                materia_cod=materia_cod,
            )
            return "Asignación reactivada correctamente."

        insert_docente_materia(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
            estado_codigo=estado_codigo,
        )
        return "Asignación creada correctamente."

    def cambiar_estado_asignacion(
        self,
        docente_cod: int,
        materia_cod: int,
        nuevo_estado_codigo: int,
    ) -> str:
        docente_cod = self._normalizar_int(docente_cod, "Docente")
        materia_cod = self._normalizar_int(materia_cod, "Materia")
        nuevo_estado_codigo = self._normalizar_int(nuevo_estado_codigo, "Estado")

        if not exists_docente_materia(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        ):
            raise ValueError("La asignación indicada no existe.")

        update_estado_docente_materia(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
            nuevo_estado_codigo=nuevo_estado_codigo,
        )
        return "Estado de la asignación actualizado correctamente."

    def desactivar_asignacion(
        self,
        docente_cod: int,
        materia_cod: int,
    ) -> str:
        docente_cod = self._normalizar_int(docente_cod, "Docente")
        materia_cod = self._normalizar_int(materia_cod, "Materia")

        if not exists_docente_materia(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        ):
            raise ValueError("La asignación indicada no existe.")

        inactivo = get_estado_codigo_by_desc(self.conn, "Inactivo")

        update_estado_docente_materia(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
            nuevo_estado_codigo=inactivo,
        )
        return "Asignación desactivada correctamente."