from __future__ import annotations

from tkinter import StringVar, ttk


class ListadoMatriculasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)

        # =========================
        # Layout principal
        # =========================
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Cache de datos para filtros / refresh
        self._all_rows: list[tuple] = []

        # =========================
        # Parte superior: filtro / form
        # =========================
        top_frame = ttk.LabelFrame(self, text="Filtros de matrícula", padding=10)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Curso:").grid(
            row=0, column=0, padx=(0, 8), pady=2, sticky="w"
        )

        self.curso_var = StringVar(value="Todos")
        self.cmb_curso = ttk.Combobox(
            top_frame,
            textvariable=self.curso_var,
            state="readonly",
            values=["Todos"],
        )
        self.cmb_curso.grid(row=0, column=1, padx=(0, 8), pady=2, sticky="ew")
        self.cmb_curso.bind("<<ComboboxSelected>>", self._on_curso_selected)

        self.btn_limpiar_filtro = ttk.Button(
            top_frame,
            text="Limpiar filtro",
            command=self.reset_filter,
        )
        self.btn_limpiar_filtro.grid(row=0, column=2, pady=2, sticky="e")

        # =========================
        # Parte inferior: grid
        # =========================
        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=1, column=0, sticky="nsew")
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        cols = ("Matricula_ID", "Estudiante", "Curso", "Docente", "Fecha", "Estado")
        self.tree = ttk.Treeview(grid_frame, columns=cols, show="headings", height=18)

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160, anchor="w")

        self.tree.column("Matricula_ID", width=160, anchor="center")
        self.tree.column("Fecha", width=110, anchor="center")
        self.tree.column("Estado", width=110, anchor="center")

        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def bind_select(self, callback):
        self.tree.bind("<<TreeviewSelect>>", callback)

    def fill_rows(self, rows: list[tuple]):
        """
        Carga todas las filas en caché y refresca el grid según el filtro actual.
        """
        self._all_rows = rows[:] if rows else []
        self._refresh_courses()
        self._apply_filter()

    def clear(self):
        self._all_rows = []
        self._clear_tree()
        self.cmb_curso["values"] = ["Todos"]
        self.curso_var.set("Todos")

    def reset_filter(self):
        self.curso_var.set("Todos")
        self._apply_filter()

    # ==========================================
    # Métodos internos
    # ==========================================
    def _on_curso_selected(self, event=None):
        self._apply_filter()

    def _refresh_courses(self):
        """
        Refresca las opciones del combobox de cursos a partir de los datos cargados.
        Se asume que la columna 'Curso' está en la posición 2.
        """
        cursos = sorted(
            {
                str(r[2]).strip()
                for r in self._all_rows
                if len(r) > 2 and str(r[2]).strip()
            }
        )

        values = ["Todos"] + cursos
        self.cmb_curso["values"] = values

        # Si el valor actual ya no existe, volver a "Todos"
        if self.curso_var.get() not in values:
            self.curso_var.set("Todos")

    def _apply_filter(self):
        """
        Aplica el filtro por curso y refresca el grid.
        """
        curso_sel = self.curso_var.get().strip()

        if not curso_sel or curso_sel == "Todos":
            filtered_rows = self._all_rows
        else:
            filtered_rows = [
                r
                for r in self._all_rows
                if len(r) > 2 and str(r[2]).strip() == curso_sel
            ]

        self._render_rows(filtered_rows)

    def _render_rows(self, rows: list[tuple]):
        self._clear_tree()

        for r in rows:
            try:
                self.tree.insert("", "end", values=r)
            except Exception:
                pass

    def _clear_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)