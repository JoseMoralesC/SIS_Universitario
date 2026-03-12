from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.error_handler import handle_exception, show_warning
from app.endpoints.matriculas_materia import (
    consulta_matricula_estudiante_endpoints as consulta_ep,
)


class ConsultaMatriculaEstudianteTab(ttk.Frame):
    """
    Tab de consulta de matrícula por estudiante.

    Flujo:
    1) Seleccionar período
    2) Seleccionar curso
    3) Seleccionar estudiante
    4) Consultar matrícula
    """

    def __init__(self, parent, db_user: str, db_pass: str):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass

        self.periodos = []
        self.cursos = []
        self.estudiantes = []

        self._loaded = False

        self._build_ui()

    # =========================================================
    # Lifecycle
    # =========================================================
    def ensure_loaded(self):
        if self._loaded:
            return

        try:
            self._load_periodos()
        finally:
            self._loaded = True

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self):

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # -----------------------------------------------------
        # Frame filtros (arriba)
        # -----------------------------------------------------

        filtros = ttk.LabelFrame(self, text="Consulta de Matrícula por Estudiante")
        filtros.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        for i in range(6):
            filtros.columnconfigure(i, weight=1)

        # PERIODO
        ttk.Label(filtros, text="Período").grid(row=0, column=0, sticky="w")

        self.cbo_periodo = ttk.Combobox(filtros, state="readonly")
        self.cbo_periodo.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.cbo_periodo.bind("<<ComboboxSelected>>", self._on_periodo)

        # CURSO
        ttk.Label(filtros, text="Curso").grid(row=0, column=1, sticky="w")

        self.cbo_curso = ttk.Combobox(filtros, state="readonly")
        self.cbo_curso.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.cbo_curso.bind("<<ComboboxSelected>>", self._on_curso)

        # ESTUDIANTE
        ttk.Label(filtros, text="Estudiante").grid(row=0, column=2, sticky="w")

        self.cbo_estudiante = ttk.Combobox(filtros, state="readonly")
        self.cbo_estudiante.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # BOTONES
        self.btn_consultar = ttk.Button(
            filtros,
            text="Consultar",
            command=self._consultar,
        )
        self.btn_consultar.grid(row=1, column=3, padx=5, pady=5)

        self.btn_limpiar = ttk.Button(
            filtros,
            text="Limpiar",
            command=self._limpiar,
        )
        self.btn_limpiar.grid(row=1, column=4, padx=5, pady=5)

        self.btn_completar = ttk.Button(
            filtros,
            text="Completar Matrícula",
            command=self._completar_matricula,
        )
        self.btn_completar.grid(row=1, column=5, padx=5, pady=5)

        # -----------------------------------------------------
        # GRID (abajo)
        # -----------------------------------------------------

        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        columnas = (
            "materia",
            "dias",
            "jornada",
            "horario",
            "docente",
            "estado",
            "fecha",
        )

        self.grid = ttk.Treeview(
            grid_frame,
            columns=columnas,
            show="headings",
        )

        self.grid.heading("materia", text="Materia")
        self.grid.heading("dias", text="Días")
        self.grid.heading("jornada", text="Jornada")
        self.grid.heading("horario", text="Horario")
        self.grid.heading("docente", text="Docente")
        self.grid.heading("estado", text="Estado")
        self.grid.heading("fecha", text="Fecha Matrícula")

        self.grid.column("materia", width=250, anchor="w")
        self.grid.column("dias", width=120, anchor="center")
        self.grid.column("jornada", width=120, anchor="center")
        self.grid.column("horario", width=250, anchor="w")
        self.grid.column("docente", width=220, anchor="w")
        self.grid.column("estado", width=100, anchor="center")
        self.grid.column("fecha", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(
            grid_frame,
            orient="vertical",
            command=self.grid.yview,
        )

        self.grid.configure(yscrollcommand=scrollbar.set)

        self.grid.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    # =========================================================
    # CARGA COMBOBOX
    # =========================================================
    def _load_periodos(self):

        try:
            self.periodos = consulta_ep.obtener_periodos_con_matricula(
                self.db_user,
                self.db_pass,
            )

            self.cbo_periodo["values"] = [p["label"] for p in self.periodos]

        except Exception as e:
            handle_exception(self, e, context="Cargar períodos")

    def _on_periodo(self, event=None):

        try:
            idx = self.cbo_periodo.current()

            if idx < 0:
                return

            periodo = self.periodos[idx]

            self.cursos = consulta_ep.obtener_cursos_por_periodo(
                self.db_user,
                self.db_pass,
                periodo_id=periodo["periodo_id"],
                anio=periodo["anio"],
            )

            self.cbo_curso.set("")
            self.cbo_curso["values"] = [c["label"] for c in self.cursos]

            self.estudiantes = []
            self.cbo_estudiante.set("")
            self.cbo_estudiante["values"] = []

            self.grid.delete(*self.grid.get_children())

        except Exception as e:
            handle_exception(self, e, context="Cargar cursos por período")

    def _on_curso(self, event=None):

        try:
            idx_periodo = self.cbo_periodo.current()
            idx_curso = self.cbo_curso.current()

            if idx_periodo < 0 or idx_curso < 0:
                return

            periodo = self.periodos[idx_periodo]
            curso = self.cursos[idx_curso]

            self.estudiantes = consulta_ep.obtener_estudiantes_por_periodo_curso(
                self.db_user,
                self.db_pass,
                periodo_id=periodo["periodo_id"],
                anio=periodo["anio"],
                curso_cod=curso["curso_cod"],
            )

            self.cbo_estudiante.set("")
            self.cbo_estudiante["values"] = [e["label"] for e in self.estudiantes]

            self.grid.delete(*self.grid.get_children())

        except Exception as e:
            handle_exception(self, e, context="Cargar estudiantes por curso")

    # =========================================================
    # CONSULTA
    # =========================================================
    def _consultar(self):

        try:
            idx_periodo = self.cbo_periodo.current()
            idx_curso = self.cbo_curso.current()
            idx_estudiante = self.cbo_estudiante.current()

            if idx_periodo < 0 or idx_curso < 0 or idx_estudiante < 0:
                show_warning(
                    self,
                    "Consulta de matrícula",
                    "Debe seleccionar período, curso y estudiante.",
                )
                return

            periodo = self.periodos[idx_periodo]
            curso = self.cursos[idx_curso]
            estudiante = self.estudiantes[idx_estudiante]

            rows = consulta_ep.consultar_matricula_estudiante(
                self.db_user,
                self.db_pass,
                carnet=estudiante["carnet"],
                periodo_id=periodo["periodo_id"],
                anio=periodo["anio"],
                curso_cod=curso["curso_cod"],
            )

            self.grid.delete(*self.grid.get_children())

            for r in rows:
                self.grid.insert(
                    "",
                    "end",
                    values=(
                        r["materia"],
                        r["dias"],
                        r["jornada"],
                        r["horario_detalle"],
                        r["docente"],
                        r["estado"],
                        r["fecha_matricula"],
                    ),
                )

        except Exception as e:
            handle_exception(self, e, context="Consultar matrícula del estudiante")

    # =========================================================
    # LIMPIAR
    # =========================================================
    def _limpiar(self):

        self.cbo_periodo.set("")
        self.cbo_curso.set("")
        self.cbo_estudiante.set("")

        self.cursos = []
        self.estudiantes = []

        self.cbo_curso["values"] = []
        self.cbo_estudiante["values"] = []

        self.grid.delete(*self.grid.get_children())

    # =========================================================
    # COMPLETAR MATRÍCULA
    # =========================================================
    def _completar_matricula(self):
        """
        Aquí luego conectaremos el módulo de facturación.
        """
        show_warning(
            self,
            "Completar matrícula",
            "Módulo de facturación aún no implementado.",
        )