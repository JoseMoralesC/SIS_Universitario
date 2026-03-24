# app/ui/mantenimientos/base_tab.py
from __future__ import annotations

import tkinter as tk
import unicodedata
from tkinter import ttk, messagebox

from app.core.error_handler import show_warning
from app.services.security.permission_service import (
    get_maintenance_permissions_state,
)


class MaintenanceTab(ttk.Frame):
    """
    Tab genérico para Mantenimientos:
    - Izquierda: Formulario + botones CRUD
    - Derecha: Grid (Treeview)

    Además:
    - Centraliza validación visual de permisos CRUD.
    - Deshabilita acciones según permisos del recurso.
    - Mantiene compatibilidad con subclases actuales.
    """

    def __init__(self, parent, title: str, resource_key: str | None = None):
        super().__init__(parent)
        self.title = title
        self.resource_key = resource_key or self._normalize_resource_key(title)

        self.vars: dict[str, tk.StringVar] = {}
        self.tree: ttk.Treeview | None = None

        self.btn_nuevo: ttk.Button | None = None
        self.btn_guardar: ttk.Button | None = None
        self.btn_actualizar: ttk.Button | None = None
        self.btn_eliminar: ttk.Button | None = None

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

        self._build_ui()
        self.refresh_permissions()

    # -----------------------------
    # Helpers permisos
    # -----------------------------
    def _normalize_resource_key(self, value: object) -> str:
        text = str(value or "").strip().lower()
        if not text:
            return ""

        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.replace(" ", "_").replace("-", "_")

        aliases = {
            "programas": "programas",
            "cursos": "cursos",
            "docentes": "docentes",
            "estudiantes": "estudiantes",
            "becas": "becas",
            "becados": "becados",
            "periodos": "periodos",
            "periodos_academicos": "periodos",
            "periodo": "periodos",
            "asignacion": "asignacion",
            "asignaciones": "asignacion",
        }

        return aliases.get(text, text)

    def _safe_permissions_state(self) -> dict:
        try:
            state = get_maintenance_permissions_state(self.resource_key)
            if isinstance(state, dict) and state:
                return state
        except Exception:
            pass

        # fallback seguro si por alguna razón el servicio no responde
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
        """
        Relee el estado de permisos del recurso actual y actualiza botones/UI.
        """
        self.permissions_state = self._safe_permissions_state()
        self._apply_permissions_to_ui()

    def _apply_permissions_to_ui(self):
        access = bool(self.permissions_state.get("access", False))
        can_create = bool(self.permissions_state.get("create", False))
        can_update = bool(self.permissions_state.get("update", False))
        can_delete = bool(self.permissions_state.get("delete", False))

        if self.btn_nuevo is not None:
            self._set_button_enabled(self.btn_nuevo, access)

        if self.btn_guardar is not None:
            self._set_button_enabled(self.btn_guardar, access and can_create)

        if self.btn_actualizar is not None:
            self._set_button_enabled(self.btn_actualizar, access and can_update)

        if self.btn_eliminar is not None:
            self._set_button_enabled(self.btn_eliminar, access and can_delete)

        self._apply_form_access(access)

    def _apply_form_access(self, access: bool):
        """
        Si el usuario no tiene acceso al mantenimiento,
        deja el formulario y el grid en modo no interactivo.
        """
        if not hasattr(self, "left") or not hasattr(self, "right"):
            return

        try:
            self._set_children_state(self.left, enabled=access)
        except Exception:
            pass

        try:
            self._set_children_state(self.right, enabled=access)
        except Exception:
            pass

        # Reforzar estado final de botones según CRUD
        if access:
            self._apply_permissions_to_buttons_only()

    def _apply_permissions_to_buttons_only(self):
        access = bool(self.permissions_state.get("access", False))
        can_create = bool(self.permissions_state.get("create", False))
        can_update = bool(self.permissions_state.get("update", False))
        can_delete = bool(self.permissions_state.get("delete", False))

        if self.btn_nuevo is not None:
            self._set_button_enabled(self.btn_nuevo, access)

        if self.btn_guardar is not None:
            self._set_button_enabled(self.btn_guardar, access and can_create)

        if self.btn_actualizar is not None:
            self._set_button_enabled(self.btn_actualizar, access and can_update)

        if self.btn_eliminar is not None:
            self._set_button_enabled(self.btn_eliminar, access and can_delete)

    def _set_children_state(self, parent, *, enabled: bool):
        desired = "!disabled" if enabled else "disabled"

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
                        child.state((desired,))
                    else:
                        child.state(("disabled",))
                    continue

                if isinstance(child, ttk.Checkbutton) or isinstance(child, ttk.Radiobutton):
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

    def _set_button_enabled(self, button: ttk.Button, enabled: bool):
        try:
            if enabled:
                button.state(("!disabled",))
            else:
                button.state(("disabled",))
        except Exception:
            pass

    def _action_label(self, action_key: str) -> str:
        labels = {
            "access": "acceder",
            "create": "guardar",
            "update": "actualizar",
            "delete": "eliminar",
        }
        return labels.get(action_key, action_key)

    def _is_action_allowed(self, action_key: str) -> bool:
        if action_key == "access":
            return bool(self.permissions_state.get("access", False))
        if action_key == "create":
            return bool(self.permissions_state.get("access", False)) and bool(self.permissions_state.get("create", False))
        if action_key == "update":
            return bool(self.permissions_state.get("access", False)) and bool(self.permissions_state.get("update", False))
        if action_key == "delete":
            return bool(self.permissions_state.get("access", False)) and bool(self.permissions_state.get("delete", False))
        return False

    def _deny_action(self, action_key: str):
        accion = self._action_label(action_key)
        show_warning(
            self,
            "Permisos",
            f"No tienes permisos para {accion} en {self.title}.",
        )

    def can_access(self) -> bool:
        return self._is_action_allowed("access")

    def can_create(self) -> bool:
        return self._is_action_allowed("create")

    def can_update(self) -> bool:
        return self._is_action_allowed("update")

    def can_delete(self) -> bool:
        return self._is_action_allowed("delete")

    # -----------------------------
    #  UI base
    # -----------------------------
    def _build_ui(self):
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)

        self.left = ttk.LabelFrame(self, text="Formulario", padding=(12, 10))
        self.right = ttk.LabelFrame(self, text="Listado", padding=(10, 10))
        self.left.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=12)
        self.right.grid(row=0, column=1, sticky="nsew", padx=(8, 12), pady=12)

        self.left.columnconfigure(0, weight=0)
        self.left.columnconfigure(1, weight=1)

        # Subclases implementan campos y grid
        self._build_form(self.left)
        ttk.Separator(self.left).grid(row=99, column=0, columnspan=2, sticky="ew", pady=(14, 10))

        btns = ttk.Frame(self.left)
        btns.grid(row=100, column=0, columnspan=2, sticky="ew")
        btns.columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_nuevo = ttk.Button(btns, text="Nuevo", command=self._on_nuevo_click, width=12)
        self.btn_guardar = ttk.Button(btns, text="Guardar", command=self._on_guardar_click, width=12)
        self.btn_actualizar = ttk.Button(btns, text="Actualizar", command=self._on_actualizar_click, width=12)
        self.btn_eliminar = ttk.Button(btns, text="Eliminar", command=self._on_eliminar_click, width=12)

        self.btn_nuevo.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.btn_guardar.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        self.btn_actualizar.grid(row=0, column=2, sticky="ew", padx=8, pady=8)
        self.btn_eliminar.grid(row=0, column=3, sticky="ew", padx=8, pady=8)

        for i in range(4):
            btns.columnconfigure(i, weight=1, uniform="crud")

        self._build_grid(self.right)

    def _build_form(self, parent: ttk.LabelFrame):
        pass

    def _build_grid(self, parent: ttk.LabelFrame):
        pass

    # -----------------------------
    # Wrappers con validación
    # -----------------------------
    def _on_nuevo_click(self):
        if not self._is_action_allowed("access"):
            self._deny_action("access")
            return
        self.on_nuevo()

    def _on_guardar_click(self):
        if not self._is_action_allowed("create"):
            self._deny_action("create")
            return
        self.on_guardar()

    def _on_actualizar_click(self):
        if not self._is_action_allowed("update"):
            self._deny_action("update")
            return
        self.on_actualizar()

    def _on_eliminar_click(self):
        if not self._is_action_allowed("delete"):
            self._deny_action("delete")
            return
        self.on_eliminar()

    # -----------------------------
    #  Acciones (subclase)
    # -----------------------------
    def on_nuevo(self):
        pass

    def on_guardar(self):
        messagebox.showinfo("Guardar", f"[{self.title}] Pendiente de implementar en el CRUD real.")

    def on_actualizar(self):
        messagebox.showinfo("Actualizar", f"[{self.title}] Pendiente de implementar en el CRUD real.")

    def on_eliminar(self):
        messagebox.showinfo("Eliminar", f"[{self.title}] Pendiente de implementar en el CRUD real.")