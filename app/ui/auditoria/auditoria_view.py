from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.error_handler import (
    handle_exception,
)
from app.endpoints.auditoria_consulta_endpoints import (
    get_auditoria_filtros_endpoint,
    listar_auditoria_endpoint,
    get_auditoria_resumen_endpoint,
    get_diccionario_movimientos_endpoint,
    get_registro_afectado_auditoria_endpoint,
)


class AuditoriaView(ttk.Frame):
    """
    Vista de consulta para el auditor.

    Funcionalidades:
    - resumen superior de movimientos
    - filtros por usuario / movimiento / tabla / texto
    - tabla principal de auditoría
    - popup de detalle al seleccionar un registro
    - popup con diccionario de movimientos

    Acceso:
    - el endpoint ya valida que solo el auditor pueda consultar
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

        self.rows_data: list[dict] = []

        self.usuarios_options: list[dict] = []
        self.movimientos_options: list[dict] = []
        self.tablas_options: list[dict] = []

        self.usuario_display_to_id: dict[str, int | None] = {}
        self.mov_display_to_code: dict[str, int | None] = {}
        self.tabla_display_to_code: dict[str, str | None] = {}

        # filtros
        self.var_filtro_usuario = tk.StringVar(value="Todos")
        self.var_filtro_movimiento = tk.StringVar(value="Todos")
        self.var_filtro_tabla = tk.StringVar(value="Todos")
        self.var_filtro_texto = tk.StringVar()

        # resumen
        self.var_total = tk.StringVar(value="0")
        self.var_insertados = tk.StringVar(value="0")
        self.var_actualizados = tk.StringVar(value="0")
        self.var_eliminados = tk.StringVar(value="0")
        self.var_consultas = tk.StringVar(value="0")
        self.var_logins = tk.StringVar(value="0")

        self._detail_popup: tk.Toplevel | None = None
        self._diccionario_popup: tk.Toplevel | None = None

        self._build_ui()
        self._load_initial_data()

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Frame(self, padding=(16, 16, 16, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Auditoría del Sistema",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text="Consulta legible de movimientos registrados en dbo.Auditoria.",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._build_summary(self)
        self._build_body(self)

    def _build_summary(self, parent) -> None:
        summary = ttk.LabelFrame(parent, text="Resumen", padding=12)
        summary.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        for i in range(6):
            summary.columnconfigure(i, weight=1)

        self._create_summary_card(summary, "Total", self.var_total, 0)
        self._create_summary_card(summary, "Insertados", self.var_insertados, 1)
        self._create_summary_card(summary, "Actualizados", self.var_actualizados, 2)
        self._create_summary_card(summary, "Eliminados", self.var_eliminados, 3)
        self._create_summary_card(summary, "Consultas", self.var_consultas, 4)
        self._create_summary_card(summary, "Logins", self.var_logins, 5)

    def _create_summary_card(
        self,
        parent,
        title: str,
        variable: tk.StringVar,
        col: int,
    ) -> None:
        frame = ttk.Frame(parent, padding=8)
        frame.grid(row=0, column=col, sticky="nsew", padx=4, pady=2)

        ttk.Label(
            frame,
            text=title,
            font=("Segoe UI", 10, "bold"),
            anchor="center",
        ).pack(fill="x")

        ttk.Label(
            frame,
            textvariable=variable,
            font=("Segoe UI", 18, "bold"),
            anchor="center",
        ).pack(fill="x", pady=(6, 0))

    def _build_body(self, parent) -> None:
        body = ttk.Frame(parent)
        body.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        self._build_filters(body)
        self._build_table(body)

    def _build_filters(self, parent) -> None:
        filtros = ttk.LabelFrame(parent, text="Filtros", padding=12)
        filtros.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filtros.columnconfigure(1, weight=1)
        filtros.columnconfigure(3, weight=1)
        filtros.columnconfigure(5, weight=1)
        filtros.columnconfigure(7, weight=1)

        ttk.Label(filtros, text="Usuario:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.cmb_usuario = ttk.Combobox(
            filtros,
            textvariable=self.var_filtro_usuario,
            state="readonly",
        )
        self.cmb_usuario.grid(row=0, column=1, sticky="ew", pady=4, padx=(0, 12))

        ttk.Label(filtros, text="Movimiento:").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=4)
        self.cmb_movimiento = ttk.Combobox(
            filtros,
            textvariable=self.var_filtro_movimiento,
            state="readonly",
        )
        self.cmb_movimiento.grid(row=0, column=3, sticky="ew", pady=4, padx=(0, 12))

        ttk.Label(filtros, text="Tabla:").grid(row=0, column=4, sticky="w", padx=(0, 8), pady=4)
        self.cmb_tabla = ttk.Combobox(
            filtros,
            textvariable=self.var_filtro_tabla,
            state="readonly",
        )
        self.cmb_tabla.grid(row=0, column=5, sticky="ew", pady=4, padx=(0, 12))

        ttk.Label(filtros, text="Texto libre:").grid(row=0, column=6, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(
            filtros,
            textvariable=self.var_filtro_texto,
        ).grid(row=0, column=7, sticky="ew", pady=4)

        actions = ttk.Frame(filtros)
        actions.grid(row=1, column=0, columnspan=8, sticky="e", pady=(10, 0))

        ttk.Button(
            actions,
            text="Diccionario de movimientos",
            command=self._open_diccionario_movimientos_popup,
        ).grid(row=0, column=0, padx=(0, 14))

        ttk.Button(
            actions,
            text="Buscar",
            command=self._on_search,
        ).grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            actions,
            text="Limpiar",
            command=self._on_clear_filters,
        ).grid(row=0, column=2, padx=(0, 8))

        ttk.Button(
            actions,
            text="Recargar",
            command=self._load_initial_data,
        ).grid(row=0, column=3)

    def _build_table(self, parent) -> None:
        table_box = ttk.LabelFrame(parent, text="Registros", padding=10)
        table_box.grid(row=1, column=0, sticky="nsew")
        table_box.columnconfigure(0, weight=1)
        table_box.rowconfigure(0, weight=1)

        columns = (
            "auditoria_id",
            "fecha_movimiento",
            "usuario_display",
            "movimiento_label",
            "tabla_label",
            "id_row_tabla",
        )

        self.tree = ttk.Treeview(
            table_box,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(table_box, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.heading("auditoria_id", text="ID")
        self.tree.heading("fecha_movimiento", text="Fecha")
        self.tree.heading("usuario_display", text="Usuario")
        self.tree.heading("movimiento_label", text="Movimiento")
        self.tree.heading("tabla_label", text="Tabla")
        self.tree.heading("id_row_tabla", text="Id Row")

        self.tree.column("auditoria_id", width=70, anchor="center", stretch=False)
        self.tree.column("fecha_movimiento", width=180, anchor="center", stretch=False)
        self.tree.column("usuario_display", width=280, anchor="w", stretch=True)
        self.tree.column("movimiento_label", width=190, anchor="w", stretch=False)
        self.tree.column("tabla_label", width=180, anchor="w", stretch=False)
        self.tree.column("id_row_tabla", width=420, anchor="w", stretch=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

    # =========================================================
    # Carga de datos
    # =========================================================
    def _load_initial_data(self) -> None:
        try:
            self._load_filters()
            self._load_summary()
            self._load_table()
        except Exception as e:
            handle_exception(self, e, context="Carga inicial auditoría")

    def _load_filters(self) -> None:
        result = get_auditoria_filtros_endpoint(
            self.db_user,
            self.db_pass,
        )
        data = result.get("data") or {}

        self.usuarios_options = data.get("usuarios") or []
        self.movimientos_options = data.get("movimientos") or []
        self.tablas_options = data.get("tablas") or []

        usuario_values = ["Todos"]
        self.usuario_display_to_id = {"Todos": None}
        for item in self.usuarios_options:
            display = str(item.get("display") or "").strip()
            codigo = item.get("codigo_usuario")
            if display:
                usuario_values.append(display)
                self.usuario_display_to_id[display] = codigo

        movimiento_values = ["Todos"]
        self.mov_display_to_code = {"Todos": None}
        for item in self.movimientos_options:
            display = str(item.get("display") or "").strip()
            codigo = item.get("codigo")
            if display:
                movimiento_values.append(display)
                self.mov_display_to_code[display] = codigo

        tabla_values = ["Todos"]
        self.tabla_display_to_code = {"Todos": None}
        for item in self.tablas_options:
            display = str(item.get("display") or "").strip()
            codigo = item.get("codigo")
            if display:
                tabla_values.append(display)
                self.tabla_display_to_code[display] = codigo

        self.cmb_usuario["values"] = usuario_values
        self.cmb_movimiento["values"] = movimiento_values
        self.cmb_tabla["values"] = tabla_values

        if not self.var_filtro_usuario.get():
            self.var_filtro_usuario.set("Todos")
        if not self.var_filtro_movimiento.get():
            self.var_filtro_movimiento.set("Todos")
        if not self.var_filtro_tabla.get():
            self.var_filtro_tabla.set("Todos")

    def _load_summary(self) -> None:
        result = get_auditoria_resumen_endpoint(
            self.db_user,
            self.db_pass,
            top=300,
        )
        data = result.get("data") or {}

        self.var_total.set(str(data.get("total_registros", 0)))
        self.var_insertados.set(str(data.get("insertados", 0)))
        self.var_actualizados.set(str(data.get("actualizados", 0)))
        self.var_eliminados.set(str(data.get("eliminados", 0)))
        self.var_consultas.set(str(data.get("consultas", 0)))
        self.var_logins.set(str(data.get("logins", 0)))

    def _load_table(self) -> None:
        selected_usuario = self.var_filtro_usuario.get().strip() or "Todos"
        selected_movimiento = self.var_filtro_movimiento.get().strip() or "Todos"
        selected_tabla = self.var_filtro_tabla.get().strip() or "Todos"
        texto = self.var_filtro_texto.get().strip() or None

        codigo_usuario = self.usuario_display_to_id.get(selected_usuario)
        movimiento_cod = self.mov_display_to_code.get(selected_movimiento)
        id_tabla = self.tabla_display_to_code.get(selected_tabla)

        result = listar_auditoria_endpoint(
            self.db_user,
            self.db_pass,
            codigo_usuario=codigo_usuario,
            movimiento_cod=movimiento_cod,
            id_tabla=id_tabla,
            texto=texto,
            top=300,
        )

        self.rows_data = result.get("data") or []
        self._fill_tree(self.rows_data)

    def _fill_tree(self, rows: list[dict]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, row in enumerate(rows):
            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    row.get("auditoria_id"),
                    self._safe_str(row.get("fecha_movimiento")),
                    row.get("usuario_display"),
                    row.get("movimiento_label"),
                    row.get("tabla_label"),
                    row.get("row_display"),
                ),
            )

        if rows:
            first_iid = self.tree.get_children()[0]
            self.tree.selection_set(first_iid)
            self.tree.focus(first_iid)
            self._show_detail_popup_by_iid(first_iid)

    # =========================================================
    # Eventos
    # =========================================================
    def _on_search(self) -> None:
        try:
            self._close_detail_popup()
            self._load_table()
        except Exception as e:
            handle_exception(self, e, context="Búsqueda de auditoría")

    def _on_clear_filters(self) -> None:
        self.var_filtro_usuario.set("Todos")
        self.var_filtro_movimiento.set("Todos")
        self.var_filtro_tabla.set("Todos")
        self.var_filtro_texto.set("")
        self._close_detail_popup()
        self._load_initial_data()

    def _on_tree_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        iid = selection[0]
        self._show_detail_popup_by_iid(iid)

    def _on_tree_double_click(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        iid = selection[0]
        self._show_detail_popup_by_iid(iid)

    # =========================================================
    # Popup detalle
    # =========================================================
    def _show_detail_popup_by_iid(self, iid: str) -> None:
        try:
            index = int(iid)
        except (TypeError, ValueError):
            return

        if index < 0 or index >= len(self.rows_data):
            return

        row = self.rows_data[index]
        self._open_detail_popup(row)

    def _open_detail_popup(self, row: dict) -> None:
        self._close_detail_popup()

        detalle_registro = self._get_registro_afectado_data(row)

        popup = tk.Toplevel(self)
        popup.title("Detalle del Registro de Auditoría")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        popup.resizable(True, True)
        popup.minsize(820, 620)
        popup.configure(bg="#f3f6fa")

        self._detail_popup = popup

        try:
            parent_x = self.winfo_toplevel().winfo_rootx()
            parent_y = self.winfo_toplevel().winfo_rooty()
            parent_w = self.winfo_toplevel().winfo_width()
            parent_h = self.winfo_toplevel().winfo_height()

            width = 900
            height = 700

            x = parent_x + (parent_w // 2) - (width // 2)
            y = parent_y + (parent_h // 2) - (height // 2)

            popup.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            popup.geometry("900x700")

        outer = ttk.Frame(popup, padding=16)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Detalle del Registro",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text="Información completa del movimiento seleccionado.",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        content = ttk.Frame(outer)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        auditoria_box = ttk.LabelFrame(content, text="Datos de Auditoría", padding=14)
        auditoria_box.grid(row=0, column=0, sticky="ew")
        auditoria_box.columnconfigure(1, weight=1)
        auditoria_box.columnconfigure(3, weight=1)

        self._popup_field(auditoria_box, "Auditoría ID:", self._safe_str(row.get("auditoria_id")), 0, 0)
        self._popup_field(auditoria_box, "Código Usuario:", self._safe_str(row.get("codigo_usuario")), 0, 2)

        self._popup_field(auditoria_box, "Usuario:", self._safe_str(row.get("usuario_display")), 1, 0, colspan=3)
        self._popup_field(auditoria_box, "Fecha:", self._safe_str(row.get("fecha_movimiento")), 2, 0, colspan=3)

        movimiento_full = (
            f"{self._safe_str(row.get('movimiento_cod'))} - "
            f"{self._safe_str(row.get('movimiento_label'))}"
        )
        self._popup_field(auditoria_box, "Movimiento:", movimiento_full, 3, 0, colspan=3)

        tabla_full = (
            f"{self._safe_str(row.get('id_tabla'))} - "
            f"{self._safe_str(row.get('tabla_label'))}"
        )
        self._popup_field(auditoria_box, "Tabla:", tabla_full, 4, 0, colspan=3)

        self._popup_field(
            auditoria_box,
            "Id Row Tabla:",
            self._safe_str(row.get("row_display")),
            5,
            0,
            colspan=3,
            height=4,
        )

        afectado_box = ttk.LabelFrame(content, text="Dato / Registro Afectado", padding=14)
        afectado_box.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        afectado_box.columnconfigure(0, weight=1)
        afectado_box.rowconfigure(1, weight=1)

        estado_texto = self._safe_str(detalle_registro.get("estado_texto"))
        ttk.Label(
            afectado_box,
            text=estado_texto,
            font=("Segoe UI", 10, "italic"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        text_frame = ttk.Frame(afectado_box)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        txt_detalle = tk.Text(
            text_frame,
            height=16,
            wrap="word",
            relief="solid",
            bd=1,
            font=("Segoe UI", 10),
        )
        txt_detalle.grid(row=0, column=0, sticky="nsew")

        txt_scroll = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=txt_detalle.yview,
        )
        txt_scroll.grid(row=0, column=1, sticky="ns")
        txt_detalle.configure(yscrollcommand=txt_scroll.set)

        txt_detalle.insert("1.0", self._safe_str(detalle_registro.get("texto")))
        txt_detalle.configure(state="disabled")

        footer = ttk.Frame(outer)
        footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))

        ttk.Button(
            footer,
            text="Cerrar",
            command=self._close_detail_popup,
        ).pack(side="right")

    def _get_registro_afectado_data(self, row: dict) -> dict:
        try:
            result = get_registro_afectado_auditoria_endpoint(
                self.db_user,
                self.db_pass,
                id_tabla=row.get("id_tabla"),
                id_row_tabla=row.get("id_row_tabla"),
            )
            data = result.get("data") or {}

            ok = bool(data.get("ok"))
            tabla_label = self._safe_str(data.get("tabla_label")) or self._safe_str(row.get("tabla_label"))
            mensaje = self._safe_str(data.get("mensaje"))
            texto = self._safe_str(data.get("texto_completo"))

            if not texto:
                texto = mensaje or "No hay información disponible para este registro."

            if ok:
                estado_texto = f"Detalle resuelto para: {tabla_label}"
            else:
                estado_texto = "No fue posible reconstruir completamente el dato afectado."
                if mensaje:
                    estado_texto += f" {mensaje}"

            return {
                "ok": ok,
                "estado_texto": estado_texto,
                "texto": texto,
                "raw": data,
            }

        except Exception as e:
            return {
                "ok": False,
                "estado_texto": "Ocurrió un error al consultar el dato afectado.",
                "texto": f"No fue posible cargar el dato afectado.\n\nDetalle técnico: {e}",
                "raw": {},
            }

    def _popup_field(
        self,
        parent,
        label_text: str,
        value: str,
        row: int,
        col: int,
        colspan: int = 1,
        height: int = 1,
    ) -> None:
        ttk.Label(parent, text=label_text).grid(
            row=row,
            column=col,
            sticky="nw",
            padx=(0, 8),
            pady=6,
        )

        if height > 1:
            txt = tk.Text(
                parent,
                height=height,
                wrap="word",
                relief="solid",
                bd=1,
                font=("Segoe UI", 10),
            )
            txt.grid(
                row=row,
                column=col + 1,
                columnspan=colspan,
                sticky="ew",
                pady=6,
            )
            txt.insert("1.0", value or "")
            txt.configure(state="disabled")
        else:
            ent = ttk.Entry(parent)
            ent.grid(
                row=row,
                column=col + 1,
                columnspan=colspan,
                sticky="ew",
                pady=6,
            )
            ent.insert(0, value or "")
            ent.configure(state="readonly")

    def _close_detail_popup(self) -> None:
        try:
            if self._detail_popup is not None and self._detail_popup.winfo_exists():
                self._detail_popup.destroy()
        except Exception:
            pass
        finally:
            self._detail_popup = None

    # =========================================================
    # Popup diccionario de movimientos
    # =========================================================
    def _open_diccionario_movimientos_popup(self) -> None:
        try:
            self._close_diccionario_popup()

            result = get_diccionario_movimientos_endpoint(
                self.db_user,
                self.db_pass,
            )
            rows = result.get("data") or []

            popup = tk.Toplevel(self)
            popup.title("Diccionario de Movimientos")
            popup.transient(self.winfo_toplevel())
            popup.grab_set()
            popup.resizable(True, True)
            popup.minsize(760, 460)

            self._diccionario_popup = popup

            try:
                parent_x = self.winfo_toplevel().winfo_rootx()
                parent_y = self.winfo_toplevel().winfo_rooty()
                parent_w = self.winfo_toplevel().winfo_width()
                parent_h = self.winfo_toplevel().winfo_height()

                width = 860
                height = 520

                x = parent_x + (parent_w // 2) - (width // 2)
                y = parent_y + (parent_h // 2) - (height // 2)

                popup.geometry(f"{width}x{height}+{x}+{y}")
            except Exception:
                popup.geometry("860x520")

            outer = ttk.Frame(popup, padding=16)
            outer.pack(fill="both", expand=True)
            outer.columnconfigure(0, weight=1)
            outer.rowconfigure(1, weight=1)

            header = ttk.Frame(outer)
            header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
            header.columnconfigure(0, weight=1)

            ttk.Label(
                header,
                text="Diccionario de Movimientos",
                font=("Segoe UI", 15, "bold"),
            ).grid(row=0, column=0, sticky="w")

            ttk.Label(
                header,
                text="Catálogo oficial de códigos y descripciones para interpretar la auditoría.",
                font=("Segoe UI", 10),
            ).grid(row=1, column=0, sticky="w", pady=(4, 0))

            table_box = ttk.LabelFrame(outer, text="Movimientos", padding=10)
            table_box.grid(row=1, column=0, sticky="nsew")
            table_box.columnconfigure(0, weight=1)
            table_box.rowconfigure(0, weight=1)

            columns = ("movimiento_cod", "descripcion", "estado_label")

            tree = ttk.Treeview(
                table_box,
                columns=columns,
                show="headings",
                height=18,
            )
            tree.grid(row=0, column=0, sticky="nsew")

            vsb = ttk.Scrollbar(table_box, orient="vertical", command=tree.yview)
            vsb.grid(row=0, column=1, sticky="ns")
            hsb = ttk.Scrollbar(table_box, orient="horizontal", command=tree.xview)
            hsb.grid(row=1, column=0, sticky="ew")

            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            tree.heading("movimiento_cod", text="Código")
            tree.heading("descripcion", text="Descripción")
            tree.heading("estado_label", text="Estado")

            tree.column("movimiento_cod", width=100, anchor="center", stretch=False)
            tree.column("descripcion", width=560, anchor="w", stretch=True)
            tree.column("estado_label", width=120, anchor="center", stretch=False)

            for idx, row in enumerate(rows):
                tree.insert(
                    "",
                    "end",
                    iid=str(idx),
                    values=(
                        row.get("movimiento_cod"),
                        row.get("descripcion"),
                        row.get("estado_label"),
                    ),
                )

            footer = ttk.Frame(outer)
            footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))

            ttk.Button(
                footer,
                text="Cerrar",
                command=self._close_diccionario_popup,
            ).pack(side="right")

        except Exception as e:
            handle_exception(self, e, context="Diccionario de movimientos")

    def _close_diccionario_popup(self) -> None:
        try:
            if self._diccionario_popup is not None and self._diccionario_popup.winfo_exists():
                self._diccionario_popup.destroy()
        except Exception:
            pass
        finally:
            self._diccionario_popup = None

    # =========================================================
    # Helpers
    # =========================================================
    @staticmethod
    def _safe_str(value) -> str:
        if value is None:
            return ""
        return str(value)