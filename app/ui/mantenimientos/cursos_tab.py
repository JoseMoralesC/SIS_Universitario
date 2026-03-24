# app/ui/mantenimientos/cursos_tab.py
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.mantenimiento.cursos_endpoints import (
    get_lookups,
    listar_cursos,
    siguiente_materia_cod,
    crear_curso,
    actualizar_curso,
    eliminar_curso,
)

from app.core.error_handler import (
    handle_exception,
    show_info,
    show_warning,
)

from app.ui.components.confirm_dialog import show_confirm


class CursosTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        # Lookups
        self.estado_desc_to_cod: dict[str, int] = {}
        self.estado_cod_to_desc: dict[int, str] = {}
        self.programa_desc_to_cod: dict[str, int] = {}
        self.programa_cod_to_desc: dict[int, str] = {}

        self._loaded = False

        super().__init__(parent, "Cursos", resource_key="cursos")
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
        for it in self.tree.get_children():
            self.tree.delete(it)

    # -----------------------------
    # UI
    # -----------------------------
    def _build_form(self, parent: ttk.LabelFrame):
        self.vars["Materia_Cod"] = tk.StringVar(value="")
        self.vars["Descripcion"] = tk.StringVar(value="")
        self.vars["Programa"] = tk.StringVar(value="")
        self.vars["Precio"] = tk.StringVar(value="")
        self.vars["Estado"] = tk.StringVar(value="")

        r = 0

        def add_entry(label: str, key: str, readonly: bool = False):
            nonlocal r
            ttk.Label(parent, text=f"{label}:").grid(row=r, column=0, sticky="w", pady=6)
            ent = ttk.Entry(parent, textvariable=self.vars[key])
            ent.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
            if readonly:
                ent.state(["readonly"])
            r += 1

        add_entry("ID", "Materia_Cod", readonly=True)
        add_entry("Descripción", "Descripcion")

        ttk.Label(parent, text="Programa:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_programa = ttk.Combobox(
            parent,
            textvariable=self.vars["Programa"],
            state="readonly",
            width=26,
        )
        self.cb_programa.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

        add_entry("Precio", "Precio")

        ttk.Label(parent, text="Estado:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_estado = ttk.Combobox(
            parent,
            textvariable=self.vars["Estado"],
            state="readonly",
            width=26,
        )
        self.cb_estado.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

    def _build_grid(self, parent: ttk.LabelFrame):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        cols = ("ID", "Descripción", "Programa ID", "Programa", "Precio", "Estado")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {
            "ID": 60,
            "Descripción": 260,
            "Programa ID": 80,
            "Programa": 220,
            "Precio": 100,
            "Estado": 100,
        }
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=base_widths.get(c, 140), anchor="w", stretch=True)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def _autosize_columns(self):
        if not self.tree:
            return
        font = tkfont.nametofont("TkDefaultFont")
        for col in self.tree["columns"]:
            max_w = font.measure(col) + 20
            for item in self.tree.get_children():
                v = self.tree.set(item, col)
                w = font.measure(str(v)) + 20
                if w > max_w:
                    max_w = w
            if col == "ID":
                max_w = min(max_w, 70)
            else:
                max_w = min(max_w, 420)
            self.tree.column(col, width=max_w)

    # -----------------------------
    # BLANK / RESET + DATA
    # -----------------------------
    def reset_view_blank(self):
        self.vars["Materia_Cod"].set("")
        self.vars["Descripcion"].set("")
        self.vars["Precio"].set("")

        try:
            self.cb_programa["values"] = []
            self.cb_estado["values"] = []
        except Exception:
            pass

        self.vars["Programa"].set("")
        self.vars["Estado"].set("")

        self._clear_grid()

    def _load_lookups(self):
        if not self.can_access():
            self.estado_desc_to_cod = {}
            self.estado_cod_to_desc = {}
            self.programa_desc_to_cod = {}
            self.programa_cod_to_desc = {}

            try:
                self.cb_programa["values"] = []
                self.cb_estado["values"] = []
            except Exception:
                pass

            self.vars["Programa"].set("")
            self.vars["Estado"].set("")
            return

        try:
            estados, programas = get_lookups(self.db_user, self.db_pass)
        except Exception as e:
            handle_exception(self, e, context="Cargar catálogos (Cursos)")
            estados, programas = [], []

        self.estado_desc_to_cod = {desc: cod for cod, desc in estados}
        self.estado_cod_to_desc = {cod: desc for cod, desc in estados}
        self.programa_desc_to_cod = {desc: cod for cod, desc in programas}
        self.programa_cod_to_desc = {cod: desc for cod, desc in programas}

        self.cb_estado["values"] = list(self.estado_desc_to_cod.keys())
        self.cb_programa["values"] = list(self.programa_desc_to_cod.keys())

        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])
        else:
            self.vars["Estado"].set("")

        if self.cb_programa["values"]:
            self.vars["Programa"].set(self.cb_programa["values"][0])
        else:
            self.vars["Programa"].set("")

    def refresh_grid(self):
        if not self.tree:
            return

        self._clear_grid()

        if not self.can_access():
            return

        try:
            rows = listar_cursos(self.db_user, self.db_pass)
        except Exception as e:
            handle_exception(self, e, context="Cargar cursos")
            return

        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], str(r[4]), r[5]))

        self._autosize_columns()

    # -----------------------------
    # SELECTION
    # -----------------------------
    def _selected_id(self) -> int | None:
        if not self.tree:
            return None
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], "values")
        try:
            return int(values[0])
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

        v = self.tree.item(sel[0], "values")
        self.vars["Materia_Cod"].set(str(v[0]))
        self.vars["Descripcion"].set(str(v[1]))

        prog_name = str(v[3]).strip()
        if prog_name in self.programa_desc_to_cod:
            self.vars["Programa"].set(prog_name)
        else:
            if self.cb_programa["values"]:
                self.vars["Programa"].set(self.cb_programa["values"][0])
            else:
                self.vars["Programa"].set("")

        self.vars["Precio"].set("" if v[4] is None else str(v[4]))
        self.vars["Estado"].set(str(v[5]))

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        if not self.can_access():
            self._deny_action("access")
            return

        self.ensure_loaded()

        try:
            new_id = siguiente_materia_cod(self.db_user, self.db_pass)
            self.vars["Materia_Cod"].set(str(new_id))
        except Exception as e:
            handle_exception(self, e, context="Generar ID (Cursos)")
            self.vars["Materia_Cod"].set("")

        self.vars["Descripcion"].set("")
        self.vars["Precio"].set("")

        if self.cb_programa["values"]:
            self.vars["Programa"].set(self.cb_programa["values"][0])
        else:
            self.vars["Programa"].set("")

        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])
        else:
            self.vars["Estado"].set("")

        if self.tree:
            self.tree.selection_remove(self.tree.selection())

    def on_guardar(self):
        if not self.can_create():
            self._deny_action("create")
            return

        self.ensure_loaded()

        id_txt = self.vars["Materia_Cod"].get().strip()
        if not id_txt.isdigit():
            show_warning(self, "Validación", "Debe presionar 'Nuevo' para generar el ID antes de guardar.")
            return

        desc = self.vars["Descripcion"].get().strip()
        prog_desc = self.vars["Programa"].get().strip()
        precio_txt = self.vars["Precio"].get().strip()
        est_desc = self.vars["Estado"].get().strip()

        if not desc:
            show_warning(self, "Validación", "La descripción es requerida.")
            return

        if prog_desc not in self.programa_desc_to_cod:
            show_warning(self, "Validación", "Programa inválido.")
            return
        if est_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        try:
            crear_curso(
                self.db_user,
                self.db_pass,
                materia_cod=int(id_txt),
                descripcion=desc,
                curso_cod=self.programa_desc_to_cod[prog_desc],
                precio=precio_txt,
                estado_codigo=self.estado_desc_to_cod[est_desc],
            )
        except Exception as e:
            handle_exception(self, e, context="Guardar curso")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Curso guardado correctamente.")

    def on_actualizar(self):
        if not self.can_update():
            self._deny_action("update")
            return

        self.ensure_loaded()

        materia_cod = self._selected_id()
        if not materia_cod:
            show_warning(self, "Actualizar", "Seleccione un curso del listado para actualizar.")
            return

        desc = self.vars["Descripcion"].get().strip()
        prog_desc = self.vars["Programa"].get().strip()
        precio_txt = self.vars["Precio"].get().strip()
        est_desc = self.vars["Estado"].get().strip()

        if not desc:
            show_warning(self, "Validación", "La descripción es requerida.")
            return

        if prog_desc not in self.programa_desc_to_cod:
            show_warning(self, "Validación", "Programa inválido.")
            return
        if est_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        try:
            actualizar_curso(
                self.db_user,
                self.db_pass,
                materia_cod=materia_cod,
                descripcion=desc,
                curso_cod=self.programa_desc_to_cod[prog_desc],
                precio=precio_txt,
                estado_codigo=self.estado_desc_to_cod[est_desc],
            )
        except Exception as e:
            handle_exception(self, e, context="Actualizar curso")
            return

        self.refresh_grid()
        show_info(self, "Éxito", "Curso actualizado correctamente.")

    def on_eliminar(self):
        if not self.can_delete():
            self._deny_action("delete")
            return

        self.ensure_loaded()

        materia_cod = self._selected_id()
        if not materia_cod:
            show_warning(self, "Eliminar", "Seleccione un curso del listado para eliminar.")
            return

        if not show_confirm(self, "Confirmar", f"¿Pasar a INACTIVO el curso ID {materia_cod}?"):
            return

        try:
            eliminar_curso(self.db_user, self.db_pass, materia_cod)
        except Exception as e:
            handle_exception(self, e, context="Eliminar curso")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Curso pasado a INACTIVO correctamente.")