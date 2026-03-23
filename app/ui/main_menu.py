# app/ui/main_menu.py
# Menú Principal + Mantenimientos con fichas.
# Estructura/Shell
# Docentes (CRUD REAL) vive en app/ui/mantenimientos/docentes_tab.py con lazy-load.

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

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
        db_user: str,
        db_pass: str,
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

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # -----------------------------
        # Sidebar (con scroll)
        # -----------------------------
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        # Canvas para scroll vertical
        sb_canvas = tk.Canvas(sidebar, bg="#1f2a35", highlightthickness=0)
        sb_canvas.pack(side="left", fill="both", expand=False)

        sb_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=sb_canvas.yview)
        sb_scroll.pack(side="right", fill="y")

        sb_canvas.configure(yscrollcommand=sb_scroll.set)

        # Frame real donde van los widgets
        sb_inner = ttk.Frame(sb_canvas, style="Sidebar.TFrame")
        sb_canvas.create_window((0, 0), window=sb_inner, anchor="nw")

        def _sb_on_configure(_evt=None):
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all"))

        sb_inner.bind("<Configure>", _sb_on_configure)

        # Scroll con rueda del mouse cuando el puntero está sobre el sidebar
        def _sb_on_mousewheel(event):
            sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        sb_canvas.bind_all("<MouseWheel>", _sb_on_mousewheel)

        # --- Contenido del sidebar ---
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
        add_menu_btn("Plan de Programas", "plan_programas", 7)
        add_menu_btn("Contenidos", "contenidos", 8)
        add_menu_btn("Malla Programas/Cursos", "malla", 9)

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

        # mostrar por defecto
        self.on_menu_click("mantenimiento")

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
        for k, b in self.menu_buttons.items():
            b.configure(bg="#2f445d" if k == key else "#223142")

        self._hide_all_views()

        if key == "mantenimiento":
            self.view_mantenimientos.grid()
            self.notebook.select(self.tab_inicio)

        elif key == "matricula_materias":
            self.view_matriculas_materia.grid()
            self.view_matriculas_materia.ensure_loaded()

        else:
            self.view_placeholder.grid()
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
            try:
                self.master.destroy()
            except Exception:
                self.destroy()
            return

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
    db_user: str,
    db_pass: str,
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
