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

        self._build_ui()
        self._load_lookups()
        self._set_defaults()

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        wrapper = ttk.Frame(self, padding=16)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Registro de Usuarios",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text="Creación de usuarios del sistema con rol principal y credenciales seguras.",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(wrapper)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        card = ttk.LabelFrame(body, text="Datos del usuario", padding=14)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Identificación:").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.entry_id_usuario = ttk.Entry(
            card,
            textvariable=self.var_id_usuario,
        )
        self.entry_id_usuario.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        ttk.Label(card, text="Usuario/Login:").grid(
            row=0, column=1, sticky="w", pady=(0, 4)
        )
        self.entry_usuario = ttk.Entry(
            card,
            textvariable=self.var_usuario,
        )
        self.entry_usuario.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(card, text="Nombre completo:").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.entry_nombre_usuario = ttk.Entry(
            card,
            textvariable=self.var_nombre_usuario,
        )
        self.entry_nombre_usuario.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        ttk.Label(card, text="Correo:").grid(
            row=2, column=1, sticky="w", pady=(0, 4)
        )
        self.entry_correo = ttk.Entry(
            card,
            textvariable=self.var_correo,
        )
        self.entry_correo.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(card, text="Tipo de usuario:").grid(
            row=4, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.cbo_tipo_usuario = ttk.Combobox(
            card,
            textvariable=self.var_tipo_usuario,
            state="readonly",
        )
        self.cbo_tipo_usuario.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        ttk.Label(card, text="Estado de usuario:").grid(
            row=4, column=1, sticky="w", pady=(0, 4)
        )
        self.cbo_estado_usuario = ttk.Combobox(
            card,
            textvariable=self.var_estado_usuario,
            state="readonly",
        )
        self.cbo_estado_usuario.grid(row=5, column=1, sticky="ew", pady=(0, 10))

        ttk.Label(card, text="Rol principal:").grid(
            row=6, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.cbo_rol = ttk.Combobox(
            card,
            textvariable=self.var_rol,
            state="readonly",
        )
        self.cbo_rol.grid(row=7, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        ttk.Checkbutton(
            card,
            text="Debe cambiar clave en el próximo inicio de sesión",
            variable=self.var_debe_cambiar,
        ).grid(row=7, column=1, sticky="w", pady=(0, 10))

        ttk.Label(card, text="Contraseña:").grid(
            row=8, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
        )
        self.entry_clave = ttk.Entry(
            card,
            textvariable=self.var_clave,
            show="*",
        )
        self.entry_clave.grid(row=9, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        ttk.Label(card, text="Confirmar contraseña:").grid(
            row=8, column=1, sticky="w", pady=(0, 4)
        )
        self.entry_confirmar_clave = ttk.Entry(
            card,
            textvariable=self.var_confirmar_clave,
            show="*",
        )
        self.entry_confirmar_clave.grid(row=9, column=1, sticky="ew", pady=(0, 10))

        acciones = ttk.Frame(body)
        acciones.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        acciones.columnconfigure(0, weight=1)

        btns = ttk.Frame(acciones)
        btns.grid(row=0, column=0, sticky="e")

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