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

        # Layout principal: formulario arriba / listado abajo
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.top = ttk.LabelFrame(self, text="Formulario", padding=12)
        self.bottom = ttk.LabelFrame(self, text="Listado", padding=10)

        self.top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        self.bottom.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 12))

        self.top.columnconfigure(0, weight=1)
        self.bottom.columnconfigure(0, weight=1)
        self.bottom.rowconfigure(0, weight=1)

        # -------------------------------------------------
        # Bloque superior interno
        # -------------------------------------------------
        self.form_frame = ttk.LabelFrame(
            self.top,
            text="Asignación Docente - Materia",
            padding=12,
        )
        self.form_frame.grid(row=0, column=0, sticky="ew")

        self.form_frame.columnconfigure(0, weight=0)
        self.form_frame.columnconfigure(1, weight=1)

        row = 0

        ttk.Label(self.form_frame, text="Curso:").grid(
            row=row, column=0, sticky="w", pady=4, padx=(0, 8)
        )

        self.cbo_curso = ttk.Combobox(
            self.form_frame,
            textvariable=self.vars["curso"],
            state="readonly",
        )
        self.cbo_curso.grid(row=row, column=1, sticky="ew", pady=4)
        self.cbo_curso.bind("<<ComboboxSelected>>", self._on_curso_changed)
        row += 1

        ttk.Label(self.form_frame, text="Docente:").grid(
            row=row, column=0, sticky="w", pady=4, padx=(0, 8)
        )

        self.cbo_docente = ttk.Combobox(
            self.form_frame,
            textvariable=self.vars["docente"],
            state="disabled",
        )
        self.cbo_docente.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Label(self.form_frame, text="Materia:").grid(
            row=row, column=0, sticky="w", pady=4, padx=(0, 8)
        )

        self.cbo_materia = ttk.Combobox(
            self.form_frame,
            textvariable=self.vars["materia"],
            state="disabled",
        )
        self.cbo_materia.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Separator(self.form_frame).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        btns = ttk.Frame(self.form_frame)
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

        # -------------------------------------------------
        # GRID abajo
        # -------------------------------------------------
        self.tree = ttk.Treeview(
            self.bottom,
            columns=("docente", "curso", "materia", "estado"),
            show="headings",
        )

        self.tree.heading("docente", text="Docente")
        self.tree.heading("curso", text="Curso")
        self.tree.heading("materia", text="Materia")
        self.tree.heading("estado", text="Estado")

        self.tree.column("docente", width=220)
        self.tree.column("curso", width=260)
        self.tree.column("materia", width=260)
        self.tree.column("estado", width=120, anchor="center")

        vsb = ttk.Scrollbar(self.bottom, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.bottom, orient="horizontal", command=self.tree.xview)

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
    # Helpers
    # =====================================================
    def _extract_materia_cod_from_repo_row(self, row: tuple) -> int | None:
        try:
            # row del repo:
            # 0 = id_logico
            # 1 = curso
            # 2 = materia
            # 3 = docente
            # 4 = estado
            # 5 = fecha
            materia_display = str(row[2]).strip()
            head = materia_display.split("-", 1)[0].strip()
            return int(head)
        except Exception:
            return None

    def _map_repo_row_to_tree_row(self, row: tuple) -> tuple:
        # row del repo:
        # 0 = id_logico
        # 1 = curso
        # 2 = materia
        # 3 = docente
        # 4 = estado
        # 5 = fecha
        return (
            str(row[3]),  # docente
            str(row[1]),  # curso
            str(row[2]),  # materia
            str(row[4]),  # estado
        )

    def _filter_rows_by_selected_course(self, rows: list[tuple]) -> list[tuple]:
        curso_display = self.vars["curso"].get()
        curso_cod = self._curso_display_to_cod.get(curso_display)

        if not curso_cod:
            return rows

        allowed_materia_codes = set(self._materia_display_to_cod.values())
        if not allowed_materia_codes:
            return []

        filtered: list[tuple] = []

        for row in rows:
            materia_cod = self._extract_materia_cod_from_repo_row(row)
            if materia_cod in allowed_materia_codes:
                filtered.append(row)

        return filtered

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

            self._docente_display_to_cod = {}
            self._materia_display_to_cod = {}

            if not curso_cod:
                self.refresh_grid()
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

            self.refresh_grid()

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

            rows = self._filter_rows_by_selected_course(rows)

            for item in self.tree.get_children():
                self.tree.delete(item)

            for r in rows:
                self.tree.insert("", "end", values=self._map_repo_row_to_tree_row(r))

        except Exception as e:
            handle_exception(self, e, context="Listado Docente - Materia")

    # =====================================================
    # Actions
    # =====================================================
    def on_nuevo(self):
        self.reset_view_blank()
        self.refresh_grid()

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