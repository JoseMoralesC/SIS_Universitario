# app/ui/mantenimientos/base_tab.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox


class MaintenanceTab(ttk.Frame):
    """
    Tab genérico para Mantenimientos:
    - Izquierda: Formulario + botones CRUD
    - Derecha: Grid (Treeview)

    NOTA: Este archivo es UI base (estructura).
    La lógica real se implementa en subclases.
    """

    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.title = title
        self.vars: dict[str, tk.StringVar] = {}
        self.tree: ttk.Treeview | None = None
        self._build_ui()

    # -----------------------------
    #  UI base 
    # -----------------------------
    def _build_ui(self):
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)

        self.left = ttk.LabelFrame(self, text="Formulario", padding=(12, 10))
        self.right = ttk.LabelFrame(self, text="Listado", padding=(10, 10))
        self.left.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=12)
        self.right.grid(row=0, column=1, sticky="nsew", padx=(8, 12), pady=12)

        self.left.columnconfigure(0, weight=0)
        self.left.columnconfigure(1, weight=1)

        # Subclases implementan campos y grid
        self._build_form(self.left)
        ttk.Separator(self.left).grid(row=99, column=0, columnspan=2, sticky="ew", pady=(14, 10))

        btns = ttk.Frame(self.left)
        btns.grid(row=100, column=0, columnspan=2, sticky="ew")
        btns.columnconfigure((0, 1, 2, 3), weight=1)

        # --- Botones CRUD ---
        buttons = [
            ("Nuevo", self.on_nuevo),
            ("Guardar", self.on_guardar),
            ("Actualizar", self.on_actualizar),
            ("Eliminar", self.on_eliminar),
        ]

        for i, (txt, cmd) in enumerate(buttons):
            b = ttk.Button(btns, text=txt, command=cmd)
            b.configure(width=12)
            b.grid(row=0, column=i, sticky="ew", padx=8, pady=8)

        # 
        for i in range(4):
            btns.columnconfigure(i, weight=1, uniform="crud")

        self._build_grid(self.right)

    def _build_form(self, parent: ttk.LabelFrame):
        pass

    def _build_grid(self, parent: ttk.LabelFrame):
        pass

    # -----------------------------
    #  Acciones (subclase)
    # -----------------------------
    def on_nuevo(self):
        pass

    def on_guardar(self):
        messagebox.showinfo("Guardar", f"[{self.title}] Pendiente de implementar en el CRUD real.")

    def on_actualizar(self):
        messagebox.showinfo("Actualizar", f"[{self.title}] Pendiente de implementar en el CRUD real.")

    def on_eliminar(self):
        messagebox.showinfo("Eliminar", f"[{self.title}] Pendiente de implementar en el CRUD real.")