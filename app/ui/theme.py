# app/ui/theme.py
from __future__ import annotations

from tkinter import ttk


def apply_theme(root) -> None:
    """
    Aplica un estilo global (ttk) UNA sola vez.
    Afecta a TODOS los widgets ttk existentes y futuros:
    Button, Entry, Combobox, Treeview, etc.
    """
    style = ttk.Style(root)

    # Tema base más "moderno" que el default (mejor control de estilos)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # ---------- Paleta (centralizada) ----------
    # Nota: ttk no permite 100% control en todos los SO/temas,
    # pero clam suele respetar bastante.
    bg_app = "#0b1220"
    card_bg = "#0f172a"
    border = "#1f2a44"
    text = "#e5e7eb"
    text_muted = "#cbd5e1"

    btn_bg = "#111c33"
    btn_bg_active = "#16264a"
    btn_border = "#2b3a5f"

    # ---------- Ajustes globales ----------
    style.configure(".", background=bg_app, foreground=text)
    style.configure("TFrame", background=bg_app)
    style.configure("TLabel", background=bg_app, foreground=text)
    style.configure("TLabelframe", background=bg_app, foreground=text)
    style.configure("TLabelframe.Label", background=bg_app, foreground=text_muted)

    # Inputs
    style.configure(
        "TEntry",
        padding=(10, 7),
        fieldbackground=card_bg,
        foreground=text,
        bordercolor=border,
        lightcolor=border,
        darkcolor=border,
        insertcolor=text,
    )
    style.configure(
        "TCombobox",
        padding=(10, 7),
        fieldbackground=card_bg,
        foreground=text,
        bordercolor=border,
        lightcolor=border,
        darkcolor=border,
        arrowsize=14,
    )

    # ---------- BOTONES (lo principal que pediste) ----------
    style.configure(
        "TButton",
        padding=(12, 8),
        background=btn_bg,
        foreground=text,
        bordercolor=btn_border,
        lightcolor=btn_border,
        darkcolor=btn_border,
        focusthickness=2,
        focuscolor=border,
    )
    style.map(
        "TButton",
        background=[
            ("pressed", "#0e1a33"),
            ("active", btn_bg_active),
            ("disabled", "#0d1426"),
        ],
        foreground=[
            ("disabled", "#7c8697"),
        ],
        bordercolor=[
            ("active", "#3b4f7a"),
            ("pressed", "#2b3a5f"),
        ],
    )

    # Treeview (grid)
    style.configure(
        "Treeview",
        background=card_bg,
        fieldbackground=card_bg,
        foreground=text,
        bordercolor=border,
        rowheight=28,
    )
    style.configure(
        "Treeview.Heading",
        padding=(10, 8),
        background=btn_bg,
        foreground=text,
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", btn_bg_active)],
    )

    # Scrollbar (discreto)
    style.configure("Vertical.TScrollbar", background=bg_app, troughcolor=bg_app, bordercolor=bg_app)
    style.configure("Horizontal.TScrollbar", background=bg_app, troughcolor=bg_app, bordercolor=bg_app)