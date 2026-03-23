from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.ui.views.mantenimientos_view import MantenimientosView


class MainMenuView(ttk.Frame):
    """
    Versión embebida del MainMenu (SHELL GENERAL).
    Vive dentro de WelcomeWindow (o cualquier parent Frame).
    """

    def __init__(
        self,
        parent,
        usuario: str | None,
        db_user: str,
        db_pass: str,
        codigo_usuario: int,
        on_exit_request=None
    ):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario
        self.on_exit_request = on_exit_request  # callback para salir/volver a welcome

        # Matrículas (lazy-load)
        self._matriculas_loaded = False
        self._matriculas_view = None

        # Matrícula por materias (lazy-load)
        self._matricula_materias_loaded = False
        self._matricula_materias_view = None

        # Asistencias (lazy-load)
        self._asistencias_loaded = False
        self._asistencias_view = None

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # =====================================================
        # Sidebar (con scroll)
        # =====================================================
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        sb_canvas = tk.Canvas(sidebar, bg="#1f2a35", highlightthickness=0)
        sb_canvas.pack(side="left", fill="both", expand=False)

        sb_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=sb_canvas.yview)
        sb_scroll.pack(side="right", fill="y")
        sb_canvas.configure(yscrollcommand=sb_scroll.set)

        sb_inner = ttk.Frame(sb_canvas, style="Sidebar.TFrame")
        sb_canvas.create_window((0, 0), window=sb_inner, anchor="nw")

        def _sb_on_configure(_evt=None):
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all"))

        sb_inner.bind("<Configure>", _sb_on_configure)

        def _sb_on_mousewheel(event):
            sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        sb_canvas.bind_all("<MouseWheel>", _sb_on_mousewheel)

        ttk.Label(
            sb_inner,
            text="Admin Docente",
            style="SidebarTitle.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(18, 8))

        user_txt = f"Usuario: {self.usuario}" if self.usuario else "Usuario: (no autenticado)"
        ttk.Label(
            sb_inner,
            text=user_txt,
            style="SidebarUser.TLabel"
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

        self.menu_buttons: dict[str, tk.Button] = {}

        def add_menu_btn(text: str, key: str, row: int):
            btn = tk.Button(
                sb_inner,
                text=text,
                bg="#223142",
                fg="white",
                activebackground="#2f445d",
                activeforeground="white",
                relief="groove",
                bd=2,
                font=("Segoe UI", 11, "bold"),
                cursor="hand2",
                padx=8,
                pady=10,
                command=lambda: self.on_menu_click(key),
            )
            btn.grid(row=row, column=0, sticky="ew", padx=14, pady=6)
            self.menu_buttons[key] = btn

        add_menu_btn("Mantenimiento", "mantenimiento", 2)
        add_menu_btn("Matrículas", "matriculas", 3)
        add_menu_btn("Matrícula por Materias", "matricula_materias", 4)
        add_menu_btn("Asistencias", "asistencias", 5)
        add_menu_btn("Asignación Docentes", "asignacion_docentes", 6)


        btn_salir = tk.Button(
            sb_inner,
            text="Salir",
            bg="#6b1d1d",
            fg="white",
            activebackground="#8a2727",
            activeforeground="white",
            relief="groove",
            bd=2,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            padx=8,
            pady=10,
            command=self.on_exit,
        )
        btn_salir.grid(row=10, column=0, sticky="ew", padx=14, pady=(18, 14))

        # Ajuste ancho sidebar
        self.update_idletasks()
        req_w = sb_inner.winfo_reqwidth()
        target_w = req_w + 8
        sidebar.configure(width=target_w)
        sb_canvas.configure(width=target_w)

        # =====================================================
        # Área derecha
        # =====================================================
        self.content = ttk.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # =====================================================
        # View: Mantenimientos
        # =====================================================
        self.view_mantenimientos = MantenimientosView(
            self.content,
            usuario=self.usuario,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.view_mantenimientos.grid(row=0, column=0, sticky="nsew")

        # =====================================================
        # View: Matrículas (lazy-load)
        # =====================================================
        self.view_matriculas = ttk.Frame(self.content)
        self.view_matriculas.grid(row=0, column=0, sticky="nsew")
        self.view_matriculas.rowconfigure(0, weight=1)
        self.view_matriculas.columnconfigure(0, weight=1)

        self._matriculas_placeholder_label = ttk.Label(
            self.view_matriculas,
            text="Módulo Matrículas en construcción.\n(Entregable #3: Matrículas)",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self._matriculas_placeholder_label.grid(row=0, column=0, sticky="nsew")

        # =====================================================
        # View: Matrícula por Materias (lazy-load)
        # =====================================================
        self.view_matricula_materias = ttk.Frame(self.content)
        self.view_matricula_materias.grid(row=0, column=0, sticky="nsew")
        self.view_matricula_materias.rowconfigure(0, weight=1)
        self.view_matricula_materias.columnconfigure(0, weight=1)

        self._matricula_materias_placeholder_label = ttk.Label(
            self.view_matricula_materias,
            text="Módulo Matrícula por Materias en construcción.\n(Backend listo, pendiente de integración UI embebida)",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self._matricula_materias_placeholder_label.grid(row=0, column=0, sticky="nsew")

        # =====================================================
        # View: Asistencias (lazy-load)
        # =====================================================
        self.view_asistencias = ttk.Frame(self.content)
        self.view_asistencias.grid(row=0, column=0, sticky="nsew")
        self.view_asistencias.rowconfigure(0, weight=1)
        self.view_asistencias.columnconfigure(0, weight=1)

        self._asistencias_placeholder_label = ttk.Label(
            self.view_asistencias,
            text="Módulo Asistencias en construcción.\n(Entregable #5: Registro de listas de asistencia)",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self._asistencias_placeholder_label.grid(row=0, column=0, sticky="nsew")

        # =====================================================
        # Placeholder general otras opciones
        # =====================================================
        self.view_placeholder = ttk.Frame(self.content)
        self.view_placeholder.grid(row=0, column=0, sticky="nsew")
        self.view_placeholder.rowconfigure(0, weight=1)
        self.view_placeholder.columnconfigure(0, weight=1)

        self.placeholder_label = ttk.Label(
            self.view_placeholder,
            text="Módulo en construcción.\n(Para Entregable #2, el foco es: Mantenimientos)",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self.placeholder_label.grid(row=0, column=0, sticky="nsew")

        self.on_menu_click("mantenimiento")

    def _hide_all_views(self):
        self.view_mantenimientos.grid_remove()
        self.view_matriculas.grid_remove()
        self.view_matricula_materias.grid_remove()
        self.view_asistencias.grid_remove()
        self.view_placeholder.grid_remove()

    def _ensure_matriculas_loaded(self):
        """
        Carga (una sola vez) la vista real de Matrículas.
        Si todavía no está creada, mantiene el placeholder sin romper la app.
        """
        if self._matriculas_loaded:
            return

        try:
            from app.ui.views.matriculas_view import MatriculasView  # type: ignore
        except Exception:
            self._matriculas_loaded = True
            self._matriculas_view = None
            return

        try:
            if self._matriculas_placeholder_label is not None:
                self._matriculas_placeholder_label.destroy()
                self._matriculas_placeholder_label = None
        except Exception:
            pass

        self._matriculas_view = MatriculasView(
            self.view_matriculas,
            usuario=self.usuario,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self._matriculas_view.grid(row=0, column=0, sticky="nsew")

        self._matriculas_loaded = True

    def _ensure_matricula_materias_loaded(self):
        """
        Carga (una sola vez) la vista real de Matrícula por Materias.
        Si falla el import o la construcción, muestra el error real.
        """
        if self._matricula_materias_loaded:
            return

        try:
            from app.ui.views.matriculas_materia_view import MatriculasMateriaView  # type: ignore

            try:
                if self._matricula_materias_placeholder_label is not None:
                    self._matricula_materias_placeholder_label.destroy()
                    self._matricula_materias_placeholder_label = None
            except Exception:
                pass

            self._matricula_materias_view = MatriculasMateriaView(
                self.view_matricula_materias,
                usuario=self.usuario,
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
            self._matricula_materias_view.grid(row=0, column=0, sticky="nsew")

            self._matricula_materias_loaded = True

        except Exception as e:
            self._matricula_materias_loaded = False
            self._matricula_materias_view = None
            messagebox.showerror(
                "Error cargando Matrícula por Materias",
                f"No se pudo cargar el módulo.\n\nDetalle:\n{e}"
            )

    def _ensure_asistencias_loaded(self):
        """
        Carga (una sola vez) la vista real de Asistencias.
        Si falla el import o la construcción, muestra el error real.
        """
        if self._asistencias_loaded:
            return

        try:
            from app.ui.asistencias.asistencias_tab import AsistenciasTab  # type: ignore

            try:
                if self._asistencias_placeholder_label is not None:
                    self._asistencias_placeholder_label.destroy()
                    self._asistencias_placeholder_label = None
            except Exception:
                pass

            self._asistencias_view = AsistenciasTab(
                self.view_asistencias,
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
            self._asistencias_view.grid(row=0, column=0, sticky="nsew")

            self._asistencias_loaded = True

        except Exception as e:
            self._asistencias_loaded = False
            self._asistencias_view = None
            messagebox.showerror(
                "Error cargando Asistencias",
                f"No se pudo cargar el módulo.\n\nDetalle:\n{e}"
            )

    def on_menu_click(self, key: str):
        for k, b in self.menu_buttons.items():
            b.configure(bg="#2f445d" if k == key else "#223142")

        self._hide_all_views()

        if key == "mantenimiento":
            self.view_mantenimientos.grid()
            self.view_mantenimientos.select_home()

        elif key == "asignacion_docentes":
            self.view_mantenimientos.grid()
            self.view_mantenimientos.select_asignacion()

        elif key == "matriculas":
            self.view_matriculas.grid()
            self._ensure_matriculas_loaded()

        elif key == "matricula_materias":
            self.view_matricula_materias.grid()
            self._ensure_matricula_materias_loaded()

        elif key == "asistencias":
            self.view_asistencias.grid()
            self._ensure_asistencias_loaded()

        else:
            self.view_placeholder.grid()
            self.placeholder_label.configure(
                text=(
                    f"Módulo '{key}' en construcción.\n"
                    "Para Entregable #3, el foco es: Matrículas, Asistencias y Reportes.\n"
                    "Mantenimientos ya está completo desde el Entregable #2 y versionado como 3.0"
                )
            )

    def on_exit(self):
        salir_todo = messagebox.askyesno(
            "Salir",
            "¿Deseas salir del sistema?\n\nSI: se cierra todo.\nNO: vuelves al Welcome."
        )
        if callable(self.on_exit_request):
            self.on_exit_request(salir_todo)