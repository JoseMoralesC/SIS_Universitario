from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.core.exceptions import ValidationError
from app.core.session import set_session
from app.services.auth_service import (
    login_sistema,
    CredencialesInvalidasError,
    UsuarioBloqueadoError,
    UsuarioInactivoError,
    RolNoAsignadoError,
)


class LoginDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, title="Login del sistema"):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)

        self.result = None  # dict(session_data) o None

        # --- modal ---
        self.transient(master)
        self.grab_set()

        # --- UI ---
        frm = ttk.Frame(self, padding=14)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Usuario:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(frm, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=6)

        self.var_user = tk.StringVar()
        self.var_pass = tk.StringVar()

        ent_user = ttk.Entry(frm, textvariable=self.var_user, width=30)
        ent_pass = ttk.Entry(frm, textvariable=self.var_pass, show="*", width=30)
        ent_user.grid(row=0, column=1, pady=6, padx=(10, 0))
        ent_pass.grid(row=1, column=1, pady=6, padx=(10, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        btns.columnconfigure((0, 1), weight=1)

        ttk.Button(btns, text="Ingresar", command=self._ok).grid(row=0, column=0, sticky="ew", padx=6)
        ttk.Button(btns, text="Cancelar", command=self._cancel).grid(row=0, column=1, sticky="ew", padx=6)

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())

        self.protocol("WM_DELETE_WINDOW", self._cancel)

        # centrar sobre master
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        ent_user.focus_set()

    def _ok(self):
        u = self.var_user.get().strip()
        p = self.var_pass.get().strip()

        if not u or not p:
            messagebox.showwarning("Validación", "Debe ingresar usuario y contraseña.")
            return

        try:
            session_data = login_sistema(u, p)
            set_session(session_data)
            self.result = session_data
            self.destroy()

        except CredencialesInvalidasError as e:
            messagebox.showerror("Login", str(e))

        except UsuarioInactivoError as e:
            messagebox.showerror("Login", str(e))

        except UsuarioBloqueadoError as e:
            messagebox.showerror("Login", str(e))

        except RolNoAsignadoError as e:
            messagebox.showerror("Login", str(e))

        except ValidationError as e:
            messagebox.showerror("Login", str(e))

        except Exception as e:
            messagebox.showerror("Login", f"Ocurrió un error inesperado.\n\nDetalle: {e}")

    def _cancel(self):
        self.result = None
        self.destroy()


def run_login_window(master: tk.Misc | None = None):
    """
    - Si master viene, abre Toplevel modal.
    - Si no viene, crea root temporal y funciona standalone.
    - Retorna session_data o None.
    """
    if master is None:
        root = tk.Tk()
        root.withdraw()
        dlg = LoginDialog(root)
        root.wait_window(dlg)
        result = dlg.result
        root.destroy()
        return result

    dlg = LoginDialog(master)
    master.wait_window(dlg)
    return dlg.result