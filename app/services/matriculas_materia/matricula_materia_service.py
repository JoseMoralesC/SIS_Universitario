from __future__ import annotations

import pyodbc

from app.repositories.matriculas_materia.matricula_materia_repo import (
    count_materias_activas_estudiante_periodo,
    docente_activo,
    docente_asignado_a_materia,
    estudiante_activo,
    estudiante_matriculado_en_curso_de_materia,
    exists_docente,
    exists_estudiante,
    exists_materia,
    exists_matricula_materia,
    fetch_beca_estudiante,
    fetch_docentes_disponibles_para_materia,
    fetch_estados,
    fetch_estudiantes_activos,
    fetch_materias_disponibles_estudiante,
    fetch_matricula_curso_activa_estudiante,
    fetch_periodos_matricula_curso_activos,
    get_estado_codigo_by_desc,
    insert_matricula_materia,
    list_matricula_materia,
    list_matricula_materia_por_estudiante_periodo,
    materia_activa,
    matricula_materia_activa,
    reactivar_matricula_materia,
    update_estado_matricula_materia,
)


class MatriculaMateriaService:
    """
    Servicio de negocio para la Tab:
    Matrícula del estudiante por materia.
    """

    MAX_MATERIAS = 6

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

    def _normalizar_carnet(self, carnet: str) -> str:
        carnet_norm = str(carnet or "").strip()
        if not carnet_norm:
            raise ValueError("Carnet inválido.")
        return carnet_norm

    def _asegurar_estudiante_valido(self, carnet: str) -> None:
        if not exists_estudiante(self.conn, carnet):
            raise ValueError("El estudiante indicado no existe.")

        if not estudiante_activo(self.conn, carnet):
            raise ValueError("El estudiante indicado no está activo.")

    def _asegurar_materia_valida(self, materia_cod: int) -> None:
        if not exists_materia(self.conn, materia_cod):
            raise ValueError("La materia indicada no existe.")

        if not materia_activa(self.conn, materia_cod):
            raise ValueError("La materia indicada no está activa.")

    def _asegurar_docente_valido(self, docente_cod: int) -> None:
        if not exists_docente(self.conn, docente_cod):
            raise ValueError("El docente indicado no existe.")

        if not docente_activo(self.conn, docente_cod):
            raise ValueError("El docente indicado no está activo.")

    def _asegurar_estudiante_en_curso_correcto(
        self,
        *,
        carnet: str,
        materia_cod: int,
        periodo: int,
    ) -> None:
        if not estudiante_matriculado_en_curso_de_materia(
            self.conn,
            carnet=carnet,
            materia_cod=materia_cod,
            periodo=periodo,
        ):
            raise ValueError(
                "El estudiante no está matriculado en el curso/carrera correspondiente a la materia seleccionada en ese período."
            )

    def _asegurar_docente_asignado_a_materia(
        self,
        *,
        docente_cod: int,
        materia_cod: int,
    ) -> None:
        if not docente_asignado_a_materia(
            self.conn,
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        ):
            raise ValueError(
                "El docente seleccionado no está asignado a la materia indicada."
            )

    def _obtener_beca_normalizada(self, carnet: str) -> str | None:
        beca = fetch_beca_estudiante(self.conn, carnet=carnet)
        if not beca:
            return None

        _, nombre_beca, _ = beca
        nombre = str(nombre_beca or "").strip().lower()

        # Normalización tolerante
        if "excelencia" in nombre:
            return "excelencia"
        if "cultural" in nombre:
            return "cultural"
        if "deport" in nombre:
            return "deportiva"
        if "basica" in nombre or "básica" in nombre:
            return "basica"

        return nombre if nombre else None

    def _minimo_por_beca(self, carnet: str) -> int:
        beca = self._obtener_beca_normalizada(carnet)

        if beca == "excelencia":
            return 5
        if beca == "cultural":
            return 3
        if beca == "deportiva":
            return 2

        # Beca básica o sin beca:
        return 1

    def _validar_maximo_materias(
        self,
        *,
        carnet: str,
        periodo: int,
        es_reactivacion: bool = False,
    ) -> None:
        total_actual = count_materias_activas_estudiante_periodo(
            self.conn,
            carnet=carnet,
            periodo=periodo,
        )

        # Insert o reactivación agregan 1 activa al total
        total_final = total_actual if False else total_actual + 1

        if total_final > self.MAX_MATERIAS:
            raise ValueError(
                f"El estudiante no puede matricular más de {self.MAX_MATERIAS} materias en un mismo período."
            )

    # =====================================================
    # Lookups
    # =====================================================
    def obtener_estudiantes_activos(self) -> list[tuple[str, str]]:
        return fetch_estudiantes_activos(self.conn)

    def obtener_periodos_activos(self) -> list:
        """
        Compatibilidad temporal para transición de período:

        Puede devolver cualquiera de estas estructuras:
        - [2026, 2027]
        - [("2026-I", 2026), ("2026-II", 2026)]
        - [(1, "2026-I", 2026), (2, "2026-II", 2026)]

        El tab de UI ya sabe interpretar estas variantes.
        """
        rows = fetch_periodos_matricula_curso_activos(self.conn)

        normalized: list = []

        for r in rows:
            try:
                if isinstance(r, (tuple, list)):
                    if len(r) >= 3:
                        periodo_id = int(r[0])
                        periodo_codigo = str(r[1]).strip()
                        anio = int(r[2])
                        normalized.append((periodo_id, periodo_codigo, anio))
                    elif len(r) == 2:
                        a = r[0]
                        b = r[1]

                        if isinstance(a, str) and not str(a).isdigit():
                            normalized.append((str(a).strip(), int(b)))
                        elif isinstance(b, str) and not str(b).isdigit():
                            normalized.append((str(b).strip(), int(a)))
                        else:
                            normalized.append(int(a))
                    elif len(r) == 1:
                        normalized.append(int(r[0]))
                else:
                    normalized.append(int(r))
            except Exception:
                continue

        return normalized

    def obtener_estados(self) -> list[tuple[int, str]]:
        return fetch_estados(self.conn)

    def obtener_matricula_curso_estudiante(
        self,
        carnet: str,
        periodo: int,
    ) -> tuple | None:
        carnet = self._normalizar_carnet(carnet)
        periodo = self._normalizar_int(periodo, "Periodo")

        self._asegurar_estudiante_valido(carnet)

        return fetch_matricula_curso_activa_estudiante(
            self.conn,
            carnet=carnet,
            periodo=periodo,
        )

    def obtener_materias_disponibles_estudiante(
        self,
        carnet: str,
        periodo: int,
    ) -> list[tuple[int, str, int, str]]:
        carnet = self._normalizar_carnet(carnet)
        periodo = self._normalizar_int(periodo, "Periodo")

        self._asegurar_estudiante_valido(carnet)

        return fetch_materias_disponibles_estudiante(
            self.conn,
            carnet=carnet,
            periodo=periodo,
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

    def obtener_beca_estudiante(
        self,
        carnet: str,
    ) -> tuple | None:
        carnet = self._normalizar_carnet(carnet)
        self._asegurar_estudiante_valido(carnet)
        return fetch_beca_estudiante(self.conn, carnet=carnet)

    def obtener_restricciones_beca(
        self,
        carnet: str,
    ) -> dict:
        carnet = self._normalizar_carnet(carnet)
        self._asegurar_estudiante_valido(carnet)

        beca = self._obtener_beca_normalizada(carnet)
        minimo = self._minimo_por_beca(carnet)

        return {
            "beca": beca,
            "minimo_materias": minimo,
            "maximo_materias": self.MAX_MATERIAS,
        }

    # =====================================================
    # Grid / Listados
    # =====================================================
    def listar_matriculas(self) -> list[tuple]:
        return list_matricula_materia(self.conn)

    def listar_matriculas_por_estudiante_periodo(
        self,
        carnet: str,
        periodo: int,
    ) -> list[tuple]:
        carnet = self._normalizar_carnet(carnet)
        periodo = self._normalizar_int(periodo, "Periodo")

        self._asegurar_estudiante_valido(carnet)

        return list_matricula_materia_por_estudiante_periodo(
            self.conn,
            carnet=carnet,
            periodo=periodo,
        )

    # =====================================================
    # Commands
    # =====================================================
    def matricular_estudiante_en_materia(
        self,
        *,
        carnet: str,
        materia_cod: int,
        periodo: int,
        docente_cod: int,
        estado_codigo: int = 1,
    ) -> str:
        """
        Reglas:
        - estudiante debe existir y estar activo
        - materia debe existir y estar activa
        - docente debe existir y estar activo
        - docente debe estar asignado a la materia
        - estudiante debe estar matriculado al curso/carrera correcto en ese periodo
        - no duplicar activa
        - si existe inactiva, se reactiva
        - máximo general 6 materias
        """
        carnet = self._normalizar_carnet(carnet)
        materia_cod = self._normalizar_int(materia_cod, "Materia")
        periodo = self._normalizar_int(periodo, "Periodo")
        docente_cod = self._normalizar_int(docente_cod, "Docente")
        estado_codigo = self._normalizar_int(estado_codigo, "Estado")

        self._asegurar_estudiante_valido(carnet)
        self._asegurar_materia_valida(materia_cod)
        self._asegurar_docente_valido(docente_cod)
        self._asegurar_docente_asignado_a_materia(
            docente_cod=docente_cod,
            materia_cod=materia_cod,
        )
        self._asegurar_estudiante_en_curso_correcto(
            carnet=carnet,
            materia_cod=materia_cod,
            periodo=periodo,
        )

        if matricula_materia_activa(
            self.conn,
            carnet=carnet,
            materia_cod=materia_cod,
            periodo=periodo,
        ):
            raise ValueError(
                "El estudiante ya tiene activa esa materia en el período indicado."
            )

        # Validar máximo antes de insertar o reactivar
        self._validar_maximo_materias(
            carnet=carnet,
            periodo=periodo,
        )

        if exists_matricula_materia(
            self.conn,
            carnet=carnet,
            materia_cod=materia_cod,
            periodo=periodo,
        ):
            reactivar_matricula_materia(
                self.conn,
                carnet=carnet,
                materia_cod=materia_cod,
                periodo=periodo,
                docente_cod=docente_cod,
            )
            return "Matrícula por materia reactivada correctamente."

        insert_matricula_materia(
            self.conn,
            carnet=carnet,
            materia_cod=materia_cod,
            periodo=periodo,
            docente_cod=docente_cod,
            estado_codigo=estado_codigo,
        )
        return "Matrícula por materia creada correctamente."

    def cambiar_estado_matricula(
        self,
        *,
        matricula_materia_id: int,
        nuevo_estado_codigo: int,
    ) -> str:
        matricula_materia_id = self._normalizar_int(
            matricula_materia_id,
            "Matrícula por materia",
        )
        nuevo_estado_codigo = self._normalizar_int(
            nuevo_estado_codigo,
            "Estado",
        )

        update_estado_matricula_materia(
            self.conn,
            matricula_materia_id=matricula_materia_id,
            nuevo_estado_codigo=nuevo_estado_codigo,
        )
        return "Estado de la matrícula por materia actualizado correctamente."

    def desactivar_matricula(
        self,
        *,
        matricula_materia_id: int,
    ) -> str:
        matricula_materia_id = self._normalizar_int(
            matricula_materia_id,
            "Matrícula por materia",
        )
        inactivo = get_estado_codigo_by_desc(self.conn, "Inactivo")

        update_estado_matricula_materia(
            self.conn,
            matricula_materia_id=matricula_materia_id,
            nuevo_estado_codigo=inactivo,
        )
        return "Matrícula por materia desactivada correctamente."

    # =====================================================
    # Validaciones / utilitarios de negocio
    # =====================================================
    def validar_rango_actual_beca(
        self,
        *,
        carnet: str,
        periodo: int,
    ) -> dict:
        """
        Utilitario para UI o validaciones previas.
        No bloquea aún por mínimos, porque el mínimo debe validarse
        al cierre/proceso final del bloque de matrícula o al confirmar.
        """
        carnet = self._normalizar_carnet(carnet)
        periodo = self._normalizar_int(periodo, "Periodo")

        self._asegurar_estudiante_valido(carnet)

        total_actual = count_materias_activas_estudiante_periodo(
            self.conn,
            carnet=carnet,
            periodo=periodo,
        )
        restr = self.obtener_restricciones_beca(carnet)

        minimo = int(restr["minimo_materias"])
        maximo = int(restr["maximo_materias"])
        beca = restr["beca"]

        cumple_minimo_actual = total_actual >= minimo
        disponible_restante = max(0, maximo - total_actual)

        return {
            "beca": beca,
            "total_actual": total_actual,
            "minimo_requerido": minimo,
            "maximo_permitido": maximo,
            "cumple_minimo_actual": cumple_minimo_actual,
            "disponibles_restantes": disponible_restante,
        }