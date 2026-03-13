# app/ui/asistencias/asistencias_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import date

from app.endpoints.asistencias import asistencias_endpoints as ep
from app.core.error_handler import show_warning, show_info, handle_exception


class AsistenciasTab(ttk.Frame):

    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.estudiantes = []
        self.asistentes = []
        self.ausentes = []

        self._build_ui()
        self._load_periodos()

    # =====================================================
    # UI
    # =====================================================

    def _build_ui(self):

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Periodo").grid(row=0, column=0, padx=5)
        self.cb_periodo = ttk.Combobox(top, width=20, state="readonly")
        self.cb_periodo.grid(row=1, column=0, padx=5)
        self.cb_periodo.bind("<<ComboboxSelected>>", self._on_periodo)

        ttk.Label(top, text="Curso").grid(row=0, column=1, padx=5)
        self.cb_curso = ttk.Combobox(top, width=20, state="readonly")
        self.cb_curso.grid(row=1, column=1, padx=5)
        self.cb_curso.bind("<<ComboboxSelected>>", self._on_curso)

        ttk.Label(top, text="Materia").grid(row=0, column=2, padx=5)
        self.cb_materia = ttk.Combobox(top, width=20, state="readonly")
        self.cb_materia.grid(row=1, column=2, padx=5)
        self.cb_materia.bind("<<ComboboxSelected>>", self._on_materia)

        ttk.Label(top, text="Docente").grid(row=0, column=3, padx=5)
        self.cb_docente = ttk.Combobox(top, width=25, state="readonly")
        self.cb_docente.grid(row=1, column=3, padx=5)
        self.cb_docente.bind("<<ComboboxSelected>>", self._on_docente)

        ttk.Label(top, text="Fecha").grid(row=0, column=4, padx=5)
        self.fecha_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(top, textvariable=self.fecha_var, width=12).grid(row=1, column=4)

        ttk.Label(top, text="Día").grid(row=0, column=5, padx=5)
        self.lbl_dia = ttk.Label(top, text="-")
        self.lbl_dia.grid(row=1, column=5)

        # =====================================================
        # LISTAS
        # =====================================================

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # asistentes
        frame_a = ttk.LabelFrame(body, text="Asistentes")
        frame_a.pack(side="left", fill="both", expand=True, padx=5)

        self.cb_asistentes = ttk.Combobox(frame_a, state="readonly")
        self.cb_asistentes.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            frame_a,
            text="Agregar",
            command=self._add_asistente
        ).pack(pady=5)

        self.list_asistentes = tk.Listbox(frame_a, height=15)
        self.list_asistentes.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(
            frame_a,
            text="Quitar",
            command=self._remove_asistente
        ).pack(pady=5)

        # ausentes
        frame_f = ttk.LabelFrame(body, text="Ausentes")
        frame_f.pack(side="left", fill="both", expand=True, padx=5)

        self.cb_ausentes = ttk.Combobox(frame_f, state="readonly")
        self.cb_ausentes.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            frame_f,
            text="Agregar",
            command=self._add_ausente
        ).pack(pady=5)

        self.list_ausentes = tk.Listbox(frame_f, height=15)
        self.list_ausentes.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(
            frame_f,
            text="Quitar",
            command=self._remove_ausente
        ).pack(pady=5)

        # guardar
        ttk.Button(
            self,
            text="Guardar lista",
            command=self._guardar
        ).pack(pady=10)

    # =====================================================
    # LOADERS
    # =====================================================

    def _load_periodos(self):
        try:
            rows = ep.get_periodos_activos(self.db_user, self.db_pass)

            self.periodos = rows
            self.cb_periodo["values"] = [r["label"] for r in rows]

        except Exception as e:
            handle_exception(e)

    def _on_periodo(self, event=None):
        try:
            idx = self.cb_periodo.current()
            periodo_id = self.periodos[idx]["id"]

            rows = ep.get_cursos_por_periodo(
                self.db_user,
                self.db_pass,
                periodo_id,
            )

            self.cursos = rows
            self.cb_curso["values"] = [r["label"] for r in rows]

        except Exception as e:
            handle_exception(e)

    def _on_curso(self, event=None):

        try:
            periodo = self.periodos[self.cb_periodo.current()]["id"]
            curso = self.cursos[self.cb_curso.current()]["id"]

            rows = ep.get_materias_por_periodo_curso(
                self.db_user,
                self.db_pass,
                periodo,
                curso,
            )

            self.materias = rows
            self.cb_materia["values"] = [r["label"] for r in rows]

        except Exception as e:
            handle_exception(e)

    def _on_materia(self, event=None):

        try:
            periodo = self.periodos[self.cb_periodo.current()]["id"]
            curso = self.cursos[self.cb_curso.current()]["id"]
            materia = self.materias[self.cb_materia.current()]["id"]

            horario = ep.get_horario_principal_materia(
                self.db_user,
                self.db_pass,
                materia
            )

            if horario:
                self.lbl_dia.config(text=horario["dia_nombre"])

            rows = ep.get_docentes_por_periodo_curso_materia(
                self.db_user,
                self.db_pass,
                periodo,
                curso,
                materia,
            )

            self.docentes = rows
            self.cb_docente["values"] = [r["label"] for r in rows]

        except Exception as e:
            handle_exception(e)

    def _on_docente(self, event=None):

        try:
            periodo = self.periodos[self.cb_periodo.current()]["id"]
            curso = self.cursos[self.cb_curso.current()]["id"]
            materia = self.materias[self.cb_materia.current()]["id"]
            docente = self.docentes[self.cb_docente.current()]["id"]

            rows = ep.get_estudiantes_grupo(
                self.db_user,
                self.db_pass,
                periodo,
                curso,
                materia,
                docente
            )

            self.estudiantes = rows

            self._refresh_combos()

        except Exception as e:
            handle_exception(e)

    # =====================================================
    # LIST MANAGEMENT
    # =====================================================

    def _refresh_combos(self):

        disponibles = [
            e for e in self.estudiantes
            if e["carnet"] not in self.asistentes
            and e["carnet"] not in self.ausentes
        ]

        labels = [e["label"] for e in disponibles]

        self.cb_asistentes["values"] = labels
        self.cb_ausentes["values"] = labels

    def _add_asistente(self):

        idx = self.cb_asistentes.current()
        if idx < 0:
            return

        label = self.cb_asistentes.get()
        carnet = label.split("|")[0].strip()

        self.asistentes.append(carnet)
        self.list_asistentes.insert(tk.END, label)

        self._refresh_combos()

    def _add_ausente(self):

        idx = self.cb_ausentes.current()
        if idx < 0:
            return

        label = self.cb_ausentes.get()
        carnet = label.split("|")[0].strip()

        self.ausentes.append(carnet)
        self.list_ausentes.insert(tk.END, label)

        self._refresh_combos()

    def _remove_asistente(self):

        sel = self.list_asistentes.curselection()
        if not sel:
            return

        idx = sel[0]
        label = self.list_asistentes.get(idx)

        carnet = label.split("|")[0].strip()

        self.asistentes.remove(carnet)
        self.list_asistentes.delete(idx)

        self._refresh_combos()

    def _remove_ausente(self):

        sel = self.list_ausentes.curselection()
        if not sel:
            return

        idx = sel[0]
        label = self.list_ausentes.get(idx)

        carnet = label.split("|")[0].strip()

        self.ausentes.remove(carnet)
        self.list_ausentes.delete(idx)

        self._refresh_combos()

    # =====================================================
    # SAVE
    # =====================================================

    def _guardar(self):

        try:
            periodo = self.periodos[self.cb_periodo.current()]["id"]
            curso = self.cursos[self.cb_curso.current()]["id"]
            materia = self.materias[self.cb_materia.current()]["id"]
            docente = self.docentes[self.cb_docente.current()]["id"]

            result = ep.save_asistencia(
                self.db_user,
                self.db_pass,
                periodo_id=periodo,
                curso_cod=curso,
                materia_cod=materia,
                docente_cod=docente,
                fecha_clase=self.fecha_var.get(),
                asistentes=self.asistentes,
                ausentes=self.ausentes,
                codigo_usuario=self.codigo_usuario,
            )

            show_info(
                f"Asistencia {result['accion']} correctamente\n"
                f"Asistentes: {result['total_asistentes']}\n"
                f"Ausentes: {result['total_ausentes']}"
            )

        except Exception as e:
            handle_exception(e)