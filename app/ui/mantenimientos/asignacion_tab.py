from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.mantenimiento.asignacion_endpoints import (
    get_lookups,
    get_docentes_disponibles_para_programa,
    listar_asignaciones,
    crear_asignacion,
    actualizar_asignacion,
    eliminar_asignacion,
)

from app.core.error_handler import (
    handle_exception,
    show_info,
    show_warning,
)

from app.ui.components.confirm_dialog import show_confirm


class AsignacionTab(MaintenanceTab):
    """
    Tab de asignación de docentes a carreras/programas.
    Trabaja sobre dbo.Curso_Docente.
    """

    def __init__(self, parent, db_user: str | None, db_pass: str | None, codigo_usuario: int | None):
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.programa_desc_to_cod: dict[str, int] = {}
        self.programa_cod_to_desc: dict[int, str] = {}

        self.docente_desc_to_cod: dict[str, int] = {}
        self.docente_cod_to_desc: dict[int, str] = {}

        self._loaded = False

        super().__init__(parent, "Asignación", resource_key="asignacion")
        self.reset_view_blank()

    # ------------------------------------------------
    # LOAD
    # ------------------------------------------------
    def ensure_loaded(self):
        if not self.can_access():
            self._loaded = True
            self._clear_grid()
            return

        if getattr(self, "_loaded", False):
            return

        self._load_lookups()
        self.refresh_grid()
        self._loaded = True

    # ------------------------------------------------
    # HELPERS
    # ------------------------------------------------
    def _clear_grid(self):
        if not self.tree:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _clear_selection_fields(self):
        self.vars["Curso_Cod"].set("")
        self.vars["Docente_Cod"].set("")
        self.vars["Programa"].set("")
        self.vars["Docente"].set("")

        try:
            self.cb_docente["values"] = []
        except Exception:
            pass

        self.cb_docente.configure(state="disabled")

    # ------------------------------------------------
    # UI
    # ------------------------------------------------
    def _build_form(self, parent: ttk.LabelFrame):
        self.vars["Curso_Cod"] = tk.StringVar(value="")
        self.vars["Programa"] = tk.StringVar(value="")
        self.vars["Docente"] = tk.StringVar(value="")
        self.vars["Docente_Cod"] = tk.StringVar(value="")

        r = 0

        ttk.Label(parent, text="Código Programa:").grid(row=r, column=0, sticky="w", pady=6)
        ent_curso = ttk.Entry(parent, textvariable=self.vars["Curso_Cod"], state="readonly")
        ent_curso.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1



        ttk.Label(parent, text="Carrera / Programa:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_programa = ttk.Combobox(
            parent,
            textvariable=self.vars["Programa"],
            state="readonly",
            width=32,
        )
        self.cb_programa.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        self.cb_programa.bind("<<ComboboxSelected>>", self._on_programa_change)
        r += 1

        ttk.Label(parent, text="Docente:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_docente = ttk.Combobox(
            parent,
            textvariable=self.vars["Docente"],
            state="disabled",
            width=32,
        )
        self.cb_docente.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        self.cb_docente.bind("<<ComboboxSelected>>", self._on_docente_change)
        r += 1

        ttk.Label(parent, text="Código Docente:").grid(row=r, column=0, sticky="w", pady=6)
        ent_doc = ttk.Entry(parent, textvariable=self.vars["Docente_Cod"], state="readonly")
        ent_doc.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

    def _build_grid(self, parent: ttk.LabelFrame):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        cols = ("Id", "Curso_Cod", "Programa", "Docente_Cod", "Docente")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {
            "Id": 1,
            "Curso_Cod": 90,
            "Programa": 220,
            "Docente_Cod": 100,
            "Docente": 240,
        }

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=base_widths.get(c, 140), anchor="w", stretch=True)

        self.tree.column("Id", width=0, stretch=False)
        self.tree.heading("Id", text="")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    # ------------------------------------------------
    # RESET
    # ------------------------------------------------
    def reset_view_blank(self):
        self.vars["Curso_Cod"].set("")
        self.vars["Docente_Cod"].set("")

        try:
            self.cb_programa["values"] = []
            self.cb_docente["values"] = []
        except Exception:
            pass

        self.vars["Programa"].set("")
        self.vars["Docente"].set("")
        self.cb_docente.configure(state="disabled")

        self._clear_grid()

    # ------------------------------------------------
    # HELPERS UI
    # ------------------------------------------------
    def _build_programa_display(self, curso_cod: int, descripcion: str) -> str:
        return f"{int(curso_cod)} - {descripcion}"

    def _build_docente_display(self, docente_cod: int, nombre: str) -> str:
        return f"{int(docente_cod)} - {nombre}"

    def _cargar_docentes_para_programa(self, curso_cod: int, docente_cod_actual: int | None = None):
        try:
            docentes = get_docentes_disponibles_para_programa(
                self.db_user,
                self.db_pass,
                curso_cod=curso_cod,
                docente_cod_actual=docente_cod_actual,
            )
        except Exception as e:
            handle_exception(self, e, context="Cargar docentes filtrados")
            docentes = []

        docente_displays = [
            self._build_docente_display(cod, nombre)
            for cod, nombre in docentes
        ]

        self.docente_desc_to_cod = {
            self._build_docente_display(cod, nombre): cod
            for cod, nombre in docentes
        }
        self.docente_cod_to_desc = {
            cod: self._build_docente_display(cod, nombre)
            for cod, nombre in docentes
        }

        self.cb_docente["values"] = docente_displays

        if docente_displays:
            self.cb_docente.configure(state="readonly")
            if docente_cod_actual is not None and docente_cod_actual in self.docente_cod_to_desc:
                self.vars["Docente"].set(self.docente_cod_to_desc[docente_cod_actual])
                self.vars["Docente_Cod"].set(str(docente_cod_actual))
            else:
                self.vars["Docente"].set("")
                self.vars["Docente_Cod"].set("")
        else:
            self.vars["Docente"].set("")
            self.vars["Docente_Cod"].set("")
            self.cb_docente.configure(state="disabled")

    def _on_programa_change(self, _evt=None):
        if not self.can_access():
            return

        value = self.vars["Programa"].get().strip()
        curso_cod = self.programa_desc_to_cod.get(value)
        self.vars["Curso_Cod"].set("" if curso_cod is None else str(curso_cod))

        self.vars["Docente"].set("")
        self.vars["Docente_Cod"].set("")
        self.cb_docente["values"] = []
        self.cb_docente.configure(state="disabled")

        if curso_cod is None:
            return

        docente_cod_actual = None
        try:
            docente_cod_actual = int((self.vars["Docente_Cod"].get() or "").strip())
        except Exception:
            docente_cod_actual = None

        self._cargar_docentes_para_programa(curso_cod, docente_cod_actual=docente_cod_actual)

        if not self.cb_docente["values"]:
            show_warning(
                self,
                "Sin docentes disponibles",
                "No hay docentes disponibles y compatibles para la carrera/programa seleccionado.",
            )

    def _on_docente_change(self, _evt=None):
        if not self.can_access():
            return

        value = self.vars["Docente"].get().strip()
        docente_cod = self.docente_desc_to_cod.get(value)
        self.vars["Docente_Cod"].set("" if docente_cod is None else str(docente_cod))

    # ------------------------------------------------
    # DATA
    # ------------------------------------------------
    def _load_lookups(self):
        if not self.can_access():
            self.programa_desc_to_cod = {}
            self.programa_cod_to_desc = {}
            self.docente_desc_to_cod = {}
            self.docente_cod_to_desc = {}

            try:
                self.cb_programa["values"] = []
                self.cb_docente["values"] = []
            except Exception:
                pass

            self.vars["Programa"].set("")
            self.vars["Docente"].set("")
            self.vars["Curso_Cod"].set("")
            self.vars["Docente_Cod"].set("")
            self.cb_docente.configure(state="disabled")
            return

        try:
            programas, _docentes = get_lookups(self.db_user, self.db_pass)
        except Exception as e:
            handle_exception(self, e, context="Cargar catálogos")
            programas = []

        programa_displays = [
            self._build_programa_display(cod, desc)
            for cod, desc in programas
        ]

        self.programa_desc_to_cod = {
            self._build_programa_display(cod, desc): cod
            for cod, desc in programas
        }
        self.programa_cod_to_desc = {
            cod: self._build_programa_display(cod, desc)
            for cod, desc in programas
        }

        self.docente_desc_to_cod = {}
        self.docente_cod_to_desc = {}

        self.cb_programa["values"] = programa_displays
        self.cb_docente["values"] = []
        self.cb_docente.configure(state="disabled")

        # FIX: siempre dejar ambos combos en blanco
        self.vars["Programa"].set("")
        self.vars["Curso_Cod"].set("")
        self.vars["Docente"].set("")
        self.vars["Docente_Cod"].set("")

    def refresh_grid(self):
        if not self.tree:
            return

        self._clear_grid()

        if not self.can_access():
            return

        try:
            rows = listar_asignaciones(
                self.db_user,
                self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Cargar asignaciones")
            return

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=(r[0], r[1], r[2], r[3], r[4]),
            )

        self._autosize_columns()

    def _autosize_columns(self):
        if not self.tree:
            return

        font = tkfont.nametofont("TkDefaultFont")

        for col in self.tree["columns"]:
            if col == "Id":
                continue

            max_width = font.measure(col) + 20

            for item in self.tree.get_children():
                value = self.tree.set(item, col)
                width = font.measure(str(value)) + 20
                if width > max_width:
                    max_width = width

            if col in ("Curso_Cod", "Docente_Cod"):
                max_width = min(max_width, 110)
            else:
                max_width = min(max_width, 350)

            self.tree.column(col, width=max_width)

    # ------------------------------------------------
    # SELECCIÓN
    # ------------------------------------------------
    def _selected_pair(self) -> tuple[int, int] | None:
        if not self.tree:
            return None

        sel = self.tree.selection()
        if not sel:
            return None

        values = self.tree.item(sel[0], "values")
        try:
            curso_cod = int(values[1])
            docente_cod = int(values[3])
            return curso_cod, docente_cod
        except Exception:
            return None

    def on_row_select(self, _evt=None):
        if not self.can_access():
            return

        if not self.tree:
            return

        sel = self.tree.selection()
        if not sel:
            return

        values = self.tree.item(sel[0], "values")

        try:
            curso_cod = int(values[1])
            docente_cod = int(values[3])
        except Exception:
            return

        self.vars["Curso_Cod"].set(str(curso_cod))
        self.vars["Docente_Cod"].set(str(docente_cod))
        self.vars["Programa"].set(self.programa_cod_to_desc.get(curso_cod, ""))

        self._cargar_docentes_para_programa(curso_cod, docente_cod_actual=docente_cod)
        self.vars["Docente"].set(self.docente_cod_to_desc.get(docente_cod, ""))

    # ------------------------------------------------
    # CRUD
    # ------------------------------------------------
    def on_nuevo(self):
        if not self.can_access():
            self._deny_action("access")
            return

        self.ensure_loaded()

        self._clear_selection_fields()

        if self.tree:
            self.tree.selection_remove(self.tree.selection())

    def on_guardar(self):
        if not self.can_create():
            self._deny_action("create")
            return

        self.ensure_loaded()

        programa_desc = self.vars["Programa"].get().strip()
        docente_desc = self.vars["Docente"].get().strip()

        if programa_desc not in self.programa_desc_to_cod:
            show_warning(self, "Validación", "Debe seleccionar una carrera/programa válida.")
            return

        if docente_desc not in self.docente_desc_to_cod:
            show_warning(self, "Validación", "Debe seleccionar un docente válido.")
            return

        curso_cod = self.programa_desc_to_cod[programa_desc]
        docente_cod = self.docente_desc_to_cod[docente_desc]

        try:
            crear_asignacion(
                self.db_user,
                self.db_pass,
                curso_cod=curso_cod,
                docente_cod=docente_cod,
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Guardar asignación")
            return

        self.refresh_grid()
        self._load_lookups()
        self._clear_selection_fields()
        if self.tree:
            self.tree.selection_remove(self.tree.selection())
        show_info(self, "Éxito", "Asignación guardada correctamente.")

    def on_actualizar(self):
        if not self.can_update():
            self._deny_action("update")
            return

        self.ensure_loaded()

        selected = self._selected_pair()
        if not selected:
            show_warning(self, "Actualizar", "Seleccione una asignación del listado para actualizar.")
            return

        programa_desc = self.vars["Programa"].get().strip()
        docente_desc = self.vars["Docente"].get().strip()

        if programa_desc not in self.programa_desc_to_cod:
            show_warning(self, "Validación", "Debe seleccionar una carrera/programa válida.")
            return

        if docente_desc not in self.docente_desc_to_cod:
            show_warning(self, "Validación", "Debe seleccionar un docente válido.")
            return

        curso_cod_original, docente_cod_original = selected
        curso_cod_nuevo = self.programa_desc_to_cod[programa_desc]
        docente_cod_nuevo = self.docente_desc_to_cod[docente_desc]

        try:
            actualizar_asignacion(
                self.db_user,
                self.db_pass,
                curso_cod_original=curso_cod_original,
                docente_cod_original=docente_cod_original,
                curso_cod_nuevo=curso_cod_nuevo,
                docente_cod_nuevo=docente_cod_nuevo,
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Actualizar asignación")
            return

        self.refresh_grid()
        self._load_lookups()
        self._clear_selection_fields()
        if self.tree:
            self.tree.selection_remove(self.tree.selection())
        show_info(self, "Éxito", "Asignación actualizada correctamente.")

    def on_eliminar(self):
        if not self.can_delete():
            self._deny_action("delete")
            return

        self.ensure_loaded()

        selected = self._selected_pair()
        if not selected:
            show_warning(self, "Eliminar", "Seleccione una asignación del listado para eliminar.")
            return

        curso_cod, docente_cod = selected

        if not show_confirm(
            self,
            "Confirmar",
            f"¿Desea eliminar la asignación Programa {curso_cod} / Docente {docente_cod}?",
        ):
            return

        try:
            eliminar_asignacion(
                self.db_user,
                self.db_pass,
                curso_cod=curso_cod,
                docente_cod=docente_cod,
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Eliminar asignación")
            return

        self.refresh_grid()
        self._load_lookups()
        self._clear_selection_fields()
        if self.tree:
            self.tree.selection_remove(self.tree.selection())
        show_info(self, "Éxito", "Asignación eliminada correctamente.")