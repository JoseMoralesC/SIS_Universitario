# app/ui/asistencias/asistencias_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.asistencias.asistencia_registro_tab import AsistenciaRegistroTab
from app.ui.asistencias.asistencia_consulta_tab import AsistenciaConsultaTab


class AsistenciasTab(ttk.Frame):
    """
    Contenedor principal del módulo de listas de asistencia.

    Tabs:
    1) Registrar / Editar
    2) Consultar listas
    """

    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self._build_ui()

    def _build_ui(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.tab_registro = AsistenciaRegistroTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
            on_open_consulta=self._abrir_consulta_desde_registro,
            on_refresh_consulta=self._refresh_consulta_silent,
        )

        self.tab_consulta = AsistenciaConsultaTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
            on_load_edit=self._cargar_en_edicion_desde_consulta,
        )

        self.notebook.add(self.tab_registro, text="Registrar / Editar")
        self.notebook.add(self.tab_consulta, text="Consultar listas")

    def _abrir_consulta_desde_registro(
        self,
        periodo: dict,
        curso: dict,
        materia: dict,
        docente: dict,
        fecha: str,
    ):
        self.notebook.select(self.tab_consulta)
        self.tab_consulta.apply_context_from_registro(
            periodo=periodo,
            curso=curso,
            materia=materia,
            docente=docente,
            fecha=fecha,
        )

    def _refresh_consulta_silent(self):
        try:
            self.tab_consulta.buscar_listas(silent=True)
        except Exception:
            pass

    def _cargar_en_edicion_desde_consulta(self, item: dict):
        self.tab_registro.load_context_and_edit(item)
        self.notebook.select(self.tab_registro)

    def ensure_loaded(self):
        """
        Mantiene compatibilidad si luego quieres usar carga diferida
        como en otros tabs del proyecto.
        """
        return