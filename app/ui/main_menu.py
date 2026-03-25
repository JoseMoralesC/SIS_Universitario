# app/ui/main_menu.py
# Menú Principal + Mantenimientos con fichas.
# Estructura/Shell
# Docentes (CRUD REAL) vive en app/ui/mantenimientos/docentes_tab.py con lazy-load.

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.core.session import (
    get_session,
    get_nombre_usuario,
    get_rol_codigo,
    get_rol_nombre,
    clear_session,
)
from app.services.security.permission_service import can_access_module
from app.ui.theme import apply_theme
from app.ui.mantenimientos.base_tab import MaintenanceTab
from app.ui.mantenimientos.docentes_tab import DocentesTab
from app.ui.mantenimientos.cursos_tab import CursosTab
from app.ui.mantenimientos.estudiantes_tab import EstudiantesTab
from app.ui.mantenimientos.programas_tab import ProgramasTab
from app.ui.mantenimientos.becas_tab import BecasTab
from app.ui.mantenimientos.becados_tab import BecadosTab
from app.ui.views.matriculas_materia_view import MatriculasMateriaView


class MainMenuWindow(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        usuario: str | None,
        db_user: str | None,
        db_pass: str | None,
        codigo_usuario: int | None = None,
        on_back_to_welcome=None,
    ):
        super().__init__(master)
        apply_theme(self)
        self._on_back_to_welcome = on_back_to_welcome

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.session_data = get_session() or {}
        self.nombre_usuario = get_nombre_usuario() or self.usuario or ""
        self.codigo_rol = (get_rol_codigo() or "").strip().upper()
        self.nombre_rol = get_rol_nombre() or self.codigo_rol or "SIN ROL"

        self.title("Sistema Administrativo Docente – Menú Moderno")
        self.minsize(1100, 620)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TNotebook.Tab", padding=(6, 4))
        style.configure("Sidebar.TFrame", background="#1f2a35")
        style.configure(
            "SidebarTitle.TLabel",
            background="#1f2a35",
            foreground="white",
            font=("Segoe UI", 14, "bold"),
        )
        style.configure(
            "SidebarUser.TLabel",
            background="#1f2a35",
            foreground="#c7d2e0",
            font=("Segoe UI", 10),
        )

        self.menu_buttons: dict[str, tk.Button] = {}
        self._menu_definitions: dict[str, dict] = {}

        self._build_ui()

    # =====================================================
    # Permisos / acceso
    # =====================================================
    def _can_access_mantenimientos(self) -> bool:
        return can_access_module("mantenimientos")

    def _can_access_matriculas(self) -> bool:
        return can_access_module("matriculas")

    def _can_access_matricula_materias(self) -> bool:
        return can_access_module("matricula_materias")

    def _can_access_asistencias(self) -> bool:
        return can_access_module("asistencias")

    def _has_access(self, key: str) -> bool:
        access_map = {
            "mantenimiento": self._can_access_mantenimientos(),
            "matriculas": self._can_access_matriculas(),
            "matricula_materias": self._can_access_matricula_materias(),
            "asistencias": self._can_access_asistencias(),
            "asignacion_docentes": self._can_access_mantenimientos(),
            "plan_programas": self._can_access_mantenimientos(),
            "contenidos": self._can_access_mantenimientos(),
            "malla": self._can_access_mantenimientos(),
        }
        return access_map.get(key, False)

    def _deny_access(self, key: str) -> None:
        mensajes = {
            "mantenimiento": "Tu rol actual no tiene acceso al módulo de Mantenimientos.",
            "matriculas": "Tu rol actual no tiene acceso al módulo de Matrículas.",
            "matricula_materias": "Tu rol actual no tiene acceso al módulo de Matrícula por Materias.",
            "asistencias": "Tu rol actual no tiene acceso al módulo de Asistencias.",
            "asignacion_docentes": "Tu rol actual no tiene acceso a Asignación de Docentes.",
            "plan_programas": "Tu rol actual no tiene acceso a Plan de Programas.",
            "contenidos": "Tu rol actual no tiene acceso a Contenidos.",
            "malla": "Tu rol actual no tiene acceso a Malla Programas/Cursos.",
        }
        messagebox.showwarning(
            "Acceso restringido",
            mensajes.get(key, "No tienes permisos para acceder a este módulo."),
        )

    def _get_default_menu_key(self) -> str:
        preferred_order = [
            "mantenimiento",
            "matricula_materias",
            "matriculas",
            "asistencias",
            "asignacion_docentes",
            "plan_programas",
            "contenidos",
            "malla",
        ]
        for key in preferred_order:
            if self._has_access(key):
                return key
        return "placeholder"

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # -----------------------------
        # Sidebar (con scroll)
        # -----------------------------
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
            try:
                sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        sb_canvas.bind_all("<MouseWheel>", _sb_on_mousewheel)

        ttk.Label(
            sb_inner,
            text="Admin Docente",
            style="SidebarTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(18, 8))

        user_txt = f"Usuario: {self.usuario}" if self.usuario else "Usuario: (no autenticado)"
        ttk.Label(
            sb_inner,
            text=user_txt,
            style="SidebarUser.TLabel",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        nombre_txt = f"Nombre: {self.nombre_usuario}" if self.nombre_usuario else "Nombre: -"
        ttk.Label(
            sb_inner,
            text=nombre_txt,
            style="SidebarUser.TLabel",
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 4))

        rol_txt = f"Rol: {self.nombre_rol}" if self.nombre_rol else "Rol: SIN ROL"
        ttk.Label(
            sb_inner,
            text=rol_txt,
            style="SidebarUser.TLabel",
        ).grid(row=3, column=0, sticky="w", padx=16, pady=(0, 16))

        def add_menu_btn(text: str, key: str, row: int, enabled: bool = True):
            btn = tk.Button(
                sb_inner,
                text=text,
                bg="#223142" if enabled else "#3d4852",
                fg="white" if enabled else "#c6cbd1",
                activebackground="#2f445d" if enabled else "#3d4852",
                activeforeground="white",
                relief="groove",
                bd=2,
                font=("Segoe UI", 11, "bold"),
                cursor="hand2" if enabled else "arrow",
                padx=8,
                pady=10,
                state="normal" if enabled else "disabled",
                command=lambda: self.on_menu_click(key),
            )
            btn.grid(row=row, column=0, sticky="ew", padx=14, pady=6)
            self.menu_buttons[key] = btn
            self._menu_definitions[key] = {
                "text": text,
                "enabled": enabled,
            }

        add_menu_btn("Mantenimiento", "mantenimiento", 4, self._can_access_mantenimientos())
        add_menu_btn("Matrículas", "matriculas", 5, self._can_access_matriculas())
        add_menu_btn(
            "Matrícula por Materias",
            "matricula_materias",
            6,
            self._can_access_matricula_materias(),
        )
        add_menu_btn("Asistencias", "asistencias", 7, self._can_access_asistencias())
        add_menu_btn("Asignación Docentes", "asignacion_docentes", 8, self._can_access_mantenimientos())
        add_menu_btn("Plan de Programas", "plan_programas", 9, self._can_access_mantenimientos())
        add_menu_btn("Contenidos", "contenidos", 10, self._can_access_mantenimientos())
        add_menu_btn("Malla Programas/Cursos", "malla", 11, self._can_access_mantenimientos())

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
        btn_salir.grid(row=20, column=0, sticky="ew", padx=14, pady=(18, 14))

        self.update_idletasks()
        req_w = sb_inner.winfo_reqwidth()
        target_w = req_w + 8
        sidebar.configure(width=target_w)
        sb_canvas.configure(width=target_w)

        # -----------------------------
        # Área derecha
        # -----------------------------
        self.content = ttk.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # =====================================================
        # VIEW: MANTENIMIENTOS
        # =====================================================
        self.view_mantenimientos = ttk.Frame(self.content)
        self.view_mantenimientos.grid(row=0, column=0, sticky="nsew")
        self.view_mantenimientos.rowconfigure(0, weight=1)
        self.view_mantenimientos.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.view_mantenimientos)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.tab_inicio = ttk.Frame(self.notebook)
        msg = ttk.Label(
            self.tab_inicio,
            text=(
                "¡Bienvenido a Mantenimientos!\n\n"
                "Desde aquí podrás administrar la información del sistema de forma ordenada y rápida.\n\n"
                "• Selecciona una pestaña para acceder a su formulario y listado.\n"
                "• Los datos se cargan cuando entras a cada sección, para mantener un mejor rendimiento.\n"
                "• Si alguna pestaña aún está en construcción, se habilitará más adelante automáticamente."
            ),
            anchor="center",
            font=("Segoe UI", 13),
        )
        msg.pack(expand=True, fill="both", padx=20, pady=20)

        self.tab_docentes = DocentesTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
        )
        self.tab_cursos = CursosTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
        )
        self.tab_estudiantes = EstudiantesTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
        )
        self.tab_programas = ProgramasTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
        )
        self.tab_becas = BecasTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
        )
        self.tab_becados = BecadosTab(
            self.notebook,
            db_user=self.db_user,
            db_pass=self.db_pass,
        )

        self.notebook.add(self.tab_inicio, text="Inicio")
        self.notebook.add(self.tab_docentes, text="Docentes")
        self.notebook.add(self.tab_cursos, text="Cursos")
        self.notebook.add(self.tab_estudiantes, text="Estudiantes")
        self.notebook.add(self.tab_programas, text="Programas")
        self.notebook.add(self.tab_becas, text="Becas")
        self.notebook.add(self.tab_becados, text="Becados")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # =====================================================
        # VIEW: MATRÍCULA POR MATERIAS
        # =====================================================
        self.view_matriculas_materia = MatriculasMateriaView(
            self.content,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.view_matriculas_materia.grid(row=0, column=0, sticky="nsew")
        self.view_matriculas_materia.grid_remove()

        # =====================================================
        # VIEW: PLACEHOLDER OTRAS OPCIONES
        # =====================================================
        self.view_placeholder = ttk.Frame(self.content)
        self.view_placeholder.grid(row=0, column=0, sticky="nsew")
        self.view_placeholder.rowconfigure(0, weight=1)
        self.view_placeholder.columnconfigure(0, weight=1)

        self.placeholder_label = ttk.Label(
            self.view_placeholder,
            text=(
                "Módulo en construcción.\n"
                "(Para Entregable #3, el foco es: Matrículas, Asistencias y Reportes.\n"
                "Mantenimientos ya está completo desde el Entregable #2 y versionado como 3.0)"
            ),
            anchor="center",
            font=("Segoe UI", 14),
        )
        self.placeholder_label.grid(row=0, column=0, sticky="nsew")

        default_key = self._get_default_menu_key()
        self.on_menu_click(default_key)

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
        elif current == str(self.tab_becas):
            self.tab_becas.ensure_loaded()
        elif current == str(self.tab_becados):
            self.tab_becados.ensure_loaded()

    def _hide_all_views(self):
        self.view_mantenimientos.grid_remove()
        self.view_matriculas_materia.grid_remove()
        self.view_placeholder.grid_remove()

    def on_menu_click(self, key: str):
        if key != "placeholder" and not self._has_access(key):
            self._deny_access(key)
            return

        for k, b in self.menu_buttons.items():
            enabled = self._menu_definitions.get(k, {}).get("enabled", True)
            if not enabled:
                b.configure(bg="#3d4852", fg="#c6cbd1")
            else:
                b.configure(bg="#2f445d" if k == key else "#223142", fg="white")

        self._hide_all_views()

        if key == "mantenimiento":
            self.view_mantenimientos.grid()
            self.notebook.select(self.tab_inicio)

        elif key == "asignacion_docentes":
            self.view_mantenimientos.grid()
            try:
                self.notebook.select(self.tab_inicio)
            except Exception:
                pass

        elif key == "plan_programas":
            self.view_placeholder.grid()
            self.placeholder_label.configure(
                text=(
                    "Módulo 'plan_programas' en construcción.\n"
                    "Queda reservado para funciones administrativas del sistema."
                )
            )

        elif key == "contenidos":
            self.view_placeholder.grid()
            self.placeholder_label.configure(
                text=(
                    "Módulo 'contenidos' en construcción.\n"
                    "Queda reservado para funciones administrativas del sistema."
                )
            )

        elif key == "malla":
            self.view_placeholder.grid()
            self.placeholder_label.configure(
                text=(
                    "Módulo 'malla' en construcción.\n"
                    "Queda reservado para funciones administrativas del sistema."
                )
            )

        elif key == "matricula_materias":
            self.view_matriculas_materia.grid()
            self.view_matriculas_materia.ensure_loaded()

        elif key == "matriculas":
            self.view_placeholder.grid()
            self.placeholder_label.configure(
                text=(
                    "Módulo 'matriculas' en construcción.\n"
                    "(Para Entregable #3, el foco es: Matrículas, Asistencias y Reportes.\n"
                    "Mantenimientos ya está completo desde el Entregable #2 y versionado como 3.0)"
                )
            )

        elif key == "asistencias":
            self.view_placeholder.grid()
            self.placeholder_label.configure(
                text=(
                    "Módulo 'asistencias' en construcción.\n"
                    "(Para Entregable #5, el foco es el registro de listas de asistencia)"
                )
            )

        else:
            self.view_placeholder.grid()
            if not any(self._has_access(k) for k in self.menu_buttons.keys()):
                self.placeholder_label.configure(
                    text=(
                        "Tu usuario no tiene módulos habilitados actualmente.\n"
                        "Consulta con el administrador del sistema."
                    )
                )
            else:
                self.placeholder_label.configure(
                    text=(
                        f"Módulo '{key}' en construcción.\n"
                        "(Para Entregable #3, el foco es: Matrículas, Asistencias y Reportes.\n"
                        "Mantenimientos ya está completo desde el Entregable #2 y versionado como 3.0)"
                    )
                )

    def on_exit(self):
        salir_todo = messagebox.askyesno(
            "Salir",
            "¿Deseas salir del sistema?\n\n"
            "SI: se cierra todo el programa.\n"
            "NO: se cierra el menú y vuelves al Welcome."
        )

        if salir_todo:
            clear_session()
            try:
                self.master.destroy()
            except Exception:
                self.destroy()
            return

        clear_session()

        if callable(getattr(self, "_on_back_to_welcome", None)):
            try:
                self._on_back_to_welcome(self)
            except TypeError:
                self.destroy()
                self._on_back_to_welcome()
        else:
            self.destroy()
            try:
                self.master.deiconify()
            except Exception:
                pass


def run_main_menu(
    usuario: str | None,
    db_user: str | None,
    db_pass: str | None,
    codigo_usuario: int | None = None,
    parent: tk.Misc | None = None,
    on_back_to_welcome=None,
    fullscreen: bool = True,
):
    # Modo integrado: el parent es WelcomeWindow (Tk ya existente)
    if parent is not None:
        win = MainMenuWindow(
            master=parent,
            usuario=usuario,
            db_user=db_user,
            db_pass=db_pass,
            codigo_usuario=codigo_usuario,
            on_back_to_welcome=on_back_to_welcome,
        )

        try:
            win.protocol("WM_DELETE_WINDOW", win.on_exit)
        except Exception:
            pass

        if fullscreen:
            try:
                win.state("zoomed")
            except Exception:
                pass

            try:
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                win.geometry(f"{sw}x{sh}+0+0")
            except Exception:
                pass

        win.focus_force()
        return win

    # Modo standalone: crea root oculto para soportar Toplevel
    root = tk.Tk()
    root.withdraw()

    win = MainMenuWindow(
        master=root,
        usuario=usuario,
        db_user=db_user,
        db_pass=db_pass,
        codigo_usuario=codigo_usuario,
        on_back_to_welcome=None,
    )

    try:
        win.protocol("WM_DELETE_WINDOW", win.on_exit)
    except Exception:
        pass

    if fullscreen:
        try:
            win.state("zoomed")
        except Exception:
            pass

        try:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            win.geometry(f"{sw}x{sh}+0+0")
        except Exception:
            pass

    win.focus_force()
    root.mainloop()
    return None