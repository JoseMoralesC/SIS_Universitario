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
from app.ui.components.toast import Toast
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

        self._perfil_loaded = False
        self._perfil_view = None

        self._auditoria_loaded = False
        self._auditoria_view = None

        self._matriculas_loaded = False
        self._matriculas_view = None

        self._matricula_materias_loaded = False
        self._matricula_materias_view = None

        self._asistencias_loaded = False
        self._asistencias_view = None

        self._registro_loaded = False
        self._registro_view = None

        self.menu_buttons: dict[str, tk.Button] = {}
        self._menu_definitions: dict[str, dict] = {}

        self._welcome_toast: Toast | None = None

        self._build_ui()
        self.after(300, self._show_role_welcome_toast)

    # =====================================================
    # Permisos / acceso
    # =====================================================
    def _can_access_mi_perfil(self) -> bool:
        return True

    def _can_access_auditoria(self) -> bool:
        return self.codigo_rol == "CONSULTA" or self._get_tipo_usuario() == 2

    def _can_access_mantenimientos(self) -> bool:
        return can_access_module("mantenimientos")

    def _can_access_matriculas(self) -> bool:
        return can_access_module("matriculas")

    def _can_access_matricula_materias(self) -> bool:
        return can_access_module("matricula_materias")

    def _can_access_asistencias(self) -> bool:
        return can_access_module("asistencias")

    def _can_access_registro(self) -> bool:
        return self.codigo_rol == "ADMIN"

    def _get_tipo_usuario(self) -> int | None:
        value = self.session_data.get("tipo_usuario")
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _has_access(self, key: str) -> bool:
        access_map = {
            "mi_perfil": self._can_access_mi_perfil(),
            "auditoria": self._can_access_auditoria(),
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
            "mi_perfil": "No fue posible acceder al perfil del usuario activo.",
            "auditoria": "Tu usuario no tiene acceso al módulo de Auditoría.",
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
    # Bienvenida por rol usando Toast
    # =====================================================
    def _get_role_welcome_profile(self) -> dict[str, str]:
        rol = (self.codigo_rol or "").strip().upper()
        nombre = self.nombre_usuario or self.usuario or "Usuario"

        perfiles = {
            "ADMIN": {
                "title": "Acceso al sistema",
                "message": (
                    f"Bienvenido {nombre} al Sistema de Gestión Académica\n\n"
                    "Perfil: Administrador\n\n"
                    "Tienes acceso administrativo del sistema.\n"
                    "Puedes gestionar usuarios, mantenimientos, parametrización y supervisar "
                    "el funcionamiento general de los módulos habilitados.\n\n"
                ),
            },
            "AUDITOR": {
                "title": "Acceso al sistema",
                "message": (
                    f"Bienvenido {nombre} al Sistema de Gestión Académica\n\n"
                    "Perfil: Auditor\n\n"
                    "Tu perfil está orientado a revisión, control y seguimiento.\n"
                    "Debes operar únicamente dentro de los módulos y consultas "
                    "habilitados para auditoría.\n\n"
                ),
            },
            "CONSULTA": {
                "title": "Acceso al sistema",
                "message": (
                    f"Bienvenido {nombre} al Sistema de Gestión Académica\n\n"
                    "Perfil: Consulta / Auditor\n\n"
                    "Tu acceso está orientado a revisión y análisis de movimientos del sistema.\n"
                    "Puedes consultar el módulo de auditoría según los permisos asignados.\n\n"
                ),
            },
            "DOCENTE": {
                "title": "Acceso al sistema",
                "message": (
                    f"Bienvenido {nombre} al Sistema de Gestión Académica\n\n"
                    "Perfil: Docente\n\n"
                    "Tu acceso está orientado exclusivamente al módulo de Asistencias.\n"
                    "Desde este perfil podrás registrar y consultar listas de asistencia "
                    "según los permisos asignados.\n\n"
                ),
            },
            "OPERADOR": {
                "title": "Acceso al sistema",
                "message": (
                    f"Bienvenido {nombre} al Sistema de Gestión Académica\n\n"
                    "Perfil: Operador\n\n"
                    "Tu perfil está orientado a la operación diaria y al registro de datos "
                    "en los módulos habilitados por permisos.\n\n"
                ),
            },
        }

        return perfiles.get(
            rol,
            {
                "title": "Acceso al sistema",
                "message": (
                    f"Bienvenido {nombre} al Sistema de Gestión Académica\n\n"
                    f"Perfil: {self.nombre_rol or 'Sin rol'}\n\n"
                    "Has iniciado sesión correctamente.\n"
                    "Tu acceso al sistema dependerá de los permisos asociados a tu rol."
                ),
            },
        )

    def _show_role_welcome_toast(self):
        profile = self._get_role_welcome_profile()

        try:
            if self._welcome_toast is not None and self._welcome_toast.winfo_exists():
                return
        except Exception:
            self._welcome_toast = None

        self._welcome_toast = Toast(
            parent=self,
            title=profile["title"],
            message=profile["message"],
            duration_ms=15000,
            width=700,
            bg="#0f1c2a",
            y_offset=-40,
            wrap_pad=50,
            margin=12,
            animate=True,
            step=20,
            delay_ms=18,
            slide_in_from="right",
            slide_out_to="right",
            slide_extra_px=180,
        )

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

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
            self._menu_definitions[key] = {
                "text": text,
                "enabled": True,
            }

        visible_menu_items = [
            ("Mi Perfil", "mi_perfil"),
            ("Auditoría", "auditoria"),
            ("Mantenimiento", "mantenimiento"),
            ("Registro", "registro"),
            ("Matrículas", "matriculas"),
            ("Matrícula por Materias", "matricula_materias"),
            ("Asistencias", "asistencias"),
            ("Asignación Docentes", "asignacion_docentes"),
        ]

        current_row = 2
        for text, key in visible_menu_items:
            if self._has_access(key):
                add_menu_btn(text, key, current_row)
                current_row += 1

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

        self.content = ttk.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # -------------------------------------------------
        # Mi Perfil
        # -------------------------------------------------
        self.view_perfil = ttk.Frame(self.content)
        self.view_perfil.grid(row=0, column=0, sticky="nsew")
        self.view_perfil.rowconfigure(0, weight=1)
        self.view_perfil.columnconfigure(0, weight=1)

        self._perfil_placeholder_label = ttk.Label(
            self.view_perfil,
            text="Módulo Mi Perfil en carga...",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self._perfil_placeholder_label.grid(row=0, column=0, sticky="nsew")

        # -------------------------------------------------
        # Auditoría
        # -------------------------------------------------
        self.view_auditoria = ttk.Frame(self.content)
        self.view_auditoria.grid(row=0, column=0, sticky="nsew")
        self.view_auditoria.rowconfigure(0, weight=1)
        self.view_auditoria.columnconfigure(0, weight=1)

        self._auditoria_placeholder_label = ttk.Label(
            self.view_auditoria,
            text="Módulo Auditoría en carga...",
            anchor="center",
            font=("Segoe UI", 14),
        )
        self._auditoria_placeholder_label.grid(row=0, column=0, sticky="nsew")

        # -------------------------------------------------
        # Mantenimientos
        # -------------------------------------------------
        self.view_mantenimientos = MantenimientosView(
            self.content,
            usuario=self.usuario,
            db_user=self.db_user,
            db_pass=self.db_pass,
            codigo_usuario=self.codigo_usuario,
        )
        self.view_mantenimientos.grid(row=0, column=0, sticky="nsew")

        # -------------------------------------------------
        # Registro
        # -------------------------------------------------
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

        # -------------------------------------------------
        # Matrículas
        # -------------------------------------------------
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

        # -------------------------------------------------
        # Matrícula por materias
        # -------------------------------------------------
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

        # -------------------------------------------------
        # Asistencias
        # -------------------------------------------------
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

        # -------------------------------------------------
        # Placeholder general
        # -------------------------------------------------
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
            "mi_perfil",
            "auditoria",
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
        self.view_perfil.grid_remove()
        self.view_auditoria.grid_remove()
        self.view_mantenimientos.grid_remove()
        self.view_registro.grid_remove()
        self.view_matriculas.grid_remove()
        self.view_matricula_materias.grid_remove()
        self.view_asistencias.grid_remove()
        self.view_placeholder.grid_remove()

    def _ensure_perfil_loaded(self):
        if self._perfil_loaded:
            return

        try:
            from app.ui.security.perfil_usuario_view import PerfilUsuarioView  # type: ignore

            try:
                if self._perfil_placeholder_label is not None:
                    self._perfil_placeholder_label.destroy()
                    self._perfil_placeholder_label = None
            except Exception:
                pass

            self._perfil_view = PerfilUsuarioView(
                self.view_perfil,
                usuario=self.usuario,
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
            self._perfil_view.grid(row=0, column=0, sticky="nsew")
            self._perfil_loaded = True

        except Exception as e:
            self._perfil_loaded = False
            self._perfil_view = None
            messagebox.showerror(
                "Error cargando Mi Perfil",
                f"No se pudo cargar el módulo.\n\nDetalle:\n{e}"
            )

    def _ensure_auditoria_loaded(self):
        if self._auditoria_loaded:
            return

        try:
            from app.ui.auditoria.auditoria_view import AuditoriaView  # type: ignore

            try:
                if self._auditoria_placeholder_label is not None:
                    self._auditoria_placeholder_label.destroy()
                    self._auditoria_placeholder_label = None
            except Exception:
                pass

            self._auditoria_view = AuditoriaView(
                self.view_auditoria,
                usuario=self.usuario,
                db_user=self.db_user,
                db_pass=self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
            self._auditoria_view.grid(row=0, column=0, sticky="nsew")
            self._auditoria_loaded = True

        except Exception as e:
            self._auditoria_loaded = False
            self._auditoria_view = None
            messagebox.showerror(
                "Error cargando Auditoría",
                f"No se pudo cargar el módulo.\n\nDetalle:\n{e}"
            )

    def _ensure_registro_loaded(self):
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
            b.configure(bg="#2f445d" if k == key else "#223142", fg="white")

        self._hide_all_views()

        if key == "mi_perfil":
            self.view_perfil.grid()
            self._ensure_perfil_loaded()

        elif key == "auditoria":
            self.view_auditoria.grid()
            self._ensure_auditoria_loaded()

        elif key == "mantenimiento":
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
            if not self.menu_buttons:
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
        try:
            if self._welcome_toast is not None and self._welcome_toast.winfo_exists():
                self._welcome_toast.close()
        except Exception:
            pass

        salir_todo = messagebox.askyesno(
            "Salir",
            "¿Deseas salir del sistema?\n\nSI: se cierra todo.\nNO: se cerrará la sesión actual y volverás al Welcome."
        )
        if callable(self.on_exit_request):
            self.on_exit_request(salir_todo)