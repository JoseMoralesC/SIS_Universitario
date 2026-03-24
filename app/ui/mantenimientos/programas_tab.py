# app/ui/mantenimientos/programas_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.mantenimiento.programas_endpoints import (
    get_lookups,
    listar_programas,
    siguiente_curso_cod,
    crear_programa,
    actualizar_programa,
    eliminar_programa,
    obtener_jornadas_programa,
)

from app.core.error_handler import (
    handle_exception,
    show_info,
    show_warning,
)

from app.ui.components.confirm_dialog import show_confirm


class ProgramasTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.estado_desc_to_cod: dict[str, int] = {}
        self.estado_cod_to_desc: dict[int, str] = {}

        # Horario Tipo (cantidad de jornadas)
        self.horario_desc_to_id = {
            "1 jornada disponible": 1,
            "2 jornadas disponibles": 2,
            "3 jornadas disponibles": 3,
        }
        self.horario_id_to_desc = {v: k for k, v in self.horario_desc_to_id.items()}

        self._loaded = False

        super().__init__(parent, "Programas", resource_key="programas")
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
    # Helpers
    # ------------------------------------------------
    def _clear_grid(self):
        if not self.tree:
            return
        for it in self.tree.get_children():
            self.tree.delete(it)

    def _get_jornadas_ids(self) -> list[int]:
        ids: list[int] = []
        if self.vars["J_Mañana"].get():
            ids.append(1)
        if self.vars["J_Tarde"].get():
            ids.append(2)
        if self.vars["J_Noche"].get():
            ids.append(3)
        return ids

    def _set_jornadas_checks(self, jornadas_ids: list[int] | None):
        jornadas_ids = jornadas_ids or []
        self.vars["J_Mañana"].set(1 in jornadas_ids)
        self.vars["J_Tarde"].set(2 in jornadas_ids)
        self.vars["J_Noche"].set(3 in jornadas_ids)

    def _normalize_horario_desc(self, value: object) -> str:
        """
        Acepta que el repo/grilla traiga:
        - texto ("2 jornadas disponibles")
        - o número/str numérica (2 / "2")
        y lo convierte al texto exacto del combobox.
        """
        if value is None:
            return ""

        s = str(value).strip()

        # Si ya es una de las opciones del combo
        if s in self.horario_desc_to_id:
            return s

        # Si viene numérico: 1/2/3
        try:
            n = int(s)
            return self.horario_id_to_desc.get(n, "")
        except Exception:
            return ""

    # ------------------------------------------------
    # UI
    # ------------------------------------------------
    def _build_form(self, parent: ttk.LabelFrame):
        self.vars["Curso_Cod"] = tk.StringVar(value="")
        self.vars["Descripcion"] = tk.StringVar(value="")
        self.vars["Horario_Tipo"] = tk.StringVar(value="")
        self.vars["Precio_Matricula"] = tk.StringVar(value="")
        self.vars["Estado"] = tk.StringVar(value="")

        # Jornadas
        self.vars["J_Mañana"] = tk.BooleanVar(value=False)
        self.vars["J_Tarde"] = tk.BooleanVar(value=False)
        self.vars["J_Noche"] = tk.BooleanVar(value=False)

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

        ttk.Label(parent, text="Horario:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_horario = ttk.Combobox(
            parent,
            textvariable=self.vars["Horario_Tipo"],
            state="readonly",
            width=26,
        )
        self.cb_horario["values"] = list(self.horario_desc_to_id.keys())
        self.cb_horario.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

        ttk.Label(parent, text="Jornadas:").grid(row=r, column=0, sticky="w", pady=6)
        wrap = ttk.Frame(parent)
        wrap.grid(row=r, column=1, sticky="w", padx=(10, 0), pady=6)

        ttk.Checkbutton(wrap, text="Mañana", variable=self.vars["J_Mañana"]).grid(row=0, column=0, padx=(0, 10))
        ttk.Checkbutton(wrap, text="Tarde", variable=self.vars["J_Tarde"]).grid(row=0, column=1, padx=(0, 10))
        ttk.Checkbutton(wrap, text="Noche", variable=self.vars["J_Noche"]).grid(row=0, column=2)
        r += 1

        add_entry("Precio Matrícula", "Precio_Matricula")

        ttk.Label(parent, text="Estado:").grid(row=r, column=0, sticky="w", pady=6)
        self.cb_estado = ttk.Combobox(
            parent,
            textvariable=self.vars["Estado"],
            state="readonly",
            width=26,
        )
        self.cb_estado.grid(row=r, column=1, sticky="ew", padx=(10, 0), pady=6)
        r += 1

    # ------------------------------------------------
    # GRID
    # ------------------------------------------------
    def _build_grid(self, parent: ttk.LabelFrame):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        cols = ("ID", "Descripción", "Horario", "Precio", "Estado")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings")

        base_widths = {"ID": 60, "Descripción": 240, "Horario": 180, "Precio": 110, "Estado": 120}
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

    # ------------------------------------------------
    # DATA
    # ------------------------------------------------
    def reset_view_blank(self):
        self.vars["Curso_Cod"].set("")
        self.vars["Descripcion"].set("")
        self.vars["Horario_Tipo"].set("")
        self.vars["Precio_Matricula"].set("")
        self._set_jornadas_checks([])

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
            handle_exception(self, e, context="Cargar estados (Programas)")
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
            rows = listar_programas(self.db_user, self.db_pass, codigo_usuario=self.codigo_usuario)
        except Exception as e:
            handle_exception(self, e, context="Cargar programas")
            return

        for r in rows:
            horario_desc = self._normalize_horario_desc(r[2])
            self.tree.insert("", "end", values=(r[0], r[1], horario_desc, str(r[3]), r[4]))

    # ------------------------------------------------
    # SELECTION
    # ------------------------------------------------
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

        self.vars["Curso_Cod"].set(str(v[0]))
        self.vars["Descripcion"].set(str(v[1]))
        self.vars["Horario_Tipo"].set(self._normalize_horario_desc(v[2]))
        self.vars["Precio_Matricula"].set(str(v[3]))
        self.vars["Estado"].set(str(v[4]))

        # Cargar jornadas reales desde DB
        try:
            jornadas_ids = obtener_jornadas_programa(
                self.db_user,
                self.db_pass,
                int(v[0]),
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Cargar jornadas del programa")
            jornadas_ids = []
        self._set_jornadas_checks(jornadas_ids)

    # ------------------------------------------------
    # CRUD
    # ------------------------------------------------
    def on_nuevo(self):
        if not self.can_access():
            self._deny_action("access")
            return

        self.ensure_loaded()

        try:
            new_id = siguiente_curso_cod(self.db_user, self.db_pass, codigo_usuario=self.codigo_usuario)
            self.vars["Curso_Cod"].set(str(new_id))
        except Exception as e:
            handle_exception(self, e, context="Generar ID (Programas)")
            self.vars["Curso_Cod"].set("")

        self.vars["Descripcion"].set("")
        self.vars["Horario_Tipo"].set("")
        self.vars["Precio_Matricula"].set("")
        self._set_jornadas_checks([])

        if self.cb_estado["values"]:
            self.vars["Estado"].set(self.cb_estado["values"][0])
        else:
            self.vars["Estado"].set("")

        try:
            if self.tree:
                self.tree.selection_remove(self.tree.selection())
        except Exception:
            pass

    def on_guardar(self):
        if not self.can_create():
            self._deny_action("create")
            return

        self.ensure_loaded()

        id_txt = self.vars["Curso_Cod"].get().strip()
        if not id_txt.isdigit():
            show_warning(self, "Validación", "Debe presionar 'Nuevo' para generar el ID antes de guardar.")
            return

        estado_desc = self.vars["Estado"].get().strip()
        horario_desc = self.vars["Horario_Tipo"].get().strip()

        if estado_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        # Normalizar por si quedó "1"/"2"/"3"
        horario_desc = self._normalize_horario_desc(horario_desc)
        horario_id = self.horario_desc_to_id.get(horario_desc)
        jornadas_ids = self._get_jornadas_ids()

        try:
            crear_programa(
                self.db_user,
                self.db_pass,
                curso_cod=int(id_txt),
                descripcion=self.vars["Descripcion"].get(),
                horario_tipo_id=horario_id,
                jornadas_ids=jornadas_ids,
                precio_matricula=self.vars["Precio_Matricula"].get(),
                estado_codigo=self.estado_desc_to_cod[estado_desc],
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Guardar programa")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Programa guardado correctamente.")

    def on_actualizar(self):
        if not self.can_update():
            self._deny_action("update")
            return

        self.ensure_loaded()

        curso_cod = self._selected_id()
        if not curso_cod:
            show_warning(self, "Actualizar", "Seleccione un programa del listado para actualizar.")
            return

        estado_desc = self.vars["Estado"].get().strip()
        horario_desc = self.vars["Horario_Tipo"].get().strip()

        if estado_desc not in self.estado_desc_to_cod:
            show_warning(self, "Validación", "Estado inválido.")
            return

        horario_desc = self._normalize_horario_desc(horario_desc)
        horario_id = self.horario_desc_to_id.get(horario_desc)
        jornadas_ids = self._get_jornadas_ids()

        try:
            actualizar_programa(
                self.db_user,
                self.db_pass,
                curso_cod=curso_cod,
                descripcion=self.vars["Descripcion"].get(),
                horario_tipo_id=horario_id,
                jornadas_ids=jornadas_ids,
                precio_matricula=self.vars["Precio_Matricula"].get(),
                estado_codigo=self.estado_desc_to_cod[estado_desc],
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            handle_exception(self, e, context="Actualizar programa")
            return

        self.refresh_grid()
        show_info(self, "Éxito", "Programa actualizado correctamente.")

    def on_eliminar(self):
        if not self.can_delete():
            self._deny_action("delete")
            return

        self.ensure_loaded()

        curso_cod = self._selected_id()
        if not curso_cod:
            show_warning(self, "Eliminar", "Seleccione un programa del listado para eliminar.")
            return

        if not show_confirm(self, "Confirmar", f"¿Pasar a INACTIVO el programa ID {curso_cod}?"):
            return

        try:
            eliminar_programa(self.db_user, self.db_pass, curso_cod, codigo_usuario=self.codigo_usuario)
        except Exception as e:
            handle_exception(self, e, context="Eliminar programa")
            return

        self.refresh_grid()
        self.on_nuevo()
        show_info(self, "Éxito", "Programa pasado a INACTIVO correctamente.")