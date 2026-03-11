from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.error_handler import handle_exception, show_info, show_warning
from app.ui.components.confirm_dialog import show_confirm
from app.endpoints.matriculas_materia import (
    matricula_materia_endpoints as mm_ep,
)


class MatriculaMateriaTab(ttk.Frame):
    """
    Tab UI - Entregable #4
    Matrícula de estudiantes por materia.

    Flujo:
    1) Seleccionar estudiante
    2) Seleccionar período
    3) Cargar matrícula de curso activa + beca + restricciones
    4) Cargar materias disponibles
    5) Seleccionar materia
    6) Cargar docentes disponibles para esa materia
    7) Guardar matrícula por materia
    """

    def __init__(self, parent, db_user: str, db_pass: str, codigo_usuario: int):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.vars: dict[str, tk.StringVar] = {}

        self._loaded = False

        self._estudiante_display_to_carnet: dict[str, str] = {}

        # Compatibilidad:
        # display visible -> anio lógico
        self._periodo_display_to_anio: dict[str, int] = {}

        self._materia_display_to_cod: dict[str, int] = {}
        self._docente_display_to_cod: dict[str, int] = {}
        self._estado_display_to_cod: dict[str, int] = {}

        self._selected_matricula_id: int | None = None

        self._build_ui()
        self.reset_view_blank()

    # =====================================================
    # Lifecycle
    # =====================================================
    def ensure_loaded(self):
        if self._loaded:
            return
        self._load_initial_lookups()
        self.refresh_grid()
        self._loaded = True

    # =====================================================
    # Vars
    # =====================================================
    def _ensure_vars(self):
        self.vars.setdefault("estudiante", tk.StringVar())
        self.vars.setdefault("periodo", tk.StringVar())
        self.vars.setdefault("curso", tk.StringVar())
        self.vars.setdefault("beca", tk.StringVar())
        self.vars.setdefault("minimo", tk.StringVar())
        self.vars.setdefault("maximo", tk.StringVar())
        self.vars.setdefault("actuales", tk.StringVar())
        self.vars.setdefault("restantes", tk.StringVar())
        self.vars.setdefault("estado_beca", tk.StringVar())
        self.vars.setdefault("materia", tk.StringVar())
        self.vars.setdefault("docente", tk.StringVar())
        self.vars.setdefault("estado", tk.StringVar())

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self._ensure_vars()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # =====================================================
        # FORMULARIO SUPERIOR - CONTEXTO + RESTRICCIONES
        # =====================================================
        self.top = ttk.LabelFrame(self, text="Formulario", padding=(12, 10))
        self.top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

        self.top.columnconfigure(0, weight=1)
        self.top.columnconfigure(1, weight=1)

        # -------------------------
        # Bloque 1: Contexto
        # -------------------------
        self.frm_contexto = ttk.LabelFrame(self.top, text="Contexto académico", padding=(10, 8))
        self.frm_contexto.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        self.frm_contexto.columnconfigure(1, weight=1)

        ttk.Label(
            self.frm_contexto,
            text="Matrícula por Materia",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(self.frm_contexto, text="Estudiante:").grid(row=1, column=0, sticky="w", pady=4)
        self.cbo_estudiante = ttk.Combobox(
            self.frm_contexto,
            textvariable=self.vars["estudiante"],
            state="readonly",
        )
        self.cbo_estudiante.grid(row=1, column=1, sticky="ew", pady=4)
        self.cbo_estudiante.bind("<<ComboboxSelected>>", self._on_contexto_changed)

        ttk.Label(self.frm_contexto, text="Período:").grid(row=2, column=0, sticky="w", pady=4)
        self.cbo_periodo = ttk.Combobox(
            self.frm_contexto,
            textvariable=self.vars["periodo"],
            state="readonly",
        )
        self.cbo_periodo.grid(row=2, column=1, sticky="ew", pady=4)
        self.cbo_periodo.bind("<<ComboboxSelected>>", self._on_contexto_changed)

        ttk.Label(self.frm_contexto, text="Curso/Carrera:").grid(row=3, column=0, sticky="w", pady=4)
        self.ent_curso = ttk.Entry(
            self.frm_contexto,
            textvariable=self.vars["curso"],
            state="readonly",
        )
        self.ent_curso.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(self.frm_contexto, text="Beca:").grid(row=4, column=0, sticky="w", pady=4)
        self.ent_beca = ttk.Entry(
            self.frm_contexto,
            textvariable=self.vars["beca"],
            state="readonly",
        )
        self.ent_beca.grid(row=4, column=1, sticky="ew", pady=4)

        # -------------------------
        # Bloque 2: Restricciones
        # -------------------------
        self.frm_restricciones = ttk.LabelFrame(self.top, text="Restricciones de carga", padding=(10, 8))
        self.frm_restricciones.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)

        self.frm_restricciones.columnconfigure(1, weight=1)

        ttk.Label(self.frm_restricciones, text="Mínimo materias:").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_minimo = ttk.Entry(
            self.frm_restricciones,
            textvariable=self.vars["minimo"],
            state="readonly",
        )
        self.ent_minimo.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(self.frm_restricciones, text="Máximo materias:").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_maximo = ttk.Entry(
            self.frm_restricciones,
            textvariable=self.vars["maximo"],
            state="readonly",
        )
        self.ent_maximo.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(self.frm_restricciones, text="Materias actuales:").grid(row=2, column=0, sticky="w", pady=4)
        self.ent_actuales = ttk.Entry(
            self.frm_restricciones,
            textvariable=self.vars["actuales"],
            state="readonly",
        )
        self.ent_actuales.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(self.frm_restricciones, text="Disponibles restantes:").grid(row=3, column=0, sticky="w", pady=4)
        self.ent_restantes = ttk.Entry(
            self.frm_restricciones,
            textvariable=self.vars["restantes"],
            state="readonly",
        )
        self.ent_restantes.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(self.frm_restricciones, text="Estado beca/rango:").grid(row=4, column=0, sticky="w", pady=4)
        self.ent_estado_beca = ttk.Entry(
            self.frm_restricciones,
            textvariable=self.vars["estado_beca"],
            state="readonly",
        )
        self.ent_estado_beca.grid(row=4, column=1, sticky="ew", pady=4)

        # =====================================================
        # FORMULARIO INTERMEDIO - ASIGNACIÓN
        # =====================================================
        self.middle = ttk.LabelFrame(self, text="Asignación", padding=(12, 10))
        self.middle.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.middle.columnconfigure(1, weight=1)

        ttk.Label(self.middle, text="Materia:").grid(row=0, column=0, sticky="w", pady=4)
        self.cbo_materia = ttk.Combobox(
            self.middle,
            textvariable=self.vars["materia"],
            state="disabled",
        )
        self.cbo_materia.grid(row=0, column=1, sticky="ew", pady=4)
        self.cbo_materia.bind("<<ComboboxSelected>>", self._on_materia_changed)

        ttk.Label(self.middle, text="Docente:").grid(row=1, column=0, sticky="w", pady=4)
        self.cbo_docente = ttk.Combobox(
            self.middle,
            textvariable=self.vars["docente"],
            state="disabled",
        )
        self.cbo_docente.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(self.middle, text="Estado (auto):").grid(row=2, column=0, sticky="w", pady=4)
        self.ent_estado = ttk.Entry(
            self.middle,
            textvariable=self.vars["estado"],
            state="readonly",
        )
        self.ent_estado.grid(row=2, column=1, sticky="ew", pady=4)

        btns = ttk.Frame(self.middle)
        btns.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for i in range(4):
            btns.columnconfigure(i, weight=1, uniform="crud")

        self.btn_nuevo = ttk.Button(btns, text="Nuevo", command=self.on_nuevo)
        self.btn_guardar = ttk.Button(btns, text="Guardar", command=self.on_guardar)
        self.btn_actualizar = ttk.Button(btns, text="Actualizar Estado", command=self.on_actualizar)
        self.btn_eliminar = ttk.Button(btns, text="Eliminar", command=self.on_eliminar)

        self.btn_nuevo.grid(row=0, column=0, sticky="ew", padx=4, pady=6)
        self.btn_guardar.grid(row=0, column=1, sticky="ew", padx=4, pady=6)
        self.btn_actualizar.grid(row=0, column=2, sticky="ew", padx=4, pady=6)
        self.btn_eliminar.grid(row=0, column=3, sticky="ew", padx=4, pady=6)

        # =====================================================
        # GRID ABAJO
        # =====================================================
        self.bottom = ttk.LabelFrame(self, text="Listado", padding=(10, 10))
        self.bottom.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self.bottom.rowconfigure(0, weight=1)
        self.bottom.columnconfigure(0, weight=1)

        cols = (
            "matricula_materia_id",
            "carnet",
            "estudiante",
            "curso",
            "materia",
            "periodo",
            "docente",
            "estado",
            "fecha",
        )
        self.tree = ttk.Treeview(
            self.bottom,
            columns=cols,
            show="headings",
            height=14,
        )

        headings = {
            "matricula_materia_id": "ID",
            "carnet": "Carnet",
            "estudiante": "Estudiante",
            "curso": "Curso",
            "materia": "Materia",
            "periodo": "Período",
            "docente": "Docente",
            "estado": "Estado",
            "fecha": "Fecha",
        }

        widths = {
            "matricula_materia_id": 70,
            "carnet": 110,
            "estudiante": 220,
            "curso": 220,
            "materia": 220,
            "periodo": 90,
            "docente": 220,
            "estado": 110,
            "fecha": 100,
        }

        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], minwidth=70, anchor="w", stretch=True)

        self.tree.column("matricula_materia_id", anchor="center", stretch=False)
        self.tree.column("carnet", anchor="center", stretch=False)
        self.tree.column("periodo", anchor="center", stretch=False)
        self.tree.column("estado", anchor="center", stretch=False)
        self.tree.column("fecha", anchor="center", stretch=False)

        vsb = ttk.Scrollbar(self.bottom, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.bottom, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    # =====================================================
    # Reset / state
    # =====================================================
    def reset_view_blank(self):
        self._ensure_vars()

        self._selected_matricula_id = None

        self.vars["estudiante"].set("")
        self.vars["periodo"].set("")
        self.vars["curso"].set("")
        self.vars["beca"].set("")
        self.vars["minimo"].set("")
        self.vars["maximo"].set("")
        self.vars["actuales"].set("")
        self.vars["restantes"].set("")
        self.vars["estado_beca"].set("")
        self.vars["materia"].set("")
        self.vars["docente"].set("")
        self.vars["estado"].set("Se asigna automáticamente")

        self._materia_display_to_cod = {}
        self._docente_display_to_cod = {}

        if hasattr(self, "cbo_materia"):
            self.cbo_materia["values"] = []
            self.cbo_materia.set("")
            self.cbo_materia.configure(state="disabled")

        if hasattr(self, "cbo_docente"):
            self.cbo_docente["values"] = []
            self.cbo_docente.set("")
            self.cbo_docente.configure(state="disabled")

        if hasattr(self, "tree"):
            try:
                self.tree.selection_remove(self.tree.selection())
            except Exception:
                pass

    def _reset_contexto_dependiente(self):
        self.vars["curso"].set("")
        self.vars["beca"].set("")
        self.vars["minimo"].set("")
        self.vars["maximo"].set("")
        self.vars["actuales"].set("")
        self.vars["restantes"].set("")
        self.vars["estado_beca"].set("")
        self.vars["materia"].set("")
        self.vars["docente"].set("")

        self._materia_display_to_cod = {}
        self._docente_display_to_cod = {}

        self.cbo_materia["values"] = []
        self.cbo_materia.set("")
        self.cbo_materia.configure(state="disabled")

        self.cbo_docente["values"] = []
        self.cbo_docente.set("")
        self.cbo_docente.configure(state="disabled")

    # =====================================================
    # Lookups
    # =====================================================
    def _load_initial_lookups(self):
        try:
            estudiantes = mm_ep.fetch_estudiantes_activos_matricula_materia(
                self.db_user,
                self.db_pass,
            )
            periodos = mm_ep.fetch_periodos_activos_matricula_materia(
                self.db_user,
                self.db_pass,
            )
            estados = mm_ep.fetch_estados_matricula_materia(
                self.db_user,
                self.db_pass,
            )

            self._estudiante_display_to_carnet = {}
            for carnet, nombre in estudiantes:
                display = f"{carnet} - {nombre}"
                self._estudiante_display_to_carnet[display] = str(carnet)

            # Compatibilidad:
            # Si el endpoint devuelve solo años -> mostrar año
            # Si devuelve periodo nuevo + año -> mostrar periodo nuevo, usar año lógicamente
            self._periodo_display_to_anio = {}

            for p in periodos:
                try:
                    if isinstance(p, (tuple, list)):
                        if len(p) >= 3:
                            # ejemplo esperado:
                            # (periodo_id, periodo_codigo, anio)
                            periodo_codigo = str(p[1]).strip()
                            anio = int(p[2])
                            display = periodo_codigo or str(anio)
                            self._periodo_display_to_anio[display] = anio
                        elif len(p) == 2:
                            # posible compatibilidad:
                            # (periodo_codigo, anio) o (anio, periodo_codigo)
                            a = p[0]
                            b = p[1]

                            if isinstance(a, str) and not str(a).isdigit():
                                display = str(a).strip()
                                anio = int(b)
                            elif isinstance(b, str) and not str(b).isdigit():
                                display = str(b).strip()
                                anio = int(a)
                            else:
                                anio = int(a)
                                display = str(anio)

                            self._periodo_display_to_anio[display] = anio
                        elif len(p) == 1:
                            anio = int(p[0])
                            self._periodo_display_to_anio[str(anio)] = anio
                    else:
                        anio = int(p)
                        self._periodo_display_to_anio[str(anio)] = anio
                except Exception:
                    continue

            self._estado_display_to_cod = {}
            for codigo, desc in estados:
                self._estado_display_to_cod[str(desc)] = int(codigo)

            self.cbo_estudiante["values"] = list(self._estudiante_display_to_carnet.keys())
            self.cbo_periodo["values"] = list(self._periodo_display_to_anio.keys())

        except Exception as e:
            handle_exception(self, e, context="Carga inicial Matrícula por Materia")

    # =====================================================
    # Helpers parse
    # =====================================================
    def _get_carnet_selected(self) -> str | None:
        display = (self.vars["estudiante"].get() or "").strip()
        return self._estudiante_display_to_carnet.get(display)

    def _get_periodo_selected(self) -> int | None:
        """
        Lógica temporal:
        devuelve el AÑO aunque visualmente el usuario vea 2026-I, 2026-II, etc.
        """
        display = (self.vars["periodo"].get() or "").strip()
        if not display:
            return None

        anio = self._periodo_display_to_anio.get(display)
        if anio is not None:
            return int(anio)

        try:
            return int(display)
        except Exception:
            return None

    def _get_periodo_display_selected(self) -> str:
        return (self.vars["periodo"].get() or "").strip()

    def _get_materia_selected(self) -> int | None:
        display = (self.vars["materia"].get() or "").strip()
        return self._materia_display_to_cod.get(display)

    def _get_docente_selected(self) -> int | None:
        display = (self.vars["docente"].get() or "").strip()
        return self._docente_display_to_cod.get(display)

    def _get_estado_inactivo_cod(self) -> int | None:
        for desc, cod in self._estado_display_to_cod.items():
            if str(desc).strip().lower() == "inactivo":
                return int(cod)
        return None

    # =====================================================
    # Grid
    # =====================================================
    def refresh_grid(self):
        try:
            rows = mm_ep.list_matricula_materia_rows(
                self.db_user,
                self.db_pass,
            )
            self._fill_tree(rows)
        except Exception as e:
            handle_exception(self, e, context="Listado Matrícula por Materia")

    def _refresh_grid_contextual(self):
        carnet = self._get_carnet_selected()
        periodo = self._get_periodo_selected()

        if carnet and periodo:
            try:
                rows = mm_ep.list_matricula_materia_rows_por_estudiante_periodo(
                    self.db_user,
                    self.db_pass,
                    carnet=carnet,
                    periodo=periodo,
                )
                self._fill_tree_contextual(rows, carnet)
                return
            except Exception as e:
                handle_exception(self, e, context="Listado por estudiante/período")

        self.refresh_grid()

    def _fill_tree(self, rows: list[tuple]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in rows:
            try:
                self.tree.insert("", "end", values=r)
            except Exception:
                pass

    def _fill_tree_contextual(self, rows: list[tuple], carnet: str):
        """
        Convierte el listado contextual a las columnas del grid general.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        estudiante_display = (self.vars["estudiante"].get() or "").strip()
        estudiante_nombre = estudiante_display.split(" - ", 1)[1].strip() if " - " in estudiante_display else estudiante_display
        curso_txt = (self.vars["curso"].get() or "").strip()
        periodo_txt = self._get_periodo_display_selected() or (self._get_periodo_selected() or "")

        for r in rows:
            try:
                matricula_id, materia_txt, docente_txt, estado_txt, fecha_txt = r
                row = (
                    matricula_id,
                    carnet,
                    estudiante_nombre,
                    curso_txt,
                    materia_txt,
                    periodo_txt,
                    docente_txt,
                    estado_txt,
                    fecha_txt,
                )
                self.tree.insert("", "end", values=row)
            except Exception:
                pass

    # =====================================================
    # Contexto dependiente
    # =====================================================
    def _on_contexto_changed(self, _evt=None):
        try:
            carnet = self._get_carnet_selected()
            periodo = self._get_periodo_selected()

            self._reset_contexto_dependiente()

            if not carnet or not periodo:
                self._refresh_grid_contextual()
                return

            matricula_curso = mm_ep.fetch_matricula_curso_estudiante(
                self.db_user,
                self.db_pass,
                carnet=carnet,
                periodo=periodo,
            )

            if not matricula_curso:
                show_warning(
                    self,
                    "Sin matrícula de curso",
                    "El estudiante no posee matrícula activa de curso/carrera en el período seleccionado.",
                )
                self._refresh_grid_contextual()
                return

            curso_cod, curso_desc = matricula_curso
            self.vars["curso"].set(f"{curso_cod} - {curso_desc}")

            beca = mm_ep.fetch_beca_estudiante(
                self.db_user,
                self.db_pass,
                carnet,
            )
            if beca:
                _, nombre_beca, pct = beca
                self.vars["beca"].set(f"{nombre_beca} ({pct}%)")
            else:
                self.vars["beca"].set("Sin beca")

            restr = mm_ep.fetch_restricciones_beca(
                self.db_user,
                self.db_pass,
                carnet,
            )
            rango = mm_ep.validar_rango_actual_beca(
                self.db_user,
                self.db_pass,
                carnet,
                periodo,
            )

            minimo = int(restr.get("minimo_materias", 1))
            maximo = int(restr.get("maximo_materias", 6))
            total_actual = int(rango.get("total_actual", 0))
            restantes = int(rango.get("disponibles_restantes", maximo))
            cumple_min = bool(rango.get("cumple_minimo_actual", False))
            beca_norm = restr.get("beca")

            self.vars["minimo"].set(str(minimo))
            self.vars["maximo"].set(str(maximo))
            self.vars["actuales"].set(str(total_actual))
            self.vars["restantes"].set(str(restantes))

            if beca_norm in (None, "", "basica"):
                if total_actual >= 1:
                    self.vars["estado_beca"].set("Carga válida en progreso.")
                else:
                    self.vars["estado_beca"].set("Debe matricular al menos 1 materia.")
            else:
                if cumple_min:
                    self.vars["estado_beca"].set("Ya cumple el mínimo requerido por la beca.")
                else:
                    faltan = max(0, minimo - total_actual)
                    self.vars["estado_beca"].set(f"Le faltan {faltan} materia(s) para cumplir el mínimo.")

            self._cargar_materias_disponibles(carnet, periodo, restantes)
            self._refresh_grid_contextual()

        except Exception as e:
            handle_exception(self, e, context="Cambio de contexto Matrícula por Materia")

    def _cargar_materias_disponibles(self, carnet: str, periodo: int, restantes: int):
        materias = mm_ep.fetch_materias_disponibles_estudiante(
            self.db_user,
            self.db_pass,
            carnet=carnet,
            periodo=periodo,
        )

        self._materia_display_to_cod = {}
        values: list[str] = []

        for materia_cod, materia_desc, curso_cod, curso_desc in materias:
            display = f"{materia_cod} - {materia_desc}"
            self._materia_display_to_cod[display] = int(materia_cod)
            values.append(display)

        self.cbo_materia["values"] = values
        self.cbo_materia.set("")
        self.cbo_docente["values"] = []
        self.cbo_docente.set("")
        self.cbo_docente.configure(state="disabled")

        if restantes <= 0:
            self.cbo_materia.configure(state="disabled")
            show_info(
                self,
                "Máximo alcanzado",
                "El estudiante ya alcanzó el máximo de 6 materias en este período.",
            )
            return

        if not values:
            self.cbo_materia.configure(state="disabled")
            show_info(
                self,
                "Sin materias disponibles",
                "No hay materias disponibles para matricular en este período.",
            )
            return

        self.cbo_materia.configure(state="readonly")

    def _on_materia_changed(self, _evt=None):
        try:
            materia_cod = self._get_materia_selected()

            self._docente_display_to_cod = {}
            self.cbo_docente["values"] = []
            self.cbo_docente.set("")
            self.cbo_docente.configure(state="disabled")

            if not materia_cod:
                return

            docentes = mm_ep.fetch_docentes_disponibles_para_materia(
                self.db_user,
                self.db_pass,
                materia_cod,
            )

            values: list[str] = []
            for docente_cod, docente_nombre in docentes:
                display = f"{docente_cod} - {docente_nombre}"
                self._docente_display_to_cod[display] = int(docente_cod)
                values.append(display)

            self.cbo_docente["values"] = values

            if not values:
                show_warning(
                    self,
                    "Sin docentes",
                    "La materia seleccionada no tiene docentes asignados.",
                )
                return

            self.cbo_docente.configure(state="readonly")

        except Exception as e:
            handle_exception(self, e, context="Carga de docentes por materia")

    def _on_row_selected(self, _evt=None):
        try:
            sel = self.tree.selection()
            if not sel:
                self._selected_matricula_id = None
                return

            vals = self.tree.item(sel[0], "values")
            if not vals:
                self._selected_matricula_id = None
                return

            self._selected_matricula_id = int(vals[0])
        except Exception:
            self._selected_matricula_id = None

    # =====================================================
    # Actions
    # =====================================================
    def on_nuevo(self):
        try:
            est = self.vars["estudiante"].get()
            per = self.vars["periodo"].get()

            self.reset_view_blank()

            if self._loaded:
                self._load_initial_lookups()

            # Mantener estudiante/período si el usuario ya estaba trabajando
            if est:
                self.vars["estudiante"].set(est)
            if per:
                self.vars["periodo"].set(per)

            if est and per:
                self._on_contexto_changed()

        except Exception as e:
            handle_exception(self, e, context="Nuevo Matrícula por Materia")

    def on_guardar(self):
        try:
            carnet = self._get_carnet_selected()
            periodo = self._get_periodo_selected()
            materia_cod = self._get_materia_selected()
            docente_cod = self._get_docente_selected()

            if not carnet:
                show_warning(self, "Validación", "Selecciona un estudiante.")
                return
            if not periodo:
                show_warning(self, "Validación", "Selecciona un período.")
                return
            if not materia_cod:
                show_warning(self, "Validación", "Selecciona una materia.")
                return
            if not docente_cod:
                show_warning(self, "Validación", "Selecciona un docente.")
                return

            msg = mm_ep.assign_matricula_materia(
                db_user=self.db_user,
                db_pass=self.db_pass,
                carnet=carnet,
                materia_cod=int(materia_cod),
                periodo=int(periodo),
                docente_cod=int(docente_cod),
                estado_codigo=1,
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Matrícula por Materia", msg)

            # Mantener contexto y limpiar dependientes
            self.vars["materia"].set("")
            self.vars["docente"].set("")
            self.cbo_docente["values"] = []
            self.cbo_docente.set("")
            self.cbo_docente.configure(state="disabled")

            self._on_contexto_changed()

        except Exception as e:
            handle_exception(self, e, context="Guardar Matrícula por Materia")

    def on_actualizar(self):
        try:
            if not self._selected_matricula_id:
                show_warning(self, "Validación", "Selecciona una matrícula del listado.")
                return

            estados = mm_ep.fetch_estados_matricula_materia(
                self.db_user,
                self.db_pass,
            )
            activo_cod = None
            for cod, desc in estados:
                if str(desc).strip().lower() == "activo":
                    activo_cod = int(cod)
                    break

            if activo_cod is None:
                show_warning(self, "Validación", "No se encontró el estado Activo.")
                return

            msg = mm_ep.update_estado_matricula_materia_endpoint(
                db_user=self.db_user,
                db_pass=self.db_pass,
                matricula_materia_id=int(self._selected_matricula_id),
                nuevo_estado_codigo=int(activo_cod),
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Actualizar Estado", msg)
            self._on_contexto_changed()

        except Exception as e:
            handle_exception(self, e, context="Actualizar Estado Matrícula por Materia")

    def on_eliminar(self):
        try:
            if not self._selected_matricula_id:
                show_warning(self, "Validación", "Selecciona una matrícula del listado.")
                return

            ok = show_confirm(
                self,
                "Eliminar matrícula por materia",
                "¿Deseas desactivar la matrícula por materia seleccionada?",
                yes_text="Sí, desactivar",
                no_text="Cancelar",
            )
            if not ok:
                return

            msg = mm_ep.delete_matricula_materia_endpoint(
                db_user=self.db_user,
                db_pass=self.db_pass,
                matricula_materia_id=int(self._selected_matricula_id),
                codigo_usuario=self.codigo_usuario,
            )

            show_info(self, "Eliminar", msg)
            self._selected_matricula_id = None
            self._on_contexto_changed()

        except Exception as e:
            handle_exception(self, e, context="Eliminar Matrícula por Materia")