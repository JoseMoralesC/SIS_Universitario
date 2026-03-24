# app/ui/mantenimientos/periodos_tab.py
from __future__ import annotations

import calendar as _cal
import datetime as _dt
import tkinter as tk
from tkinter import ttk

from app.core.error_handler import handle_exception, show_info, show_warning
from app.endpoints.mantenimiento import periodos_endpoints as p_ep
from app.services.security.permission_service import (
    get_maintenance_permissions_state,
)
from app.ui.components.confirm_dialog import show_confirm


class _CalendarPopup(tk.Toplevel):
    """
    Selector de fecha con calendario (sin dependencias externas).
    Devuelve la fecha en formato YYYY-MM-DD.
    """

    def __init__(self, parent: tk.Misc, title: str, on_pick):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_pick = on_pick

        today = _dt.date.today()
        self._year = today.year
        self._month = today.month

        self._build_ui()
        self._render()

        try:
            self.update_idletasks()
            px = parent.winfo_rootx() + 80
            py = parent.winfo_rooty() + 80
            self.geometry(f"+{px}+{py}")
        except Exception:
            pass

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.grid(row=0, column=0, sticky="nsew")

        hdr = ttk.Frame(root)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        ttk.Button(hdr, text="◀", width=4, command=self._prev_month).grid(row=0, column=0, sticky="w")
        self.lbl_month = ttk.Label(hdr, text="", anchor="center", font=("Segoe UI", 11, "bold"))
        self.lbl_month.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(hdr, text="▶", width=4, command=self._next_month).grid(row=0, column=2, sticky="e")

        self.grid_frame = ttk.Frame(root)
        self.grid_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        days = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]
        for c, d in enumerate(days):
            ttk.Label(
                self.grid_frame,
                text=d,
                anchor="center",
                width=4,
                font=("Segoe UI", 9, "bold"),
            ).grid(row=0, column=c, padx=2, pady=(0, 4))

        self._day_buttons: list[tk.Button] = []

        foot = ttk.Frame(root)
        foot.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        foot.columnconfigure(0, weight=1)
        ttk.Button(foot, text="Cerrar", command=self.destroy).grid(row=0, column=0, sticky="e")

    def _render(self):
        for b in self._day_buttons:
            try:
                b.destroy()
            except Exception:
                pass
        self._day_buttons.clear()

        month_name = _dt.date(self._year, self._month, 1).strftime("%B %Y").capitalize()
        self.lbl_month.configure(text=month_name)

        cal = _cal.Calendar(firstweekday=_cal.MONDAY)
        weeks = cal.monthdayscalendar(self._year, self._month)

        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.grid_frame, text="", width=4).grid(row=r, column=c, padx=2, pady=2)
                    continue

                d = _dt.date(self._year, self._month, day)

                btn = tk.Button(
                    self.grid_frame,
                    text=str(day),
                    width=4,
                    relief="groove",
                    bd=1,
                    font=("Segoe UI", 9),
                    cursor="hand2",
                    command=(lambda dd=d: self._pick(dd)),
                )
                btn.grid(row=r, column=c, padx=2, pady=2)
                self._day_buttons.append(btn)

    def _pick(self, d: _dt.date):
        try:
            self._on_pick(d)
        finally:
            self.destroy()

    def _prev_month(self):
        y, m = self._year, self._month
        if m == 1:
            y -= 1
            m = 12
        else:
            m -= 1
        self._year, self._month = y, m
        self._render()

    def _next_month(self):
        y, m = self._year, self._month
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
        self._year, self._month = y, m
        self._render()


