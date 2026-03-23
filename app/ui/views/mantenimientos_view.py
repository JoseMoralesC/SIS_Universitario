from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

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
    Contiene el Notebook (Inicio + CRUD tabs).
    """

    def __init__(self, parent, usuario: str | None, db_user: str, db_pass: str, codigo_usuario: int):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        # refs para background (evita garbage-collector)
        self._home_bg_original = None
        self._home_bg_photo = None
        self._home_bg_canvas = None

        self._build_ui()

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
                self._home_bg_canvas.create_image(0, 0, image=self._home_bg_photo, anchor="nw", tags="bg")
                self._home_bg_canvas.tag_lower("bg")
            except Exception:
                self._home_bg_canvas.configure(bg="#2b2b2b")
                self._home_bg_canvas.delete("bg")

        home_canvas.bind("<Configure>", _resize_home_bg)

        overlay = ttk.Frame(home_canvas)
        home_canvas.create_window((0, 0), window=overlay, anchor="nw")
        overlay.columnconfigure(0, weight=1)
        overlay.rowconfigure(0, weight=1)

        # =====================================================
        # Tabs CRUD
        # =====================================================
        self.tab_periodos = PeriodosTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
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

        # =====================================================
        # Orden de tabs
        # =====================================================
        self.notebook.add(self.tab_home, text="Inicio")
        self.notebook.add(self.tab_periodos, text="Períodos")
        self.notebook.add(self.tab_programas, text="Programas")
        self.notebook.add(self.tab_cursos, text="Cursos")
        self.notebook.add(self.tab_docentes, text="Docentes")
        self.notebook.add(self.tab_asignacion, text="Asignación")
        self.notebook.add(self.tab_estudiantes, text="Estudiantes")
        self.notebook.add(self.tab_becas, text="Becas")
        self.notebook.add(self.tab_becados, text="Becados")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, _evt=None):
        current = self.notebook.select()

        if current == str(self.tab_docentes):
            self.tab_docentes.ensure_loaded()
        elif current == str(self.tab_cursos):
            self.tab_cursos.ensure_loaded()
        elif current == str(self.tab_programas):
            self.tab_programas.ensure_loaded()
        elif current == str(self.tab_estudiantes):
            self.tab_estudiantes.ensure_loaded()
        elif current == str(self.tab_asignacion):
            self.tab_asignacion.ensure_loaded()
        elif current == str(self.tab_becados):
            self.tab_becados.ensure_loaded()
        elif current == str(self.tab_becas):
            self.tab_becas.ensure_loaded()
        elif current == str(self.tab_periodos):
            self.tab_periodos.ensure_loaded()

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
        try:
            self.tab_asignacion.ensure_loaded()
        except Exception:
            pass

        try:
            self.notebook.select(self.tab_asignacion)
        except Exception:
            pass