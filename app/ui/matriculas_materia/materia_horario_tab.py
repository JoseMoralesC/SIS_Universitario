from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.error_handler import handle_exception, show_info, show_warning
from app.ui.components.confirm_dialog import show_confirm
from app.endpoints.matriculas_materia import (
    materia_horario_endpoints as mh_ep,
)


class MateriaHorarioTab(ttk.Frame):
    """
    Tab UI - Entregable #4
    Asignación de horarios a materias.
    """

    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.vars: dict[str, tk.StringVar] = {}

        self._curso_display_to_cod: dict[str, int] = {}
        self._materia_display_to_cod: dict[str, int] = {}
        self._dia_display_to_cod: dict[str, str] = {}
        self._jornada_display_to_cod: dict[str, int] = {}

        self._selected_horario_id: int | None = None
        self._loaded = False

        self._build_ui()
        self.reset_view_blank()

    def ensure_loaded(self):
        if self._loaded:
            return
        self._load_initial_lookups()
        self.refresh_grid()
        self._loaded = True

    def _ensure_vars(self):
        self.vars.setdefault("curso", tk.StringVar())
        self.vars.setdefault("materia", tk.StringVar())
        self.vars.setdefault("dia", tk.StringVar())
        self.vars.setdefault("jornada", tk.StringVar())

    def _build_ui(self):
        self._ensure_vars()

        # Layout principal: formulario arriba / listado abajo
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.top = ttk.LabelFrame(self, text="Formulario", padding=(12, 10))
        self.bottom = ttk.LabelFrame(self, text="Listado", padding=(10, 10))

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
            text="Horario de Materias",
            padding=(12, 10),
        )
        self.form_frame.grid(row=0, column=0, sticky="ew")

        self.form_frame.columnconfigure(0, weight=0)
        self.form_frame.columnconfigure(1, weight=1)

        row = 0

        ttk.Label(
            self.form_frame,
            text="Asignación de Horario por Materia",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1

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

        ttk.Label(self.form_frame, text="Día:").grid(
            row=row, column=0, sticky="w", pady=4, padx=(0, 8)
        )
        self.cbo_dia = ttk.Combobox(
            self.form_frame,
            textvariable=self.vars["dia"],
            state="readonly",
        )
        self.cbo_dia.grid(row=row, column=1, sticky="ew", pady=4)
        self.cbo_dia.bind("<<ComboboxSelected>>", self._on_dia_changed)
        row += 1

        ttk.Label(self.form_frame, text="Jornada:").grid(
            row=row, column=0, sticky="w", pady=4, padx=(0, 8)
        )
        self.cbo_jornada = ttk.Combobox(
            self.form_frame,
            textvariable=self.vars["jornada"],
            state="readonly",
        )
        self.cbo_jornada.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Separator(self.form_frame).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(12, 10)
        )
        row += 1

        btns = ttk.Frame(self.form_frame)
        btns.grid(row=row, column=0, columnspan=2, sticky="ew")
        for i in range(4):
            btns.columnconfigure(i, weight=1, uniform="crud")

        self.btn_nuevo = ttk.Button(btns, text="Nuevo", command=self.on_nuevo)
        self.btn_guardar = ttk.Button(btns, text="Guardar", command=self.on_guardar)
        self.btn_actualizar = ttk.Button(btns, text="Actualizar Estado", command=self.on_actualizar)
        self.btn_eliminar = ttk.Button(btns, text="Eliminar", command=self.on_eliminar)

        self.btn_nuevo.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.btn_guardar.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        self.btn_actualizar.grid(row=0, column=2, sticky="ew", padx=8, pady=8)
        self.btn_eliminar.grid(row=0, column=3, sticky="ew", padx=8, pady=8)

        # -------------------------------------------------
        # GRID abajo
        # -------------------------------------------------
        cols = ("horario_id", "materia", "dia", "jornada", "estado")
        self.tree = ttk.Treeview(self.bottom, columns=cols, show="headings", height=18)

        headings = {
            "horario_id": "ID",
            "materia": "Materia",
            "dia": "Día",
            "jornada": "Jornada",
            "estado": "Estado",
        }

        widths = {
            "horario_id": 70,
            "materia": 220,
            "dia": 140,
            "jornada": 180,
            "estado": 110,
        }

        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], minwidth=70, anchor="w", stretch=True)

        self.tree.column("horario_id", anchor="center", stretch=False)
        self.tree.column("estado", anchor="center", stretch=False)

        vsb = ttk.Scrollbar(self.bottom, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.bottom, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    def reset_view_blank(self):
        self._ensure_vars()
        self._selected_horario_id = None

        self.vars["curso"].set("")
        self.vars["materia"].set("")
        self.vars["dia"].set("")
        self.vars["jornada"].set("")

        self._materia_display_to_cod = {}

        self.cbo_materia["values"] = []
        self.cbo_materia.set("")
        self.cbo_materia.configure(state="disabled")

        self.cbo_jornada.set("")

        if hasattr(self, "tree"):
            try:
                self.tree.selection_remove(self.tree.selection())
            except Exception:
                pass

    def _load_initial_lookups(self):
        try:
            cursos = mh_ep.fetch_cursos_activos_materia_horario(self.db_user, self.db_pass)
            dias = mh_ep.fetch_dias_semana_materia_horario(self.db_user, self.db_pass)
            jornadas = mh_ep.fetch_jornadas_materia_horario(self.db_user, self.db_pass)

            self._curso_display_to_cod = {}
            self._materia_display_to_cod = {}
            self._dia_display_to_cod = {}
            self._jornada_display_to_cod = {}

            curso_values: list[str] = []
            dia_values: list[str] = []
            jornada_values: list[str] = []

            for curso_cod, curso_desc in cursos:
                display = f"{curso_cod} - {curso_desc}"
                self._curso_display_to_cod[display] = int(curso_cod)
                curso_values.append(display)

            for dia_cod, dia_nombre in dias:
                display = f"{dia_cod} - {dia_nombre}"
                self._dia_display_to_cod[display] = str(dia_cod)
                dia_values.append(display)

            for jornada_id, jornada_desc in jornadas:
                display = f"{jornada_id} - {jornada_desc}"
                self._jornada_display_to_cod[display] = int(jornada_id)
                jornada_values.append(display)

            self.cbo_curso["values"] = curso_values
            self.cbo_materia["values"] = []
            self.cbo_dia["values"] = dia_values
            self.cbo_jornada["values"] = jornada_values

        except Exception as e:
            handle_exception(self, e, context="Carga inicial Horario de Materias")

    def _get_curso_selected(self) -> int | None:
        display = (self.vars["curso"].get() or "").strip()
        return self._curso_display_to_cod.get(display)

    def _get_materia_selected(self) -> int | None:
        display = (self.vars["materia"].get() or "").strip()
        return self._materia_display_to_cod.get(display)

    def _get_dia_selected(self) -> str | None:
        display = (self.vars["dia"].get() or "").strip()
        return self._dia_display_to_cod.get(display)

    def _get_jornada_selected(self) -> int | None:
        display = (self.vars["jornada"].get() or "").strip()
        return self._jornada_display_to_cod.get(display)

    def _extract_materia_cod_from_row(self, row: tuple) -> int | None:
        try:
            materia_display = str(row[1]).strip()
            head = materia_display.split("-", 1)[0].strip()
            return int(head)
        except Exception:
            return None

    def _filter_rows_by_selected_course(self, rows: list[tuple]) -> list[tuple]:
        curso_cod = self._get_curso_selected()
        if not curso_cod:
            return rows

        allowed_materia_codes = set(self._materia_display_to_cod.values())
        if not allowed_materia_codes:
            return []

        filtered: list[tuple] = []

        for row in rows:
            materia_cod = self._extract_materia_cod_from_row(row)
            if materia_cod in allowed_materia_codes:
                filtered.append(row)

        return filtered

    def _on_curso_changed(self, _evt=None):
        try:
            curso_cod = self._get_curso_selected()

            self.vars["materia"].set("")
            self.vars["dia"].set("")
            self.vars["jornada"].set("")

            self.cbo_materia["values"] = []
            self.cbo_materia.set("")
            self.cbo_materia.configure(state="disabled")

            self.cbo_jornada.set("")
            self._materia_display_to_cod = {}

            if not curso_cod:
                self.refresh_grid()
                return

            materias = mh_ep.fetch_materias_por_curso_con_docente_materia_horario(
                self.db_user,
                self.db_pass,
                int(curso_cod),
            )

            materia_values: list[str] = []

            for materia_cod, materia_desc in materias:
                display = f"{materia_cod} - {materia_desc}"
                self._materia_display_to_cod[display] = int(materia_cod)
                materia_values.append(display)

            self.cbo_materia["values"] = materia_values

            if materia_values:
                self.cbo_materia.configure(state="readonly")
            else:
                show_warning(
                    self,
                    "Sin materias",
                    "No hay materias para el curso seleccionado con docente asignado.",
                )

            self.refresh_grid()

        except Exception as e:
            handle_exception(self, e, context="Cambio de curso Horario de Materias")

    def _on_dia_changed(self, _evt=None):
        try:
            dia_cod = self._get_dia_selected()

            jornadas = mh_ep.fetch_jornadas_materia_horario(self.db_user, self.db_pass)
            self._jornada_display_to_cod = {}
            jornada_values: list[str] = []

            for jornada_id, jornada_desc in jornadas:
                if dia_cod == "S" and int(jornada_id) == 3:
                    continue

                display = f"{jornada_id} - {jornada_desc}"
                self._jornada_display_to_cod[display] = int(jornada_id)
                jornada_values.append(display)

            self.cbo_jornada["values"] = jornada_values
            self.cbo_jornada.set("")

        except Exception as e:
            handle_exception(self, e, context="Cambio de día Horario de Materias")

    def _on_row_selected(self, _evt=None):
        try:
            sel = self.tree.selection()
            if not sel:
                self._selected_horario_id = None
                return

            vals = self.tree.item(sel[0], "values")
            if not vals:
                self._selected_horario_id = None
                return

            self._selected_horario_id = int(vals[0])
        except Exception:
            self._selected_horario_id = None

    def refresh_grid(self):
        try:
            rows = mh_ep.list_materia_horario_rows(self.db_user, self.db_pass)
            rows = self._filter_rows_by_selected_course(rows)
            self._fill_tree(rows)
            self._selected_horario_id = None
        except Exception as e:
            handle_exception(self, e, context="Listado Horario de Materias")

    def _fill_tree(self, rows: list[tuple]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in rows:
            try:
                self.tree.insert("", "end", values=r)
            except Exception:
                pass

    def on_nuevo(self):
        try:
            self.reset_view_blank()
            self.refresh_grid()
        except Exception as e:
            handle_exception(self, e, context="Nuevo Horario de Materias")

    def on_guardar(self):
        try:
            materia_cod = self._get_materia_selected()
            dia_cod = self._get_dia_selected()
            jornada_id = self._get_jornada_selected()

            if not materia_cod:
                show_warning(self, "Validación", "Selecciona una materia.")
                return
            if not dia_cod:
                show_warning(self, "Validación", "Selecciona un día.")
                return
            if not jornada_id:
                show_warning(self, "Validación", "Selecciona una jornada.")
                return

            msg = mh_ep.assign_materia_horario(
                db_user=self.db_user,
                db_pass=self.db_pass,
                materia_cod=int(materia_cod),
                dia_cod=str(dia_cod),
                jornada_id=int(jornada_id),
                estado_codigo=1,
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Horario de Materias", msg)
            self.refresh_grid()

            self.vars["dia"].set("")
            self.vars["jornada"].set("")
            self.cbo_jornada.set("")
            self._on_dia_changed()

        except Exception as e:
            handle_exception(self, e, context="Guardar Horario de Materias")

    def on_actualizar(self):
        try:
            if not self._selected_horario_id:
                show_warning(self, "Validación", "Selecciona un horario del listado.")
                return

            msg = mh_ep.update_estado_materia_horario_endpoint(
                db_user=self.db_user,
                db_pass=self.db_pass,
                horario_id=int(self._selected_horario_id),
                nuevo_estado=1,
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Actualizar Estado", msg)
            self.refresh_grid()

        except Exception as e:
            handle_exception(self, e, context="Actualizar Estado Horario de Materias")

    def on_eliminar(self):
        try:
            if not self._selected_horario_id:
                show_warning(self, "Validación", "Selecciona un horario del listado.")
                return

            ok = show_confirm(
                self,
                "Eliminar horario",
                "¿Deseas desactivar el horario seleccionado?",
                yes_text="Sí, desactivar",
                no_text="Cancelar",
            )
            if not ok:
                return

            msg = mh_ep.delete_materia_horario_endpoint(
                db_user=self.db_user,
                db_pass=self.db_pass,
                horario_id=int(self._selected_horario_id),
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Eliminar", msg)
            self._selected_horario_id = None
            self.refresh_grid()

        except Exception as e:
            handle_exception(self, e, context="Eliminar Horario de Materias")