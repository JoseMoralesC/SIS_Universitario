from __future__ import annotations

import datetime as _dt
import tkinter as tk
from tkinter import ttk

from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.endpoints.mantenimiento.becados_endpoints import (
    get_lookups,
    listar_becados,
    siguiente_id_becado,
    crear_becado,
    actualizar_becado,
    eliminar_becado,
)
from app.core.error_handler import handle_exception, show_info, show_warning
from app.ui.components.confirm_dialog import show_confirm


class BecadosTab(MaintenanceTab):
    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.estudiante_display_to_carnet: dict[str, str] = {}
        self.carnet_to_estudiante_display: dict[str, str] = {}
        self.beca_display_to_id: dict[str, int] = {}
        self.id_to_beca_display: dict[int, str] = {}
        self.beca_id_to_pct: dict[int, int] = {}

        # Control de modo / originales para regla de fecha en Update
        self._mode: str = "new"  # "new" | "update"
        self._orig_id_beca: int | None = None
        self._orig_fecha: str | None = None
        self._orig_carnet: str | None = None
        self._orig_est_display: str | None = None

        self._loaded = False

        super().__init__(parent, "Becados")
        self.reset_view_blank()

    def ensure_loaded(self):
        if getattr(self, "_loaded", False):
            return
        self._load_lookups()
        self.refresh_grid()
        self._loaded = True

    def _ensure_vars(self):
        if not isinstance(getattr(self, "vars", None), dict):
            self.vars = {}
        self.vars.setdefault("id_becado", tk.StringVar())
        self.vars.setdefault("estudiante", tk.StringVar())
        self.vars.setdefault("carnet_view", tk.StringVar())  # only view
        self.vars.setdefault("beca", tk.StringVar())
        self.vars.setdefault("porcentaje", tk.StringVar())
        self.vars.setdefault("fecha_aplicacion", tk.StringVar())

    # -----------------------------
    # Helpers (fecha)
    # -----------------------------
    def _today(self) -> str:
        return _dt.date.today().isoformat()

    # -----------------------------
    # UI
    # -----------------------------
    def reset_view_blank(self):
        """
        Modo Nuevo:
        - ID auto (readonly)
        - Combos con estudiantes disponibles (no becados)
        - Carnet view en blanco hasta seleccionar
        - Fecha: hoy, readonly
        """
        self._ensure_vars()
        self._mode = "new"
        self._orig_id_beca = None
        self._orig_fecha = None
        self._orig_carnet = None
        self._orig_est_display = None

        self.vars["estudiante"].set("")
        self.vars["carnet_view"].set("")
        self.vars["beca"].set("")
        self.vars["porcentaje"].set("")
        self.vars["fecha_aplicacion"].set(self._today())

        self._load_next_id()

        # Cargar combos si ya existen widgets
        try:
            self._load_lookups()
        except Exception:
            pass

        # Fecha siempre readonly
        try:
            if hasattr(self, "entry_fecha"):
                self.entry_fecha.configure(state="readonly")
        except Exception:
            pass

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

        title = ttk.Label(parent, text="Asignación de Becas a Estudiantes", font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(parent, text="ID Registro:", font=lbl_font).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_id = ttk.Entry(parent, textvariable=self.vars["id_becado"], font=entry_font, state="readonly", width=18)
        self.entry_id.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Estudiante:", font=lbl_font).grid(row=2, column=0, sticky="w", pady=4)
        self.cbo_est = ttk.Combobox(parent, textvariable=self.vars["estudiante"], state="readonly")
        self.cbo_est.grid(row=2, column=1, sticky="ew", pady=4)
        self.cbo_est.bind("<<ComboboxSelected>>", self._on_estudiante_selected)

        ttk.Label(parent, text="Carnet:", font=lbl_font).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_carnet = ttk.Entry(parent, textvariable=self.vars["carnet_view"], font=entry_font, state="readonly", width=18)
        self.entry_carnet.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Tipo de Beca:", font=lbl_font).grid(row=4, column=0, sticky="w", pady=4)
        self.cbo_beca = ttk.Combobox(parent, textvariable=self.vars["beca"], state="readonly")
        self.cbo_beca.grid(row=4, column=1, sticky="ew", pady=4)
        self.cbo_beca.bind("<<ComboboxSelected>>", self._on_beca_selected)

        ttk.Label(parent, text="% Descuento:", font=lbl_font).grid(row=5, column=0, sticky="w", pady=4)
        self.entry_pct = ttk.Entry(parent, textvariable=self.vars["porcentaje"], font=entry_font, state="readonly", width=18)
        self.entry_pct.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Fecha Aplicación (YYYY-MM-DD):", font=lbl_font).grid(row=6, column=0, sticky="w", pady=4)
        self.entry_fecha = ttk.Entry(parent, textvariable=self.vars["fecha_aplicacion"], font=entry_font, state="readonly")
        self.entry_fecha.grid(row=6, column=1, sticky="ew", pady=4)

        parent.columnconfigure(1, weight=1)

    def _build_grid(self, parent: ttk.LabelFrame):
        cols = ("id_becado", "carnet", "estudiante", "beca", "fecha_aplicacion")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)

        self.tree.heading("id_becado", text="ID")
        self.tree.heading("carnet", text="Carnet")
        self.tree.heading("estudiante", text="Estudiante")
        self.tree.heading("beca", text="Beca")
        self.tree.heading("fecha_aplicacion", text="Fecha Aplicación")

        self.tree.column("id_becado", width=55, minwidth=45, anchor="center", stretch=False)
        self.tree.column("carnet", width=110, minwidth=90, anchor="center", stretch=False)
        self.tree.column("estudiante", width=210, minwidth=160, anchor="w", stretch=True)
        self.tree.column("beca", width=160, minwidth=120, anchor="w", stretch=True)
        self.tree.column("fecha_aplicacion", width=120, minwidth=110, anchor="center", stretch=False)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

        self.refresh_grid()

    # -----------------------------
    # Lookups
    # -----------------------------
    def _load_lookups(self):
        # ✅ FIX: no pasar codigo_usuario si endpoint no lo acepta
        data = get_lookups(self.db_user, self.db_pass)

        estudiantes = data.get("estudiantes") or []
        becas = data.get("becas") or []

        # estudiantes: [(carnet, nombre), ...]
        self.estudiante_display_to_carnet = {}
        self.carnet_to_estudiante_display = {}

        for r in estudiantes:
            carnet = str(r[0])
            nombre = str(r[1])
            display = nombre
            self.estudiante_display_to_carnet[display] = carnet
            self.carnet_to_estudiante_display[carnet] = display

        # becas: [(id_beca, nombre, pct), ...]
        self.beca_display_to_id = {}
        self.id_to_beca_display = {}
        self.beca_id_to_pct = {}

        for r in becas:
            id_beca = int(r[0])
            nombre_beca = str(r[1])
            try:
                pct = int(r[2])
            except Exception:
                pct = 0

            display = nombre_beca
            self.beca_display_to_id[display] = id_beca
            self.id_to_beca_display[id_beca] = display
            self.beca_id_to_pct[id_beca] = pct

        if hasattr(self, "cbo_est"):
            self.cbo_est["values"] = list(self.estudiante_display_to_carnet.keys())
        if hasattr(self, "cbo_beca"):
            self.cbo_beca["values"] = list(self.beca_display_to_id.keys())

    def _ensure_student_in_combo(self, carnet: str, nombre: str):
        carnet = (carnet or "").strip()
        nombre = (nombre or "").strip()
        if not carnet or not nombre:
            return

        display = nombre
        if display not in self.estudiante_display_to_carnet:
            self.estudiante_display_to_carnet[display] = carnet
        if carnet not in self.carnet_to_estudiante_display:
            self.carnet_to_estudiante_display[carnet] = display

        if hasattr(self, "cbo_est"):
            self.cbo_est["values"] = list(self.estudiante_display_to_carnet.keys())

    def _on_estudiante_selected(self, _evt=None):
        try:
            self._ensure_vars()
            est_disp = (self.vars["estudiante"].get() or "").strip()
            carnet = self.estudiante_display_to_carnet.get(est_disp, "")
            self.vars["carnet_view"].set(carnet)
        except Exception as e:
            handle_exception(self, e)

    def _on_beca_selected(self, _evt=None):
        try:
            self._ensure_vars()
            beca_display = (self.vars["beca"].get() or "").strip()
            if not beca_display:
                self.vars["porcentaje"].set("")
                return

            id_beca = self.beca_display_to_id.get(beca_display)
            if id_beca is None:
                self.vars["porcentaje"].set("")
                return

            pct = self.beca_id_to_pct.get(int(id_beca), 0)
            self.vars["porcentaje"].set(str(pct))

            # Regla Update: fecha cambia SOLO si cambia la beca
            if self._mode == "update" and self._orig_id_beca is not None:
                if int(id_beca) != int(self._orig_id_beca):
                    self.vars["fecha_aplicacion"].set(self._today())
                else:
                    if self._orig_fecha:
                        self.vars["fecha_aplicacion"].set(self._orig_fecha)

        except Exception as e:
            handle_exception(self, e)

    def _get_selected_ids(self) -> tuple[str, int]:
        est_disp = (self.vars["estudiante"].get() or "").strip()
        beca_disp = (self.vars["beca"].get() or "").strip()

        if not est_disp:
            raise ValueError("Debe seleccionar un estudiante.")
        if not beca_disp:
            raise ValueError("Debe seleccionar un tipo de beca.")

        carnet = self.estudiante_display_to_carnet.get(est_disp)
        if not carnet:
            raise ValueError("Estudiante inválido o no encontrado.")

        id_beca = self.beca_display_to_id.get(beca_disp)
        if id_beca is None:
            raise ValueError("Beca inválida o no encontrada.")

        return carnet, int(id_beca)

    # -----------------------------
    # Data
    # -----------------------------
    def refresh_grid(self):
        try:
            if self.tree is None:
                return

            # ✅ FIX: no pasar codigo_usuario si endpoint no lo acepta
            rows = listar_becados(self.db_user, self.db_pass)

            for item in self.tree.get_children():
                self.tree.delete(item)

            for r in rows:
                # esperado: (id_becado, carnet, nombre_est, id_beca, nombre_beca, pct, fecha)
                id_becado = r[0]
                carnet = r[1]
                nombre_est = r[2]
                nombre_beca = r[4]
                fecha = r[6] if len(r) > 6 else ""

                self.tree.insert("", "end", values=(id_becado, carnet, nombre_est, nombre_beca, fecha))

        except Exception as e:
            handle_exception(self, e)

    def _load_next_id(self):
        try:
            self._ensure_vars()
            # ✅ FIX: no pasar codigo_usuario si endpoint no lo acepta
            next_id = siguiente_id_becado(self.db_user, self.db_pass)
            self.vars["id_becado"].set(str(next_id))
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

            # vals = (id_becado, carnet, estudiante_nombre, beca_nombre, fecha_aplicacion)
            id_becado = str(vals[0])
            carnet = str(vals[1])
            estudiante_nombre = str(vals[2])
            beca_nombre = str(vals[3])
            fecha = str(vals[4])

            self._mode = "update"
            self._orig_fecha = fecha
            self._orig_carnet = carnet
            self._orig_est_display = estudiante_nombre
            self._orig_id_beca = self.beca_display_to_id.get(beca_nombre)

            # Asegurar estudiante (aunque ya esté becado)
            self._ensure_student_in_combo(carnet=carnet, nombre=estudiante_nombre)

            self.vars["id_becado"].set(id_becado)
            self.vars["estudiante"].set(estudiante_nombre)
            self.vars["carnet_view"].set(carnet)
            self.vars["beca"].set(beca_nombre)

            # ✅ FIX: porcentaje correcto desde lookup
            id_beca = self.beca_display_to_id.get(beca_nombre)
            pct = self.beca_id_to_pct.get(int(id_beca), 0) if id_beca is not None else 0
            self.vars["porcentaje"].set(str(pct))

            self.vars["fecha_aplicacion"].set(fecha)

            try:
                if hasattr(self, "entry_fecha"):
                    self.entry_fecha.configure(state="readonly")
            except Exception:
                pass

        except Exception as e:
            handle_exception(self, e)

    # -----------------------------
    # CRUD
    # -----------------------------
    def on_nuevo(self):
        self.reset_view_blank()

    def on_guardar(self):
        """
        Nuevo:
        - Fecha: hoy automática (readonly)
        - Estudiante solo de disponibles (no becados)
        """
        try:
            self._ensure_vars()
            carnet, id_beca = self._get_selected_ids()

            fecha = self._today()
            self.vars["fecha_aplicacion"].set(fecha)

            id_becado_txt = (self.vars["id_becado"].get() or "").strip()
            if not id_becado_txt.isdigit():
                show_warning(self, "Validación", "Debe presionar 'Nuevo' para generar el ID antes de guardar.")
                return

            ok = crear_becado(
                self.db_user,
                self.db_pass,
                int(id_becado_txt),
                carnet,
                int(id_beca),
                fecha,
            )
            if ok:
                show_info(self, "Éxito", "Beca asignada correctamente.")
                self.reset_view_blank()
        except Exception as e:
            handle_exception(self, e)

    def on_actualizar(self):
        """
        Update:
        - Si NO cambia la beca: mantener fecha original
        - Si cambia la beca: fecha = hoy
        """
        try:
            self._ensure_vars()

            if self._mode != "update":
                show_warning(self, "Validación", "Seleccione un registro del listado para actualizar.")
                return

            carnet, id_beca = self._get_selected_ids()

            if self._orig_id_beca is not None and int(id_beca) != int(self._orig_id_beca):
                fecha = self._today()
            else:
                fecha = (self._orig_fecha or "").strip() or self._today()

            self.vars["fecha_aplicacion"].set(fecha)

            id_becado_txt = (self.vars["id_becado"].get() or "").strip()
            if not id_becado_txt.isdigit():
                show_warning(self, "Validación", "ID inválido.")
                return

            ok = actualizar_becado(
                self.db_user,
                self.db_pass,
                int(id_becado_txt),
                carnet,
                int(id_beca),
                fecha,
            )
            if ok:
                show_info(self, "Éxito", "Registro actualizado correctamente.")
                self.refresh_grid()
                self.reset_view_blank()

        except Exception as e:
            handle_exception(self, e)

    def on_eliminar(self):
        try:
            self._ensure_vars()

            id_becado_txt = (self.vars["id_becado"].get() or "").strip()
            if not id_becado_txt.isdigit():
                show_warning(self, "Validación", "Seleccione un registro válido para eliminar.")
                return

            if not show_confirm(self, "Confirmar", "¿Deseas eliminar esta asignación de beca?"):
                return

            ok = eliminar_becado(self.db_user, self.db_pass, int(id_becado_txt))
            if ok:
                show_info(self, "Éxito", "Asignación eliminada correctamente.")
                self.reset_view_blank()
        except Exception as e:
            handle_exception(self, e)