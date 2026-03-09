# app/ui/views/matriculas_materia_view.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.matriculas_materia.docente_materia_tab import DocenteMateriaTab
from app.ui.matriculas_materia.materia_horario_tab import MateriaHorarioTab
from app.ui.matriculas_materia.matricula_materia_tab import MatriculaMateriaTab


class MatriculasMateriaView(ttk.Frame):
    """
    View principal del módulo de Matrículas por Materia.

    Contiene las 3 tabs del Entregable #4:

    1) Docente ↔ Materia
    2) Materia ↔ Horario
    3) Estudiante ↔ Materia
    """

    def __init__(
        self,
        parent,
        usuario: str | None = None,
        db_user: str = "",
        db_pass: str = "",
        codigo_usuario: int = 0,
    ):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self._tabs_loaded = False

        self._build_ui()

    # =====================================================
    # UI
    # =====================================================

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        # Notebook principal
        self.notebook = ttk.Notebook(container)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # =====================================================
        # Tabs
        # =====================================================

        self.tab_docente_materia = DocenteMateriaTab(
            self.notebook,
            self.db_user,
            self.db_pass,
            self.codigo_usuario,
        )

        self.tab_materia_horario = MateriaHorarioTab(
            self.notebook,
            self.db_user,
            self.db_pass,
            self.codigo_usuario,
        )

        self.tab_matricula_materia = MatriculaMateriaTab(
            self.notebook,
            self.db_user,
            self.db_pass,
            self.codigo_usuario,
        )

        # =====================================================
        # Add tabs
        # =====================================================

        self.notebook.add(
            self.tab_docente_materia,
            text="Docentes por Materia",
        )

        self.notebook.add(
            self.tab_materia_horario,
            text="Horarios de Materia",
        )

        self.notebook.add(
            self.tab_matricula_materia,
            text="Matrícula por Materia",
        )

        # Evento cambio de tab
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # =====================================================
    # Lifecycle
    # =====================================================

    def ensure_loaded(self):
        """
        Carga inicial segura del módulo.
        """
        if self._tabs_loaded:
            return

        try:
            if hasattr(self.tab_docente_materia, "ensure_loaded"):
                self.tab_docente_materia.ensure_loaded()

            if hasattr(self.tab_materia_horario, "ensure_loaded"):
                self.tab_materia_horario.ensure_loaded()

            if hasattr(self.tab_matricula_materia, "ensure_loaded"):
                self.tab_matricula_materia.ensure_loaded()
        finally:
            self._tabs_loaded = True

    # =====================================================
    # Eventos
    # =====================================================

    def _on_tab_changed(self, event):
        try:
            tab = event.widget.nametowidget(event.widget.select())

            if hasattr(tab, "ensure_loaded"):
                tab.ensure_loaded()

        except Exception:
            pass