class PeriodosTab(ttk.Frame):
    def __init__(
        self,
        parent,
        db_user: str | None,
        db_pass: str | None,
        codigo_usuario: int | None = None,
    ):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.resource_key = "periodos"

        self.vars: dict[str, tk.StringVar] = {}

        self._estado_display_to_cod: dict[str, int] = {}
        self._selected_periodo_id: int | None = None
        self._loaded = False

        self.permissions_state: dict = {
            "resource": self.resource_key,
            "is_admin": False,
            "access": True,
            "create": True,
            "update": True,
            "delete": True,
            "matched": {},
            "candidates": {},
        }

        self._btn_fecha_inicio: ttk.Button | None = None
        self._btn_fecha_fin: ttk.Button | None = None

        self._build_ui()
        self.refresh_permissions()
        self.reset_form()

    # =====================================================
    # Vars
    # =====================================================
    def _ensure_vars(self):
        self.vars.setdefault("periodo_codigo", tk.StringVar())
        self.vars.setdefault("anio", tk.StringVar())
        self.vars.setdefault("numero_periodo", tk.StringVar())
        self.vars.setdefault("fecha_inicio", tk.StringVar())
        self.vars.setdefault("fecha_fin", tk.StringVar())
        self.vars.setdefault("estado", tk.StringVar())

    # =====================================================
    # Permisos
    # =====================================================
    def _safe_permissions_state(self) -> dict:
        try:
            state = get_maintenance_permissions_state(self.resource_key)
            if isinstance(state, dict) and state:
                return state
        except Exception:
            pass

        return {
            "resource": self.resource_key,
            "is_admin": False,
            "access": True,
            "create": True,
            "update": True,
            "delete": True,
            "matched": {},
            "candidates": {},
        }

    def refresh_permissions(self):
        self.permissions_state = self._safe_permissions_state()
        self._apply_permissions_to_ui()

    def _is_action_allowed(self, action_key: str) -> bool:
        access = bool(self.permissions_state.get("access", False))
        create = bool(self.permissions_state.get("create", False))
        update = bool(self.permissions_state.get("update", False))
        delete = bool(self.permissions_state.get("delete", False))

        if action_key == "access":
            return access
        if action_key == "create":
            return access and create
        if action_key == "update":
            return access and update
        if action_key == "delete":
            return access and delete
        return False

    def _action_label(self, action_key: str) -> str:
        labels = {
            "access": "acceder",
            "create": "guardar",
            "update": "actualizar",
            "delete": "eliminar",
        }
        return labels.get(action_key, action_key)

    def _deny_action(self, action_key: str):
        accion = self._action_label(action_key)
        show_warning(
            self,
            "Permisos",
            f"No tienes permisos para {accion} en Períodos.",
        )

    def _set_button_enabled(self, button: ttk.Button | None, enabled: bool):
        if button is None:
            return
        try:
            if enabled:
                button.state(("!disabled",))
            else:
                button.state(("disabled",))
        except Exception:
            pass

    def _apply_permissions_to_ui(self):
        access = bool(self.permissions_state.get("access", False))
        can_create = bool(self.permissions_state.get("create", False))
        can_update = bool(self.permissions_state.get("update", False))
        can_delete = bool(self.permissions_state.get("delete", False))

        self._set_children_state(self.top, enabled=access)
        self._set_children_state(self.bottom, enabled=access)

        self._set_button_enabled(self.btn_nuevo, access)
        self._set_button_enabled(self.btn_guardar, access and can_create)
        self._set_button_enabled(self.btn_actualizar, access and can_update)
        self._set_button_enabled(self.btn_eliminar, access and can_delete)

        self._set_button_enabled(self._btn_fecha_inicio, access)
        self._set_button_enabled(self._btn_fecha_fin, access)

    def _set_children_state(self, parent, *, enabled: bool):
        for child in parent.winfo_children():
            try:
                if isinstance(child, ttk.Frame) or isinstance(child, ttk.LabelFrame):
                    self._set_children_state(child, enabled=enabled)
                    continue

                if isinstance(child, ttk.Treeview):
                    if enabled:
                        child.state(("!disabled",))
                    else:
                        child.state(("disabled",))
                    continue

                if isinstance(child, ttk.Label) or isinstance(child, ttk.Separator):
                    continue

                if isinstance(child, ttk.Entry):
                    states = set(child.state())
                    is_readonly = "readonly" in states
                    if enabled:
                        if is_readonly:
                            child.state(("readonly",))
                        else:
                            child.state(("!disabled",))
                    else:
                        child.state(("disabled",))
                    continue

                if isinstance(child, ttk.Combobox):
                    current_state = str(child.cget("state"))
                    if enabled:
                        if current_state == "readonly":
                            child.configure(state="readonly")
                        else:
                            child.configure(state="normal")
                    else:
                        child.configure(state="disabled")
                    continue

                if isinstance(child, ttk.Button):
                    if enabled:
                        child.state(("!disabled",))
                    else:
                        child.state(("disabled",))
                    continue

                try:
                    if enabled:
                        child.state(("!disabled",))
                    else:
                        child.state(("disabled",))
                except Exception:
                    pass

            except Exception:
                continue

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self._ensure_vars()

        # Layout principal: formulario arriba / grid abajo
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.top = ttk.LabelFrame(self, text="Formulario", padding=12)
        self.bottom = ttk.LabelFrame(self, text="Listado", padding=10)

        self.top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        self.bottom.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 12))

        self.top.columnconfigure(0, weight=1)
        self.bottom.columnconfigure(0, weight=1)
        self.bottom.rowconfigure(0, weight=1)

        # -------------------------------------------------
        # Formulario interno
        # -------------------------------------------------
        self.form_frame = ttk.LabelFrame(
            self.top,
            text="Período",
            padding=12,
        )
        self.form_frame.grid(row=0, column=0, sticky="ew")

        self.form_frame.columnconfigure(0, weight=0)
        self.form_frame.columnconfigure(1, weight=1)

        row = 0

        ttk.Label(self.form_frame, text="Año:").grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
        self.ent_anio = ttk.Entry(self.form_frame, textvariable=self.vars["anio"])
        self.ent_anio.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Label(self.form_frame, text="Número período:").grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
        self.cbo_numero_periodo = ttk.Combobox(
            self.form_frame,
            textvariable=self.vars["numero_periodo"],
            state="readonly",
            values=("1", "2", "3"),
        )
        self.cbo_numero_periodo.grid(row=row, column=1, sticky="ew", pady=4)
        self.cbo_numero_periodo.bind("<<ComboboxSelected>>", self._on_periodo_data_changed)
        row += 1

        ttk.Label(self.form_frame, text="Fecha inicio:").grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
        fecha_inicio_row = ttk.Frame(self.form_frame)
        fecha_inicio_row.grid(row=row, column=1, sticky="ew", pady=4)
        fecha_inicio_row.columnconfigure(0, weight=1)

        self.ent_fecha_inicio = ttk.Entry(
            fecha_inicio_row,
            textvariable=self.vars["fecha_inicio"],
            state="readonly",
        )
        self.ent_fecha_inicio.grid(row=0, column=0, sticky="ew")

        self._btn_fecha_inicio = ttk.Button(
            fecha_inicio_row,
            text="📅",
            width=3,
            command=self._open_fecha_inicio_calendar,
        )
        self._btn_fecha_inicio.grid(row=0, column=1, padx=(6, 0))
        row += 1

        ttk.Label(self.form_frame, text="Fecha fin:").grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
        fecha_fin_row = ttk.Frame(self.form_frame)
        fecha_fin_row.grid(row=row, column=1, sticky="ew", pady=4)
        fecha_fin_row.columnconfigure(0, weight=1)

        self.ent_fecha_fin = ttk.Entry(
            fecha_fin_row,
            textvariable=self.vars["fecha_fin"],
            state="readonly",
        )
        self.ent_fecha_fin.grid(row=0, column=0, sticky="ew")

        self._btn_fecha_fin = ttk.Button(
            fecha_fin_row,
            text="📅",
            width=3,
            command=self._open_fecha_fin_calendar,
        )
        self._btn_fecha_fin.grid(row=0, column=1, padx=(6, 0))
        row += 1

        ttk.Label(self.form_frame, text="Estado:").grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
        self.cbo_estado = ttk.Combobox(
            self.form_frame,
            textvariable=self.vars["estado"],
            state="readonly",
        )
        self.cbo_estado.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Label(self.form_frame, text="Código:").grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
        self.ent_periodo_codigo = ttk.Entry(
            self.form_frame,
            textvariable=self.vars["periodo_codigo"],
            state="readonly",
        )
        self.ent_periodo_codigo.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Separator(self.form_frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        btns = ttk.Frame(self.form_frame)
        btns.grid(row=row, column=0, columnspan=2, sticky="ew")

        for i in range(4):
            btns.columnconfigure(i, weight=1)

        self.btn_nuevo = ttk.Button(btns, text="Nuevo", command=self.on_nuevo)
        self.btn_guardar = ttk.Button(btns, text="Guardar", command=self.on_guardar)
        self.btn_actualizar = ttk.Button(btns, text="Actualizar", command=self.on_actualizar)
        self.btn_eliminar = ttk.Button(btns, text="Eliminar", command=self.on_eliminar)

        self.btn_nuevo.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self.btn_guardar.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        self.btn_actualizar.grid(row=0, column=2, sticky="ew", padx=6, pady=6)
        self.btn_eliminar.grid(row=0, column=3, sticky="ew", padx=6, pady=6)

        # -------------------------------------------------
        # Grid abajo
        # -------------------------------------------------
        cols = ("id", "codigo", "anio", "numero", "inicio", "fin", "estado")
        self.tree = ttk.Treeview(self.bottom, columns=cols, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("anio", text="Año")
        self.tree.heading("numero", text="Núm.")
        self.tree.heading("inicio", text="Fecha Inicio")
        self.tree.heading("fin", text="Fecha Fin")
        self.tree.heading("estado", text="Estado")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("codigo", width=100, anchor="center")
        self.tree.column("anio", width=80, anchor="center")
        self.tree.column("numero", width=80, anchor="center")
        self.tree.column("inicio", width=120, anchor="center")
        self.tree.column("fin", width=120, anchor="center")
        self.tree.column("estado", width=120, anchor="center")

        vsb = ttk.Scrollbar(self.bottom, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.bottom, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)
        self.ent_anio.bind("<KeyRelease>", self._on_periodo_data_changed)

    # =====================================================
    # Lifecycle
    # =====================================================
    def ensure_loaded(self):
        if not self._is_action_allowed("access"):
            self._loaded = True
            return

        if self._loaded:
            return

        self._load_lookups()
        self.refresh_grid()
        self._loaded = True

    # =====================================================
    # Load
    # =====================================================
    def _load_lookups(self):
        if not self._is_action_allowed("access"):
            return

        try:
            estados = p_ep.fetch_estados_periodos(self.db_user, self.db_pass)

            self._estado_display_to_cod = {}
            values: list[str] = []

            for cod, desc in estados:
                txt = str(desc)
                self._estado_display_to_cod[txt] = int(cod)
                values.append(txt)

            self.cbo_estado["values"] = values

            if "Activo" in self._estado_display_to_cod:
                self.vars["estado"].set("Activo")

        except Exception as e:
            handle_exception(self, e, context="Carga inicial Períodos")

    # =====================================================
    # Helpers
    # =====================================================
    def _update_periodo_codigo_preview(self):
        anio = (self.vars["anio"].get() or "").strip()
        numero = (self.vars["numero_periodo"].get() or "").strip()

        roman_map = {
            "1": "I",
            "2": "II",
            "3": "III",
        }

        if anio and numero in roman_map:
            self.vars["periodo_codigo"].set(f"{anio}-{roman_map[numero]}")
        else:
            self.vars["periodo_codigo"].set("")

    def _on_periodo_data_changed(self, _evt=None):
        self._update_periodo_codigo_preview()

    def _open_fecha_inicio_calendar(self):
        if not self._is_action_allowed("access"):
            self._deny_action("access")
            return

        def _set(d: _dt.date):
            self.vars["fecha_inicio"].set(d.isoformat())

        _CalendarPopup(self, "Seleccionar fecha de inicio", on_pick=_set)

    def _open_fecha_fin_calendar(self):
        if not self._is_action_allowed("access"):
            self._deny_action("access")
            return

        def _set(d: _dt.date):
            self.vars["fecha_fin"].set(d.isoformat())

        _CalendarPopup(self, "Seleccionar fecha final", on_pick=_set)

    # =====================================================
    # Grid
    # =====================================================
    def refresh_grid(self):
        if not self._is_action_allowed("access"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._selected_periodo_id = None
            return

        try:
            rows = p_ep.list_periodos_rows(
                self.db_user,
                self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )

            for item in self.tree.get_children():
                self.tree.delete(item)

            for r in rows:
                self.tree.insert("", "end", values=r)

            self._selected_periodo_id = None

        except Exception as e:
            handle_exception(self, e, context="Listado Períodos")

    def _on_row_selected(self, _evt=None):
        if not self._is_action_allowed("access"):
            self._selected_periodo_id = None
            return

        try:
            sel = self.tree.selection()
            if not sel:
                self._selected_periodo_id = None
                return

            vals = self.tree.item(sel[0], "values")
            if not vals:
                self._selected_periodo_id = None
                return

            self._selected_periodo_id = int(vals[0])

            self.vars["periodo_codigo"].set(str(vals[1]))
            self.vars["anio"].set(str(vals[2]))
            self.vars["numero_periodo"].set(str(vals[3]))
            self.vars["fecha_inicio"].set(str(vals[4]))
            self.vars["fecha_fin"].set(str(vals[5]))
            self.vars["estado"].set(str(vals[6]))

        except Exception:
            self._selected_periodo_id = None

    # =====================================================
    # Actions
    # =====================================================
    def on_nuevo(self):
        if not self._is_action_allowed("access"):
            self._deny_action("access")
            return

        self.reset_form()

    def on_guardar(self):
        if not self._is_action_allowed("create"):
            self._deny_action("create")
            return

        try:
            anio = (self.vars["anio"].get() or "").strip()
            numero_periodo = (self.vars["numero_periodo"].get() or "").strip()
            fecha_inicio = (self.vars["fecha_inicio"].get() or "").strip()
            fecha_fin = (self.vars["fecha_fin"].get() or "").strip()
            estado_desc = (self.vars["estado"].get() or "").strip()

            estado_codigo = self._estado_display_to_cod.get(estado_desc)
            if not estado_codigo:
                show_warning(self, "Validación", "Debes seleccionar un estado.")
                return

            msg = p_ep._create_periodo_impl(
                db_user=self.db_user,
                db_pass=self.db_pass,
                anio=int(anio),
                numero_periodo=int(numero_periodo),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado_codigo=int(estado_codigo),
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Períodos", msg)
            self.refresh_grid()
            self.reset_form()

        except Exception as e:
            handle_exception(self, e, context="Guardar Período")

    def on_actualizar(self):
        if not self._is_action_allowed("update"):
            self._deny_action("update")
            return

        try:
            if not self._selected_periodo_id:
                show_warning(self, "Validación", "Selecciona un período del listado.")
                return

            anio = (self.vars["anio"].get() or "").strip()
            numero_periodo = (self.vars["numero_periodo"].get() or "").strip()
            fecha_inicio = (self.vars["fecha_inicio"].get() or "").strip()
            fecha_fin = (self.vars["fecha_fin"].get() or "").strip()
            estado_desc = (self.vars["estado"].get() or "").strip()

            estado_codigo = self._estado_display_to_cod.get(estado_desc)
            if not estado_codigo:
                show_warning(self, "Validación", "Debes seleccionar un estado.")
                return

            msg = p_ep.update_periodo_endpoint(
                db_user=self.db_user,
                db_pass=self.db_pass,
                periodo_id=int(self._selected_periodo_id),
                anio=int(anio),
                numero_periodo=int(numero_periodo),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado_codigo=int(estado_codigo),
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Períodos", msg)
            self.refresh_grid()

        except Exception as e:
            handle_exception(self, e, context="Actualizar Período")

    def on_eliminar(self):
        if not self._is_action_allowed("delete"):
            self._deny_action("delete")
            return

        try:
            if not self._selected_periodo_id:
                show_warning(self, "Validación", "Selecciona un período del listado.")
                return

            ok = show_confirm(
                self,
                "Eliminar período",
                "¿Deseas desactivar el período seleccionado?",
                yes_text="Sí, desactivar",
                no_text="Cancelar",
            )
            if not ok:
                return

            msg = p_ep.delete_periodo_endpoint(
                db_user=self.db_user,
                db_pass=self.db_pass,
                periodo_id=int(self._selected_periodo_id),
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Períodos", msg)
            self.refresh_grid()
            self.reset_form()

        except Exception as e:
            handle_exception(self, e, context="Eliminar Período")

    # =====================================================
    # Reset
    # =====================================================
    def reset_form(self):
        self._selected_periodo_id = None

        self.vars["periodo_codigo"].set("")
        self.vars["anio"].set("")
        self.vars["numero_periodo"].set("")
        self.vars["fecha_inicio"].set("")
        self.vars["fecha_fin"].set("")

        if "Activo" in self._estado_display_to_cod:
            self.vars["estado"].set("Activo")
        else:
            self.vars["estado"].set("")

        if hasattr(self, "tree"):
            try:
                self.tree.selection_remove(self.tree.selection())
            except Exception:
                pass