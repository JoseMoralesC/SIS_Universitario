from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

from app.core.error_handler import show_warning
from app.services.security.permission_service import (
    can_access_maintenance,
    can_access_module,
)
from app.ui.components.toast import Toast
from app.ui.mantenimientos.docentes_tab import DocentesTab
from app.ui.mantenimientos.cursos_tab import CursosTab
from app.ui.mantenimientos.estudiantes_tab import EstudiantesTab
from app.ui.mantenimientos.programas_tab import ProgramasTab
from app.ui.mantenimientos.becas_tab import BecasTab
from app.ui.mantenimientos.becados_tab import BecadosTab
from app.ui.mantenimientos.periodos_tab import PeriodosTab
from app.ui.mantenimientos.asignacion_tab import AsignacionTab


class MantenimientosView(ttk.Frame):
    """
    Módulo: Mantenimientos
    Contiene el Notebook (Inicio + tabs de mantenimiento).
    """

    def __init__(
        self,
        parent,
        usuario: str | None,
        db_user: str | None,
        db_pass: str | None,
        codigo_usuario: int,
    ):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        # refs para background (evita garbage-collector)
        self._home_bg_original = None
        self._home_bg_photo = None
        self._home_bg_canvas = None

        self._tabs_by_key: dict[str, ttk.Frame] = {}
        self._tab_order: list[tuple[str, str]] = []

        self._build_ui()

    # =====================================================
    # Permisos
    # =====================================================
    def _can_access_module(self) -> bool:
        return can_access_module("mantenimientos")

    def _can_access_tab(self, resource_key: str) -> bool:
        return can_access_maintenance(resource_key)

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # =====================================================
        # TAB: Inicio
        # =====================================================
        self.tab_home = ttk.Frame(self.notebook)

        Toast(
            parent=self,
            title="Panel de Mantenimientos",
            message=(
                "Administra la información del sistema de forma rápida y ordenada.\n\n"
                "• Selecciona una pestaña para ver su formulario y listado.\n"
                "• Los datos se cargan al ingresar a cada sección.\n"
                "• Usa Nuevo / Guardar / Actualizar / Eliminar según corresponda."
            ),
            duration_ms=7000,
            slide_in_from="right",
            slide_out_to="right",
            step=20,
            delay_ms=18,
        )

        home_canvas = tk.Canvas(self.tab_home, highlightthickness=0, bd=0)
        home_canvas.pack(fill="both", expand=True)
        self._home_bg_canvas = home_canvas

        self._home_bg_original = None
        try:
            from PIL import Image  # type: ignore

            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            assets_dir = os.path.join(app_dir, "assets")
            img_path = os.path.join(assets_dir, "background.png")

            if os.path.exists(img_path):
                self._home_bg_original = Image.open(img_path).convert("RGB")
            else:
                self._home_bg_original = None
        except Exception:
            self._home_bg_original = None

        def _resize_home_bg(event):
            if self._home_bg_canvas is None:
                return

            w, h = max(1, int(event.width)), max(1, int(event.height))

            if self._home_bg_original is None:
                self._home_bg_canvas.configure(bg="#2b2b2b")
                self._home_bg_canvas.delete("bg")
                return

            try:
                from PIL import ImageTk  # type: ignore

                resized = self._home_bg_original.resize((w, h))
                self._home_bg_photo = ImageTk.PhotoImage(resized)

                self._home_bg_canvas.delete("bg")
                self._home_bg_canvas.create_image(
                    0,
                    0,
                    image=self._home_bg_photo,
                    anchor="nw",
                    tags="bg",
                )
                self._home_bg_canvas.tag_lower("bg")
            except Exception:
                self._home_bg_canvas.configure(bg="#2b2b2b")
                self._home_bg_canvas.delete("bg")

        home_canvas.bind("<Configure>", _resize_home_bg)

        overlay = ttk.Frame(home_canvas)
        home_canvas.create_window((0, 0), window=overlay, anchor="nw")
        overlay.columnconfigure(0, weight=1)
        overlay.rowconfigure(0, weight=1)

        # Siempre existe el tab de inicio
        self.notebook.add(self.tab_home, text="Inicio")

        # Si por alguna razón se construyó la vista sin acceso de módulo,
        # no cargamos tabs funcionales.
        if not self._can_access_module():
            self._build_no_access_home(overlay)
            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
            return

        # =====================================================
        # Tabs CRUD / Mantenimientos
        # =====================================================
        self._create_tabs()
        self._add_allowed_tabs()

        # Si el rol tiene acceso al módulo pero no a ningún recurso concreto
        if not self._tab_order:
            self._build_no_sections_home(overlay)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_no_access_home(self, overlay: ttk.Frame):
        card = ttk.LabelFrame(overlay, text="Acceso restringido", padding=18)
        card.grid(row=0, column=0, padx=24, pady=24, sticky="nw")

        ttk.Label(
            card,
            text=(
                "Tu usuario no tiene permisos para acceder al módulo de Mantenimientos."
            ),
            justify="left",
        ).grid(row=0, column=0, sticky="w")

    def _build_no_sections_home(self, overlay: ttk.Frame):
        card = ttk.LabelFrame(overlay, text="Sin secciones disponibles", padding=18)
        card.grid(row=0, column=0, padx=24, pady=24, sticky="nw")

        ttk.Label(
            card,
            text=(
                "Tu rol puede ingresar al módulo, pero no tiene permisos de acceso "
                "a ninguna sección de mantenimiento disponible."
            ),
            justify="left",
        ).grid(row=0, column=0, sticky="w")

    def _create_tabs(self):
        self.tab_periodos = PeriodosTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.tab_programas = ProgramasTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.tab_cursos = CursosTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.tab_docentes = DocentesTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.tab_asignacion = AsignacionTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.tab_estudiantes = EstudiantesTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.tab_becas = BecasTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.tab_becados = BecadosTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )

        self._tabs_by_key = {
            "periodos": self.tab_periodos,
            "programas": self.tab_programas,
            "cursos": self.tab_cursos,
            "docentes": self.tab_docentes,
            "asignacion": self.tab_asignacion,
            "estudiantes": self.tab_estudiantes,
            "becas": self.tab_becas,
            "becados": self.tab_becados,
        }

    def _add_allowed_tabs(self):
        definitions = [
            ("periodos", "Períodos"),
            ("programas", "Programas"),
            ("cursos", "Cursos"),
            ("docentes", "Docentes"),
            ("asignacion", "Asignación"),
            ("estudiantes", "Estudiantes"),
            ("becas", "Becas"),
            ("becados", "Becados"),
        ]

        self._tab_order.clear()

        for key, label in definitions:
            if not self._can_access_tab(key):
                continue

            tab = self._tabs_by_key.get(key)
            if tab is None:
                continue

            self.notebook.add(tab, text=label)
            self._tab_order.append((key, label))

    def _ensure_tab_loaded(self, tab_widget):
        try:
            if hasattr(tab_widget, "ensure_loaded"):
                tab_widget.ensure_loaded()
        except Exception:
            pass

    def _on_tab_changed(self, _evt=None):
        current = self.notebook.select()

        for key, _label in self._tab_order:
            tab_widget = self._tabs_by_key.get(key)
            if tab_widget is not None and current == str(tab_widget):
                self._ensure_tab_loaded(tab_widget)
                return

    # =====================================================
    # Helpers públicos
    # =====================================================
    def select_home(self):
        try:
            self.notebook.select(self.tab_home)
        except Exception:
            pass

    def select_asignacion(self):
        """
        Muestra directamente el tab de Asignación Docentes
        reutilizando el módulo ya existente dentro de Mantenimientos.
        """
        if not self._can_access_module():
            show_warning(
                self,
                "Permisos",
                "No tienes permisos para acceder al módulo de Mantenimientos.",
            )
            return

        if not self._can_access_tab("asignacion"):
            show_warning(
                self,
                "Permisos",
                "No tienes permisos para acceder a Asignación.",
            )
            return

        try:
            self.tab_asignacion.ensure_loaded()
        except Exception:
            pass

        try:
            self.notebook.select(self.tab_asignacion)
        except Exception:
            pass