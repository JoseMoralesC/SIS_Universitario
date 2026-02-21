# app/ui/mantenimientos/cursos_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.cursos_endpoints import (
    get_lookups,
    listar_cursos,
    siguiente_materia_cod,
    crear_curso,
    actualizar_curso,
    eliminar_curso,
)
from app.services.cursos_service import ValidationError


class CursosTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str):
        self.db_user = db_user
        self.db_pass = db_pass

        # Lookups
        self.estado_desc_to_cod: dict[str, int] = {}
        self.estado_cod_to_desc: dict[int, str] = {}
        self.programa_desc_to_cod: dict[str, int] = {}
        self.programa_cod_to_desc: dict[int, str] = {}

        self._loaded = False

        super().__init__(parent, "Cursos")
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
        self.vars["Materia_Cod"] = tk.StringVar(value="")
        self.vars["Descripcion"] = tk.StringVar(value="")
        self.vars["Programa"] = tk.StringVar(value="")
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
        self.cb_programa = ttk.Combobox(parent, textvariable=self.vars["Programa"], state="readonly", width=26)
        self.cb_programa.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

        ttk.Label(parent, text="Estado:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_estado = ttk.Combobox(parent, textvariable=self.vars["Estado"], state="readonly", width=26)
        self.cb_estado.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

    def _build_grid(self, parent: ttk.LabelFrame):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        cols = ("ID", "Descripción", "Programa ID", "Programa", "Estado")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {"ID": 60, "Descripción": 260, "Programa ID": 80, "Programa": 220, "Estado": 100}
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
    # blank/reset + data
    # -----------------------------
    def reset_view_blank(self):
        self.vars["Materia_Cod"].set("")
        self.vars["Descripcion"].set("")

        try:
            self.cb_programa["values"] = []
            self.cb_estado["values"] = []
        except Exception:
            pass

        self.vars["Programa"].set("")
        self.vars["Estado"].set("")

        if self.tree:
            for it in self.tree.get_children():
                self.tree.delete(it)

    def _load_lookups(self):
        try:
            estados, programas = get_lookups(self.db_user, self.db_pass)
        except Exception as e:
            messagebox.showerror("DB", f"No se pudieron cargar catálogos:\n{e}")
            estados, programas = [], []

        self.estado_desc_to_cod = {desc: cod for cod, desc in estados}
        self.estado_cod_to_desc = {cod: desc for cod, desc in estados}
        self.programa_desc_to_cod = {desc: cod for cod, desc in programas}
        self.programa_cod_to_desc = {cod: desc for cod, desc in programas}

        self.cb_estado["values"] = list(self.estado_desc_to_cod.keys())
        self.cb_programa["values"] = list(self.programa_desc_to_cod.keys())

        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])
        if self.cb_programa["values"]:
            self.vars["Programa"].set(self.cb_programa["values"][0])

    def refresh_grid(self):
        if not self.tree:
            return
        for it in self.tree.get_children():
            self.tree.delete(it)

        try:
            rows = listar_cursos(self.db_user, self.db_pass)
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo cargar Cursos:\n{e}")
            return

        for r in rows:
            # (Materia_Cod, Materia_Desc, Curso_Cod, Programa_Desc, Estado_Desc)
            self.tree.insert(
                "",
                "end",
                values=(r[0], r[1], r[2], r[3], r[4])
            )

        self._autosize_columns()

    # -----------------------------
    # selection
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
        if not self.tree:
            return
        sel = self.tree.selection()
        if not sel:
            return

        v = self.tree.item(sel[0], "values")
        self.vars["Materia_Cod"].set(str(v[0]))
        self.vars["Descripcion"].set(str(v[1]))

        # v[2] es Programa ID, v[3] es Programa nombre
        self.vars["Programa"].set(str(v[3]))
        self.vars["Estado"].set(str(v[4]))

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        self.ensure_loaded()

        try:
            new_id = siguiente_materia_cod(self.db_user, self.db_pass)
            self.vars["Materia_Cod"].set(str(new_id))
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo obtener el siguiente ID:\n{e}")
            self.vars["Materia_Cod"].set("")

        self.vars["Descripcion"].set("")
        if self.cb_programa["values"]:
            self.vars["Programa"].set(self.cb_programa["values"][0])
        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])

        if self.tree:
            self.tree.selection_remove(self.tree.selection())

    def on_guardar(self):
        self.ensure_loaded()

        id_txt = self.vars["Materia_Cod"].get().strip()
        if not id_txt.isdigit():
            messagebox.showwarning("Validación", "Debe presionar 'Nuevo' para generar el ID antes de guardar.")
            return

        desc = self.vars["Descripcion"].get().strip()
        prog_desc = self.vars["Programa"].get().strip()
        est_desc = self.vars["Estado"].get().strip()

        if prog_desc not in self.programa_desc_to_cod:
            messagebox.showwarning("Validación", "Programa inválido.")
            return
        if est_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
            return

        try:
            crear_curso(
                self.db_user,
                self.db_pass,
                materia_cod=int(id_txt),
                descripcion=desc,
                curso_cod=self.programa_desc_to_cod[prog_desc],
                estado_codigo=self.estado_desc_to_cod[est_desc],
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo guardar el curso:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Curso guardado correctamente.")

    def on_actualizar(self):
        self.ensure_loaded()

        materia_cod = self._selected_id()
        if not materia_cod:
            messagebox.showwarning("Actualizar", "Seleccione un curso del listado para actualizar.")
            return

        desc = self.vars["Descripcion"].get().strip()
        prog_desc = self.vars["Programa"].get().strip()
        est_desc = self.vars["Estado"].get().strip()

        if prog_desc not in self.programa_desc_to_cod:
            messagebox.showwarning("Validación", "Programa inválido.")
            return
        if est_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
            return

        try:
            actualizar_curso(
                self.db_user,
                self.db_pass,
                materia_cod=materia_cod,
                descripcion=desc,
                curso_cod=self.programa_desc_to_cod[prog_desc],
                estado_codigo=self.estado_desc_to_cod[est_desc],
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo actualizar el curso:\n{e}")
            return

        self.refresh_grid()
        messagebox.showinfo("Éxito", "Curso actualizado correctamente.")

    def on_eliminar(self):
        self.ensure_loaded()

        materia_cod = self._selected_id()
        if not materia_cod:
            messagebox.showwarning("Eliminar", "Seleccione un curso del listado para eliminar.")
            return

        if not messagebox.askyesno("Confirmar", f"¿Eliminar el curso ID {materia_cod}?"):
            return

        try:
            eliminar_curso(self.db_user, self.db_pass, materia_cod)
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo eliminar el curso:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Curso eliminado correctamente.")