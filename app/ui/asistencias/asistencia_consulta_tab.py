# app/ui/asistencias/asistencia_consulta_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry

from app.endpoints.asistencias import asistencias_endpoints as ep
from app.core.error_handler import (
    show_warning,
    show_info,
    handle_exception,
)
from app.core.session import get_session


class AsistenciaConsultaTab(ttk.Frame):
    """
    Tab de consulta de listas de asistencia.

    Reglas aplicadas:
    - ADMIN / REGISTRO / ADMINISTRADOR / OPERADOR:
      pueden consultar todo el contexto habilitado por negocio.
    - DOCENTE:
      solo consulta sus propias listas y su propio contexto académico.
    """

    def __init__(
        self,
        parent,
        db_user: str,
        db_pass: str,
        on_load_edit=None,
    ):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.on_load_edit = on_load_edit

        self.q_periodos: list[dict] = []
        self.q_cursos: list[dict] = []
        self.q_materias: list[dict] = []
        self.q_docentes: list[dict] = []

        self.consulta_rows: list[dict] = []

        self._session_data = get_session() or {}

        self._build_ui()
        self._apply_role_ui_rules()
        self._load_periodos_consulta()

    # =========================================================
    # Sesión / helpers de rol
    # =========================================================
    def _normalize_token(self, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().upper().replace(" ", "_").replace("-", "_")

    def _is_admin_like_session(self) -> bool:
        codigo_rol = self._normalize_token(self._session_data.get("codigo_rol"))
        descripcion_tipo = self._normalize_token(self._session_data.get("descripcion_tipo"))

        if codigo_rol in {"ADMIN", "REGISTRO"}:
            return True

        if descripcion_tipo in {"ADMINISTRADOR", "OPERADOR"}:
            return True

        return False

    def _is_docente_restringido_session(self) -> bool:
        if self._is_admin_like_session():
            return False

        codigo_rol = self._normalize_token(self._session_data.get("codigo_rol"))
        return codigo_rol == "DOCENTE"

    def _apply_role_ui_rules(self):
        """
        Ajustes visuales.
        La seguridad fuerte ya vive en service/endpoints.
        """
        if self._is_docente_restringido_session():
            self.q_cb_docente.configure(state="disabled")
        else:
            self.q_cb_docente.configure(state="readonly")

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # -----------------------------------------------------
        # Filtros consulta
        # -----------------------------------------------------
        filtros = ttk.LabelFrame(self, text="Filtros de Consulta")
        filtros.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        for i in range(8):
            filtros.columnconfigure(i, weight=1)

        ttk.Label(filtros, text="Período").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))
        self.q_cb_periodo = ttk.Combobox(filtros, state="readonly")
        self.q_cb_periodo.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.q_cb_periodo.bind("<<ComboboxSelected>>", self._on_q_periodo)

        ttk.Label(filtros, text="Curso").grid(row=0, column=1, sticky="w", padx=5, pady=(5, 0))
        self.q_cb_curso = ttk.Combobox(filtros, state="readonly")
        self.q_cb_curso.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.q_cb_curso.bind("<<ComboboxSelected>>", self._on_q_curso)

        ttk.Label(filtros, text="Materia").grid(row=0, column=2, sticky="w", padx=5, pady=(5, 0))
        self.q_cb_materia = ttk.Combobox(filtros, state="readonly")
        self.q_cb_materia.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        self.q_cb_materia.bind("<<ComboboxSelected>>", self._on_q_materia)

        ttk.Label(filtros, text="Docente").grid(row=0, column=3, sticky="w", padx=5, pady=(5, 0))
        self.q_cb_docente = ttk.Combobox(filtros, state="readonly")
        self.q_cb_docente.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        ttk.Label(filtros, text="Fecha desde").grid(row=0, column=4, sticky="w", padx=5, pady=(5, 0))
        self.q_fecha_desde_var = tk.StringVar()
        self.q_entry_fecha_desde = DateEntry(
            filtros,
            textvariable=self.q_fecha_desde_var,
            date_pattern="yyyy-mm-dd",
            state="readonly",
        )
        self.q_entry_fecha_desde.grid(row=1, column=4, sticky="ew", padx=5, pady=5)

        ttk.Label(filtros, text="Fecha hasta").grid(row=0, column=5, sticky="w", padx=5, pady=(5, 0))
        self.q_fecha_hasta_var = tk.StringVar()
        self.q_entry_fecha_hasta = DateEntry(
            filtros,
            textvariable=self.q_fecha_hasta_var,
            date_pattern="yyyy-mm-dd",
            state="readonly",
        )
        self.q_entry_fecha_hasta.grid(row=1, column=5, sticky="ew", padx=5, pady=5)

        ttk.Button(
            filtros,
            text="Buscar",
            command=self._buscar_listas,
        ).grid(row=1, column=6, padx=5, pady=5)

        ttk.Button(
            filtros,
            text="Limpiar",
            command=self._limpiar_filtros_consulta,
        ).grid(row=1, column=7, padx=5, pady=5)

        # -----------------------------------------------------
        # Grilla consulta
        # -----------------------------------------------------
        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        columnas = (
            "id",
            "fecha",
            "dia",
            "curso",
            "materia",
            "docente",
            "asistentes",
            "ausentes",
            "registrados",
            "pendientes",
        )

        self.grid_consulta = ttk.Treeview(
            grid_frame,
            columns=columnas,
            show="headings",
        )

        self.grid_consulta.heading("id", text="ID")
        self.grid_consulta.heading("fecha", text="Fecha")
        self.grid_consulta.heading("dia", text="Día")
        self.grid_consulta.heading("curso", text="Curso")
        self.grid_consulta.heading("materia", text="Materia")
        self.grid_consulta.heading("docente", text="Docente")
        self.grid_consulta.heading("asistentes", text="Asist.")
        self.grid_consulta.heading("ausentes", text="Aus.")
        self.grid_consulta.heading("registrados", text="Registrados")
        self.grid_consulta.heading("pendientes", text="Pendientes")

        self.grid_consulta.column("id", width=60, anchor="center")
        self.grid_consulta.column("fecha", width=100, anchor="center")
        self.grid_consulta.column("dia", width=100, anchor="center")
        self.grid_consulta.column("curso", width=180, anchor="w")
        self.grid_consulta.column("materia", width=220, anchor="w")
        self.grid_consulta.column("docente", width=220, anchor="w")
        self.grid_consulta.column("asistentes", width=70, anchor="center")
        self.grid_consulta.column("ausentes", width=70, anchor="center")
        self.grid_consulta.column("registrados", width=90, anchor="center")
        self.grid_consulta.column("pendientes", width=90, anchor="center")

        self.grid_consulta.grid(row=0, column=0, sticky="nsew")
        self.grid_consulta.bind("<<TreeviewSelect>>", self._on_select_consulta)
        self.grid_consulta.bind("<Double-1>", lambda e: self._ver_detalle_desde_consulta())

        sb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.grid_consulta.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.grid_consulta.configure(yscrollcommand=sb.set)

        # -----------------------------------------------------
        # Resumen selección
        # -----------------------------------------------------
        resumen = ttk.LabelFrame(self, text="Resumen de la Lista Seleccionada")
        resumen.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))

        for i in range(4):
            resumen.columnconfigure(i, weight=1)

        self.lbl_q_periodo = ttk.Label(resumen, text="Período: -")
        self.lbl_q_periodo.grid(row=0, column=0, sticky="w", padx=10, pady=6)

        self.lbl_q_curso = ttk.Label(resumen, text="Curso: -")
        self.lbl_q_curso.grid(row=0, column=1, sticky="w", padx=10, pady=6)

        self.lbl_q_materia = ttk.Label(resumen, text="Materia: -")
        self.lbl_q_materia.grid(row=0, column=2, sticky="w", padx=10, pady=6)

        self.lbl_q_docente = ttk.Label(resumen, text="Docente: -")
        self.lbl_q_docente.grid(row=0, column=3, sticky="w", padx=10, pady=6)

        self.lbl_q_fecha = ttk.Label(resumen, text="Fecha: -")
        self.lbl_q_fecha.grid(row=1, column=0, sticky="w", padx=10, pady=6)

        self.lbl_q_total = ttk.Label(resumen, text="Total grupo: -")
        self.lbl_q_total.grid(row=1, column=1, sticky="w", padx=10, pady=6)

        self.lbl_q_reg = ttk.Label(resumen, text="Registrados: -")
        self.lbl_q_reg.grid(row=1, column=2, sticky="w", padx=10, pady=6)

        self.lbl_q_pen = ttk.Label(resumen, text="Pendientes: -")
        self.lbl_q_pen.grid(row=1, column=3, sticky="w", padx=10, pady=6)

        # -----------------------------------------------------
        # Acciones consulta
        # -----------------------------------------------------
        acciones = ttk.Frame(self)
        acciones.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))

        ttk.Button(
            acciones,
            text="Ver detalle",
            command=self._ver_detalle_desde_consulta,
        ).pack(side="left", padx=5)

        ttk.Button(
            acciones,
            text="Cargar en edición",
            command=self._cargar_desde_consulta_a_edicion,
        ).pack(side="left", padx=5)

        ttk.Button(
            acciones,
            text="Refrescar resultados",
            command=self._buscar_listas,
        ).pack(side="left", padx=5)

    # =========================================================
    # Helpers
    # =========================================================
    def _set_combobox_by_item_id(self, combobox: ttk.Combobox, data: list[dict], item_id: int):
        values = [r["label"] for r in data]
        combobox["values"] = values

        for idx, item in enumerate(data):
            if int(item["id"]) == int(item_id):
                combobox.current(idx)
                return

        combobox.set("")

    def _try_autoselect_single(self, combobox: ttk.Combobox, rows: list[dict]) -> bool:
        if len(rows) == 1:
            combobox.current(0)
            return True
        return False

    def _clear_combo(self, combobox: ttk.Combobox, data_attr: str):
        setattr(self, data_attr, [])
        combobox.set("")
        combobox["values"] = []

    def _refresh_docente_combo_state(self):
        if self._is_docente_restringido_session():
            if len(self.q_docentes) == 1:
                self.q_cb_docente.current(0)
            self.q_cb_docente.configure(state="disabled")
        else:
            self.q_cb_docente.configure(state="readonly")

    # =========================================================
    # Consulta - loaders
    # =========================================================
    def _load_periodos_consulta(self):
        try:
            rows = ep.get_periodos_activos(self.db_user, self.db_pass)
            self.q_periodos = rows
            self.q_cb_periodo["values"] = [r["label"] for r in rows]

            if rows and self._is_docente_restringido_session():
                self.q_cb_periodo.current(0)
                self._on_q_periodo()

        except Exception as e:
            handle_exception(self, e, context="Cargar períodos de consulta")

    def _on_q_periodo(self, event=None):
        try:
            idx = self.q_cb_periodo.current()
            if idx < 0:
                self._clear_combo(self.q_cb_curso, "q_cursos")
                self._clear_combo(self.q_cb_materia, "q_materias")
                self._clear_combo(self.q_cb_docente, "q_docentes")
                return

            periodo_id = self.q_periodos[idx]["id"]

            rows = ep.get_cursos_por_periodo(
                self.db_user,
                self.db_pass,
                periodo_id,
            )

            self.q_cursos = rows
            self.q_cb_curso.set("")
            self.q_cb_materia.set("")
            self.q_cb_docente.set("")
            self.q_cb_curso["values"] = [r["label"] for r in rows]
            self.q_cb_materia["values"] = []
            self.q_cb_docente["values"] = []
            self.q_materias = []
            self.q_docentes = []

            if self._try_autoselect_single(self.q_cb_curso, rows):
                self._on_q_curso()

        except Exception as e:
            handle_exception(self, e, context="Cargar cursos de consulta")

    def _on_q_curso(self, event=None):
        try:
            if self.q_cb_periodo.current() < 0 or self.q_cb_curso.current() < 0:
                self._clear_combo(self.q_cb_materia, "q_materias")
                self._clear_combo(self.q_cb_docente, "q_docentes")
                return

            periodo_id = self.q_periodos[self.q_cb_periodo.current()]["id"]
            curso_cod = self.q_cursos[self.q_cb_curso.current()]["id"]

            rows = ep.get_materias_por_periodo_curso(
                self.db_user,
                self.db_pass,
                periodo_id,
                curso_cod,
            )

            self.q_materias = rows
            self.q_cb_materia.set("")
            self.q_cb_docente.set("")
            self.q_cb_materia["values"] = [r["label"] for r in rows]
            self.q_cb_docente["values"] = []
            self.q_docentes = []

            if self._try_autoselect_single(self.q_cb_materia, rows):
                self._on_q_materia()

        except Exception as e:
            handle_exception(self, e, context="Cargar materias de consulta")

    def _on_q_materia(self, event=None):
        try:
            if (
                self.q_cb_periodo.current() < 0
                or self.q_cb_curso.current() < 0
                or self.q_cb_materia.current() < 0
            ):
                self._clear_combo(self.q_cb_docente, "q_docentes")
                return

            periodo_id = self.q_periodos[self.q_cb_periodo.current()]["id"]
            curso_cod = self.q_cursos[self.q_cb_curso.current()]["id"]
            materia_cod = self.q_materias[self.q_cb_materia.current()]["id"]

            rows = ep.get_docentes_por_periodo_curso_materia(
                self.db_user,
                self.db_pass,
                periodo_id,
                curso_cod,
                materia_cod,
            )

            self.q_docentes = rows
            self.q_cb_docente.set("")
            self.q_cb_docente["values"] = [r["label"] for r in rows]
            self._refresh_docente_combo_state()

            if self._try_autoselect_single(self.q_cb_docente, rows):
                if self._is_docente_restringido_session():
                    self._buscar_listas(silent=True)

        except Exception as e:
            handle_exception(self, e, context="Cargar docentes de consulta")

    # =========================================================
    # Consulta - acciones
    # =========================================================
    def _buscar_listas(self, silent: bool = False):
        try:
            periodo_id = None
            curso_cod = None
            materia_cod = None
            docente_cod = None

            if self.q_cb_periodo.current() >= 0:
                periodo_id = self.q_periodos[self.q_cb_periodo.current()]["id"]

            if self.q_cb_curso.current() >= 0:
                curso_cod = self.q_cursos[self.q_cb_curso.current()]["id"]

            if self.q_cb_materia.current() >= 0:
                materia_cod = self.q_materias[self.q_cb_materia.current()]["id"]

            if self.q_cb_docente.current() >= 0:
                docente_cod = self.q_docentes[self.q_cb_docente.current()]["id"]

            rows = ep.search_listas_asistencia(
                self.db_user,
                self.db_pass,
                periodo_id=periodo_id,
                curso_cod=curso_cod,
                materia_cod=materia_cod,
                docente_cod=docente_cod,
                fecha_desde=self.q_fecha_desde_var.get().strip() or None,
                fecha_hasta=self.q_fecha_hasta_var.get().strip() or None,
                solo_activas=True,
            )

            self.consulta_rows = rows
            self.grid_consulta.delete(*self.grid_consulta.get_children())

            for item in rows:
                self.grid_consulta.insert(
                    "",
                    tk.END,
                    iid=str(item["asistencia_lista_id"]),
                    values=(
                        item["asistencia_lista_id"],
                        item["fecha_clase"],
                        item["dia_nombre"],
                        item["curso_desc"],
                        item["materia_desc"],
                        item["docente_nombre"],
                        item["total_asistentes"],
                        item["total_ausentes"],
                        item["total_registrados"],
                        item["pendientes"],
                    ),
                )

            self._clear_resumen_consulta()

            if not silent and not rows:
                show_info(self, "Consulta", "No se encontraron listas con los filtros indicados.")

        except Exception as e:
            handle_exception(self, e, context="Consultar listas")

    def buscar_listas(self, silent: bool = False):
        self._buscar_listas(silent=silent)

    def _limpiar_filtros_consulta(self):
        self.q_cb_periodo.set("")
        self.q_cb_curso.set("")
        self.q_cb_materia.set("")
        self.q_cb_docente.set("")

        self.q_cursos = []
        self.q_materias = []
        self.q_docentes = []

        self.q_cb_curso["values"] = []
        self.q_cb_materia["values"] = []
        self.q_cb_docente["values"] = []

        self.q_fecha_desde_var.set("")
        self.q_fecha_hasta_var.set("")

        self.grid_consulta.delete(*self.grid_consulta.get_children())
        self.consulta_rows = []
        self._clear_resumen_consulta()

        if self._is_docente_restringido_session() and self.q_periodos:
            self.q_cb_periodo.current(0)
            self._on_q_periodo()

    def _clear_resumen_consulta(self):
        self.lbl_q_periodo.config(text="Período: -")
        self.lbl_q_curso.config(text="Curso: -")
        self.lbl_q_materia.config(text="Materia: -")
        self.lbl_q_docente.config(text="Docente: -")
        self.lbl_q_fecha.config(text="Fecha: -")
        self.lbl_q_total.config(text="Total grupo: -")
        self.lbl_q_reg.config(text="Registrados: -")
        self.lbl_q_pen.config(text="Pendientes: -")

    def _get_selected_consulta_item(self) -> dict | None:
        sel = self.grid_consulta.selection()
        if not sel:
            return None

        item_id = int(sel[0])
        for row in self.consulta_rows:
            if int(row["asistencia_lista_id"]) == item_id:
                return row
        return None

    def _on_select_consulta(self, event=None):
        try:
            item = self._get_selected_consulta_item()
            if not item:
                self._clear_resumen_consulta()
                return

            self.lbl_q_periodo.config(text=f"Período: {item['periodo_label']}")
            self.lbl_q_curso.config(text=f"Curso: {item['curso_desc']}")
            self.lbl_q_materia.config(text=f"Materia: {item['materia_desc']}")
            self.lbl_q_docente.config(text=f"Docente: {item['docente_nombre']}")
            self.lbl_q_fecha.config(
                text=f"Fecha: {item['fecha_clase']} ({item['dia_nombre']})"
            )
            self.lbl_q_total.config(text=f"Total grupo: {item['total_grupo']}")
            self.lbl_q_reg.config(text=f"Registrados: {item['total_registrados']}")
            self.lbl_q_pen.config(text=f"Pendientes: {item['pendientes']}")

        except Exception as e:
            handle_exception(self, e, context="Seleccionar lista")

    def _ver_detalle_desde_consulta(self):
        try:
            item = self._get_selected_consulta_item()
            if not item:
                show_warning(self, "Consulta", "Debe seleccionar una lista.")
                return

            self._open_detalle_popup(item["asistencia_lista_id"])

        except Exception as e:
            handle_exception(self, e, context="Ver detalle")

    def _cargar_desde_consulta_a_edicion(self):
        item = self._get_selected_consulta_item()
        if not item:
            show_warning(self, "Consulta", "Debe seleccionar una lista.")
            return

        if callable(self.on_load_edit):
            self.on_load_edit(item)

    def apply_context_from_registro(
        self,
        periodo: dict,
        curso: dict,
        materia: dict,
        docente: dict,
        fecha: str,
    ):
        try:
            self._set_combobox_by_item_id(self.q_cb_periodo, self.q_periodos, periodo["id"])
            self._on_q_periodo()

            self._set_combobox_by_item_id(self.q_cb_curso, self.q_cursos, curso["id"])
            self._on_q_curso()

            self._set_combobox_by_item_id(self.q_cb_materia, self.q_materias, materia["id"])
            self._on_q_materia()

            self._set_combobox_by_item_id(self.q_cb_docente, self.q_docentes, docente["id"])
            self._refresh_docente_combo_state()

            self.q_fecha_desde_var.set(fecha)
            self.q_fecha_hasta_var.set(fecha)

            self._buscar_listas()

        except Exception as e:
            handle_exception(self, e, context="Ver listas del contexto")

    # =========================================================
    # Popup detalle
    # =========================================================
    def _open_detalle_popup(self, asistencia_lista_id: int):
        data = ep.get_asistencia_by_id(
            self.db_user,
            self.db_pass,
            asistencia_lista_id,
        )
        if not data:
            show_warning(self, "Consulta", "No se encontró la lista solicitada.")
            return

        resumen = ep.get_resumen_lista_asistencia(
            self.db_user,
            self.db_pass,
            asistencia_lista_id,
        )

        win = tk.Toplevel(self)
        win.title(f"Detalle Lista #{asistencia_lista_id}")
        win.transient(self.winfo_toplevel())
        win.grab_set()
        win.geometry("1000x560")
        win.minsize(900, 500)

        win.rowconfigure(2, weight=1)
        win.columnconfigure(0, weight=1)

        cab = data["cabecera"]

        top = ttk.LabelFrame(win, text="Encabezado")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        for i in range(4):
            top.columnconfigure(i, weight=1)

        ttk.Label(top, text=f"ID Lista: {cab['asistencia_lista_id']}").grid(
            row=0, column=0, sticky="w", padx=8, pady=6
        )
        ttk.Label(top, text=f"Período: {cab['periodo_label']}").grid(
            row=0, column=1, sticky="w", padx=8, pady=6
        )
        ttk.Label(top, text=f"Curso: {cab['curso_desc']}").grid(
            row=0, column=2, sticky="w", padx=8, pady=6
        )
        ttk.Label(top, text=f"Materia: {cab['materia_desc']}").grid(
            row=0, column=3, sticky="w", padx=8, pady=6
        )

        ttk.Label(top, text=f"Docente: {cab['docente_nombre']}").grid(
            row=1, column=0, sticky="w", padx=8, pady=6
        )
        ttk.Label(top, text=f"Día: {cab['dia_nombre']}").grid(
            row=1, column=1, sticky="w", padx=8, pady=6
        )
        ttk.Label(top, text=f"Fecha clase: {cab['fecha_clase']}").grid(
            row=1, column=2, sticky="w", padx=8, pady=6
        )
        ttk.Label(top, text=f"Fecha registro: {cab['fecha_registro']}").grid(
            row=1, column=3, sticky="w", padx=8, pady=6
        )

        mid = ttk.LabelFrame(win, text="Resumen")
        mid.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        for i in range(4):
            mid.columnconfigure(i, weight=1)

        ttk.Label(mid, text=f"Total grupo: {resumen['total_grupo'] if resumen else '-'}").grid(
            row=0, column=0, sticky="w", padx=8, pady=6
        )
        ttk.Label(mid, text=f"Asistentes: {resumen['total_asistentes'] if resumen else '-'}").grid(
            row=0, column=1, sticky="w", padx=8, pady=6
        )
        ttk.Label(mid, text=f"Ausentes: {resumen['total_ausentes'] if resumen else '-'}").grid(
            row=0, column=2, sticky="w", padx=8, pady=6
        )
        ttk.Label(mid, text=f"Pendientes: {resumen['pendientes'] if resumen else '-'}").grid(
            row=0, column=3, sticky="w", padx=8, pady=6
        )

        grid_frame = ttk.Frame(win)
        grid_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        columnas = ("carnet", "nombre", "estado", "observacion")
        tree = ttk.Treeview(grid_frame, columns=columnas, show="headings")

        tree.heading("carnet", text="Carnet")
        tree.heading("nombre", text="Nombre")
        tree.heading("estado", text="Estado")
        tree.heading("observacion", text="Observación")

        tree.column("carnet", width=120, anchor="center")
        tree.column("nombre", width=320, anchor="w")
        tree.column("estado", width=100, anchor="center")
        tree.column("observacion", width=260, anchor="w")

        detalle = sorted(data.get("detalle", []), key=lambda x: x["nombre"].lower())
        for row in detalle:
            tree.insert(
                "",
                tk.END,
                values=(
                    row["carnet"],
                    row["nombre"],
                    "Asistió" if row["estado_asistencia"] == "A" else "Ausente",
                    row.get("observacion") or "",
                ),
            )

        tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(grid_frame, orient="vertical", command=tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=sb.set)

        acciones = ttk.Frame(win)
        acciones.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        ttk.Button(
            acciones,
            text="Cargar en edición",
            command=lambda: self._cargar_popup_en_edicion(win, resumen or data["cabecera"]),
        ).pack(side="left", padx=5)

        ttk.Button(
            acciones,
            text="Cerrar",
            command=win.destroy,
        ).pack(side="right", padx=5)

    def _cargar_popup_en_edicion(self, popup: tk.Toplevel, item: dict):
        popup.destroy()

        if "periodo_id" in item and "curso_cod" in item:
            if callable(self.on_load_edit):
                self.on_load_edit(item)