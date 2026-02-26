# app/ui/views/main_menu_view.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.ui.mantenimientos.docentes_tab import DocentesTab
from app.ui.mantenimientos.cursos_tab import CursosTab
from app.ui.mantenimientos.estudiantes_tab import EstudiantesTab
from app.ui.mantenimientos.programas_tab import ProgramasTab
from app.ui.mantenimientos.becas_tab import BecasTab
from app.ui.mantenimientos.becados_tab import BecadosTab


class MainMenuView(ttk.Frame):
    """
    Versión embebida del MainMenu.
    Vive dentro de WelcomeWindow (o cualquier parent Frame).
    """

    def __init__(self, parent, usuario: str | None, db_user: str, db_pass: str, codigo_usuario: int, on_exit_request=None):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario
        self.on_exit_request = on_exit_request  # callback para salir/volver a welcome

        self._build_ui()

    def _build_ui(self):


        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Sidebar (con scroll) - COPIA EXACTA de tu main_menu.py
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

        ttk.Label(sb_inner, text="Admin Docente", style="SidebarTitle.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(18, 8)
        )

        user_txt = f"Usuario: {self.usuario}" if self.usuario else "Usuario: (no autenticado)"
        ttk.Label(sb_inner, text=user_txt, style="SidebarUser.TLabel").grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 16)
        )

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

        # Ajuste ancho
        self.update_idletasks()
        req_w = sb_inner.winfo_reqwidth()
        target_w = req_w + 8
        sidebar.configure(width=target_w)
        sb_canvas.configure(width=target_w)

        # Área derecha
        self.content = ttk.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # View: Mantenimientos
        self.view_mantenimientos = ttk.Frame(self.content)
        self.view_mantenimientos.grid(row=0, column=0, sticky="nsew")
        self.view_mantenimientos.rowconfigure(0, weight=1)
        self.view_mantenimientos.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.view_mantenimientos)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # ---- TAB: Home / Decorativo (PRO) ----
        self.tab_home = ttk.Frame(self.notebook)

        # Layout 2 columnas
        wrap = ttk.Frame(self.tab_home)
        wrap.pack(fill="both", expand=True, padx=24, pady=24)
        wrap.columnconfigure(0, weight=0)  # imagen
        wrap.columnconfigure(1, weight=1)  # texto
        wrap.rowconfigure(0, weight=1)

        # Imagen (assets)
        # Cambiá el filename por el que vos vayas a usar en /assets
        img_label = ttk.Label(wrap)
        img_label.grid(row=0, column=0, sticky="n", padx=(0, 26), pady=(6, 0))

        # Texto
        txt = ttk.Frame(wrap)
        txt.grid(row=0, column=1, sticky="nsew")
        txt.columnconfigure(0, weight=1)

        ttk.Label(
            txt,
            text="Panel de Mantenimientos",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(
            txt,
            text="Administra la información del sistema de forma rápida y ordenada.",
            font=("Segoe UI", 12),
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        bullets = (
            "• Selecciona una pestaña para ver su formulario y listado.\n"
            "• Los datos se cargan al ingresar a cada sección para mejorar el rendimiento.\n"
            "• Usa Nuevo / Guardar / Actualizar / Eliminar según corresponda.\n"
            "• Si una pestaña está en construcción, se habilitará más adelante."
        )
        ttk.Label(
            txt,
            text=bullets,
            font=("Segoe UI", 12),
            justify="left",
        ).grid(row=2, column=0, sticky="w")

        ttk.Label(
            txt,
            text="Sugerencia: mantén el sistema actualizado para evitar inconsistencias.",
            font=("Segoe UI", 10, "italic"),
        ).grid(row=3, column=0, sticky="w", pady=(16, 0))

        # Cargar imagen si Pillow existe
        try:
            import os
            from PIL import Image, ImageTk

            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # app
            assets_dir = os.path.join(app_dir, "assets")
            img_path = os.path.join(assets_dir, "background.png")
            
            if os.path.exists(img_path):
                im = Image.open(img_path)
                im.thumbnail((320, 380))  # tamaño pro para tu layout
                self._home_img_ref = ImageTk.PhotoImage(im)
                img_label.configure(image=self._home_img_ref)
            else:
                img_label.configure(text="(Imagen no encontrada en assets)", font=("Segoe UI", 10))
        except Exception:
            img_label.configure(text="(Pillow no disponible)", font=("Segoe UI", 10))

        
        self.tab_docentes = DocentesTab(self.notebook, db_user=self.db_user, db_pass=self.db_pass, codigo_usuario=self.codigo_usuario)
        self.tab_cursos = CursosTab(self.notebook, db_user=self.db_user, db_pass=self.db_pass, codigo_usuario=self.codigo_usuario)
        self.tab_estudiantes = EstudiantesTab(self.notebook, db_user=self.db_user, db_pass=self.db_pass, codigo_usuario=self.codigo_usuario)
        self.tab_programas = ProgramasTab(self.notebook, db_user=self.db_user, db_pass=self.db_pass, codigo_usuario=self.codigo_usuario)
        self.tab_becas = BecasTab(self.notebook, db_user=self.db_user, db_pass=self.db_pass, codigo_usuario=self.codigo_usuario)
        self.tab_becados = BecadosTab(self.notebook, db_user=self.db_user, db_pass=self.db_pass, codigo_usuario=self.codigo_usuario)

        self.notebook.add(self.tab_home, text="Inicio")
        self.notebook.add(self.tab_docentes, text="Docentes")
        self.notebook.add(self.tab_cursos, text="Cursos")
        self.notebook.add(self.tab_estudiantes, text="Estudiantes")
        self.notebook.add(self.tab_programas, text="Programas")
        self.notebook.add(self.tab_becas, text="Becas")
        self.notebook.add(self.tab_becados, text="Becados")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)


        # Placeholder otras opciones
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
        elif current == str(self.tab_becados):
            self.tab_becados.ensure_loaded()
        elif current == str(self.tab_becas):
            self.tab_becas.ensure_loaded()    

    def on_menu_click(self, key: str):
        for k, b in self.menu_buttons.items():
            b.configure(bg="#2f445d" if k == key else "#223142")

        if key == "mantenimiento":
            self.view_placeholder.grid_remove()
            self.view_mantenimientos.grid()
            self.notebook.select(self.tab_home)
            self.tab_inicio = self.tab_home
        else:
            self.view_mantenimientos.grid_remove()
            self.view_placeholder.grid()
            self.placeholder_label.configure(
                text=f"Módulo '{key}' en construcción.\n(Entregable #2 se centra en Mantenimientos)"
            )

    def on_exit(self):
        salir_todo = messagebox.askyesno(
            "Salir",
            "¿Deseas salir del sistema?\n\nSI: se cierra todo.\nNO: vuelves al Welcome."
        )
        if callable(self.on_exit_request):
            self.on_exit_request(salir_todo)