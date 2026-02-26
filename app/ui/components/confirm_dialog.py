# app/ui/components/confirm_dialog.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ConfirmDialog(tk.Toplevel):
    """
    Confirm modal moderno.
    - Card layout
    - Botón primario/segundario (visual por posición y texto)
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        title: str,
        message: str,
        yes_text: str = "Sí, continuar",
        no_text: str = "Cancelar",
    ):
        super().__init__(parent)

        self._result = False

        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.configure(background="#0b1220")
        self.geometry("620x240")

        shell = tk.Frame(self, bg="#0b1220")
        shell.pack(fill="both", expand=True)

        card = tk.Frame(shell, bg="#0f172a", highlightthickness=1, highlightbackground="#1f2a44")
        card.pack(fill="both", expand=True, padx=14, pady=14)

        content = tk.Frame(card, bg="#0f172a")
        content.pack(fill="both", expand=True, padx=16, pady=14)

        header = tk.Frame(content, bg="#0f172a")
        header.pack(fill="x")

        icon_wrap = tk.Frame(header, bg="#111c33", width=36, height=36, highlightthickness=1, highlightbackground="#1f2a44")
        icon_wrap.pack(side="left")
        icon_wrap.pack_propagate(False)
        tk.Label(icon_wrap, text="?", bg="#111c33", fg="#e5e7eb", font=("Segoe UI", 14, "bold")).pack(expand=True)

        titles = tk.Frame(header, bg="#0f172a")
        titles.pack(side="left", fill="x", expand=True, padx=(12, 0))

        tk.Label(titles, text=title, bg="#0f172a", fg="#f1f5f9", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        badge = tk.Label(
            titles,
            text="CONFIRMACIÓN",
            bg="#111c33",
            fg="#cbd5e1",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        )
        badge.pack(anchor="w", pady=(6, 0))

        tk.Label(
            content,
            text=message,
            bg="#0f172a",
            fg="#cbd5e1",
            justify="left",
            wraplength=560,
            font=("Segoe UI", 10),
        ).pack(fill="x", pady=(14, 12))

        footer = tk.Frame(content, bg="#0f172a")
        footer.pack(fill="x")

        # Botones: cancelar izquierda, continuar derecha
        btn_no = ttk.Button(footer, text=no_text, command=self._on_no)
        btn_yes = ttk.Button(footer, text=yes_text, command=self._on_yes)

        btn_no.pack(side="left")
        btn_yes.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_no)
        self.bind("<Escape>", lambda _e: self._on_no())
        self.bind("<Return>", lambda _e: self._on_yes())

        self.after(10, lambda: self._center_over_parent(parent))

    def _on_yes(self):
        self._result = True
        self._close()

    def _on_no(self):
        self._result = False
        self._close()

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

    @property
    def result(self) -> bool:
        return bool(self._result)


def show_confirm(
    parent: tk.Misc,
    title: str,
    message: str,
    *,
    yes_text: str = "Sí, continuar",
    no_text: str = "Cancelar",
) -> bool:
    dlg = ConfirmDialog(parent, title=title, message=message, yes_text=yes_text, no_text=no_text)
    dlg.wait_window()
    return dlg.result