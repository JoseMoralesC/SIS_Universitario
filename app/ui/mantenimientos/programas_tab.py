# app/ui/mantenimientos/programas_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

import tkinter.font as tkfont

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.programas_endpoints import (
    get_lookups,
    listar_programas,
    siguiente_curso_cod,
    crear_programa,
    actualizar_programa,
    eliminar_programa,
)
from app.services.programas_service import ValidationError


class ProgramasTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str):
        self.db_user = db_user
        self.db_pass = db_pass

        self.estado_desc_to_cod: dict[str, int] = {}
        self.estado_cod_to_desc: dict[int, str] = {}

        self._loaded = False

        super().__init__(parent, "Programas")
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
        self.vars["Curso_Cod"] = tk.StringVar(value="")
        self.vars["Descripcion"] = tk.StringVar(value="")
        self.vars["Horario"] = tk.StringVar(value="")
        self.vars["Precio_Matricula"] = tk.StringVar(value="")
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

        add_entry("ID", "Curso_Cod", readonly=True)
        add_entry("Descripción", "Descripcion")
        add_entry("Horario", "Horario")
        add_entry("Precio Matrícula", "Precio_Matricula")

        ttk.Label(parent, text="Estado:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_estado = ttk.Combobox(parent, textvariable=self.vars["Estado"], state="readonly", width=26)
        self.cb_estado.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

    def _build_grid(self, parent: ttk.LabelFrame):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        cols = ("ID", "Descripción", "Horario", "Precio", "Estado")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {"ID": 60, "Descripción": 240, "Horario": 140, "Precio": 110, "Estado": 100}
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
                max_w = min(max_w, 380)
            self.tree.column(col, width=max_w)

    # -----------------------------
    # blank/reset + data
    # -----------------------------
    def reset_view_blank(self):
        self.vars["Curso_Cod"].set("")
        self.vars["Descripcion"].set("")
        self.vars["Horario"].set("")
        self.vars["Precio_Matricula"].set("")
        try:
            self.cb_estado["values"] = []
        except Exception:
            pass
        self.vars["Estado"].set("")
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
            rows = listar_programas(self.db_user, self.db_pass)
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo cargar Programas:\n{e}")
            return

        for r in rows:
            # (Curso_Cod, Descripcion, Horario, Precio_Matricula, Estado_Desc)
            self.tree.insert("", "end", values=(r[0], r[1], r[2], str(r[3]), r[4]))

        self._autosize_columns()

    # -----------------------------
    # selection
    # -----------------------------
    def _selected_id(self) -> int | None:
        sel = self.tree.selection() if self.tree else []
        if not sel:
            return None
        values = self.tree.item(sel[0], "values")
        try:
            return int(values[0])
        except Exception:
            return None

    def on_row_select(self, _evt=None):
        sel = self.tree.selection() if self.tree else []
        if not sel:
            return
        v = self.tree.item(sel[0], "values")
        self.vars["Curso_Cod"].set(str(v[0]))
        self.vars["Descripcion"].set(str(v[1]))
        self.vars["Horario"].set("" if v[2] is None else str(v[2]))
        self.vars["Precio_Matricula"].set(str(v[3]))
        self.vars["Estado"].set(str(v[4]))

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        self.ensure_loaded()
        try:
            new_id = siguiente_curso_cod(self.db_user, self.db_pass)
            self.vars["Curso_Cod"].set(str(new_id))
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo obtener el siguiente ID:\n{e}")
            self.vars["Curso_Cod"].set("")

        self.vars["Descripcion"].set("")
        self.vars["Horario"].set("")
        self.vars["Precio_Matricula"].set("")
        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])

        if self.tree:
            self.tree.selection_remove(self.tree.selection())

    def on_guardar(self):
        self.ensure_loaded()

        id_txt = self.vars["Curso_Cod"].get().strip()
        if not id_txt.isdigit():
            messagebox.showwarning("Validación", "Debe presionar 'Nuevo' para generar el ID antes de guardar.")
            return

        estado_desc = self.vars["Estado"].get().strip()
        if estado_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
            return

        try:
            crear_programa(
                self.db_user,
                self.db_pass,
                curso_cod=int(id_txt),
                descripcion=self.vars["Descripcion"].get(),
                horario=self.vars["Horario"].get(),
                precio_matricula=self.vars["Precio_Matricula"].get(),
                estado_codigo=self.estado_desc_to_cod[estado_desc],
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo guardar el programa:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Programa guardado correctamente.")

    def on_actualizar(self):
        self.ensure_loaded()
        curso_cod = self._selected_id()
        if not curso_cod:
            messagebox.showwarning("Actualizar", "Seleccione un programa del listado para actualizar.")
            return

        estado_desc = self.vars["Estado"].get().strip()
        if estado_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
            return

        try:
            actualizar_programa(
                self.db_user,
                self.db_pass,
                curso_cod=curso_cod,
                descripcion=self.vars["Descripcion"].get(),
                horario=self.vars["Horario"].get(),
                precio_matricula=self.vars["Precio_Matricula"].get(),
                estado_codigo=self.estado_desc_to_cod[estado_desc],
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo actualizar el programa:\n{e}")
            return

        self.refresh_grid()
        messagebox.showinfo("Éxito", "Programa actualizado correctamente.")

    def on_eliminar(self):
        self.ensure_loaded()
        curso_cod = self._selected_id()
        if not curso_cod:
            messagebox.showwarning("Eliminar", "Seleccione un programa del listado para eliminar.")
            return

        if not messagebox.askyesno("Confirmar", f"¿Eliminar el programa ID {curso_cod}?"):
            return

        try:
            eliminar_programa(self.db_user, self.db_pass, curso_cod)
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo eliminar el programa:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Programa eliminado correctamente.")