# app/ui/matriculas_materia/docente_materia_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.error_handler import handle_exception, show_info, show_warning
from app.ui.components.confirm_dialog import show_confirm

from app.endpoints.matriculas_materia import (
    docente_materia_endpoints as dm_ep,
)


class DocenteMateriaTab(ttk.Frame):

    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.vars: dict[str, tk.StringVar] = {}

        self._curso_display_to_cod: dict[str, int] = {}
        self._docente_display_to_cod: dict[str, int] = {}
        self._materia_display_to_cod: dict[str, int] = {}
        self._estado_display_to_cod: dict[str, int] = {}

        self._selected_docente_cod: int | None = None
        self._selected_materia_cod: int | None = None

        self._loaded = False

        self._build_ui()
        self.reset_view_blank()

    # =====================================================
    # Vars
    # =====================================================
    def _ensure_vars(self):
        self.vars.setdefault("curso", tk.StringVar())
        self.vars.setdefault("docente", tk.StringVar())
        self.vars.setdefault("materia", tk.StringVar())
        self.vars.setdefault("estado", tk.StringVar())

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self._ensure_vars()

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)

        self.left = ttk.LabelFrame(self, text="Asignación Docente - Materia", padding=12)
        self.right = ttk.LabelFrame(self, text="Listado", padding=10)

        self.left.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=12)
        self.right.grid(row=0, column=1, sticky="nsew", padx=(8, 12), pady=12)

        self.left.columnconfigure(1, weight=1)
        self.right.columnconfigure(0, weight=1)
        self.right.rowconfigure(0, weight=1)

        row = 0

        ttk.Label(self.left, text="Curso:").grid(row=row, column=0, sticky="w", pady=4)

        self.cbo_curso = ttk.Combobox(
            self.left,
            textvariable=self.vars["curso"],
            state="readonly",
        )
        self.cbo_curso.grid(row=row, column=1, sticky="ew", pady=4)
        self.cbo_curso.bind("<<ComboboxSelected>>", self._on_curso_changed)
        row += 1

        ttk.Label(self.left, text="Docente:").grid(row=row, column=0, sticky="w", pady=4)

        self.cbo_docente = ttk.Combobox(
            self.left,
            textvariable=self.vars["docente"],
            state="disabled",
        )
        self.cbo_docente.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Label(self.left, text="Materia:").grid(row=row, column=0, sticky="w", pady=4)

        self.cbo_materia = ttk.Combobox(
            self.left,
            textvariable=self.vars["materia"],
            state="disabled",
        )
        self.cbo_materia.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Separator(self.left).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        btns = ttk.Frame(self.left)
        btns.grid(row=row, column=0, columnspan=2, sticky="ew")

        for i in range(4):
            btns.columnconfigure(i, weight=1)

        self.btn_nuevo = ttk.Button(btns, text="Nuevo", command=self.on_nuevo)
        self.btn_guardar = ttk.Button(btns, text="Guardar", command=self.on_guardar)
        self.btn_actualizar = ttk.Button(btns, text="Actualizar", command=self.on_actualizar)
        self.btn_eliminar = ttk.Button(btns, text="Eliminar", command=self.on_eliminar)

        self.btn_nuevo.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self.btn_guardar.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        self.btn_actualizar.grid(row=0, column=2, sticky="ew", padx=6, pady=6)
        self.btn_eliminar.grid(row=0, column=3, sticky="ew", padx=6, pady=6)

        # =====================================================
        # GRID
        # =====================================================
        self.tree = ttk.Treeview(
            self.right,
            columns=("docente", "materia", "estado"),
            show="headings",
        )

        self.tree.heading("docente", text="Docente")
        self.tree.heading("materia", text="Materia")
        self.tree.heading("estado", text="Estado")

        self.tree.column("docente", width=220)
        self.tree.column("materia", width=220)
        self.tree.column("estado", width=120, anchor="center")

        vsb = ttk.Scrollbar(self.right, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.right, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    # =====================================================
    # Lifecycle
    # =====================================================
    def ensure_loaded(self):
        if self._loaded:
            return

        self._load_initial_data()
        self.refresh_grid()

        self._loaded = True

    # =====================================================
    # Load
    # =====================================================
    def _load_initial_data(self):
        try:
            cursos = dm_ep.fetch_cursos_activos_docente_materia(
                self.db_user,
                self.db_pass,
            )
            estados = dm_ep.fetch_estados_docente_materia(
                self.db_user,
                self.db_pass,
            )

            self._curso_display_to_cod = {}
            values: list[str] = []

            for cod, desc in cursos:
                txt = f"{cod} - {desc}"
                self._curso_display_to_cod[txt] = int(cod)
                values.append(txt)

            self.cbo_curso["values"] = values

            self._estado_display_to_cod = {
                str(desc): int(cod) for cod, desc in estados
            }

        except Exception as e:
            handle_exception(self, e, context="Carga inicial Docente - Materia")

    # =====================================================
    # Eventos
    # =====================================================
    def _on_curso_changed(self, _evt=None):
        try:
            curso_display = self.vars["curso"].get()
            curso_cod = self._curso_display_to_cod.get(curso_display)

            self.vars["docente"].set("")
            self.vars["materia"].set("")
            self.cbo_docente["values"] = []
            self.cbo_materia["values"] = []
            self.cbo_docente.configure(state="disabled")
            self.cbo_materia.configure(state="disabled")

            if not curso_cod:
                return

            docentes = dm_ep.fetch_docentes_por_curso_docente_materia(
                self.db_user,
                self.db_pass,
                curso_cod,
            )
            materias = dm_ep.fetch_materias_por_curso_docente_materia(
                self.db_user,
                self.db_pass,
                curso_cod,
            )

            self._docente_display_to_cod = {}
            self._materia_display_to_cod = {}

            docentes_values: list[str] = []
            materias_values: list[str] = []

            for cod, nom in docentes:
                txt = f"{cod} - {nom}"
                self._docente_display_to_cod[txt] = int(cod)
                docentes_values.append(txt)

            for cod, desc in materias:
                txt = f"{cod} - {desc}"
                self._materia_display_to_cod[txt] = int(cod)
                materias_values.append(txt)

            self.cbo_docente["values"] = docentes_values
            self.cbo_materia["values"] = materias_values

            if docentes_values:
                self.cbo_docente.configure(state="readonly")
            if materias_values:
                self.cbo_materia.configure(state="readonly")

            if not docentes_values:
                show_warning(
                    self,
                    "Sin docentes",
                    "No hay docentes disponibles para el curso seleccionado.",
                )

            if not materias_values:
                show_warning(
                    self,
                    "Sin materias",
                    "No hay materias disponibles para el curso seleccionado.",
                )

        except Exception as e:
            handle_exception(self, e, context="Cambio de curso Docente - Materia")

    # =====================================================
    # Grid
    # =====================================================
    def refresh_grid(self):
        try:
            rows = dm_ep.list_docente_materia_rows(
                self.db_user,
                self.db_pass,
            )

            for item in self.tree.get_children():
                self.tree.delete(item)

            for r in rows:
                self.tree.insert("", "end", values=r)

        except Exception as e:
            handle_exception(self, e, context="Listado Docente - Materia")

    # =====================================================
    # Actions
    # =====================================================
    def on_nuevo(self):
        self.reset_view_blank()

    def on_guardar(self):
        try:
            docente = self.vars["docente"].get()
            materia = self.vars["materia"].get()

            docente_cod = self._docente_display_to_cod.get(docente)
            materia_cod = self._materia_display_to_cod.get(materia)

            if not docente_cod or not materia_cod:
                show_warning(self, "Validación", "Debe seleccionar docente y materia.")
                return

            msg = dm_ep.assign_docente_materia(
                db_user=self.db_user,
                db_pass=self.db_pass,
                docente_cod=docente_cod,
                materia_cod=materia_cod,
                estado_codigo=1,
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Asignación", msg)
            self.refresh_grid()

        except Exception as e:
            handle_exception(self, e, context="Guardar Docente - Materia")

    def on_actualizar(self):
        show_info(self, "Info", "Actualizar estado disponible desde el grid.")

    def on_eliminar(self):
        show_info(self, "Info", "Eliminar disponible desde el grid.")

    # =====================================================
    # Reset
    # =====================================================
    def reset_view_blank(self):
        self.vars["curso"].set("")
        self.vars["docente"].set("")
        self.vars["materia"].set("")

        self._docente_display_to_cod = {}
        self._materia_display_to_cod = {}

        self.cbo_docente["values"] = []
        self.cbo_materia["values"] = []

        self.cbo_docente.configure(state="disabled")
        self.cbo_materia.configure(state="disabled")