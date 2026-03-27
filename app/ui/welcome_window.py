from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, messagebox

from app.ui.views.main_menu_view import MainMenuView
from app.core.db import connect_app
from app.core.session import set_session, clear_session
from app.services.auth_service import (
    login_sistema,
    CredencialesInvalidasError,
    UsuarioInactivoError,
    UsuarioBloqueadoError,
    RolNoAsignadoError,
)
from app.repositories.auditoria_repo import insert_auditoria
from app.core.auditoria import Mov
from app.core.exceptions import ValidationError

# Pillow (para .jpg)
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


class WelcomeWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestión Académica – Bienvenida")
        self.minsize(1100, 650)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.bg_left = "#15202b"
        self.bg_right = "#f2f4f7"
        self.accent = "#2f445d"
        self.text_soft = "#c7d2e0"

        style.configure("W.Left.TFrame", background=self.bg_left)
        style.configure("W.Right.TFrame", background=self.bg_right)

        style.configure(
            "W.Title.TLabel",
            background=self.bg_left,
            foreground="white",
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "W.Sub.TLabel",
            background=self.bg_left,
            foreground=self.text_soft,
            font=("Segoe UI", 10),
        )

        style.configure(
            "W.Header.TLabel",
            background=self.bg_right,
            foreground="#1f2a35",
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "W.Text.TLabel",
            background=self.bg_right,
            foreground="#3a4b5c",
            font=("Segoe UI", 11),
        )

        style.configure("Card.TLabelframe", background="white")
        style.configure(
            "Card.TLabelframe.Label",
            background="white",
            foreground="#1f2a35",
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "Card.TLabel",
            background="white",
            foreground="#1f2a35",
            font=("Segoe UI", 10),
        )

        # Login panel style
        style.configure("LP.TFrame", background="white")
        style.configure(
            "LP.Title.TLabel",
            background="white",
            foreground="#1f2a35",
            font=("Segoe UI", 14, "bold"),
        )
        style.configure(
            "LP.Sub.TLabel",
            background="white",
            foreground="#506070",
            font=("Segoe UI", 10),
        )
        style.configure(
            "LP.Field.TLabel",
            background="white",
            foreground="#1f2a35",
            font=("Segoe UI", 10, "bold"),
        )

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=5)
        self.rowconfigure(0, weight=1)

        # -----------------------------
        # Panel izquierdo
        # -----------------------------
        left = ttk.Frame(self, style="W.Left.TFrame", width=340)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        ttk.Label(left, text="Gestión Académica", style="W.Title.TLabel").grid(
            row=0, column=0, sticky="w", padx=24, pady=(28, 6)
        )

        ttk.Label(
            left,
            text="Plataforma administrativa para\nDocentes, Estudiantes, Cursos y Programas.",
            style="W.Sub.TLabel",
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # “Estado del sistema” (informativo)
        box = tk.Frame(left, bg=self.bg_left, highlightbackground="#2a3a4a", highlightthickness=1)
        box.grid(row=2, column=0, sticky="ew", padx=24, pady=(6, 18))

        def status_line(title: str, value: str):
            row = tk.Frame(box, bg=self.bg_left)
            row.pack(fill="x", padx=12, pady=8)
            tk.Label(
                row,
                text=title,
                bg=self.bg_left,
                fg=self.text_soft,
                font=("Segoe UI", 9),
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                bg=self.bg_left,
                fg="white",
                font=("Segoe UI", 9, "bold"),
            ).pack(side="right")

        status_line("Servidor", "SQL Server Express")
        status_line("Base de datos", "Universidad")
        status_line("Modo", "Académico")
        status_line("Versión", "6.5")
        status_line("Estado", "Finalizado")

        btn_login = tk.Button(
            left,
            text="Iniciar sesión",
            bg=self.accent,
            fg="white",
            activebackground="#38506a",
            activeforeground="white",
            relief="groove",
            bd=2,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            padx=8,
            pady=10,
            command=self.toggle_login_panel,
        )
        btn_login.grid(row=3, column=0, sticky="ew", padx=24, pady=(6, 10))

        btn_exit = tk.Button(
            left,
            text="Salir",
            bg="#6b1d1d",
            fg="white",
            activebackground="#8a2727",
            activeforeground="white",
            relief="groove",
            bd=2,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            padx=8,
            pady=10,
            command=self.destroy,
        )
        btn_exit.grid(row=4, column=0, sticky="ew", padx=24, pady=(8, 24))

        # -----------------------------
        # Panel derecho
        # -----------------------------
        right = ttk.Frame(self, style="W.Right.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        self.wrap = tk.Frame(right, bg=self.bg_right)
        self.wrap.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
        self.wrap.columnconfigure(0, weight=1)
        self.wrap.rowconfigure(0, weight=1)

        self.info_wrap = tk.Frame(self.wrap, bg=self.bg_right)
        self.info_wrap.grid(row=0, column=0, sticky="nsew")
        self.info_wrap.columnconfigure(0, weight=1)
        self.info_wrap.rowconfigure(2, weight=1)

        ttk.Label(
            self.info_wrap,
            text="Bienvenido al Sistema Administrativo",
            style="W.Header.TLabel",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        ttk.Label(
            self.info_wrap,
            text="Seleccione “Iniciar sesión” para acceder al menú principal.",
            style="W.Text.TLabel",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 14))

        cards = tk.Frame(self.info_wrap, bg=self.bg_right)
        cards.grid(row=2, column=0, sticky="nsew")
        cards.columnconfigure((0, 1), weight=1)
        cards.rowconfigure((0, 1), weight=1)

        self._card(cards, 0, 0, "Mantenimientos", "CRUD de Docentes, Cursos,\nEstudiantes y Programas.")
        self._card(cards, 0, 1, "Matrículas", "Gestión de matrículas.\nMatriculas en curso, historial, etc.")
        self._card(cards, 1, 0, "Asistencias", "Control de asistencias.\ndetallada por curso y docente")
        self._card(cards, 1, 1, "Auditoria", "Consultas detalladas.\n")

        tk.Label(
            self.info_wrap,
            text="© Proyecto Académico – CUC / Programación III",
            bg=self.bg_right,
            fg="#667788",
            font=("Segoe UI", 9),
        ).grid(row=3, column=0, sticky="w", pady=(14, 0))

        self.login_panel = LoginPanel(
            parent=self.wrap,
            on_success=self._open_main_menu_embedded,
            on_cancel=self.hide_login_panel,
        )
        self.login_panel.place_forget()
        self._login_open = False

        self.main_menu_view: MainMenuView | None = None
        self.main_layer = tk.Frame(self, bg=self.bg_right)
        self.main_layer.place_forget()

        self.after(50, lambda: None)

    def _card(self, parent, r, c, title, desc):
        lf = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe", padding=(14, 12))
        lf.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
        ttk.Label(lf, text=desc, style="Card.TLabel", justify="left").grid(row=0, column=0, sticky="w")

    # -----------------------------
    # Login panel show/hide
    # -----------------------------
    def toggle_login_panel(self):
        if self._login_open:
            self.hide_login_panel()
        else:
            self.show_login_panel()

    def show_login_panel(self):
        self._login_open = True

        self.update_idletasks()
        parent = self.login_panel.master
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        panel_w = 420
        panel_h = ph

        start_x = pw
        end_x = max(0, pw - panel_w)

        self.login_panel.place(x=start_x, y=0, width=panel_w, height=panel_h)
        self.login_panel.lift()
        self.login_panel.focus_user()

        self._slide(self.login_panel, start_x, end_x, step=28)

    def hide_login_panel(self, on_done=None):
        if not self._login_open:
            if on_done:
                on_done()
            return

        self.update_idletasks()
        parent = self.login_panel.master
        pw = parent.winfo_width()

        current_x = self.login_panel.winfo_x()
        end_x = pw

        def after_hide():
            self.login_panel.place_forget()
            self._login_open = False
            if on_done:
                on_done()

        self._slide(self.login_panel, current_x, end_x, step=32, on_done=after_hide)

    def _slide(self, widget, x_from, x_to, step=24, on_done=None):
        direction = 1 if x_to > x_from else -1

        def tick(x):
            done = (direction == 1 and x >= x_to) or (direction == -1 and x <= x_to)
            if done:
                widget.place_configure(x=x_to)
                if on_done:
                    on_done()
                return

            widget.place_configure(x=x)
            self.after(10, lambda: tick(x + step * direction))

        tick(x_from)

    # -----------------------------
    # MainMenu embebido (overlay)
    # -----------------------------
    def _open_main_menu_embedded(self, session_data: dict):
        """
        Login OK -> mostrar MainMenuView embebido ocupando toda la ventana.
        """
        def _after_login_hidden():
            self.update_idletasks()
            w = self.winfo_width()
            h = self.winfo_height()
            try:
                self.state("zoomed")
            except Exception:
                pass
            self.update_idletasks()

            start_x = w
            end_x = 0

            self.main_layer.place(x=start_x, y=0, width=w, height=h)
            self.main_layer.lift()

            usuario = session_data.get("usuario")
            codigo_usuario = session_data.get("codigo_usuario")

            if self.main_menu_view is not None:
                try:
                    self.main_menu_view.destroy()
                except Exception:
                    pass
                self.main_menu_view = None

            self.main_menu_view = MainMenuView(
                parent=self.main_layer,
                usuario=usuario,
                db_user=None,
                db_pass=None,
                codigo_usuario=codigo_usuario,
                on_exit_request=self._on_main_menu_exit_request,
            )
            self.main_menu_view.pack(fill="both", expand=True)

            self._slide(self.main_layer, start_x, end_x, step=40)

        self.hide_login_panel(on_done=_after_login_hidden)

    def _reset_login_state(self):
        """
        Restablece por completo el panel de login para permitir
        un cambio limpio de usuario entre sesiones.
        """
        try:
            self.login_panel.reset_form()
        except Exception:
            pass

    def _on_main_menu_exit_request(self, salir_todo: bool):
        if salir_todo:
            clear_session()
            self._reset_login_state()
            self.destroy()
            return

        self.update_idletasks()
        w = self.winfo_width()

        current_x = self.main_layer.winfo_x()
        end_x = w

        def _done():
            self.main_layer.place_forget()

            if self.main_menu_view is not None:
                try:
                    self.main_menu_view.destroy()
                except Exception:
                    pass
                self.main_menu_view = None

            clear_session()
            self._reset_login_state()
            self.show_login_panel()

        self._slide(self.main_layer, current_x, end_x, step=44, on_done=_done)


class LoginPanel(ttk.Frame):
    def __init__(self, parent, on_success, on_cancel):
        super().__init__(parent, style="LP.TFrame")

        self.on_success = on_success
        self.on_cancel = on_cancel

        self.assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "users")
        self._avatar_index = self._build_avatar_index(self.assets_dir)

        self.var_user = tk.StringVar()
        self.var_pass = tk.StringVar()

        self.var_user.trace_add("write", lambda *_: self._update_avatar())

        self._avatar_img = None

        self._build_ui()
        self._update_avatar()

    def _build_avatar_index(self, directory: str) -> dict[str, str]:
        idx = {}
        if not os.path.isdir(directory):
            return idx
        for fn in os.listdir(directory):
            base, ext = os.path.splitext(fn)
            if ext.lower() not in (".png", ".jpg", ".jpeg", ".gif"):
                continue
            idx[base.strip().lower()] = os.path.join(directory, fn)
        return idx

    def _build_ui(self):
        card = tk.Frame(self, bg="white", highlightbackground="#d6dde6", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        card.columnconfigure(0, weight=1)

        header = tk.Frame(card, bg="white")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Iniciar sesión", style="LP.Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Ingrese sus credenciales para continuar.", style="LP.Sub.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )

        sep = ttk.Separator(card)
        sep.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 12))

        av_wrap = tk.Frame(card, bg="white")
        av_wrap.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        av_wrap.columnconfigure(1, weight=1)

        self.lbl_avatar = tk.Label(av_wrap, bg="white")
        self.lbl_avatar.grid(row=0, column=0, rowspan=3, sticky="w", padx=(0, 14))

        ttk.Label(av_wrap, text="Usuario", style="LP.Field.TLabel").grid(row=0, column=1, sticky="w")
        self.ent_user = ttk.Entry(av_wrap, textvariable=self.var_user)
        self.ent_user.grid(row=1, column=1, sticky="ew", pady=(4, 10))

        ttk.Label(av_wrap, text="Contraseña", style="LP.Field.TLabel").grid(row=2, column=1, sticky="w")
        self.ent_pass = ttk.Entry(av_wrap, textvariable=self.var_pass, show="*")
        self.ent_pass.grid(row=3, column=1, sticky="ew", pady=(4, 0))

        tip = tk.Label(
            card,
            text="Tip: al escribir el usuario, la foto se carga automáticamente.",
            bg="white",
            fg="#6a7a8a",
            font=("Segoe UI", 9),
        )
        tip.grid(row=3, column=0, sticky="w", padx=16, pady=(6, 10))

        btns = tk.Frame(card, bg="white")
        btns.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))
        btns.columnconfigure((0, 1), weight=1)

        btn_login = tk.Button(
            btns,
            text="Ingresar",
            bg="#2f445d",
            fg="white",
            activebackground="#38506a",
            activeforeground="white",
            relief="groove",
            bd=2,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=8,
            pady=10,
            command=self._submit,
        )
        btn_login.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_cancel = tk.Button(
            btns,
            text="Cancelar",
            bg="#667788",
            fg="white",
            activebackground="#74879a",
            activeforeground="white",
            relief="groove",
            bd=2,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=8,
            pady=10,
            command=self.on_cancel,
        )
        btn_cancel.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.ent_user.bind("<Return>", lambda e: self.ent_pass.focus_set())
        self.ent_pass.bind("<Return>", lambda e: self._submit())
        self.ent_pass.bind("<Escape>", lambda e: self.on_cancel())

    def focus_user(self):
        self.after(10, lambda: self.ent_user.focus_set())

    def reset_form(self):
        """
        Limpia completamente el formulario de login para soportar
        un cambio de usuario limpio al cerrar sesión.
        """
        self.var_user.set("")
        self.var_pass.set("")
        self._update_avatar()
        self.focus_user()

    def _find_avatar_path(self, username: str) -> str | None:
        key = (username or "").strip().lower()
        if not key:
            return self._avatar_index.get("default")
        if key in self._avatar_index:
            return self._avatar_index[key]
        for stem, path in self._avatar_index.items():
            if stem != "default" and stem.startswith(key):
                return path
        return self._avatar_index.get("default")

    def _update_avatar(self):
        path = self._find_avatar_path(self.var_user.get())
        if not path:
            self.lbl_avatar.configure(image="", text="")
            self._avatar_img = None
            return

        if Image is None or ImageTk is None:
            if path.lower().endswith(".png"):
                try:
                    img = tk.PhotoImage(file=path)
                    self._avatar_img = img
                    self.lbl_avatar.configure(image=img, text="")
                except Exception:
                    self.lbl_avatar.configure(image="", text="")
                    self._avatar_img = None
            else:
                self.lbl_avatar.configure(image="", text="")
                self._avatar_img = None
            return

        try:
            im = Image.open(path).convert("RGBA")
            im = im.resize((120, 120))
            img = ImageTk.PhotoImage(im)
            self._avatar_img = img
            self.lbl_avatar.configure(image=img, text="")
        except Exception:
            self.lbl_avatar.configure(image="", text="")
            self._avatar_img = None

    def _registrar_auditoria(self, codigo_usuario: int | None, movimiento_cod: int) -> None:
        """
        Registra auditoría usando la conexión técnica.
        Si falla, no bloquea el flujo de login.
        """
        if codigo_usuario is None:
            return

        conn = None
        try:
            conn = connect_app()
            insert_auditoria(conn, codigo_usuario=codigo_usuario, movimiento_cod=movimiento_cod)
        except Exception:
            pass
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def _submit(self):
        u = self.var_user.get().strip()
        p = self.var_pass.get().strip()

        if not u or not p:
            messagebox.showwarning("Validación", "Debe ingresar usuario y contraseña.")
            return

        try:
            session_data = login_sistema(u, p)
            set_session(session_data)

            codigo_usuario = session_data.get("codigo_usuario")
            self._registrar_auditoria(codigo_usuario, Mov.LOGIN_OK)

            self.var_pass.set("")
            self.on_success(session_data)

        except CredencialesInvalidasError as e:
            self._registrar_auditoria(None, Mov.LOGIN_FAIL)
            messagebox.showerror("Login", str(e))

        except UsuarioInactivoError as e:
            self._registrar_auditoria(None, Mov.LOGIN_FAIL)
            messagebox.showerror("Login", str(e))

        except UsuarioBloqueadoError as e:
            self._registrar_auditoria(None, Mov.LOGIN_FAIL)
            messagebox.showerror("Login", str(e))

        except RolNoAsignadoError as e:
            self._registrar_auditoria(None, Mov.LOGIN_FAIL)
            messagebox.showerror("Login", str(e))

        except ValidationError as e:
            self._registrar_auditoria(None, Mov.LOGIN_FAIL)
            messagebox.showerror("Login", str(e))

        except Exception as e:
            self._registrar_auditoria(None, Mov.LOGIN_FAIL)
            messagebox.showerror("Login", f"Ocurrió un error inesperado.\n\nDetalle: {e}")


def run_welcome_window():
    app = WelcomeWindow()
    app.mainloop()