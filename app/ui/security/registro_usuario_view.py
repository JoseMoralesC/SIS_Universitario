from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.core.error_handler import (
    handle_exception,
    show_info,
    show_warning,
)
from app.endpoints.security.usuarios_security_endpoints import (
    get_lookups_usuarios_security,
    create_usuario_security_endpoint,
)


class RegistroUsuarioView(ttk.Frame):
    """
    Vista de Registro de Usuarios del sistema.

    Reglas base:
    - Solo accesible por usuarios autorizados desde seguridad/permisos.
    - Registra un usuario con un único rol principal.
    - Usa lookups de BD para roles, tipos y estados.
    """

    def __init__(
        self,
        parent,
        usuario: str | None,
        db_user: str | None,
        db_pass: str | None,
        codigo_usuario: int,
    ):
        super().__init__(parent)

        self.usuario = usuario
        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.roles_data: list[dict] = []
        self.tipos_usuario_data: list[dict] = []
        self.estados_usuario_data: list[dict] = []

        self.rol_desc_to_id: dict[str, int] = {}
        self.tipo_desc_to_id: dict[str, int] = {}
        self.estado_desc_to_id: dict[str, int] = {}

        self.var_id_usuario = tk.StringVar()
        self.var_usuario = tk.StringVar()
        self.var_nombre_usuario = tk.StringVar()
        self.var_correo = tk.StringVar()
        self.var_tipo_usuario = tk.StringVar()
        self.var_estado_usuario = tk.StringVar()
        self.var_rol = tk.StringVar()
        self.var_clave = tk.StringVar()
        self.var_confirmar_clave = tk.StringVar()
        self.var_debe_cambiar = tk.BooleanVar(value=True)
        self.var_show_password = tk.BooleanVar(value=False)

        self._build_ui()
        self._load_lookups()
        self._set_defaults()
        self._bind_live_summary()

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        wrapper = ttk.Frame(self, padding=16)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=3)
        wrapper.columnconfigure(1, weight=2)
        wrapper.rowconfigure(1, weight=1)

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------
        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Registro de Usuarios",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text=(
                "Creación de usuarios del sistema con rol principal, tipo de usuario, "
                "estado inicial y credenciales seguras."
            ),
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        # -----------------------------------------------------
        # Panel principal izquierdo
        # -----------------------------------------------------
        left_panel = ttk.Frame(wrapper)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=0)
        left_panel.rowconfigure(2, weight=0)

        # Card principal
        form_card = ttk.LabelFrame(left_panel, text="Formulario de registro", padding=14)
        form_card.grid(row=0, column=0, sticky="nsew")
        form_card.columnconfigure(0, weight=1)
        form_card.rowconfigure(0, weight=0)
        form_card.rowconfigure(1, weight=0)
        form_card.rowconfigure(2, weight=0)

        # ---------------------------------------------
        # Sección 1: Información general
        # ---------------------------------------------
        sec_general = ttk.LabelFrame(form_card, text="Información general", padding=12)
        sec_general.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        sec_general.columnconfigure(0, weight=1)
        sec_general.columnconfigure(1, weight=1)

        ttk.Label(sec_general, text="Identificación").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.entry_id_usuario = ttk.Entry(
            sec_general,
            textvariable=self.var_id_usuario,
        )
        self.entry_id_usuario.grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )

        ttk.Label(sec_general, text="Usuario / Login").grid(
            row=0, column=1, sticky="w", pady=(0, 4)
        )
        self.entry_usuario = ttk.Entry(
            sec_general,
            textvariable=self.var_usuario,
        )
        self.entry_usuario.grid(
            row=1, column=1, sticky="ew", pady=(0, 10)
        )

        ttk.Label(sec_general, text="Nombre completo").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.entry_nombre_usuario = ttk.Entry(
            sec_general,
            textvariable=self.var_nombre_usuario,
        )
        self.entry_nombre_usuario.grid(
            row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )

        ttk.Label(sec_general, text="Correo").grid(
            row=2, column=1, sticky="w", pady=(0, 4)
        )
        self.entry_correo = ttk.Entry(
            sec_general,
            textvariable=self.var_correo,
        )
        self.entry_correo.grid(
            row=3, column=1, sticky="ew", pady=(0, 10)
        )

        # ---------------------------------------------
        # Sección 2: Clasificación del usuario
        # ---------------------------------------------
        sec_clasificacion = ttk.LabelFrame(form_card, text="Clasificación y acceso", padding=12)
        sec_clasificacion.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        sec_clasificacion.columnconfigure(0, weight=1)
        sec_clasificacion.columnconfigure(1, weight=1)
        sec_clasificacion.columnconfigure(2, weight=1)

        ttk.Label(sec_clasificacion, text="Tipo de usuario").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.cbo_tipo_usuario = ttk.Combobox(
            sec_clasificacion,
            textvariable=self.var_tipo_usuario,
            state="readonly",
        )
        self.cbo_tipo_usuario.grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )

        ttk.Label(sec_clasificacion, text="Estado inicial").grid(
            row=0, column=1, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.cbo_estado_usuario = ttk.Combobox(
            sec_clasificacion,
            textvariable=self.var_estado_usuario,
            state="readonly",
        )
        self.cbo_estado_usuario.grid(
            row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10)
        )

        ttk.Label(sec_clasificacion, text="Rol principal").grid(
            row=0, column=2, sticky="w", pady=(0, 4)
        )
        self.cbo_rol = ttk.Combobox(
            sec_clasificacion,
            textvariable=self.var_rol,
            state="readonly",
        )
        self.cbo_rol.grid(
            row=1, column=2, sticky="ew", pady=(0, 10)
        )

        ttk.Checkbutton(
            sec_clasificacion,
            text="Debe cambiar clave en el próximo inicio de sesión",
            variable=self.var_debe_cambiar,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # ---------------------------------------------
        # Sección 3: Seguridad
        # ---------------------------------------------
        sec_seguridad = ttk.LabelFrame(form_card, text="Seguridad", padding=12)
        sec_seguridad.grid(row=2, column=0, sticky="ew")
        sec_seguridad.columnconfigure(0, weight=1)
        sec_seguridad.columnconfigure(1, weight=1)

        ttk.Label(sec_seguridad, text="Contraseña").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.entry_clave = ttk.Entry(
            sec_seguridad,
            textvariable=self.var_clave,
            show="*",
        )
        self.entry_clave.grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )

        ttk.Label(sec_seguridad, text="Confirmar contraseña").grid(
            row=0, column=1, sticky="w", pady=(0, 4)
        )
        self.entry_confirmar_clave = ttk.Entry(
            sec_seguridad,
            textvariable=self.var_confirmar_clave,
            show="*",
        )
        self.entry_confirmar_clave.grid(
            row=1, column=1, sticky="ew", pady=(0, 10)
        )

        ttk.Checkbutton(
            sec_seguridad,
            text="Mostrar contraseñas",
            variable=self.var_show_password,
            command=self._toggle_password_visibility,
        ).grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Label(
            sec_seguridad,
            text="Recomendación: usa una clave segura y evita credenciales demasiado simples.",
            font=("Segoe UI", 9),
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # -----------------------------------------------------
        # Barra inferior de acciones
        # -----------------------------------------------------
        action_bar = ttk.Frame(left_panel)
        action_bar.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        action_bar.columnconfigure(0, weight=1)

        btns = ttk.Frame(action_bar)
        btns.grid(row=0, column=1, sticky="e")

        ttk.Button(
            btns,
            text="Limpiar",
            command=self._on_clear,
        ).grid(row=0, column=0, padx=(0, 8))

        ttk.Button(
            btns,
            text="Registrar usuario",
            command=self._on_save,
        ).grid(row=0, column=1)

        # -----------------------------------------------------
        # Panel derecho de apoyo visual
        # -----------------------------------------------------
        right_panel = ttk.Frame(wrapper)
        right_panel.grid(row=1, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=0)
        right_panel.rowconfigure(1, weight=1)

        resumen_card = ttk.LabelFrame(right_panel, text="Resumen del registro", padding=14)
        resumen_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        resumen_card.columnconfigure(1, weight=1)

        self.var_resumen_id = tk.StringVar(value="-")
        self.var_resumen_usuario = tk.StringVar(value="-")
        self.var_resumen_nombre = tk.StringVar(value="-")
        self.var_resumen_correo = tk.StringVar(value="-")
        self.var_resumen_tipo = tk.StringVar(value="-")
        self.var_resumen_estado = tk.StringVar(value="-")
        self.var_resumen_rol = tk.StringVar(value="-")
        self.var_resumen_clave = tk.StringVar(value="Pendiente")

        self._add_summary_field(resumen_card, "Identificación:", self.var_resumen_id, 0)
        self._add_summary_field(resumen_card, "Usuario:", self.var_resumen_usuario, 1)
        self._add_summary_field(resumen_card, "Nombre:", self.var_resumen_nombre, 2)
        self._add_summary_field(resumen_card, "Correo:", self.var_resumen_correo, 3)
        self._add_summary_field(resumen_card, "Tipo:", self.var_resumen_tipo, 4)
        self._add_summary_field(resumen_card, "Estado:", self.var_resumen_estado, 5)
        self._add_summary_field(resumen_card, "Rol:", self.var_resumen_rol, 6)
        self._add_summary_field(resumen_card, "Clave:", self.var_resumen_clave, 7)

        ayuda_card = ttk.LabelFrame(right_panel, text="Guía rápida", padding=14)
        ayuda_card.grid(row=1, column=0, sticky="nsew")
        ayuda_card.columnconfigure(0, weight=1)

        ttk.Label(
            ayuda_card,
            text=(
                "• Completa primero la identificación, usuario y nombre.\n\n"
                "• Selecciona el tipo, estado y rol principal.\n\n"
                "• Si agregas correo, se almacenará como dato de contacto.\n\n"
                "• La opción 'Debe cambiar clave' obliga al usuario a renovar "
                "su contraseña al iniciar sesión.\n\n"
                "• Antes de guardar, revisa el resumen para confirmar que todo "
                "quede correcto."
            ),
            justify="left",
            wraplength=300,
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="nw")

    def _add_summary_field(
        self,
        parent: ttk.Frame,
        label_text: str,
        variable: tk.StringVar,
        row: int,
    ) -> None:
        ttk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=4)

        ttk.Label(
            parent,
            textvariable=variable,
            wraplength=220,
            justify="left",
        ).grid(row=row, column=1, sticky="nw", pady=4)

    # =========================================================
    # Lookups
    # =========================================================
    def _load_lookups(self) -> None:
        try:
            data = get_lookups_usuarios_security(
                db_user=self.db_user,
                db_pass=self.db_pass,
            )

            self.roles_data = list(data.get("roles", []))
            self.tipos_usuario_data = list(data.get("tipos_usuario", []))
            self.estados_usuario_data = list(data.get("estados_usuario", []))

            self.rol_desc_to_id.clear()
            self.tipo_desc_to_id.clear()
            self.estado_desc_to_id.clear()

            roles_values: list[str] = []
            for item in self.roles_data:
                label = f"{item['nombre_rol']} ({item['codigo_rol']})"
                roles_values.append(label)
                self.rol_desc_to_id[label] = int(item["rol_id"])

            tipos_values: list[str] = []
            for item in self.tipos_usuario_data:
                label = f"{item['descripcion_tipo']} ({item['tipo_usuario']})"
                tipos_values.append(label)
                self.tipo_desc_to_id[label] = int(item["tipo_usuario"])

            estados_values: list[str] = []
            for item in self.estados_usuario_data:
                label = f"{item['descripcion_estado']} ({item['estado_usuario']})"
                estados_values.append(label)
                self.estado_desc_to_id[label] = int(item["estado_usuario"])

            self.cbo_rol["values"] = roles_values
            self.cbo_tipo_usuario["values"] = tipos_values
            self.cbo_estado_usuario["values"] = estados_values

        except Exception as e:
            handle_exception(
                self,
                "No se pudieron cargar los datos base del módulo de registro.",
                e,
            )

    def _set_defaults(self) -> None:
        self.var_id_usuario.set("")
        self.var_usuario.set("")
        self.var_nombre_usuario.set("")
        self.var_correo.set("")
        self.var_clave.set("")
        self.var_confirmar_clave.set("")
        self.var_debe_cambiar.set(True)
        self.var_show_password.set(False)
        self._toggle_password_visibility()

        if self.cbo_tipo_usuario["values"]:
            self.cbo_tipo_usuario.current(0)
        else:
            self.var_tipo_usuario.set("")

        if self.cbo_estado_usuario["values"]:
            idx_activo = 0
            for i, item in enumerate(self.estados_usuario_data):
                desc = str(item.get("descripcion_estado", "")).strip().lower()
                if desc == "activo":
                    idx_activo = i
                    break
            self.cbo_estado_usuario.current(idx_activo)
        else:
            self.var_estado_usuario.set("")

        if self.cbo_rol["values"]:
            self.cbo_rol.current(0)
        else:
            self.var_rol.set("")

        self._refresh_summary()

    # =========================================================
    # Helpers
    # =========================================================
    def _get_selected_tipo_usuario_id(self) -> int | None:
        text = self.var_tipo_usuario.get().strip()
        return self.tipo_desc_to_id.get(text)

    def _get_selected_estado_usuario_id(self) -> int | None:
        text = self.var_estado_usuario.get().strip()
        return self.estado_desc_to_id.get(text)

    def _get_selected_rol_id(self) -> int | None:
        text = self.var_rol.get().strip()
        return self.rol_desc_to_id.get(text)

    def _validate_ui(self) -> bool:
        if not self.var_id_usuario.get().strip():
            show_warning("La identificación es obligatoria.")
            self.entry_id_usuario.focus_set()
            return False

        if not self.var_usuario.get().strip():
            show_warning("El usuario/login es obligatorio.")
            self.entry_usuario.focus_set()
            return False

        if not self.var_nombre_usuario.get().strip():
            show_warning("El nombre completo es obligatorio.")
            self.entry_nombre_usuario.focus_set()
            return False

        if not self._get_selected_tipo_usuario_id():
            show_warning("Debes seleccionar un tipo de usuario.")
            self.cbo_tipo_usuario.focus_set()
            return False

        if not self._get_selected_estado_usuario_id():
            show_warning("Debes seleccionar un estado de usuario.")
            self.cbo_estado_usuario.focus_set()
            return False

        if not self._get_selected_rol_id():
            show_warning("Debes seleccionar un rol principal.")
            self.cbo_rol.focus_set()
            return False

        if not self.var_clave.get():
            show_warning("La contraseña es obligatoria.")
            self.entry_clave.focus_set()
            return False

        if not self.var_confirmar_clave.get():
            show_warning("Debes confirmar la contraseña.")
            self.entry_confirmar_clave.focus_set()
            return False

        return True

    def _collect_payload(self) -> dict:
        tipo_usuario = self._get_selected_tipo_usuario_id()
        estado_usuario = self._get_selected_estado_usuario_id()
        rol_id = self._get_selected_rol_id()

        return {
            "id_usuario": self.var_id_usuario.get().strip(),
            "usuario": self.var_usuario.get().strip(),
            "nombre_usuario": self.var_nombre_usuario.get().strip(),
            "correo": self.var_correo.get().strip() or None,
            "tipo_usuario": tipo_usuario,
            "estado_usuario": estado_usuario,
            "rol_id": rol_id,
            "clave_plana": self.var_clave.get(),
            "confirmar_clave": self.var_confirmar_clave.get(),
            "debe_cambiar_clave": bool(self.var_debe_cambiar.get()),
        }

    def _toggle_password_visibility(self) -> None:
        show_char = "" if self.var_show_password.get() else "*"
        self.entry_clave.configure(show=show_char)
        self.entry_confirmar_clave.configure(show=show_char)

    def _bind_live_summary(self) -> None:
        observed_vars = [
            self.var_id_usuario,
            self.var_usuario,
            self.var_nombre_usuario,
            self.var_correo,
            self.var_tipo_usuario,
            self.var_estado_usuario,
            self.var_rol,
            self.var_clave,
        ]
        for var in observed_vars:
            var.trace_add("write", self._on_form_change)

    def _on_form_change(self, *_args) -> None:
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        self.var_resumen_id.set(self.var_id_usuario.get().strip() or "-")
        self.var_resumen_usuario.set(self.var_usuario.get().strip() or "-")
        self.var_resumen_nombre.set(self.var_nombre_usuario.get().strip() or "-")
        self.var_resumen_correo.set(self.var_correo.get().strip() or "-")
        self.var_resumen_tipo.set(self.var_tipo_usuario.get().strip() or "-")
        self.var_resumen_estado.set(self.var_estado_usuario.get().strip() or "-")
        self.var_resumen_rol.set(self.var_rol.get().strip() or "-")
        self.var_resumen_clave.set("Definida" if self.var_clave.get() else "Pendiente")

    # =========================================================
    # Eventos
    # =========================================================
    def _on_clear(self) -> None:
        self._set_defaults()
        self.entry_id_usuario.focus_set()

    def _on_save(self) -> None:
        try:
            if not self._validate_ui():
                return

            payload = self._collect_payload()

            confirmado = messagebox.askyesno(
                "Confirmar registro",
                "¿Deseas registrar este nuevo usuario del sistema?",
            )
            if not confirmado:
                return

            result = create_usuario_security_endpoint(
                self.db_user,
                self.db_pass,
                id_usuario=payload["id_usuario"],
                usuario=payload["usuario"],
                nombre_usuario=payload["nombre_usuario"],
                tipo_usuario=payload["tipo_usuario"],
                estado_usuario=payload["estado_usuario"],
                rol_id=payload["rol_id"],
                clave_plana=payload["clave_plana"],
                confirmar_clave=payload["confirmar_clave"],
                correo=payload["correo"],
                debe_cambiar_clave=payload["debe_cambiar_clave"],
                codigo_usuario=self.codigo_usuario,
            )

            data = result.get("data", {}) if isinstance(result, dict) else {}
            usuario_creado = data.get("usuario", payload["usuario"])
            codigo_creado = data.get("codigo_usuario", "-")

            show_info(
                self,
                "Registro de usuarios",
                f"Usuario registrado correctamente.\n\n"
                f"Usuario: {usuario_creado}\n"
                f"Código: {codigo_creado}"
            )

            self._on_clear()

        except Exception as e:
            handle_exception(
                self,
                "No fue posible registrar el usuario.",
                e,
            )