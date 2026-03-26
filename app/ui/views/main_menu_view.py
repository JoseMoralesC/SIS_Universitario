from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.core.session import (
    get_session,
    get_nombre_usuario,
    get_rol_codigo,
    get_rol_nombre,
)
from app.services.security.permission_service import can_access_module
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
        db_user: str | None,
        db_pass: str | None,
        codigo_usuario: int,
        on_exit_request=None
    ):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario
        self.on_exit_request = on_exit_request

        self.session_data = get_session() or {}
        self.nombre_usuario = get_nombre_usuario() or self.usuario or ""
        self.codigo_rol = (get_rol_codigo() or "").strip().upper()
        self.nombre_rol = get_rol_nombre() or self.codigo_rol or "SIN ROL"

        # Matrículas (lazy-load)
        self._matriculas_loaded = False
        self._matriculas_view = None

        # Matrícula por materias (lazy-load)
        self._matricula_materias_loaded = False
        self._matricula_materias_view = None

        # Asistencias (lazy-load)
        self._asistencias_loaded = False
        self._asistencias_view = None

        # Registro de usuarios (lazy-load)
        self._registro_loaded = False
        self._registro_view = None

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

    def _can_access_registro(self) -> bool:
        """
        Registro de usuarios del sistema:
        acceso exclusivo para ADMINISTRADOR.
        """
        return self.codigo_rol == "ADMIN"

    def _has_access(self, key: str) -> bool:
        access_map = {
            "mantenimiento": self._can_access_mantenimientos(),
            "registro": self._can_access_registro(),
            "asignacion_docentes": self._can_access_mantenimientos(),
            "matriculas": self._can_access_matriculas(),
            "matricula_materias": self._can_access_matricula_materias(),
            "asistencias": self._can_access_asistencias(),
        }
        return access_map.get(key, False)

    def _deny_access(self, key: str) -> None:
        mensajes = {
            "mantenimiento": "Tu rol actual no tiene acceso al módulo de Mantenimientos.",
            "registro": "Tu rol actual no tiene acceso al módulo de Registro de Usuarios.",
            "asignacion_docentes": "Tu rol actual no tiene acceso a Asignación de Docentes.",
            "matriculas": "Tu rol actual no tiene acceso al módulo de Matrículas.",
            "matricula_materias": "Tu rol actual no tiene acceso al módulo de Matrícula por Materias.",
            "asistencias": "Tu rol actual no tiene acceso al módulo de Asistencias.",
        }
        messagebox.showwarning(
            "Acceso restringido",
            mensajes.get(key, "No tienes permisos para acceder a este módulo.")
        )

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # =====================================================
        # Sidebar fijo (SIN scroll)
        # =====================================================
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        sb_inner = ttk.Frame(sidebar, style="Sidebar.TFrame")
        sb_inner.grid(row=0, column=0, sticky="nsew")
        sb_inner.columnconfigure(0, weight=1)

        nombre_txt = f"Nombre: {self.nombre_usuario}" if self.nombre_usuario else "Nombre: -"
        ttk.Label(
            sb_inner,
            text=nombre_txt,
            style="SidebarUser.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(18, 4))

        rol_txt = f"Rol: {self.nombre_rol}" if self.nombre_rol else "Rol: SIN ROL"
        ttk.Label(
            sb_inner,
            text=rol_txt,
            style="SidebarUser.TLabel"
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

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

        add_menu_btn("Mantenimiento", "mantenimiento", 2, self._can_access_mantenimientos())
        add_menu_btn("Registro", "registro", 3, self._can_access_registro())
        add_menu_btn("Matrículas", "matriculas", 4, self._can_access_matriculas())
        add_menu_btn(
            "Matrícula por Materias",
            "matricula_materias",
            5,
            self._can_access_matricula_materias(),
        )
        add_menu_btn("Asistencias", "asistencias", 6, self._can_access_asistencias())
        add_menu_btn(
            "Asignación Docentes",
            "asignacion_docentes",
            7,
            self._can_access_mantenimientos(),
        )

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
        # View: Registro (lazy-load)
        # =====================================================
        self.view_registro = ttk.Frame(self.content)
        self.view_registro.grid(row=0, column=0, sticky="nsew")
        self.view_registro.rowconfigure(0, weight=1)
        self.view_registro.columnconfigure(0, weight=1)

        self._registro_placeholder_label = ttk.Label(
            self.view_registro,
            text="Módulo Registro en construcción.\n(Alta de usuarios del sistema)",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self._registro_placeholder_label.grid(row=0, column=0, sticky="nsew")

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
            text="Módulo en construcción.",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self.placeholder_label.grid(row=0, column=0, sticky="nsew")

        default_key = self._get_default_menu_key()
        self.on_menu_click(default_key)

    def _get_default_menu_key(self) -> str:
        preferred_order = [
            "mantenimiento",
            "registro",
            "matriculas",
            "matricula_materias",
            "asistencias",
            "asignacion_docentes",
        ]
        for key in preferred_order:
            if self._has_access(key):
                return key
        return "placeholder"

    def _hide_all_views(self):
        self.view_mantenimientos.grid_remove()
        self.view_registro.grid_remove()
        self.view_matriculas.grid_remove()
        self.view_matricula_materias.grid_remove()
        self.view_asistencias.grid_remove()
        self.view_placeholder.grid_remove()

    def _ensure_registro_loaded(self):
        """
        Carga (una sola vez) la vista real de Registro de Usuarios.
        Si falla el import o la construcción, muestra el error real.
        """
        if self._registro_loaded:
            return

        try:
            from app.ui.security.registro_usuario_view import RegistroUsuarioView  # type: ignore

            try:
                if self._registro_placeholder_label is not None:
                    self._registro_placeholder_label.destroy()
                    self._registro_placeholder_label = None
            except Exception:
                pass

            self._registro_view = RegistroUsuarioView(
                self.view_registro,
                usuario=self.usuario,
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
            self._registro_view.grid(row=0, column=0, sticky="nsew")

            self._registro_loaded = True

        except Exception as e:
            self._registro_loaded = False
            self._registro_view = None
            messagebox.showerror(
                "Error cargando Registro",
                f"No se pudo cargar el módulo.\n\nDetalle:\n{e}"
            )

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
            self.view_mantenimientos.select_home()

        elif key == "registro":
            self.view_registro.grid()
            self._ensure_registro_loaded()

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
                        "Pendiente de implementación."
                    )
                )

    def on_exit(self):
        salir_todo = messagebox.askyesno(
            "Salir",
            "¿Deseas salir del sistema?\n\nSI: se cierra todo.\nNO: vuelves al Welcome."
        )
        if callable(self.on_exit_request):
            self.on_exit_request(salir_todo)