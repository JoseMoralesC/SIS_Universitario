# app/ui/mantenimientos/estudiantes_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.estudiantes_endpoints import (
    get_lookups,
    listar_estudiantes,
    crear_estudiante,
    actualizar_estudiante,
    eliminar_estudiante,
)
from app.services.estudiantes_service import ValidationError


class EstudiantesTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str):
        self.db_user = db_user
        self.db_pass = db_pass

        self.estado_desc_to_cod: dict[str, int] = {}
        self.estado_cod_to_desc: dict[int, str] = {}

        self._loaded = False

        super().__init__(parent, "Estudiantes")
        self.reset_view_blank()

    def ensure_loaded(self):
        if getattr(self, "_loaded", False):
            return
        self._load_lookups()
        self.refresh_grid()
        self._loaded = True

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

        def add_entry(label: str, key: str):
            nonlocal r
            ttk.Label(parent, text=f"{label}:").grid(row=r, column=0, sticky="w", pady=6)
            ent = ttk.Entry(parent, textvariable=self.vars[key])
            ent.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
            r += 1
            return ent

        # Carnet: editable en Nuevo, readonly al seleccionar
        self.ent_carnet = add_entry("Carnet", "Carnet")
        add_entry("Identificación", "Identificacion")
        add_entry("Nombre Completo", "Nombre_Completo")
        add_entry("Dirección", "Direccion")
        add_entry("Teléfono", "Telefono")

        ttk.Label(parent, text="Estado:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_estado = ttk.Combobox(parent, textvariable=self.vars["Estado"], state="readonly", width=26)
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

            # límites
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

        if getattr(self, "ent_carnet", None) is not None:
            self.ent_carnet.state(["!readonly"])

        if self.tree:
            for it in self.tree.get_children():
                self.tree.delete(it)

    def _load_lookups(self):
        try:
            estados = get_lookups(self.db_user, self.db_pass)
        except Exception as e:
            messagebox.showerror("DB", f"No se pudieron cargar estados:\n{e}")
            estados = []

        self.estado_desc_to_cod = {desc: cod for cod, desc in estados}
        self.estado_cod_to_desc = {cod: desc for cod, desc in estados}

        self.cb_estado["values"] = list(self.estado_desc_to_cod.keys())
        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])

    def refresh_grid(self):
        if not self.tree:
            return
        for it in self.tree.get_children():
            self.tree.delete(it)

        try:
            rows = listar_estudiantes(self.db_user, self.db_pass)
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo cargar Estudiantes:\n{e}")
            return

        for r in rows:
            # (Carnet, Identificacion, Nombre_Completo, Direccion, Telefono, Estado_Desc)
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

        # Carnet readonly al editar existente
        if getattr(self, "ent_carnet", None) is not None:
            self.ent_carnet.state(["readonly"])

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        self.ensure_loaded()

        # limpiar y habilitar carnet para nuevo
        self.vars["Carnet"].set("")
        self.vars["Identificacion"].set("")
        self.vars["Nombre_Completo"].set("")
        self.vars["Direccion"].set("")
        self.vars["Telefono"].set("")

        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])

        if getattr(self, "ent_carnet", None) is not None:
            self.ent_carnet.state(["!readonly"])
            self.ent_carnet.focus_set()

        if self.tree:
            self.tree.selection_remove(self.tree.selection())

    def on_guardar(self):
        self.ensure_loaded()

        estado_desc = self.vars["Estado"].get().strip()
        if estado_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
            return

        try:
            crear_estudiante(
                self.db_user,
                self.db_pass,
                carnet=self.vars["Carnet"].get(),
                identificacion=self.vars["Identificacion"].get(),
                nombre_completo=self.vars["Nombre_Completo"].get(),
                direccion=self.vars["Direccion"].get(),
                telefono=self.vars["Telefono"].get(),
                estado_codigo=self.estado_desc_to_cod[estado_desc],
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo guardar el estudiante:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Estudiante guardado correctamente.")

    def on_actualizar(self):
        self.ensure_loaded()

        carnet = self._selected_carnet()
        if not carnet:
            messagebox.showwarning("Actualizar", "Seleccione un estudiante del listado para actualizar.")
            return

        estado_desc = self.vars["Estado"].get().strip()
        if estado_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
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
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo actualizar el estudiante:\n{e}")
            return

        self.refresh_grid()
        messagebox.showinfo("Éxito", "Estudiante actualizado correctamente.")

    def on_eliminar(self):
        self.ensure_loaded()

        carnet = self._selected_carnet()
        if not carnet:
            messagebox.showwarning("Eliminar", "Seleccione un estudiante del listado para eliminar.")
            return

        if not messagebox.askyesno("Confirmar", f"¿Eliminar el estudiante Carnet {carnet}?"):
            return

        try:
            eliminar_estudiante(self.db_user, self.db_pass, carnet)
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo eliminar el estudiante:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Estudiante eliminado correctamente.")