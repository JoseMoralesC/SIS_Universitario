# app/ui/mantenimientos/docentes_tab.py
from __future__ import annotations
import tkinter.font as tkfont
import tkinter as tk
from tkinter import ttk, messagebox



from app.endpoints.docentes_endpoints import (
    get_lookups,
    listar_docentes,
    crear_docente,
    actualizar_docente,
    eliminar_docente,
    siguiente_docente_cod,
)
from app.services.docentes_service import ValidationError

from app.ui.mantenimientos.base_tab import MaintenanceTab


class DocentesTab(MaintenanceTab):
    """
    CRUD REAL - Docentes (contra SQL Server)
    Lazy-load:
      - NO carga catálogos ni grid al crear el tab
      - Solo carga al entrar a la pestaña Docentes por primera vez
    """

    def __init__(self, parent, db_user: str, db_pass: str):
        self.db_user = db_user
        self.db_pass = db_pass

        # Lookups (desc->cod)
        self.estado_desc_to_cod: dict[str, int] = {}
        self.prof_desc_to_cod: dict[str, int] = {}

        # reverse (cod->desc)
        self.estado_cod_to_desc: dict[int, str] = {}
        self.prof_cod_to_desc: dict[int, str] = {}

        # lazy
        self._loaded = False

        super().__init__(parent, "Docentes")

        # deja todo en blanco 
        self.reset_view_blank()

    def ensure_loaded(self):
        """
        Carga catálogos + grid solo una vez (lazy-load).
        Lo llama main_menu cuando el usuario entra a la pestaña Docentes.
        """
        if getattr(self, "_loaded", False):
            return

        self._load_lookups()
        self.refresh_grid()
        self._loaded = True


    # -----------------------------
    #  UI
    # -----------------------------
    def _build_form(self, parent: ttk.LabelFrame):
        self.vars["Docente_Cod"] = tk.StringVar(value="")
        self.vars["Identificacion"] = tk.StringVar(value="")
        self.vars["Usuario_Docente"] = tk.StringVar(value="")
        self.vars["Nombre_Completo"] = tk.StringVar(value="")

        self.vars["Profesion"] = tk.StringVar(value="")
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

        add_entry("ID", "Docente_Cod", readonly=True)
        add_entry("Identificación", "Identificacion")
        add_entry("Usuario Docente", "Usuario_Docente")
        add_entry("Nombre Completo", "Nombre_Completo")

        ttk.Label(parent, text="Profesión:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_prof = ttk.Combobox(parent, textvariable=self.vars["Profesion"], state="readonly", width=26)
        self.cb_prof.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

        ttk.Label(parent, text="Estado:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_estado = ttk.Combobox(parent, textvariable=self.vars["Estado"], state="readonly", width=26)
        self.cb_estado.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

    def _build_grid(self, parent: ttk.LabelFrame):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        cols = ("ID", "Identificación", "Usuario", "Nombre", "Estado", "Profesión")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {
            "ID": 60,
            "Identificación": 130,
            "Usuario": 100,
            "Nombre": 150,
            "Estado": 70,
            "Profesión": 100,
        }

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(
                c,
                width=base_widths.get(c, 140),
                anchor="w",
                stretch=True
            )

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    # -----------------------------
    #  Lazy blank/reset
    # -----------------------------
    def reset_view_blank(self):
        self.vars["Docente_Cod"].set("")
        self.vars["Identificacion"].set("")
        self.vars["Usuario_Docente"].set("")
        self.vars["Nombre_Completo"].set("")

        # combos sin valores (no DB)
        try:
            self.cb_estado["values"] = []
            self.cb_prof["values"] = []
        except Exception:
            pass
        self.vars["Estado"].set("")
        self.vars["Profesion"].set("")

        # grid vacío
        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)

        

    # -----------------------------
    #  Data loading
    # -----------------------------
    def _load_lookups(self):
        try:
            estados, profes = get_lookups(self.db_user, self.db_pass)
        except Exception as e:
            messagebox.showerror("DB", f"No se pudieron cargar catálogos (Estado/Profesión):\n{e}")
            estados, profes = [], []

        self.estado_desc_to_cod = {desc: cod for cod, desc in estados}
        self.estado_cod_to_desc = {cod: desc for cod, desc in estados}
        self.prof_desc_to_cod = {desc: cod for cod, desc in profes}
        self.prof_cod_to_desc = {cod: desc for cod, desc in profes}

        self.cb_estado["values"] = list(self.estado_desc_to_cod.keys())
        self.cb_prof["values"] = list(self.prof_desc_to_cod.keys())

        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])
        if self.cb_prof["values"]:
            self.vars["Profesion"].set(self.cb_prof["values"][0])

    def refresh_grid(self):
        if not self.tree:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            rows = listar_docentes(self.db_user, self.db_pass)
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo cargar Docentes:\n{e}")
            return

        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], r[5]))

        self._autosize_columns()    

    def _autosize_columns(self):
        if not self.tree:
            return

        font = tkfont.nametofont("TkDefaultFont")

        for col in self.tree["columns"]:
            
            max_width = font.measure(col) + 20

            # recorrer filas
            for item in self.tree.get_children():
                value = self.tree.set(item, col)
                width = font.measure(str(value)) + 20
                if width > max_width:
                    max_width = width

            
            if col == "ID":
                max_width = min(max_width, 70)   
            elif col == "Estado":
                max_width = min(max_width, 100)
            else:
                max_width = min(max_width, 350)  

            self.tree.column(col, width=max_width)        

    # -----------------------------
    #  Selections
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
        values = self.tree.item(sel[0], "values")
        self.vars["Docente_Cod"].set(str(values[0]))
        self.vars["Identificacion"].set(str(values[1]))
        self.vars["Usuario_Docente"].set(str(values[2]))
        self.vars["Nombre_Completo"].set(str(values[3]))
        self.vars["Estado"].set(str(values[4]))
        self.vars["Profesion"].set(str(values[5]))

    # -----------------------------
    #  CRUD actions
    # -----------------------------
    def on_nuevo(self):
        self.ensure_loaded()

        try:
            new_id = siguiente_docente_cod(self.db_user, self.db_pass)
            self.vars["Docente_Cod"].set(str(new_id))
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo obtener el siguiente ID de docente:\n{e}")
            self.vars["Docente_Cod"].set("")

        self.vars["Identificacion"].set("")
        self.vars["Usuario_Docente"].set("")
        self.vars["Nombre_Completo"].set("")

        # mantener default de combos
        if getattr(self, "cb_estado", None) is not None and self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])
        if getattr(self, "cb_prof", None) is not None and self.cb_prof["values"]:
            self.vars["Profesion"].set(self.cb_prof["values"][0])

        if self.tree:
            self.tree.selection_remove(self.tree.selection())

    def on_guardar(self):
        # asegurar que catálogos estén cargados
        self.ensure_loaded()

        identificacion = self.vars["Identificacion"].get().strip()
        usuario_doc = self.vars["Usuario_Docente"].get().strip()
        nombre = self.vars["Nombre_Completo"].get().strip()
        estado_desc = self.vars["Estado"].get().strip()
        prof_desc = self.vars["Profesion"].get().strip()
        docente_cod_txt = self.vars["Docente_Cod"].get().strip()
        if not docente_cod_txt.isdigit():
            messagebox.showwarning("Validación", "Debe presionar 'Nuevo' para generar el ID antes de guardar.")
            return

        docente_cod = int(docente_cod_txt)

        if not identificacion or not usuario_doc or not nombre:
            messagebox.showwarning("Validación", "Debe completar: Identificación, Usuario Docente y Nombre Completo.")
            return

        if estado_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
            return
        if prof_desc not in self.prof_desc_to_cod:
            messagebox.showwarning("Validación", "Profesión inválida.")
            return

        try:
            crear_docente(
                self.db_user,
                self.db_pass,
                docente_cod=docente_cod,
                identificacion=identificacion,
                usuario_docente=usuario_doc,
                nombre_completo=nombre,
                estado_codigo=self.estado_desc_to_cod[estado_desc],
                profesion_cod=self.prof_desc_to_cod[prof_desc],
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo guardar el docente:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Docente guardado correctamente.")

    def on_actualizar(self):
        self.ensure_loaded()

        docente_id = self._selected_id()
        if not docente_id:
            messagebox.showwarning("Actualizar", "Seleccione un docente del listado para actualizar.")
            return

        identificacion = self.vars["Identificacion"].get().strip()
        usuario_doc = self.vars["Usuario_Docente"].get().strip()
        nombre = self.vars["Nombre_Completo"].get().strip()
        estado_desc = self.vars["Estado"].get().strip()
        prof_desc = self.vars["Profesion"].get().strip()

        if not identificacion or not usuario_doc or not nombre:
            messagebox.showwarning("Validación", "Debe completar: Identificación, Usuario Docente y Nombre Completo.")
            return
        if estado_desc not in self.estado_desc_to_cod:
            messagebox.showwarning("Validación", "Estado inválido.")
            return
        if prof_desc not in self.prof_desc_to_cod:
            messagebox.showwarning("Validación", "Profesión inválida.")
            return

        try:
            actualizar_docente(
                self.db_user,
                self.db_pass,
                docente_cod=docente_id,
                identificacion=identificacion,
                usuario_docente=usuario_doc,
                nombre_completo=nombre,
                estado_codigo=self.estado_desc_to_cod[estado_desc],
                profesion_cod=self.prof_desc_to_cod[prof_desc],
            )
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo actualizar el docente:\n{e}")
            return

        self.refresh_grid()
        messagebox.showinfo("Éxito", "Docente actualizado correctamente.")

    def on_eliminar(self):
        self.ensure_loaded()

        docente_id = self._selected_id()
        if not docente_id:
            messagebox.showwarning("Eliminar", "Seleccione un docente del listado para eliminar.")
            return

        if not messagebox.askyesno("Confirmar", f"¿Eliminar el docente ID {docente_id}?"):
            return

        try:
            eliminar_docente(self.db_user, self.db_pass, docente_id)
        except ValidationError as ve:
            messagebox.showwarning("Validación", str(ve))
            return
        except Exception as e:
            messagebox.showerror("DB", f"No se pudo eliminar el docente:\n{e}")
            return

        self.refresh_grid()
        self.on_nuevo()
        messagebox.showinfo("Éxito", "Docente eliminado correctamente.")