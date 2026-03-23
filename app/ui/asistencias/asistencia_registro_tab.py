# app/ui/asistencias/asistencia_registro_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import date, datetime

from app.endpoints.asistencias import asistencias_endpoints as ep
from app.core.error_handler import (
    show_warning,
    show_info,
    handle_exception,
)
from app.ui.components.confirm_dialog import show_confirm


class AsistenciaRegistroTab(ttk.Frame):
    """
    Tab de registro / edición de listas de asistencia.
    """

    def __init__(
        self,
        parent,
        db_user: str,
        db_pass: str,
        codigo_usuario: int,
        on_open_consulta=None,
        on_refresh_consulta=None,
    ):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario
        self.on_open_consulta = on_open_consulta
        self.on_refresh_consulta = on_refresh_consulta

        self.periodos: list[dict] = []
        self.cursos: list[dict] = []
        self.materias: list[dict] = []
        self.docentes: list[dict] = []

        self.estudiantes: list[dict] = []
        self.asistentes: list[str] = []
        self.ausentes: list[str] = []
        self.current_asistencia_lista_id: int | None = None

        self._build_ui()
        self._load_periodos()
        self._set_fecha_hoy()
        self._refresh_lbl_dia()
        self._refresh_resumen_registro()

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self):
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # -----------------------------------------------------
        # Filtros académicos
        # -----------------------------------------------------
        filtros = ttk.LabelFrame(self, text="Datos de la Lista")
        filtros.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        for i in range(8):
            filtros.columnconfigure(i, weight=1)

        ttk.Label(filtros, text="Período").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))
        self.cb_periodo = ttk.Combobox(filtros, state="readonly")
        self.cb_periodo.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.cb_periodo.bind("<<ComboboxSelected>>", self._on_periodo)

        ttk.Label(filtros, text="Curso").grid(row=0, column=1, sticky="w", padx=5, pady=(5, 0))
        self.cb_curso = ttk.Combobox(filtros, state="readonly")
        self.cb_curso.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.cb_curso.bind("<<ComboboxSelected>>", self._on_curso)

        ttk.Label(filtros, text="Materia").grid(row=0, column=2, sticky="w", padx=5, pady=(5, 0))
        self.cb_materia = ttk.Combobox(filtros, state="readonly")
        self.cb_materia.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        self.cb_materia.bind("<<ComboboxSelected>>", self._on_materia)

        ttk.Label(filtros, text="Docente").grid(row=0, column=3, sticky="w", padx=5, pady=(5, 0))
        self.cb_docente = ttk.Combobox(filtros, state="readonly")
        self.cb_docente.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        self.cb_docente.bind("<<ComboboxSelected>>", self._on_docente)

        ttk.Label(filtros, text="Fecha").grid(row=0, column=4, sticky="w", padx=5, pady=(5, 0))
        self.fecha_var = tk.StringVar()
        self.entry_fecha = ttk.Entry(
            filtros,
            textvariable=self.fecha_var,
            state="readonly",
        )
        self.entry_fecha.grid(row=1, column=4, sticky="ew", padx=5, pady=5)

        ttk.Label(filtros, text="Día").grid(row=0, column=5, sticky="w", padx=5, pady=(5, 0))
        self.lbl_dia = ttk.Label(filtros, text="-")
        self.lbl_dia.grid(row=1, column=5, sticky="w", padx=5, pady=5)

        self.btn_cargar_existente = ttk.Button(
            filtros,
            text="Cargar lista existente",
            command=self._cargar_existente_desde_contexto,
        )
        self.btn_cargar_existente.grid(row=1, column=6, padx=5, pady=5)

        self.btn_ver_contexto = ttk.Button(
            filtros,
            text="Ver listas del contexto",
            command=self._ver_listas_contexto_actual,
        )
        self.btn_ver_contexto.grid(row=1, column=7, padx=5, pady=5)

        # -----------------------------------------------------
        # Resumen superior
        # -----------------------------------------------------
        resumen = ttk.LabelFrame(self, text="Resumen del Grupo")
        resumen.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        for i in range(5):
            resumen.columnconfigure(i, weight=1)

        self.lbl_res_total = ttk.Label(resumen, text="Total grupo: 0")
        self.lbl_res_total.grid(row=0, column=0, sticky="w", padx=10, pady=8)

        self.lbl_res_asist = ttk.Label(resumen, text="Asistentes: 0")
        self.lbl_res_asist.grid(row=0, column=1, sticky="w", padx=10, pady=8)

        self.lbl_res_aus = ttk.Label(resumen, text="Ausentes: 0")
        self.lbl_res_aus.grid(row=0, column=2, sticky="w", padx=10, pady=8)

        self.lbl_res_reg = ttk.Label(resumen, text="Registrados: 0")
        self.lbl_res_reg.grid(row=0, column=3, sticky="w", padx=10, pady=8)

        self.lbl_res_pen = ttk.Label(resumen, text="Pendientes: 0")
        self.lbl_res_pen.grid(row=0, column=4, sticky="w", padx=10, pady=8)

        # -----------------------------------------------------
        # Cuerpo principal
        # -----------------------------------------------------
        body = ttk.Frame(self)
        body.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=1)

        # -------- disponibles
        frame_disp = ttk.LabelFrame(body, text="Estudiantes disponibles")
        frame_disp.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame_disp.rowconfigure(1, weight=1)
        frame_disp.columnconfigure(0, weight=1)

        self.busqueda_var = tk.StringVar()
        self.busqueda_var.trace_add("write", lambda *_: self._refresh_disponibles())

        ttk.Label(frame_disp, text="Buscar estudiante").grid(
            row=0, column=0, sticky="w", padx=5, pady=(5, 0)
        )
        self.entry_busqueda = ttk.Entry(frame_disp, textvariable=self.busqueda_var)
        self.entry_busqueda.grid(row=0, column=0, sticky="ew", padx=5, pady=(22, 5))

        list_disp_wrap = ttk.Frame(frame_disp)
        list_disp_wrap.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_disp_wrap.rowconfigure(0, weight=1)
        list_disp_wrap.columnconfigure(0, weight=1)

        self.list_disponibles = tk.Listbox(list_disp_wrap, height=18, exportselection=False)
        self.list_disponibles.grid(row=0, column=0, sticky="nsew")
        self.list_disponibles.bind("<Double-Button-1>", lambda e: self._add_asistente())

        sb_disp = ttk.Scrollbar(list_disp_wrap, orient="vertical", command=self.list_disponibles.yview)
        sb_disp.grid(row=0, column=1, sticky="ns")
        self.list_disponibles.config(yscrollcommand=sb_disp.set)

        btns_disp = ttk.Frame(frame_disp)
        btns_disp.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        btns_disp.columnconfigure(0, weight=1)
        btns_disp.columnconfigure(1, weight=1)

        ttk.Button(
            btns_disp,
            text="Marcar asistente",
            command=self._add_asistente,
        ).grid(row=0, column=0, sticky="ew", padx=2)

        ttk.Button(
            btns_disp,
            text="Marcar ausente",
            command=self._add_ausente,
        ).grid(row=0, column=1, sticky="ew", padx=2)

        # -------- asistentes
        frame_a = ttk.LabelFrame(body, text="Asistentes")
        frame_a.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        frame_a.rowconfigure(1, weight=1)
        frame_a.columnconfigure(0, weight=1)

        self.lbl_count_asist = ttk.Label(frame_a, text="Total: 0")
        self.lbl_count_asist.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        list_a_wrap = ttk.Frame(frame_a)
        list_a_wrap.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_a_wrap.rowconfigure(0, weight=1)
        list_a_wrap.columnconfigure(0, weight=1)

        self.list_asistentes = tk.Listbox(list_a_wrap, height=18, exportselection=False)
        self.list_asistentes.grid(row=0, column=0, sticky="nsew")

        sb_a = ttk.Scrollbar(list_a_wrap, orient="vertical", command=self.list_asistentes.yview)
        sb_a.grid(row=0, column=1, sticky="ns")
        self.list_asistentes.config(yscrollcommand=sb_a.set)

        ttk.Button(
            frame_a,
            text="Quitar seleccionado",
            command=self._remove_asistente,
        ).grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # -------- ausentes
        frame_f = ttk.LabelFrame(body, text="Ausentes")
        frame_f.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        frame_f.rowconfigure(1, weight=1)
        frame_f.columnconfigure(0, weight=1)

        self.lbl_count_aus = ttk.Label(frame_f, text="Total: 0")
        self.lbl_count_aus.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        list_f_wrap = ttk.Frame(frame_f)
        list_f_wrap.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_f_wrap.rowconfigure(0, weight=1)
        list_f_wrap.columnconfigure(0, weight=1)

        self.list_ausentes = tk.Listbox(list_f_wrap, height=18, exportselection=False)
        self.list_ausentes.grid(row=0, column=0, sticky="nsew")

        sb_f = ttk.Scrollbar(list_f_wrap, orient="vertical", command=self.list_ausentes.yview)
        sb_f.grid(row=0, column=1, sticky="ns")
        self.list_ausentes.config(yscrollcommand=sb_f.set)

        ttk.Button(
            frame_f,
            text="Quitar seleccionado",
            command=self._remove_ausente,
        ).grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # -----------------------------------------------------
        # Barra inferior acciones
        # -----------------------------------------------------
        acciones = ttk.Frame(self)
        acciones.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))

        ttk.Button(
            acciones,
            text="Guardar lista",
            command=self._guardar,
        ).pack(side="left", padx=5)

        ttk.Button(
            acciones,
            text="Limpiar selección",
            command=self._limpiar_seleccion_actual,
        ).pack(side="left", padx=5)

        ttk.Button(
            acciones,
            text="Refrescar grupo",
            command=self._recargar_grupo_actual,
        ).pack(side="left", padx=5)

        self.lbl_editando = ttk.Label(acciones, text="Modo: Nueva lista")
        self.lbl_editando.pack(side="right", padx=5)

    # =========================================================
    # Helpers generales
    # =========================================================
    def _set_fecha_hoy(self):
        self.fecha_var.set(str(date.today()))

    def _parse_fecha(self, fecha_texto: str) -> datetime.date:
        return datetime.strptime(str(fecha_texto).strip(), "%Y-%m-%d").date()

    def _get_fecha_dia_nombre(self, fecha_texto: str) -> str:
        try:
            fecha = self._parse_fecha(fecha_texto)
            dias = {
                0: "Lunes",
                1: "Martes",
                2: "Miércoles",
                3: "Jueves",
                4: "Viernes",
                5: "Sábado",
                6: "Domingo",
            }
            return dias[fecha.weekday()]
        except Exception:
            return "-"

    def _refresh_lbl_dia(self):
        self.lbl_dia.config(text=self._get_fecha_dia_nombre(self.fecha_var.get()))

    def _on_fecha_change(self, event=None):
        self._refresh_lbl_dia()

    def _get_selected_periodo(self) -> dict | None:
        idx = self.cb_periodo.current()
        return self.periodos[idx] if idx >= 0 else None

    def _get_selected_curso(self) -> dict | None:
        idx = self.cb_curso.current()
        return self.cursos[idx] if idx >= 0 else None

    def _get_selected_materia(self) -> dict | None:
        idx = self.cb_materia.current()
        return self.materias[idx] if idx >= 0 else None

    def _get_selected_docente(self) -> dict | None:
        idx = self.cb_docente.current()
        return self.docentes[idx] if idx >= 0 else None

    def _get_estudiante_by_carnet(self, carnet: str) -> dict | None:
        for item in self.estudiantes:
            if item["carnet"] == carnet:
                return item
        return None

    def _require_contexto_completo(self) -> tuple[dict, dict, dict, dict] | None:
        periodo = self._get_selected_periodo()
        curso = self._get_selected_curso()
        materia = self._get_selected_materia()
        docente = self._get_selected_docente()

        if not periodo:
            show_warning(self, "Validación", "Debe seleccionar un período.")
            return None
        if not curso:
            show_warning(self, "Validación", "Debe seleccionar un curso.")
            return None
        if not materia:
            show_warning(self, "Validación", "Debe seleccionar una materia.")
            return None
        if not docente:
            show_warning(self, "Validación", "Debe seleccionar un docente.")
            return None

        return periodo, curso, materia, docente

    def _set_combobox_by_item_id(self, combobox: ttk.Combobox, data: list[dict], item_id: int):
        values = [r["label"] for r in data]
        combobox["values"] = values

        for idx, item in enumerate(data):
            if int(item["id"]) == int(item_id):
                combobox.current(idx)
                return

        combobox.set("")

    # =========================================================
    # Registro helpers
    # =========================================================
    def _reset_listas(self):
        self.estudiantes = []
        self.asistentes = []
        self.ausentes = []
        self.current_asistencia_lista_id = None

        self.list_disponibles.delete(0, tk.END)
        self.list_asistentes.delete(0, tk.END)
        self.list_ausentes.delete(0, tk.END)

        self.busqueda_var.set("")
        self._refresh_resumen_registro()
        self._refresh_mode_label()

    def _limpiar_seleccion_actual(self):
        if not self.estudiantes:
            self._reset_listas()
            self._set_fecha_hoy()
            self._refresh_lbl_dia()
            return

        self.asistentes = []
        self.ausentes = []
        self.current_asistencia_lista_id = None

        self.list_asistentes.delete(0, tk.END)
        self.list_ausentes.delete(0, tk.END)

        self._set_fecha_hoy()
        self._refresh_lbl_dia()
        self._refresh_disponibles()
        self._refresh_resumen_registro()
        self._refresh_mode_label()

    def _refresh_mode_label(self):
        if self.current_asistencia_lista_id:
            self.lbl_editando.config(
                text=f"Modo: Editando lista #{self.current_asistencia_lista_id}"
            )
        else:
            self.lbl_editando.config(text="Modo: Nueva lista")

    def _refresh_resumen_registro(self):
        total = len(self.estudiantes)
        total_asist = len(self.asistentes)
        total_aus = len(self.ausentes)
        registrados = total_asist + total_aus
        pendientes = max(0, total - registrados)

        self.lbl_res_total.config(text=f"Total grupo: {total}")
        self.lbl_res_asist.config(text=f"Asistentes: {total_asist}")
        self.lbl_res_aus.config(text=f"Ausentes: {total_aus}")
        self.lbl_res_reg.config(text=f"Registrados: {registrados}")
        self.lbl_res_pen.config(text=f"Pendientes: {pendientes}")

        self.lbl_count_asist.config(text=f"Total: {total_asist}")
        self.lbl_count_aus.config(text=f"Total: {total_aus}")

    def _get_disponibles(self) -> list[dict]:
        ocupados = set(self.asistentes + self.ausentes)
        disponibles = [e for e in self.estudiantes if e["carnet"] not in ocupados]

        filtro = self.busqueda_var.get().strip().lower()
        if filtro:
            disponibles = [
                e for e in disponibles
                if filtro in e["label"].lower() or filtro in e["nombre"].lower()
            ]

        return disponibles

    def _refresh_disponibles(self):
        self.list_disponibles.delete(0, tk.END)

        for est in self._get_disponibles():
            self.list_disponibles.insert(tk.END, est["label"])

    def _refresh_listboxes_estado(self):
        self.list_asistentes.delete(0, tk.END)
        self.list_ausentes.delete(0, tk.END)

        asistentes_data = [
            self._get_estudiante_by_carnet(c) for c in self.asistentes
        ]
        ausentes_data = [
            self._get_estudiante_by_carnet(c) for c in self.ausentes
        ]

        asistentes_data = [x for x in asistentes_data if x is not None]
        ausentes_data = [x for x in ausentes_data if x is not None]

        asistentes_data.sort(key=lambda x: x["nombre"].lower())
        ausentes_data.sort(key=lambda x: x["nombre"].lower())

        for item in asistentes_data:
            self.list_asistentes.insert(tk.END, item["label"])

        for item in ausentes_data:
            self.list_ausentes.insert(tk.END, item["label"])

        self._refresh_disponibles()
        self._refresh_resumen_registro()

    def _get_selected_disponible_label(self) -> str | None:
        sel = self.list_disponibles.curselection()
        if not sel:
            return None
        return self.list_disponibles.get(sel[0])

    def _add_asistente(self):
        label = self._get_selected_disponible_label()
        if not label:
            return

        carnet = label.split("|")[0].strip()
        if carnet in self.asistentes or carnet in self.ausentes:
            return

        self.asistentes.append(carnet)
        self._refresh_listboxes_estado()

    def _add_ausente(self):
        label = self._get_selected_disponible_label()
        if not label:
            return

        carnet = label.split("|")[0].strip()
        if carnet in self.asistentes or carnet in self.ausentes:
            return

        self.ausentes.append(carnet)
        self._refresh_listboxes_estado()

    def _remove_asistente(self):
        sel = self.list_asistentes.curselection()
        if not sel:
            return

        label = self.list_asistentes.get(sel[0])
        carnet = label.split("|")[0].strip()

        if carnet in self.asistentes:
            self.asistentes.remove(carnet)

        self._refresh_listboxes_estado()

    def _remove_ausente(self):
        sel = self.list_ausentes.curselection()
        if not sel:
            return

        label = self.list_ausentes.get(sel[0])
        carnet = label.split("|")[0].strip()

        if carnet in self.ausentes:
            self.ausentes.remove(carnet)

        self._refresh_listboxes_estado()

    # =========================================================
    # Loaders tab registro
    # =========================================================
    def _load_periodos(self):
        try:
            rows = ep.get_periodos_activos(self.db_user, self.db_pass)
            self.periodos = rows
            self.cb_periodo["values"] = [r["label"] for r in rows]

            if rows:
                self.cb_periodo.current(0)
                self._on_periodo()

        except Exception as e:
            handle_exception(self, e, context="Cargar períodos")

    def _on_periodo(self, event=None):
        try:
            self._reset_listas()

            periodo = self._get_selected_periodo()
            if not periodo:
                return

            rows = ep.get_cursos_por_periodo(
                self.db_user,
                self.db_pass,
                periodo["id"],
            )

            self.cursos = rows
            self.cb_curso.set("")
            self.cb_materia.set("")
            self.cb_docente.set("")

            self.cb_curso["values"] = [r["label"] for r in rows]
            self.cb_materia["values"] = []
            self.cb_docente["values"] = []

        except Exception as e:
            handle_exception(self, e, context="Cargar cursos")

    def _on_curso(self, event=None):
        try:
            self._reset_listas()

            periodo = self._get_selected_periodo()
            curso = self._get_selected_curso()

            if not periodo or not curso:
                return

            rows = ep.get_materias_por_periodo_curso(
                self.db_user,
                self.db_pass,
                periodo["id"],
                curso["id"],
            )

            self.materias = rows
            self.cb_materia.set("")
            self.cb_docente.set("")
            self.cb_materia["values"] = [r["label"] for r in rows]
            self.cb_docente["values"] = []
            self.lbl_dia.config(text="-")

        except Exception as e:
            handle_exception(self, e, context="Cargar materias")

    def _on_materia(self, event=None):
        try:
            self._reset_listas()

            periodo = self._get_selected_periodo()
            curso = self._get_selected_curso()
            materia = self._get_selected_materia()

            if not periodo or not curso or not materia:
                return

            self._refresh_lbl_dia()

            rows = ep.get_docentes_por_periodo_curso_materia(
                self.db_user,
                self.db_pass,
                periodo["id"],
                curso["id"],
                materia["id"],
            )

            self.docentes = rows
            self.cb_docente.set("")
            self.cb_docente["values"] = [r["label"] for r in rows]

        except Exception as e:
            handle_exception(self, e, context="Cargar docentes")

    def _on_docente(self, event=None):
        try:
            self._cargar_estudiantes_contexto_actual()

        except Exception as e:
            handle_exception(self, e, context="Cargar estudiantes")

    def _cargar_estudiantes_contexto_actual(self):
        contexto = self._require_contexto_completo()
        if not contexto:
            return

        periodo, curso, materia, docente = contexto

        self._reset_listas()

        rows = ep.get_estudiantes_grupo(
            self.db_user,
            self.db_pass,
            periodo["id"],
            curso["id"],
            materia["id"],
            docente["id"],
        )

        self.estudiantes = rows
        self._refresh_disponibles()
        self._refresh_resumen_registro()

    def _recargar_grupo_actual(self):
        try:
            self._cargar_estudiantes_contexto_actual()
        except Exception as e:
            handle_exception(self, e, context="Refrescar grupo")

    # =========================================================
    # Guardado / carga existente
    # =========================================================
    def _guardar(self):
        try:
            contexto = self._require_contexto_completo()
            if not contexto:
                return

            fecha = self.fecha_var.get().strip()
            if not fecha:
                show_warning(self, "Validación", "Debe indicar la fecha de la lista.")
                return

            total_registrados = len(self.asistentes) + len(self.ausentes)
            if total_registrados == 0:
                show_warning(
                    self,
                    "Validación",
                    "Debe registrar al menos un estudiante como asistente o ausente.",
                )
                return

            pendientes = max(0, len(self.estudiantes) - total_registrados)
            if pendientes > 0:
                ok = show_confirm(
                    self,
                    title="Guardar lista incompleta",
                    message=(
                        f"Aún hay {pendientes} estudiante(s) pendientes por clasificar.\n\n"
                        "¿Desea guardar la lista de todos modos?"
                    ),
                )
                if not ok:
                    return

            periodo, curso, materia, docente = contexto

            result = ep.save_asistencia(
                self.db_user,
                self.db_pass,
                periodo_id=periodo["id"],
                curso_cod=curso["id"],
                materia_cod=materia["id"],
                docente_cod=docente["id"],
                fecha_clase=fecha,
                asistentes=self.asistentes,
                ausentes=self.ausentes,
                codigo_usuario=self.codigo_usuario,
            )

            self.current_asistencia_lista_id = int(result["asistencia_lista_id"])
            self._refresh_mode_label()
            self._refresh_resumen_registro()

            if callable(self.on_refresh_consulta):
                self.on_refresh_consulta()

            show_info(
                self,
                "Asistencia guardada",
                (
                    f"Lista {result['accion']} correctamente.\n\n"
                    f"ID Lista: {result['asistencia_lista_id']}\n"
                    f"Asistentes: {result['total_asistentes']}\n"
                    f"Ausentes: {result['total_ausentes']}\n"
                    f"Pendientes: {result['pendientes']}"
                ),
            )

        except Exception as e:
            handle_exception(self, e, context="Guardar asistencia")

    def _cargar_existente_desde_contexto(self):
        try:
            contexto = self._require_contexto_completo()
            if not contexto:
                return

            fecha = self.fecha_var.get().strip()
            if not fecha:
                show_warning(self, "Validación", "Debe indicar la fecha de la lista.")
                return

            periodo, curso, materia, docente = contexto

            data = ep.get_asistencia_existente(
                self.db_user,
                self.db_pass,
                periodo["id"],
                curso["id"],
                materia["id"],
                docente["id"],
                fecha,
            )

            if not data:
                show_info(
                    self,
                    "Lista no encontrada",
                    "No existe una lista registrada para el contexto y fecha seleccionados.",
                )
                return

            self._apply_asistencia_to_editor(data)
            show_info(
                self,
                "Lista cargada",
                f"Se cargó correctamente la lista #{data['cabecera']['asistencia_lista_id']}.",
            )

        except Exception as e:
            handle_exception(self, e, context="Cargar lista existente")

    def _apply_asistencia_to_editor(self, data: dict):
        cab = data["cabecera"]

        self.current_asistencia_lista_id = int(cab["asistencia_lista_id"])
        self.fecha_var.set(str(cab["fecha_clase"]))
        self._refresh_lbl_dia()

        self.asistentes = [item["carnet"] for item in data.get("asistentes", [])]
        self.ausentes = [item["carnet"] for item in data.get("ausentes", [])]

        self._refresh_listboxes_estado()
        self._refresh_mode_label()

    def load_context_and_edit(self, item: dict):
        """
        Carga el contexto académico en el tab de registro y luego
        trae la lista por ID para editar.
        """
        try:
            self._set_combobox_by_item_id(self.cb_periodo, self.periodos, item["periodo_id"])
            self._on_periodo()

            self._set_combobox_by_item_id(self.cb_curso, self.cursos, item["curso_cod"])
            self._on_curso()

            self._set_combobox_by_item_id(self.cb_materia, self.materias, item["materia_cod"])
            self._on_materia()

            self._set_combobox_by_item_id(self.cb_docente, self.docentes, item["docente_cod"])
            self._on_docente()

            self.fecha_var.set(str(item["fecha_clase"]))
            self._refresh_lbl_dia()

            data = ep.get_asistencia_by_id(
                self.db_user,
                self.db_pass,
                item["asistencia_lista_id"],
            )
            if not data:
                show_warning(self, "Consulta", "No se pudo cargar la lista seleccionada.")
                return

            self._apply_asistencia_to_editor(data)

        except Exception as e:
            handle_exception(self, e, context="Cargar lista en edición")

    def _ver_listas_contexto_actual(self):
        """
        Lleva el contexto del tab de registro al tab de consulta y ejecuta búsqueda.
        """
        try:
            contexto = self._require_contexto_completo()
            if not contexto:
                return

            periodo, curso, materia, docente = contexto
            fecha = self.fecha_var.get().strip()

            if callable(self.on_open_consulta):
                self.on_open_consulta(periodo, curso, materia, docente, fecha)

        except Exception as e:
            handle_exception(self, e, context="Ver listas del contexto")