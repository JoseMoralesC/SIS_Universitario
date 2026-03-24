# app/ui/mantenimientos/estudiantes_tab.py
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.mantenimiento.estudiantes_endpoints import (
    get_lookups,
    listar_estudiantes,
    siguiente_carnet,
    crear_estudiante,
    actualizar_estudiante,
    eliminar_estudiante,
)

from app.core.error_handler import (
    handle_exception,
    show_info,
    show_warning,
)

from app.ui.components.confirm_dialog import show_confirm


class EstudiantesTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.estado_desc_to_cod: dict[str, int] = {}
        self.estado_cod_to_desc: dict[int, str] = {}

        self._loaded = False

        super().__init__(parent, "Estudiantes", resource_key="estudiantes")
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

    # -----------------------------
    # UI
    # -----------------------------
    def _build_form(self, parent: ttk.LabelFrame):
        self.vars["Carnet"] = tk.StringVar(value="")
        self.vars["Identificacion"] = tk.StringVar(value="")
        self.vars["Nombre_Completo"] = tk.StringVar(value="")
        self.vars["Direccion"] = tk.StringVar(value="")
        self.vars["Telefono"] = tk.StringVar(value="")
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
            return ent

        # Carnet: SIEMPRE readonly (se autogenera con "Nuevo")
        self.ent_carnet = add_entry("Carnet", "Carnet", readonly=True)

        add_entry("Identificación", "Identificacion")
        add_entry("Nombre Completo", "Nombre_Completo")
        add_entry("Dirección", "Direccion")
        add_entry("Teléfono", "Telefono")

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

        cols = ("Carnet", "Identificación", "Nombre", "Dirección", "Teléfono", "Estado")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {
            "Carnet": 90,
            "Identificación": 120,
            "Nombre": 240,
            "Dirección": 240,
            "Teléfono": 110,
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

            if col == "Carnet":
                max_w = min(max_w, 140)
            elif col in ("Teléfono", "Estado"):
                max_w = min(max_w, 140)
            else:
                max_w = min(max_w, 420)

            self.tree.column(col, width=max_w)

    # -----------------------------
    # blank/reset + data
    # -----------------------------
    def reset_view_blank(self):
        self.vars["Carnet"].set("")
        self.vars["Identificacion"].set("")
        self.vars["Nombre_Completo"].set("")
        self.vars["Direccion"].set("")
        self.vars["Telefono"].set("")

        try:
            self.cb_estado["values"] = []
        except Exception:
            pass
        self.vars["Estado"].set("")

        self._clear_grid()

    def _load_lookups(self):
        if not self.can_access():
            self.estado_desc_to_cod = {}
            self.estado_cod_to_desc = {}

            try:
                self.cb_estado["values"] = []
            except Exception:
                pass

            self.vars["Estado"].set("")
            return

        try:
            # el endpoint actual solo recibe (db_user, db_pass)
            estados = get_lookups(self.db_user, self.db_pass)
        except Exception as e:
            handle_exception(self, e, context="Cargar estados (Estudiantes)")
            estados = []

        self.estado_desc_to_cod = {desc: cod for cod, desc in estados}
        self.estado_cod_to_desc = {cod: desc for cod, desc in estados}

        self.cb_estado["values"] = list(self.estado_desc_to_cod.keys())
        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])
        else:
            self.vars["Estado"].set("")

    def refresh_grid(self):
        if not self.tree:
            return

        self._clear_grid()

        if not self.can_access():
            return

        try:
            rows = listar_estudiantes(
                self.db_user,
                self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Cargar estudiantes")
            return

        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3] or "", r[4] or "", r[5]))

        self._autosize_columns()

    # -----------------------------
    # selection
    # -----------------------------
    def _selected_carnet(self) -> str | None:
        if not self.tree:
            return None
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], "values")
        carnet = str(values[0]).strip()
        return carnet if carnet else None

    def on_row_select(self, _evt=None):
        if not self.can_access():
            return

        if not self.tree:
            return
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0], "values")

        self.vars["Carnet"].set(str(v[0]))
        self.vars["Identificacion"].set(str(v[1]))
        self.vars["Nombre_Completo"].set(str(v[2]))
        self.vars["Direccion"].set(str(v[3]))
        self.vars["Telefono"].set(str(v[4]))
        self.vars["Estado"].set(str(v[5]))

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        if not self.can_access():
            self._deny_action("access")
            return

        self.ensure_loaded()

        # Autogenera el carnet (CUC-000X) y lo deja readonly
        try:
            # el endpoint actual no recibe codigo_usuario aquí
            new_carnet = siguiente_carnet(self.db_user, self.db_pass)
            self.vars["Carnet"].set(str(new_carnet))
        except Exception as e:
            handle_exception(self, e, context="Generar Carnet (Estudiantes)")
            self.vars["Carnet"].set("")

        self.vars["Identificacion"].set("")
        self.vars["Nombre_Completo"].set("")
        self.vars["Direccion"].set("")
        self.vars["Telefono"].set("")

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

        estado_desc = self.vars["Estado"].get().strip()
        if estado_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        carnet = self.vars["Carnet"].get().strip()
        if not carnet:
            show_warning(self, "Validación", "Debe presionar 'Nuevo' para generar el Carnet antes de guardar.")
            return

        try:
            crear_estudiante(
                self.db_user,
                self.db_pass,
                carnet=carnet,
                identificacion=self.vars["Identificacion"].get(),
                nombre_completo=self.vars["Nombre_Completo"].get(),
                direccion=self.vars["Direccion"].get(),
                telefono=self.vars["Telefono"].get(),
                estado_codigo=self.estado_desc_to_cod[estado_desc],
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Guardar estudiante")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Estudiante guardado correctamente.")

    def on_actualizar(self):
        if not self.can_update():
            self._deny_action("update")
            return

        self.ensure_loaded()

        carnet = self._selected_carnet()
        if not carnet:
            show_warning(self, "Actualizar", "Seleccione un estudiante del listado para actualizar.")
            return

        estado_desc = self.vars["Estado"].get().strip()
        if estado_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        try:
            actualizar_estudiante(
                self.db_user,
                self.db_pass,
                carnet=carnet,
                identificacion=self.vars["Identificacion"].get(),
                nombre_completo=self.vars["Nombre_Completo"].get(),
                direccion=self.vars["Direccion"].get(),
                telefono=self.vars["Telefono"].get(),
                estado_codigo=self.estado_desc_to_cod[estado_desc],
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Actualizar estudiante")
            return

        self.refresh_grid()
        show_info(self, "Éxito", "Estudiante actualizado correctamente.")

    def on_eliminar(self):
        if not self.can_delete():
            self._deny_action("delete")
            return

        self.ensure_loaded()

        carnet = self._selected_carnet()
        if not carnet:
            show_warning(self, "Eliminar", "Seleccione un estudiante del listado para eliminar.")
            return

        if not show_confirm(self, "Confirmar", f"¿Pasar a INACTIVO el estudiante Carnet {carnet}?"):
            return

        try:
            eliminar_estudiante(
                self.db_user,
                self.db_pass,
                carnet,
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Eliminar estudiante")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Estudiante pasado a INACTIVO correctamente.")