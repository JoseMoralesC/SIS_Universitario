from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.error_handler import handle_exception, show_warning, show_info
from app.endpoints.matriculas_materia import (
    facturacion_matricula_endpoints as fact_ep,
)
from app.ui.transitions.popup_slide import PopupSlider


class CompletarMatriculaPopup(tk.Toplevel):
    """
    Popup para completar el pago de matrícula.
    """

    POPUP_W = 920
    POPUP_H = 580

    def __init__(
        self,
        parent,
        db_user: str,
        db_pass: str,
        codigo_usuario: int,
        *,
        carnet: str,
        on_pago_realizado=None,
        curso_cod: int,
        periodo_id: int,
        anio: int,
        estudiante_label: str,
        curso_label: str,
        periodo_label: str,
    ):
        super().__init__(parent)

        self.db_user = db_user
        self.db_pass = db_pass
        self.codigo_usuario = codigo_usuario

        self.carnet = carnet
        self.on_pago_realizado = on_pago_realizado
        self.curso_cod = curso_cod
        self.periodo_id = periodo_id
        self.anio = anio

        self.estudiante_label = estudiante_label
        self.curso_label = curso_label
        self.periodo_label = periodo_label

        self.formas_pago = []
        self.resumen_data: dict = {}

        self._slider = PopupSlider(parent)
        self._is_closing = False

        self._popup_w = self.POPUP_W
        self._popup_h = self.POPUP_H
        self._popup_x = 0
        self._popup_y = 0

        self.title("Completar Matrícula")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_popup)

        self._configure_styles()
        self._build_ui()
        self._prepare_geometry()
        self._load_formas_pago()
        self._load_resumen()
        self._animate_in()

    # =====================================================
    # Estilos
    # =====================================================
    def _configure_styles(self):
        style = ttk.Style(self)

        try:
            style.theme_use(style.theme_use())
        except Exception:
            pass

        bg_main = "#f4f7fb"
        card_bg = "#ffffff"
        accent = "#1f4e79"

        self.configure(bg=bg_main)

        style.configure(
            "Popup.TFrame",
            background=bg_main,
        )

        style.configure(
            "PopupCard.TLabelframe",
            background=card_bg,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "PopupCard.TLabelframe.Label",
            background=card_bg,
            foreground=accent,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "PopupText.TLabel",
            background=bg_main,
            foreground="#1f2937",
            font=("Segoe UI", 10),
        )

        style.configure(
            "PopupValue.TLabel",
            background=bg_main,
            foreground="#111827",
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
        )

        style.configure(
            "Soft.TButton",
            font=("Segoe UI", 10),
            padding=(12, 8),
        )

        style.configure(
            "PopupTree.Treeview",
            rowheight=28,
            font=("Segoe UI", 10),
        )
        style.configure(
            "PopupTree.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
        )

    # =====================================================
    # Geometría / animación
    # =====================================================
    def _prepare_geometry(self):
        self.update_idletasks()

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        self._popup_x = max(20, (screen_w - self._popup_w) // 2)
        self._popup_y = max(20, (screen_h - self._popup_h) // 2)

        start_x = self._popup_x + 120
        self.geometry(f"{self._popup_w}x{self._popup_h}+{start_x}+{self._popup_y}")

    def _animate_in(self):
        self._slider.slide_in(
            self,
            w=self._popup_w,
            h=self._popup_h,
            x_to=self._popup_x,
            y=self._popup_y,
            offset=120,
            step=30,
            delay_ms=8,
        )

    def _cerrar_popup(self):
        if self._is_closing:
            return

        self._is_closing = True

        self._slider.slide_out(
            self,
            w=self._popup_w,
            h=self._popup_h,
            x_from=self.winfo_x(),
            y=self.winfo_y(),
            offset=120,
            step=30,
            delay_ms=8,
            on_done=self.destroy,
        )

    # =====================================================
    # UI
    # =====================================================
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # -------------------------------------------------
        # Header
        # -------------------------------------------------
        header = ttk.Frame(self, style="Popup.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)

        ttk.Label(
            header,
            text=f"Estudiante: {self.estudiante_label}",
            style="PopupValue.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=4)

        ttk.Label(
            header,
            text=f"Curso: {self.curso_label}",
            style="PopupValue.TLabel",
        ).grid(row=0, column=1, padx=4)

        ttk.Label(
            header,
            text=f"Período: {self.periodo_label}",
            style="PopupValue.TLabel",
        ).grid(row=0, column=2, sticky="e", padx=4)

        # -------------------------------------------------
        # Estado / beca
        # -------------------------------------------------
        estado_frame = ttk.LabelFrame(
            self,
            text="Resumen",
            style="PopupCard.TLabelframe",
        )
        estado_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        estado_frame.columnconfigure(0, weight=1)
        estado_frame.columnconfigure(1, weight=1)

        self.lbl_beca = ttk.Label(
            estado_frame,
            text="Beca: -",
            style="PopupText.TLabel",
        )
        self.lbl_beca.grid(row=0, column=0, sticky="w", padx=10, pady=8)

        self.lbl_estado_pago = ttk.Label(
            estado_frame,
            text="Estado de pago: Pendiente",
            style="PopupValue.TLabel",
        )
        self.lbl_estado_pago.grid(row=0, column=1, sticky="e", padx=10, pady=8)

        # -------------------------------------------------
        # Grid materias
        # -------------------------------------------------
        grid_frame = ttk.LabelFrame(
            self,
            text="Detalle de Materias",
            style="PopupCard.TLabelframe",
        )
        grid_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)

        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        columnas = ("materia", "docente", "precio", "descuento", "total")

        self.grid = ttk.Treeview(
            grid_frame,
            columns=columnas,
            show="headings",
            style="PopupTree.Treeview",
        )

        self.grid.heading("materia", text="Materia")
        self.grid.heading("docente", text="Docente")
        self.grid.heading("precio", text="Precio Base")
        self.grid.heading("descuento", text="Descuento")
        self.grid.heading("total", text="Monto Final")

        self.grid.column("materia", width=250, anchor="w")
        self.grid.column("docente", width=220, anchor="w")
        self.grid.column("precio", width=120, anchor="center")
        self.grid.column("descuento", width=120, anchor="center")
        self.grid.column("total", width=120, anchor="center")

        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.grid.yview)
        self.grid.configure(yscrollcommand=vsb.set)

        self.grid.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        vsb.grid(row=0, column=1, sticky="ns", pady=6, padx=(0, 6))

        # -------------------------------------------------
        # Resumen financiero
        # -------------------------------------------------
        resumen = ttk.LabelFrame(
            self,
            text="Resumen Financiero",
            style="PopupCard.TLabelframe",
        )
        resumen.grid(row=3, column=0, sticky="ew", padx=12, pady=8)

        resumen.columnconfigure(0, weight=1)
        resumen.columnconfigure(1, weight=1)
        resumen.columnconfigure(2, weight=1)

        self.lbl_subtotal = ttk.Label(
            resumen,
            text="Subtotal: ₡0",
            style="PopupValue.TLabel",
        )
        self.lbl_subtotal.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.lbl_descuento = ttk.Label(
            resumen,
            text="Descuento: ₡0",
            style="PopupValue.TLabel",
        )
        self.lbl_descuento.grid(row=0, column=1, padx=10, pady=10)

        self.lbl_total = ttk.Label(
            resumen,
            text="Total: ₡0",
            style="PopupValue.TLabel",
        )
        self.lbl_total.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        # -------------------------------------------------
        # Pago
        # -------------------------------------------------
        pago = ttk.LabelFrame(
            self,
            text="Información de Pago",
            style="PopupCard.TLabelframe",
        )
        pago.grid(row=4, column=0, sticky="ew", padx=12, pady=8)

        pago.columnconfigure(0, weight=1)
        pago.columnconfigure(1, weight=1)
        pago.columnconfigure(2, weight=1)

        ttk.Label(
            pago,
            text="Forma de pago",
            style="PopupText.TLabel",
        ).grid(row=0, column=0, padx=6, pady=(8, 2), sticky="w")

        self.cbo_pago = ttk.Combobox(pago, state="readonly")
        self.cbo_pago.grid(row=1, column=0, padx=6, pady=(0, 6), sticky="ew")
        self.cbo_pago.bind("<<ComboboxSelected>>", self._on_forma_pago_change)

        ttk.Label(
            pago,
            text="Referencia / comprobante",
            style="PopupText.TLabel",
        ).grid(row=0, column=1, padx=6, pady=(8, 2), sticky="w")

        self.var_referencia = tk.StringVar(value="")
        self.txt_referencia = ttk.Entry(
            pago,
            textvariable=self.var_referencia,
            state="readonly",
        )
        self.txt_referencia.grid(row=1, column=1, padx=6, pady=(0, 6), sticky="ew")

        ttk.Label(
            pago,
            text="Observación",
            style="PopupText.TLabel",
        ).grid(row=0, column=2, padx=6, pady=(8, 2), sticky="w")

        self.txt_obs = ttk.Entry(pago)
        self.txt_obs.grid(row=1, column=2, padx=6, pady=(0, 6), sticky="ew")

        self.lbl_pago_hint = ttk.Label(
            pago,
            text="La referencia se genera automáticamente según la forma de pago seleccionada.",
            style="PopupText.TLabel",
        )
        self.lbl_pago_hint.grid(row=2, column=0, columnspan=3, padx=6, pady=(0, 8), sticky="w")

        # -------------------------------------------------
        # Botones
        # -------------------------------------------------
        botones = ttk.Frame(self, style="Popup.TFrame")
        botones.grid(row=5, column=0, pady=(4, 14))

        self.btn_pagar = ttk.Button(
            botones,
            text="Procesar pago",
            style="Accent.TButton",
            command=self._procesar_pago,
        )
        self.btn_pagar.grid(row=0, column=0, padx=8)

        self.btn_cerrar = ttk.Button(
            botones,
            text="Cerrar",
            style="Soft.TButton",
            command=self._cerrar_popup,
        )
        self.btn_cerrar.grid(row=0, column=1, padx=8)

    # =====================================================
    # Helpers
    # =====================================================
    def _forma_pago_requiere_referencia(self, descripcion: str) -> bool:
        desc = (descripcion or "").strip().lower()

        if "efectivo" in desc:
            return False

        palabras_clave = (
            "sinpe",
            "transfer",
            "tarjeta",
            "deposit",
            "depósito",
            "banco",
            "comprobante",
        )
        return any(p in desc for p in palabras_clave)

    def _get_forma_pago_actual(self) -> tuple | None:
        idx = self.cbo_pago.current()
        if idx < 0 or idx >= len(self.formas_pago):
            return None
        return self.formas_pago[idx]

    def _clear_referencia(self):
        self.var_referencia.set("")

    def _load_referencia_preview(self):
        forma_pago = self._get_forma_pago_actual()

        if not forma_pago:
            self._clear_referencia()
            return

        try:
            referencia = fact_ep.get_referencia_pago_preview(
                self.db_user,
                self.db_pass,
                forma_pago_cod=int(forma_pago[0]),
            )
            self.var_referencia.set(referencia)
        except Exception as e:
            self._clear_referencia()
            handle_exception(self, e, context="Generar referencia de pago")

    def _on_forma_pago_change(self, _event=None):
        self._load_referencia_preview()

    # =====================================================
    # Cargar datos
    # =====================================================
    def _load_formas_pago(self):
        try:
            self.formas_pago = fact_ep.get_formas_pago(
                self.db_user,
                self.db_pass,
            )

            self.cbo_pago["values"] = [desc for _, desc in self.formas_pago]

            if self.formas_pago:
                self.cbo_pago.current(0)
                self._load_referencia_preview()

        except Exception as e:
            handle_exception(self, e, context="Cargar formas de pago")

    def _load_resumen(self):
        try:
            data = fact_ep.get_resumen_facturacion(
                self.db_user,
                self.db_pass,
                carnet=self.carnet,
                curso_cod=self.curso_cod,
                periodo_id=self.periodo_id,
                anio=self.anio,
                forma_pago_cod=self.formas_pago[0][0] if self.formas_pago else 1,
            )

            self.resumen_data = data
            beca = data["beca"]

            if beca["tiene_beca"]:
                self.lbl_beca.config(
                    text=f"Beca: {beca['nombre_beca']} ({beca['porcentaje_beca']}%)"
                )
            else:
                self.lbl_beca.config(text="Beca: No aplica")

            for item in self.grid.get_children():
                self.grid.delete(item)

            for m in data["materias"]:
                self.grid.insert(
                    "",
                    "end",
                    values=(
                        m["materia"],
                        m["docente"],
                        f"₡{m['precio_base']:,.0f}",
                        f"₡{m['monto_descuento']:,.0f}",
                        f"₡{m['monto_final']:,.0f}",
                    ),
                )

            self.lbl_subtotal.config(text=f"Subtotal: ₡{data['subtotal']:,.0f}")
            self.lbl_descuento.config(text=f"Descuento: ₡{data['descuento']:,.0f}")
            self.lbl_total.config(text=f"Total: ₡{data['total']:,.0f}")

            if int(data.get("cantidad_materias", 0)) <= 0:
                show_warning(
                    self,
                    "Facturación",
                    "No hay materias pendientes de facturar para este estudiante en el período seleccionado.",
                )

        except Exception as e:
            handle_exception(self, e, context="Cargar resumen facturación")

    # =====================================================
    # Procesar pago
    # =====================================================
    def _procesar_pago(self):
        try:
            if int(self.resumen_data.get("cantidad_materias", 0)) <= 0:
                show_warning(
                    self,
                    "Pago",
                    "No existen materias pendientes de facturar.",
                )
                return

            forma_pago = self._get_forma_pago_actual()

            if not forma_pago:
                show_warning(self, "Pago", "Debe seleccionar forma de pago.")
                return

            forma_pago_cod = int(forma_pago[0])
            forma_pago_desc = str(forma_pago[1])

            referencia = self.var_referencia.get().strip()
            observacion = self.txt_obs.get().strip()

            if self._forma_pago_requiere_referencia(forma_pago_desc) and not referencia:
                show_warning(
                    self,
                    "Pago",
                    f"La forma de pago '{forma_pago_desc}' requiere referencia automática válida.",
                )
                return

            result = fact_ep.save_facturacion_matricula(
                self.db_user,
                self.db_pass,
                carnet=self.carnet,
                curso_cod=self.curso_cod,
                periodo_id=self.periodo_id,
                anio=self.anio,
                forma_pago_cod=forma_pago_cod,
                referencia_pago=referencia,
                observacion=observacion,
                codigo_usuario=self.codigo_usuario,
            )

            self.lbl_estado_pago.config(text="Estado de pago: Cancelado")
            self.update_idletasks()

            show_info(
                self,
                "Pago procesado",
                f"Materias facturadas: {result['insertados']}\n"
                f"Referencia: {result['referencia_pago']}\n"
                f"Total pagado: ₡{result['total']:,.0f}",
            )

            if self.on_pago_realizado:
                try:
                    self.on_pago_realizado()
                except Exception:
                    pass

            self._cerrar_popup()

        except Exception as e:
            handle_exception(self, e, context="Procesar pago matrícula")