# app/ui/components/error_dialog.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ErrorDialog(tk.Toplevel):
    """
    Popup moderno (modal) para errores / avisos, con detalles opcionales.
    - Headline + badge por nivel
    - Card layout
    - Detalles colapsables
    """

    _LEVEL_META = {
        "error":   {"badge": "ERROR",      "symbol": "✕"},
        "warning": {"badge": "ADVERTENCIA","symbol": "!"},
        "info":    {"badge": "INFO",       "symbol": "i"},
    }

    def __init__(
        self,
        parent: tk.Misc,
        *,
        title: str,
        message: str,
        details: str | None = None,
        level: str = "error",  # "error" | "warning" | "info"
    ):
        super().__init__(parent)

        meta = self._LEVEL_META.get(level, self._LEVEL_META["error"])
        self._details_visible = False
        self._details = (details or "").strip()

        self.title(title)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Fondo del Toplevel (suave)
        self.configure(background="#0b1220")
        self.geometry("620x260")

        # ---------- Shell ----------
        shell = tk.Frame(self, bg="#0b1220")
        shell.pack(fill="both", expand=True)

        # ---------- Card ----------
        card = tk.Frame(shell, bg="#0f172a", highlightthickness=1, highlightbackground="#1f2a44")
        card.pack(fill="both", expand=True, padx=14, pady=14)

        # Padding interno
        content = tk.Frame(card, bg="#0f172a")
        content.pack(fill="both", expand=True, padx=16, pady=14)

        # ---------- Header ----------
        header = tk.Frame(content, bg="#0f172a")
        header.pack(fill="x")

        # Icono circular (simulado)
        icon_wrap = tk.Frame(header, bg="#111c33", width=36, height=36, highlightthickness=1, highlightbackground="#1f2a44")
        icon_wrap.pack(side="left")
        icon_wrap.pack_propagate(False)
        tk.Label(icon_wrap, text=meta["symbol"], bg="#111c33", fg="#e5e7eb", font=("Segoe UI", 14, "bold")).pack(expand=True)

        # Títulos
        titles = tk.Frame(header, bg="#0f172a")
        titles.pack(side="left", fill="x", expand=True, padx=(12, 0))

        tk.Label(titles, text=title, bg="#0f172a", fg="#f1f5f9", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        badge = tk.Label(
            titles,
            text=meta["badge"],
            bg="#111c33",
            fg="#cbd5e1",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        )
        badge.pack(anchor="w", pady=(6, 0))

        # ---------- Message ----------
        tk.Label(
            content,
            text=message,
            bg="#0f172a",
            fg="#cbd5e1",
            justify="left",
            wraplength=560,
            font=("Segoe UI", 10),
        ).pack(fill="x", pady=(12, 10))

        # ---------- Details (collapsible) ----------
        self.details_container = tk.Frame(content, bg="#0f172a")
        # se empaca solo si se muestra

        self.details_card = tk.Frame(self.details_container, bg="#0b1220", highlightthickness=1, highlightbackground="#1f2a44")
        self.details_card.pack(fill="both", expand=True)

        self.details_text = tk.Text(
            self.details_card,
            height=8,
            wrap="word",
            bg="#0b1220",
            fg="#d1d5db",
            insertbackground="#d1d5db",
            relief="flat",
            borderwidth=0,
            font=("Consolas", 9),
        )
        vsb = ttk.Scrollbar(self.details_card, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=vsb.set)

        self.details_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        vsb.grid(row=0, column=1, sticky="ns", pady=10)

        self.details_card.columnconfigure(0, weight=1)
        self.details_card.rowconfigure(0, weight=1)

        if self._details:
            self.details_text.insert("1.0", self._details)
        self.details_text.configure(state="disabled")

        # ---------- Footer ----------
        footer = tk.Frame(content, bg="#0f172a")
        footer.pack(fill="x", pady=(12, 0))

        # izquierda: toggle detalles
        self.btn_toggle = ttk.Button(footer, text="Ver detalles", command=self._toggle_details)
        self.btn_toggle.pack(side="left")

        if not self._details:
            self.btn_toggle.configure(state="disabled")

        # derecha: OK
        btn_ok = ttk.Button(footer, text="Aceptar", command=self._close)
        btn_ok.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda _e: self._close())
        self.after(10, lambda: self._center_over_parent(parent))

    def _toggle_details(self):
        if not self._details:
            return

        self._details_visible = not self._details_visible
        if self._details_visible:
            self.btn_toggle.configure(text="Ocultar detalles")
            self.details_container.pack(fill="both", expand=True, pady=(4, 0))
            self.geometry("720x520")
        else:
            self.btn_toggle.configure(text="Ver detalles")
            self.details_container.forget()
            self.geometry("620x260")

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _center_over_parent(self, parent: tk.Misc):
        try:
            self.update_idletasks()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()

            w = self.winfo_width()
            h = self.winfo_height()

            x = px + (pw // 2) - (w // 2)
            y = py + (ph // 2) - (h // 2)

            self.geometry(f"+{max(x, 10)}+{max(y, 10)}")
        except Exception:
            pass