from __future__ import annotations

from tkinter import ttk


class ListadoMatriculasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        cols = ("Matricula_ID", "Estudiante", "Curso", "Docente", "Fecha", "Estado")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160, anchor="w")

        self.tree.column("Matricula_ID", width=160, anchor="center")
        self.tree.column("Fecha", width=110, anchor="center")
        self.tree.column("Estado", width=110, anchor="center")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def bind_select(self, callback):
        self.tree.bind("<<TreeviewSelect>>", callback)

    def fill_rows(self, rows: list[tuple]):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for r in rows:
            try:
                self.tree.insert("", "end", values=r)
            except Exception:
                pass

    def clear(self):
        for i in self.tree.get_children():
            self.tree.delete(i)