# app/ui/mantenimientos/becas_tab.py
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.mantenimiento.becas_endpoints import (
    get_lookups,
    listar_becas,
    siguiente_id_beca,
    crear_beca,
    actualizar_beca,
    eliminar_beca,
)

from app.core.error_handler import (
    handle_exception,
    show_info,
    show_warning,
)

from app.ui.components.confirm_dialog import show_confirm


class BecasTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.estado_desc_to_cod: dict[str, int] = {}
        self.estado_cod_to_desc: dict[int, str] = {}

        self._loaded = False

        super().__init__(parent, "Becas", resource_key="becas")
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

    # -----------------------------
    # UI
    # -----------------------------
    def _build_form(self, parent: ttk.LabelFrame):
        self.vars["Id_Beca"] = tk.StringVar(value="")
        self.vars["Nombre_Beca"] = tk.StringVar(value="")
        self.vars["Descripcion"] = tk.StringVar(value="")
        self.vars["Porcentaje_Descuento"] = tk.StringVar(value="")
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

        add_entry("ID", "Id_Beca", readonly=True)
        add_entry("Nombre", "Nombre_Beca")
        add_entry("Descripción", "Descripcion")
        add_entry("% Descuento", "Porcentaje_Descuento")

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

        cols = ("ID", "Nombre", "Descripción", "Porcentaje", "Estado")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {
            "ID": 60,
            "Nombre": 180,
            "Descripción": 260,
            "Porcentaje": 110,
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
            elif col in ("Porcentaje", "Estado"):
                max_w = min(max_w, 130)
            else:
                max_w = min(max_w, 420)

            self.tree.column(col, width=max_w)

    # -----------------------------
    # blank/reset + data
    # -----------------------------
    def reset_view_blank(self):
        self.vars["Id_Beca"].set("")
        self.vars["Nombre_Beca"].set("")
        self.vars["Descripcion"].set("")
        self.vars["Porcentaje_Descuento"].set("")

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
            estados = get_lookups(self.db_user, self.db_pass)
        except Exception as e:
            handle_exception(self, e, context="Cargar estados (Becas)")
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
            rows = listar_becas(self.db_user, self.db_pass, codigo_usuario=self.codigo_usuario)
        except TypeError:
            # compatibilidad con endpoint antiguo si aún no recibe codigo_usuario
            try:
                rows = listar_becas(self.db_user, self.db_pass)
            except Exception as e:
                handle_exception(self, e, context="Cargar becas")
                return
        except Exception as e:
            handle_exception(self, e, context="Cargar becas")
            return

        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))

        self._autosize_columns()

    # -----------------------------
    # selection
    # -----------------------------
    def on_row_select(self, _evt=None):
        if not self.can_access():
            return

        if not self.tree:
            return

        sel = self.tree.selection()
        if not sel:
            return

        v = self.tree.item(sel[0], "values")
        self.vars["Id_Beca"].set(str(v[0]))
        self.vars["Nombre_Beca"].set(str(v[1]))
        self.vars["Descripcion"].set(str(v[2]))
        self.vars["Porcentaje_Descuento"].set(str(v[3]))
        self.vars["Estado"].set(str(v[4]))

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        if not self.can_access():
            self._deny_action("access")
            return

        self.ensure_loaded()

        try:
            try:
                new_id = siguiente_id_beca(
                    self.db_user,
                    self.db_pass,
                    codigo_usuario=self.codigo_usuario,
                )
            except TypeError:
                # compatibilidad con endpoint antiguo
                new_id = siguiente_id_beca(self.db_user, self.db_pass)

            self.vars["Id_Beca"].set(str(new_id))
        except Exception as e:
            handle_exception(self, e, context="Generar ID (Becas)")
            self.vars["Id_Beca"].set("")

        self.vars["Nombre_Beca"].set("")
        self.vars["Descripcion"].set("")
        self.vars["Porcentaje_Descuento"].set("")

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

        id_txt = self.vars["Id_Beca"].get().strip()
        if not id_txt.isdigit():
            show_warning(self, "Validación", "Debe presionar 'Nuevo' para generar el ID antes de guardar.")
            return

        nombre = self.vars["Nombre_Beca"].get().strip()
        descripcion = self.vars["Descripcion"].get().strip()
        porcentaje_txt = self.vars["Porcentaje_Descuento"].get().strip()
        estado_desc = self.vars["Estado"].get().strip()

        if not nombre:
            show_warning(self, "Validación", "El nombre de la beca es requerido.")
            return

        if not porcentaje_txt:
            show_warning(self, "Validación", "El porcentaje de descuento es requerido.")
            return

        if estado_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        try:
            porcentaje = int(porcentaje_txt)
        except ValueError:
            show_warning(self, "Validación", "El porcentaje de descuento debe ser un número entero.")
            return

        try:
            try:
                crear_beca(
                    self.db_user,
                    self.db_pass,
                    id_beca=int(id_txt),
                    nombre_beca=nombre,
                    descripcion=descripcion,
                    porcentaje_descuento=porcentaje,
                    estado_codigo=self.estado_desc_to_cod[estado_desc],
                    codigo_usuario=self.codigo_usuario,
                )
            except TypeError:
                # compatibilidad con endpoint antiguo
                crear_beca(
                    self.db_user,
                    self.db_pass,
                    id_beca=int(id_txt),
                    nombre_beca=nombre,
                    descripcion=descripcion,
                    porcentaje_descuento=porcentaje,
                    estado_codigo=self.estado_desc_to_cod[estado_desc],
                )
        except Exception as e:
            handle_exception(self, e, context="Guardar beca")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Beca guardada correctamente.")

    def on_actualizar(self):
        if not self.can_update():
            self._deny_action("update")
            return

        self.ensure_loaded()

        id_beca = self._selected_id()
        if not id_beca:
            show_warning(self, "Actualizar", "Seleccione una beca del listado para actualizar.")
            return

        nombre = self.vars["Nombre_Beca"].get().strip()
        descripcion = self.vars["Descripcion"].get().strip()
        porcentaje_txt = self.vars["Porcentaje_Descuento"].get().strip()
        estado_desc = self.vars["Estado"].get().strip()

        if not nombre:
            show_warning(self, "Validación", "El nombre de la beca es requerido.")
            return

        if not porcentaje_txt:
            show_warning(self, "Validación", "El porcentaje de descuento es requerido.")
            return

        if estado_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        try:
            porcentaje = int(porcentaje_txt)
        except ValueError:
            show_warning(self, "Validación", "El porcentaje de descuento debe ser un número entero.")
            return

        try:
            try:
                actualizar_beca(
                    self.db_user,
                    self.db_pass,
                    id_beca=id_beca,
                    nombre_beca=nombre,
                    descripcion=descripcion,
                    porcentaje_descuento=porcentaje,
                    estado_codigo=self.estado_desc_to_cod[estado_desc],
                    codigo_usuario=self.codigo_usuario,
                )
            except TypeError:
                # compatibilidad con endpoint antiguo
                actualizar_beca(
                    self.db_user,
                    self.db_pass,
                    id_beca=id_beca,
                    nombre_beca=nombre,
                    descripcion=descripcion,
                    porcentaje_descuento=porcentaje,
                    estado_codigo=self.estado_desc_to_cod[estado_desc],
                )
        except Exception as e:
            handle_exception(self, e, context="Actualizar beca")
            return

        self.refresh_grid()
        show_info(self, "Éxito", "Beca actualizada correctamente.")

    def on_eliminar(self):
        if not self.can_delete():
            self._deny_action("delete")
            return

        self.ensure_loaded()

        id_beca = self._selected_id()
        if not id_beca:
            show_warning(self, "Eliminar", "Seleccione una beca del listado para eliminar.")
            return

        if not show_confirm(self, "Confirmar", f"¿Pasar a INACTIVO la beca ID {id_beca}?"):
            return

        try:
            try:
                eliminar_beca(
                    self.db_user,
                    self.db_pass,
                    id_beca,
                    codigo_usuario=self.codigo_usuario,
                )
            except TypeError:
                # compatibilidad con endpoint antiguo
                eliminar_beca(self.db_user, self.db_pass, id_beca)
        except Exception as e:
            handle_exception(self, e, context="Eliminar beca")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Beca pasada a INACTIVO correctamente.")