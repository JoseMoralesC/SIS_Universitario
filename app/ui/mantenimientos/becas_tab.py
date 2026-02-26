from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.mantenimiento.becas_endpoints import (
    listar_becas,
    siguiente_id_beca,
    crear_beca,
    actualizar_beca,
    eliminar_beca,
)
from app.core.error_handler import handle_exception, show_info, show_warning
from app.ui.components.confirm_dialog import show_confirm


class BecasTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        self.db_user = db_user
        self.db_pass = db_pass
        self._loaded = False
        self.codigo_usuario = codigo_usuario

        super().__init__(parent, "Becas")
        self.reset_view_blank()

    def ensure_loaded(self):
        if getattr(self, "_loaded", False):
            return
        self.refresh_grid()
        self._loaded = True

    # -----------------------------
    # Helpers
    # -----------------------------
    def _ensure_vars(self):
        if not isinstance(getattr(self, "vars", None), dict):
            self.vars = {}
        self.vars.setdefault("id_beca", tk.StringVar())
        self.vars.setdefault("nombre_beca", tk.StringVar())
        self.vars.setdefault("porcentaje_descuento", tk.StringVar())

    # -----------------------------
    # UI
    # -----------------------------
    def reset_view_blank(self):
        self._ensure_vars()
        self.vars["nombre_beca"].set("")
        self.vars["porcentaje_descuento"].set("")
        self._load_next_id()
        self.refresh_grid()
        try:
            if self.tree is not None:
                self.tree.selection_remove(self.tree.selection())
        except Exception:
            pass

    def _build_form(self, parent: ttk.LabelFrame):
        self._ensure_vars()

        lbl_font = ("Segoe UI", 10)
        entry_font = ("Segoe UI", 10)

        title = ttk.Label(parent, text="Gestión de Tipos de Beca", font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(parent, text="ID Beca:", font=lbl_font).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_id = ttk.Entry(
            parent,
            textvariable=self.vars["id_beca"],
            font=entry_font,
            state="readonly",
            width=18,
        )
        self.entry_id.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Nombre Beca:", font=lbl_font).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_nombre = ttk.Entry(parent, textvariable=self.vars["nombre_beca"], font=entry_font)
        self.entry_nombre.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="% Descuento:", font=lbl_font).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_pct = ttk.Entry(parent, textvariable=self.vars["porcentaje_descuento"], font=entry_font, width=18)
        self.entry_pct.grid(row=3, column=1, sticky="ew", pady=4)

        parent.columnconfigure(1, weight=1)

    def _build_grid(self, parent: ttk.LabelFrame):
        self._ensure_vars()

        cols = ("id_beca", "nombre_beca", "porcentaje_descuento")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)

        self.tree.heading("id_beca", text="ID")
        self.tree.heading("nombre_beca", text="Nombre")
        self.tree.heading("porcentaje_descuento", text="%")

        self.tree.column("id_beca", width=90, anchor="center")
        self.tree.column("nombre_beca", width=280, anchor="w")
        self.tree.column("porcentaje_descuento", width=90, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

        self.refresh_grid()

    # -----------------------------
    # Data
    # -----------------------------
    def refresh_grid(self):
        try:
            if self.tree is None:
                return

            rows = listar_becas(self.db_user, self.db_pass)

            for item in self.tree.get_children():
                self.tree.delete(item)

            for r in rows:
                if isinstance(r, dict):
                    id_beca = r.get("id_beca")
                    nombre = r.get("nombre_beca")
                    pct = r.get("porcentaje_descuento")
                else:
                    id_beca, nombre, pct = r[0], r[1], r[2]

                self.tree.insert("", "end", values=(id_beca, nombre, pct))

        except Exception as e:
            handle_exception(self, e)

    def _load_next_id(self):
        try:
            self._ensure_vars()
            next_id = siguiente_id_beca(self.db_user, self.db_pass)
            self.vars["id_beca"].set(str(next_id))
        except Exception as e:
            handle_exception(self, e)

    def _on_row_selected(self, _evt=None):
        try:
            self._ensure_vars()
            if self.tree is None:
                return
            sel = self.tree.selection()
            if not sel:
                return
            vals = self.tree.item(sel[0], "values")
            if not vals:
                return

            self.vars["id_beca"].set(str(vals[0]))
            self.vars["nombre_beca"].set(str(vals[1]))
            self.vars["porcentaje_descuento"].set(str(vals[2]))
        except Exception as e:
            handle_exception(self, e)

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        self.reset_view_blank()

    def on_guardar(self):
        try:
            self._ensure_vars()
            nombre = (self.vars["nombre_beca"].get() or "").strip()
            pct_txt = (self.vars["porcentaje_descuento"].get() or "").strip()

            if not nombre:
                show_warning(self, "Validación", "Debe ingresar el nombre de la beca.")
                return

            if not pct_txt.isdigit():
                show_warning(self, "Validación", "El porcentaje debe ser un número entero.")
                return

            pct = int(pct_txt)
            if pct < 0 or pct > 100:
                show_warning(self, "Validación", "El porcentaje debe estar entre 0 y 100.")
                return

            # ✅ FIX: endpoint no recibe codigo_usuario (por ahora)
            ok = crear_beca(self.db_user, self.db_pass, nombre, str(pct))
            if ok:
                show_info(self, "Éxito", "Beca creada correctamente.")
                self.reset_view_blank()
        except Exception as e:
            handle_exception(self, e)

    def on_actualizar(self):
        try:
            self._ensure_vars()
            id_txt = (self.vars["id_beca"].get() or "").strip()
            if not id_txt.isdigit():
                show_warning(self, "Validación", "ID inválido.")
                return
            id_beca = int(id_txt)

            nombre = (self.vars["nombre_beca"].get() or "").strip()
            pct_txt = (self.vars["porcentaje_descuento"].get() or "").strip()

            if not nombre:
                show_warning(self, "Validación", "Debe ingresar el nombre de la beca.")
                return

            if not pct_txt.isdigit():
                show_warning(self, "Validación", "El porcentaje debe ser un número entero.")
                return

            pct = int(pct_txt)
            if pct < 0 or pct > 100:
                show_warning(self, "Validación", "El porcentaje debe estar entre 0 y 100.")
                return

            # ✅ FIX: endpoint no recibe codigo_usuario (por ahora)
            ok = actualizar_beca(self.db_user, self.db_pass, id_beca, nombre, pct)
            if ok:
                show_info(self, "Éxito", "Beca actualizada correctamente.")
                self.refresh_grid()
        except Exception as e:
            handle_exception(self, e)

    def on_eliminar(self):
        try:
            self._ensure_vars()
            id_txt = (self.vars["id_beca"].get() or "").strip()
            if not id_txt.isdigit():
                show_warning(self, "Validación", "ID inválido.")
                return
            id_beca = int(id_txt)

            if not show_confirm(self, "Confirmar", "¿Deseas eliminar esta beca?"):
                return

            # ✅ FIX: endpoint no recibe codigo_usuario (por ahora)
            ok = eliminar_beca(self.db_user, self.db_pass, id_beca)
            if ok:
                show_info(self, "Éxito", "Beca eliminada correctamente.")
                self.reset_view_blank()
        except Exception as e:
            handle_exception(self, e)