from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog

from PIL import Image, ImageTk

from app.core.error_handler import (
    handle_exception,
    show_info,
    show_warning,
)
from app.endpoints.security.perfil_usuario_endpoints import (
    get_mi_perfil_endpoint,
    update_mi_perfil_endpoint,
    upload_mi_foto_perfil_endpoint,
    remove_mi_foto_perfil_endpoint,
)


class PerfilUsuarioView(ttk.Frame):
    """
    Vista de Perfil de Usuario.

    Permite al usuario con sesión activa:
    - visualizar su información general
    - editar datos no sensibles
    - cargar / reemplazar / quitar foto de perfil

    Campos editables:
    - usuario
    - nombre_usuario
    - correo

    Campos de solo lectura:
    - ids
    - tipo de usuario
    - estado
    - rol
    - fechas de control
    - seguridad
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

        self.current_profile: dict = {}
        self._photo_image = None
        self._last_loaded_photo_path: str | None = None

        # =====================================================
        # Variables editables
        # =====================================================
        self.var_usuario = tk.StringVar()
        self.var_nombre_usuario = tk.StringVar()
        self.var_correo = tk.StringVar()

        # =====================================================
        # Variables readonly
        # =====================================================
        self.var_usuario_seguridad_id = tk.StringVar()
        self.var_codigo_usuario = tk.StringVar()
        self.var_id_usuario = tk.StringVar()
        self.var_tipo_usuario = tk.StringVar()
        self.var_estado_usuario = tk.StringVar()
        self.var_rol = tk.StringVar()
        self.var_debe_cambiar_clave = tk.StringVar()
        self.var_intentos_fallidos = tk.StringVar()
        self.var_bloqueado_hasta = tk.StringVar()
        self.var_ultimo_acceso = tk.StringVar()
        self.var_ultimo_cambio_clave = tk.StringVar()
        self.var_fecha_creacion = tk.StringVar()
        self.var_fecha_modificacion = tk.StringVar()
        self.var_foto_filename = tk.StringVar()
        self.var_foto_estado = tk.StringVar()

        self._build_ui()
        self._load_profile()

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

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------
        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Mi Perfil",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text="Consulta y actualización de datos personales no sensibles del usuario activo.",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        # -----------------------------------------------------
        # Body
        # -----------------------------------------------------
        body = ttk.Frame(wrapper)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_photo_panel(body)
        self._build_form_panel(body)

    def _build_photo_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Foto de Perfil", padding=14)
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        panel.columnconfigure(0, weight=1)

        self.photo_preview = tk.Label(
            panel,
            text="Sin imagen",
            width=180,
            height=180,
            bg="#d9dee5",
            fg="#233142",
            relief="groove",
            bd=2,
            font=("Segoe UI", 10, "bold"),
            compound="center",
            anchor="center",
            justify="center",
            wraplength=170,
        )
        self.photo_preview.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(
            panel,
            textvariable=self.var_foto_estado,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(0, 4))

        ttk.Label(
            panel,
            textvariable=self.var_foto_filename,
            font=("Segoe UI", 9),
            wraplength=190,
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))

        ttk.Button(
            panel,
            text="Cambiar / Subir foto",
            command=self._on_upload_photo,
        ).grid(row=3, column=0, sticky="ew", pady=4)

        ttk.Button(
            panel,
            text="Quitar foto",
            command=self._on_remove_photo,
        ).grid(row=4, column=0, sticky="ew", pady=4)

        ttk.Button(
            panel,
            text="Recargar perfil",
            command=self._load_profile,
        ).grid(row=5, column=0, sticky="ew", pady=4)

    def _build_form_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        # -----------------------------------------------------
        # Datos editables
        # -----------------------------------------------------
        editable_box = ttk.LabelFrame(panel, text="Datos Editables", padding=14)
        editable_box.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        editable_box.columnconfigure(1, weight=1)
        editable_box.columnconfigure(3, weight=1)

        ttk.Label(editable_box, text="Usuario:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(editable_box, textvariable=self.var_usuario).grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(editable_box, text="Nombre de usuario:").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=6)
        ttk.Entry(editable_box, textvariable=self.var_nombre_usuario).grid(row=0, column=3, sticky="ew", pady=6)

        ttk.Label(editable_box, text="Correo:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(editable_box, textvariable=self.var_correo).grid(row=1, column=1, columnspan=3, sticky="ew", pady=6)

        actions = ttk.Frame(editable_box)
        actions.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        actions.columnconfigure(0, weight=1)

        buttons = ttk.Frame(actions)
        buttons.grid(row=0, column=1, sticky="e")

        ttk.Button(
            buttons,
            text="Guardar cambios",
            command=self._on_save,
        ).grid(row=0, column=0, padx=(0, 8))

        ttk.Button(
            buttons,
            text="Restaurar",
            command=self._restore_form_from_current_profile,
        ).grid(row=0, column=1)

        # -----------------------------------------------------
        # Datos solo lectura
        # -----------------------------------------------------
        readonly_box = ttk.LabelFrame(panel, text="Información del Sistema", padding=14)
        readonly_box.grid(row=1, column=0, sticky="nsew")
        readonly_box.columnconfigure(1, weight=1)
        readonly_box.columnconfigure(3, weight=1)

        self._add_readonly_field(readonly_box, "Usuario Seguridad ID:", self.var_usuario_seguridad_id, 0, 0)
        self._add_readonly_field(readonly_box, "Código Usuario:", self.var_codigo_usuario, 0, 2)

        self._add_readonly_field(readonly_box, "ID Usuario:", self.var_id_usuario, 1, 0)
        self._add_readonly_field(readonly_box, "Tipo Usuario:", self.var_tipo_usuario, 1, 2)

        self._add_readonly_field(readonly_box, "Estado:", self.var_estado_usuario, 2, 0)
        self._add_readonly_field(readonly_box, "Rol:", self.var_rol, 2, 2)

        self._add_readonly_field(readonly_box, "Debe cambiar clave:", self.var_debe_cambiar_clave, 3, 0)
        self._add_readonly_field(readonly_box, "Intentos fallidos:", self.var_intentos_fallidos, 3, 2)

        self._add_readonly_field(readonly_box, "Bloqueado hasta:", self.var_bloqueado_hasta, 4, 0)
        self._add_readonly_field(readonly_box, "Último acceso:", self.var_ultimo_acceso, 4, 2)

        self._add_readonly_field(readonly_box, "Último cambio clave:", self.var_ultimo_cambio_clave, 5, 0)
        self._add_readonly_field(readonly_box, "Fecha creación:", self.var_fecha_creacion, 5, 2)

        self._add_readonly_field(readonly_box, "Fecha modificación:", self.var_fecha_modificacion, 6, 0)

    def _add_readonly_field(
        self,
        parent: ttk.Frame,
        label_text: str,
        variable: tk.StringVar,
        row: int,
        col: int,
    ) -> None:
        ttk.Label(parent, text=label_text).grid(
            row=row,
            column=col,
            sticky="w",
            padx=(0, 8),
            pady=6,
        )
        ent = ttk.Entry(parent, textvariable=variable, state="readonly")
        ent.grid(
            row=row,
            column=col + 1,
            sticky="ew",
            pady=6,
            padx=(0, 12 if col == 0 else 0),
        )

    # =========================================================
    # Carga / render
    # =========================================================
    def _load_profile(self) -> None:
        try:
            result = get_mi_perfil_endpoint(
                self.db_user,
                self.db_pass,
                codigo_usuario=self.codigo_usuario,
            )
            data = result.get("data") or {}
            self.current_profile = data
            self._apply_profile_to_form(data)
        except Exception as e:
            handle_exception(
                self,
                e,
                context="Carga del perfil",
            )

    def _apply_profile_to_form(self, data: dict) -> None:
        self.var_usuario.set(self._safe_str(data.get("usuario")))
        self.var_nombre_usuario.set(self._safe_str(data.get("nombre_usuario")))
        self.var_correo.set(self._safe_str(data.get("correo")))

        self.var_usuario_seguridad_id.set(self._safe_str(data.get("usuario_seguridad_id")))
        self.var_codigo_usuario.set(self._safe_str(data.get("codigo_usuario")))
        self.var_id_usuario.set(self._safe_str(data.get("id_usuario")))

        tipo_desc = self._safe_str(data.get("descripcion_tipo"))
        tipo_id = self._safe_str(data.get("tipo_usuario"))
        self.var_tipo_usuario.set(self._combine_desc_and_id(tipo_desc, tipo_id))

        estado_desc = self._safe_str(data.get("descripcion_estado"))
        estado_id = self._safe_str(data.get("estado_usuario"))
        self.var_estado_usuario.set(self._combine_desc_and_id(estado_desc, estado_id))

        rol_nombre = self._safe_str(data.get("nombre_rol"))
        rol_codigo = self._safe_str(data.get("codigo_rol"))
        self.var_rol.set(self._combine_desc_and_id(rol_nombre, rol_codigo))

        self.var_debe_cambiar_clave.set("Sí" if bool(data.get("debe_cambiar_clave")) else "No")
        self.var_intentos_fallidos.set(self._safe_str(data.get("intentos_fallidos")))
        self.var_bloqueado_hasta.set(self._format_datetime(data.get("bloqueado_hasta")))
        self.var_ultimo_acceso.set(self._format_datetime(data.get("ultimo_acceso")))
        self.var_ultimo_cambio_clave.set(self._format_datetime(data.get("ultimo_cambio_clave")))
        self.var_fecha_creacion.set(self._format_datetime(data.get("fecha_creacion")))
        self.var_fecha_modificacion.set(self._format_datetime(data.get("fecha_modificacion")))

        self.var_foto_filename.set(f"Archivo: {self._safe_str(data.get('foto_filename')) or '-'}")

        if data.get("tiene_foto_personalizada"):
            self.var_foto_estado.set("Foto personalizada")
        else:
            self.var_foto_estado.set("Foto por defecto")

        self._render_profile_image(data.get("foto_path"))

    def _restore_form_from_current_profile(self) -> None:
        if not self.current_profile:
            show_warning(self, "Perfil", "No hay datos cargados para restaurar.")
            return
        self._apply_profile_to_form(self.current_profile)

    def _render_profile_image(self, image_path: str | None) -> None:
        self._photo_image = None
        self._last_loaded_photo_path = image_path

        path = str(image_path or "").strip()
        if not path:
            self.photo_preview.configure(
                image="",
                text="Sin imagen",
                width=180,
                height=180,
            )
            return

        try:
            normalized = Path(path)
            if not normalized.exists():
                self.photo_preview.configure(
                    image="",
                    text="Imagen no encontrada",
                    width=180,
                    height=180,
                )
                return

            img = Image.open(normalized)
            img = img.convert("RGBA")
            img.thumbnail((180, 180), Image.LANCZOS)

            canvas = Image.new("RGBA", (180, 180), (217, 222, 229, 255))
            x = (180 - img.width) // 2
            y = (180 - img.height) // 2
            canvas.paste(img, (x, y), img)

            self._photo_image = ImageTk.PhotoImage(canvas)

            self.photo_preview.configure(
                image=self._photo_image,
                text="",
                width=180,
                height=180,
            )
        except Exception:
            filename = os.path.basename(path)
            self.photo_preview.configure(
                image="",
                text=f"Imagen cargada\n\n{filename}",
                width=180,
                height=180,
            )

    # =========================================================
    # Eventos
    # =========================================================
    def _on_save(self) -> None:
        try:
            usuario_seguridad_id = self.current_profile.get("usuario_seguridad_id")
            if not usuario_seguridad_id:
                show_warning(
                    self,
                    "Perfil",
                    "No se pudo identificar el usuario activo para guardar cambios.",
                )
                return

            result = update_mi_perfil_endpoint(
                self.db_user,
                self.db_pass,
                usuario_seguridad_id=usuario_seguridad_id,
                codigo_usuario=self.codigo_usuario,
                usuario=self.var_usuario.get().strip(),
                nombre_usuario=self.var_nombre_usuario.get().strip(),
                correo=self.var_correo.get().strip() or None,
            )

            data = result.get("data") or {}
            self.current_profile = data
            self._apply_profile_to_form(data)

            show_info(
                self,
                "Perfil actualizado",
                result.get("message") or "Los cambios fueron guardados correctamente.",
            )
        except Exception as e:
            handle_exception(
                self,
                e,
                context="Actualización del perfil",
            )

    def _on_upload_photo(self) -> None:
        try:
            usuario_seguridad_id = self.current_profile.get("usuario_seguridad_id")
            if not usuario_seguridad_id:
                show_warning(
                    self,
                    "Foto de perfil",
                    "No se pudo identificar el usuario activo.",
                )
                return

            file_path = filedialog.askopenfilename(
                title="Seleccionar foto de perfil",
                filetypes=[
                    ("Imágenes", "*.png *.jpg *.jpeg *.gif *.webp"),
                    ("PNG", "*.png"),
                    ("JPG", "*.jpg"),
                    ("JPEG", "*.jpeg"),
                    ("GIF", "*.gif"),
                    ("WEBP", "*.webp"),
                    ("Todos los archivos", "*.*"),
                ],
            )

            if not file_path:
                return

            result = upload_mi_foto_perfil_endpoint(
                self.db_user,
                self.db_pass,
                origen_file_path=file_path,
                usuario_seguridad_id=usuario_seguridad_id,
                codigo_usuario=self.codigo_usuario,
            )

            data = result.get("data") or {}
            self.current_profile = data
            self._apply_profile_to_form(data)

            show_info(
                self,
                "Foto de perfil",
                result.get("message") or "La foto de perfil fue actualizada correctamente.",
            )
        except Exception as e:
            handle_exception(
                self,
                e,
                context="Carga de foto de perfil",
            )

    def _on_remove_photo(self) -> None:
        try:
            usuario_seguridad_id = self.current_profile.get("usuario_seguridad_id")
            if not usuario_seguridad_id:
                show_warning(
                    self,
                    "Foto de perfil",
                    "No se pudo identificar el usuario activo.",
                )
                return

            if not self.current_profile.get("tiene_foto_personalizada"):
                show_warning(
                    self,
                    "Foto de perfil",
                    "Actualmente el perfil ya utiliza la imagen por defecto.",
                )
                return

            result = remove_mi_foto_perfil_endpoint(
                self.db_user,
                self.db_pass,
                usuario_seguridad_id=usuario_seguridad_id,
                codigo_usuario=self.codigo_usuario,
            )

            data = result.get("data") or {}
            self.current_profile = data
            self._apply_profile_to_form(data)

            show_info(
                self,
                "Foto de perfil",
                result.get("message") or "La foto personalizada fue eliminada correctamente.",
            )
        except Exception as e:
            handle_exception(
                self,
                e,
                context="Eliminación de foto de perfil",
            )

    # =========================================================
    # Helpers
    # =========================================================
    @staticmethod
    def _safe_str(value) -> str:
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _format_datetime(value) -> str:
        if value is None:
            return ""
        try:
            return str(value)
        except Exception:
            return ""

    @staticmethod
    def _combine_desc_and_id(desc: str, code: str) -> str:
        desc = (desc or "").strip()
        code = (code or "").strip()

        if desc and code:
            return f"{desc} ({code})"
        return desc or code or ""