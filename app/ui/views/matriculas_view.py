from __future__ import annotations

import calendar as _cal
import datetime as _dt
import tkinter as tk
from tkinter import ttk, messagebox

from app.endpoints.matriculas import matriculas_endpoints as m_ep

from app.ui.matriculas.listado_matriculas_tab import ListadoMatriculasTab
from app.ui.matriculas.consulta_matriculas_tab import ConsultaMatriculasTab
from app.ui.matriculas.reporte_estudiantes_tab import ReporteEstudiantesTab


class _CalendarPopup(tk.Toplevel):
    """
    Selector de fecha con calendario (sin dependencias externas).
    - Muestra mes actual con navegación.
    - Devuelve un date via callback on_pick(date).
    - Bloquea fechas menores a min_date.
    """

    def __init__(self, parent: tk.Misc, title: str, min_date: _dt.date, on_pick):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._min_date = min_date
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
            ttk.Label(self.grid_frame, text=d, anchor="center", width=4, font=("Segoe UI", 9, "bold")).grid(
                row=0, column=c, padx=2, pady=(0, 4)
            )

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
                disabled = d < self._min_date

                btn = tk.Button(
                    self.grid_frame,
                    text=str(day),
                    width=4,
                    relief="groove",
                    bd=1,
                    font=("Segoe UI", 9),
                    cursor="hand2" if not disabled else "arrow",
                    state=("disabled" if disabled else "normal"),
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


class MatriculasView(ttk.Frame):
    """
    Entregable III – Gestión de Matrículas:
    - Matricular (grid de matrículas)
    - Consulta por curso (segundo grid)
    - Reporte estudiantes por curso (tercer grid)

    Nota:
    - Matricula_ID del grid es llave compuesta: Carnet|CursoCod|Periodo
    - Periodo se maneja internamente (por defecto: año actual)
    """

    def __init__(self, parent, usuario: str | None, db_user: str, db_pass: str, codigo_usuario: int):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self._estudiantes: list[tuple[str, str]] = []
        self._cursos: list[tuple[int, str]] = []
        self._estados: list[tuple[int, str]] = []
        self._docentes_por_curso: list[tuple[int, str]] = []

        self._selected_key: tuple[str, int, int] | None = None
        self._loaded = False

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(self, padding=12)
        left.grid(row=0, column=0, sticky="nsw")
        left.columnconfigure(1, weight=1)

        ttk.Label(left, text="Gestión de Matrículas", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        ttk.Label(left, text="Curso/Programa").grid(row=1, column=0, sticky="w", pady=4)
        self.cb_curso = ttk.Combobox(left, state="readonly", width=42)
        self.cb_curso.grid(row=1, column=1, sticky="ew", pady=4)
        self.cb_curso.bind("<<ComboboxSelected>>", self._on_curso_changed)

        ttk.Label(left, text="Docente").grid(row=2, column=0, sticky="w", pady=4)
        self.cb_docente = ttk.Combobox(left, state="readonly", width=42)
        self.cb_docente.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(left, text="Estudiante").grid(row=3, column=0, sticky="w", pady=4)
        self.cb_estudiante = ttk.Combobox(left, state="readonly", width=42)
        self.cb_estudiante.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(left, text="Fecha").grid(row=4, column=0, sticky="w", pady=4)
        fecha_row = ttk.Frame(left)
        fecha_row.grid(row=4, column=1, sticky="ew", pady=4)
        fecha_row.columnconfigure(0, weight=1)

        self.ent_fecha = ttk.Entry(fecha_row)
        self.ent_fecha.grid(row=0, column=0, sticky="ew")
        ttk.Button(fecha_row, text="📅", width=3, command=self._open_calendar).grid(row=0, column=1, padx=(6, 0))

        ttk.Label(left, text="Estado (auto)").grid(row=5, column=0, sticky="w", pady=4)
        self.ent_estado = ttk.Entry(left, state="readonly")
        self.ent_estado.grid(row=5, column=1, sticky="ew", pady=4)

        actions = ttk.LabelFrame(left, text="Acciones", padding=10)
        actions.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        ttk.Button(actions, text="Matricular", command=self.on_matricular).grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6)
        )
        ttk.Button(actions, text="Cambiar estado", command=self.on_cambiar_estado).grid(
            row=1, column=0, sticky="ew", padx=8, pady=6
        )
        ttk.Button(actions, text="Eliminar selección", command=self.on_eliminar).grid(
            row=1, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(actions, text="Consulta por Curso", command=self.on_consulta_por_curso).grid(
            row=2, column=0, sticky="ew", padx=8, pady=6
        )
        ttk.Button(actions, text="Reporte Estudiantes por curso", command=self.on_reporte).grid(
            row=2, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(actions, text="Volver a Listado (todas)", command=self.refresh_grid).grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 0)
        )

        right = ttk.Frame(self, padding=(0, 12, 12, 12))
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.nb = ttk.Notebook(right)
        self.nb.grid(row=0, column=0, sticky="nsew")

        self.tab_listado = ListadoMatriculasTab(self.nb)
        self.nb.add(self.tab_listado, text="Listado Matrículas")

        self.tab_consulta = ConsultaMatriculasTab(self.nb)
        self.nb.add(self.tab_consulta, text="Consulta por Curso")

        self.tab_reporte = ReporteEstudiantesTab(self.nb)
        self.nb.add(self.tab_reporte, text="Reporte Estudiantes")

        self.tab_listado.bind_select(lambda e: self._on_row_select(self.tab_listado.tree))
        self.tab_consulta.bind_select(lambda e: self._on_row_select(self.tab_consulta.tree))

        self.ensure_loaded()

    # ------------------------------------------------------------------
    # Carga / refresh
    # ------------------------------------------------------------------
    def ensure_loaded(self):
        if self._loaded:
            return
        self._load_lookups()
        self.refresh_grid()
        self._loaded = True

    def _load_lookups(self):
        self._estudiantes = []
        self._cursos = []
        self._estados = []
        self._docentes_por_curso = []

        data = m_ep.get_lookups(
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )

        self._estados = data.get("estados", []) or []
        self._cursos = data.get("cursos", []) or []

        self.cb_curso["values"] = [f"{cod} - {desc}" for cod, desc in self._cursos]
        self.cb_estudiante["values"] = []
        self.cb_estudiante.set("")
        self.cb_curso.set("")
        self.cb_docente["values"] = []
        self.cb_docente.set("")

        self.ent_fecha.delete(0, tk.END)
        self.ent_fecha.insert(0, _dt.date.today().isoformat())

        try:
            self.ent_estado.configure(state="normal")
            self.ent_estado.delete(0, tk.END)
            self.ent_estado.insert(0, "Se asigna automáticamente")
        finally:
            self.ent_estado.configure(state="readonly")

    def refresh_grid(self):
        try:
            rows = m_ep.listar_matriculas(
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar matrículas:\n{e}")
            rows = []

        self.tab_listado.fill_rows(rows)
        self.nb.select(0)
        self._selected_key = None

        # Si ya hay curso seleccionado, recargar elegibles para evitar que
        # sigan apareciendo estudiantes con matrícula activa recién creada.
        self._refresh_estudiantes_elegibles()

    # ------------------------------------------------------------------
    # Eventos / helpers
    # ------------------------------------------------------------------
    def _open_calendar(self):
        min_date = _dt.date.today()

        def _set(d: _dt.date):
            self.ent_fecha.delete(0, tk.END)
            self.ent_fecha.insert(0, d.isoformat())

        _CalendarPopup(self, "Seleccionar fecha", min_date=min_date, on_pick=_set)

    def _refresh_estudiantes_elegibles(self):
        """
        Carga en el combo únicamente estudiantes elegibles para el curso actual,
        idealmente excluyendo los que ya tienen matrícula activa.
        """
        curso_cod = self._parse_cod_from_combo(self.cb_curso.get())
        if not curso_cod:
            self.cb_estudiante["values"] = []
            self.cb_estudiante.set("")
            return

        periodo = _dt.date.today().year
        elegibles = m_ep.get_estudiantes_elegibles(
            db_user=self.db_user,
            db_pass=self.db_pass,
            curso_cod=int(curso_cod),
            periodo=int(periodo),
            codigo_usuario=self.codigo_usuario,
        ) or []

        self.cb_estudiante["values"] = [f"{c} - {n}" for c, n in elegibles]
        self.cb_estudiante.set("")

    def _on_curso_changed(self, _evt=None):
        curso_cod = self._parse_cod_from_combo(self.cb_curso.get())
        if not curso_cod:
            self.cb_docente["values"] = []
            self.cb_docente.set("")
            self.cb_estudiante["values"] = []
            self.cb_estudiante.set("")
            return

        docentes = m_ep.get_docentes_por_curso(
            db_user=self.db_user,
            db_pass=self.db_pass,
            curso_cod=int(curso_cod),
            codigo_usuario=self.codigo_usuario,
        ) or []

        self.cb_docente["values"] = [f"{c} - {n}" for c, n in docentes]
        self.cb_docente.set("")

        self._refresh_estudiantes_elegibles()

    def _on_row_select(self, tree: ttk.Treeview):
        sel = tree.selection()
        if not sel:
            self._selected_key = None
            return

        values = tree.item(sel[0], "values")
        if not values:
            self._selected_key = None
            return

        matricula_id = str(values[0])
        parts = matricula_id.split("|")
        if len(parts) != 3:
            self._selected_key = None
            return

        carnet = parts[0].strip()
        try:
            curso_cod = int(parts[1])
            periodo = int(parts[2])
        except Exception:
            self._selected_key = None
            return

        self._selected_key = (carnet, curso_cod, periodo)

    def _active_tree_for_actions(self) -> ttk.Treeview | None:
        idx = int(self.nb.index(self.nb.select()))
        if idx == 0:
            return self.tab_listado.tree
        if idx == 1:
            return self.tab_consulta.tree
        return None

    @staticmethod
    def _parse_carnet_from_combo(value: str) -> str | None:
        value = (value or "").strip()
        if not value:
            return None
        carnet = value.split(" - ", 1)[0].strip()
        return carnet or None

    @staticmethod
    def _parse_cod_from_combo(value: str) -> int | None:
        value = (value or "").strip()
        if not value:
            return None
        try:
            head = value.split("-", 1)[0].strip()
            return int(head)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def on_matricular(self):
        carnet = self._parse_carnet_from_combo(self.cb_estudiante.get())
        curso_cod = self._parse_cod_from_combo(self.cb_curso.get())
        docente_cod = self._parse_cod_from_combo(self.cb_docente.get())
        fecha_txt = (self.ent_fecha.get() or "").strip()

        if not carnet:
            messagebox.showwarning("Falta estudiante", "Selecciona un estudiante.")
            return
        if not curso_cod:
            messagebox.showwarning("Falta curso", "Selecciona un Curso/Programa.")
            return
        if not docente_cod:
            messagebox.showwarning("Falta docente", "Selecciona un Docente (según el curso).")
            return

        try:
            fdt = _dt.date.fromisoformat(fecha_txt)
            if fdt < _dt.date.today():
                messagebox.showwarning("Fecha inválida", "La fecha no puede ser inferior a la fecha actual.")
                return
        except Exception:
            messagebox.showwarning("Fecha inválida", "Ingresa la fecha en formato YYYY-MM-DD o usa el calendario.")
            return

        periodo = _dt.date.today().year

        try:
            ok = m_ep.matricular(
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
                carnet=carnet,
                curso_cod=int(curso_cod),
                docente_cod=int(docente_cod),
                fecha=fecha_txt,
                periodo=int(periodo),
            )
            if ok:
                messagebox.showinfo("Éxito", "Matrícula registrada correctamente.")
                self.refresh_grid()
                self._refresh_estudiantes_elegibles()
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo matricular.\n\nDetalle: {ex}")

    def on_cambiar_estado(self):
        tree = self._active_tree_for_actions()
        if tree is None:
            messagebox.showwarning("Acción no disponible", "Cambia al tab 'Listado' o 'Consulta por Curso' para modificar matrículas.")
            return

        if not self._selected_key:
            messagebox.showwarning("Sin selección", "Selecciona una matrícula del grid.")
            return

        carnet, curso_cod, periodo = self._selected_key

        estados_desc = [desc for _, desc in (self._estados or [])]
        if not estados_desc:
            messagebox.showerror("Sin estados", "No hay estados disponibles en dbo.Estado_General.")
            return

        win = tk.Toplevel(self)
        win.title("Cambiar estado")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        ttk.Label(win, text="Selecciona el nuevo estado:", padding=10).grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(win, state="readonly", values=estados_desc, width=28)
        cb.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        cb.current(0)

        btns = ttk.Frame(win, padding=10)
        btns.grid(row=2, column=0, sticky="ew")
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)

        def _ok():
            nuevo = (cb.get() or "").strip()
            if not nuevo:
                return
            try:
                m_ep.cambiar_estado(
                    db_user=self.db_user,
                    db_pass=self.db_pass,
                    codigo_usuario=self.codigo_usuario,
                    carnet=carnet,
                    curso_cod=int(curso_cod),
                    periodo=int(periodo),
                    nuevo_estado=nuevo,
                )
                messagebox.showinfo("Éxito", f"Estado actualizado a: {nuevo}")
                win.destroy()
                self._refresh_active_tab_after_mutation()
                self._refresh_estudiantes_elegibles()
            except Exception as ex:
                messagebox.showerror("Error", f"No se pudo cambiar el estado.\n\nDetalle: {ex}")

        ttk.Button(btns, text="Cancelar", command=win.destroy).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(btns, text="Aplicar", command=_ok).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _refresh_active_tab_after_mutation(self):
        idx = int(self.nb.index(self.nb.select()))
        if idx == 0:
            self.refresh_grid()
            return
        if idx == 1:
            self.on_consulta_por_curso()
            return

    def on_eliminar(self):
        tree = self._active_tree_for_actions()
        if tree is None:
            messagebox.showwarning("Acción no disponible", "Cambia al tab 'Listado' o 'Consulta por Curso' para eliminar matrículas.")
            return

        if not self._selected_key:
            messagebox.showwarning("Sin selección", "Selecciona una matrícula del grid.")
            return

        ok = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Deseas eliminar la matrícula seleccionada?\n\nEsta acción no se puede deshacer.",
        )
        if not ok:
            return

        carnet, curso_cod, periodo = self._selected_key

        try:
            m_ep.eliminar_matricula(
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
                carnet=carnet,
                curso_cod=int(curso_cod),
                periodo=int(periodo),
            )
            messagebox.showinfo("Éxito", "Matrícula eliminada correctamente.")
            self._refresh_active_tab_after_mutation()
            self._refresh_estudiantes_elegibles()
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo eliminar.\n\nDetalle: {ex}")

    def on_consulta_por_curso(self):
        curso_cod = self._parse_cod_from_combo(self.cb_curso.get())
        if not curso_cod:
            messagebox.showwarning("Falta curso", "Selecciona un Curso/Programa para consultar.")
            return

        try:
            rows = m_ep.listar_matriculas_por_curso(
                db_user=self.db_user,
                db_pass=self.db_pass,
                curso_cod=int(curso_cod),
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo consultar por curso:\n{e}")
            rows = []

        self.tab_consulta.fill_rows(rows)
        self.nb.select(1)
        self._selected_key = None

    def on_reporte(self):
        cur = self._parse_cod_from_combo(self.cb_curso.get())
        if not cur:
            messagebox.showwarning("Falta curso", "Selecciona un Curso/Programa para generar el reporte.")
            return

        try:
            data = m_ep.reporte_estudiantes_por_curso(
                db_user=self.db_user,
                db_pass=self.db_pass,
                curso_cod=int(cur),
                codigo_usuario=self.codigo_usuario,
            )
        except Exception as ex:
            messagebox.showerror("Error en reporte", f"No se pudo generar el reporte.\n\nDetalle: {ex}")
            data = []

        self.tab_reporte.fill_rows(data or [])
        self.nb.select(2)

        if not data:
            messagebox.showinfo("Reporte", "No hay matrículas para el curso seleccionado.")