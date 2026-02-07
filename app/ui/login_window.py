# app/ui/login_window.py
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from app.services.auth_service import (
    login_sql_y_validar_tabla,
    UsuarioNoRegistradoError,
    AuthError
)

def run_login_window():
    root = tk.Tk()
    root.title("Login de conexión a DB")
    root.geometry("420x260")
    root.resizable(False, False)

    # ------------------ RUTAS DE IMÁGENES ------------------
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    IMG_PATH = os.path.join(BASE_DIR, "assets", "users")

    # ------------------ IMAGEN ------------------
    img_label = tk.Label(root)
    img_label.pack(pady=10)

    def cargar_imagen(nombre_usuario: str):
        nombre = nombre_usuario.strip()

        if nombre:
            archivo = f"{nombre}.jpg"
        else:
            archivo = "default.png"

        ruta = os.path.join(IMG_PATH, archivo)

        if not os.path.exists(ruta):
            ruta = os.path.join(IMG_PATH, "default.png")

        img = Image.open(ruta)
        img = img.resize((90, 90))
        img_tk = ImageTk.PhotoImage(img)

        img_label.configure(image=img_tk)
        img_label.image = img_tk  # evita garbage collector

    cargar_imagen("")  # imagen inicial

    # ------------------ USUARIO ------------------
    tk.Label(root, text="Usuario:").pack()
    entry_usuario = tk.Entry(root, width=30)
    entry_usuario.pack()
    entry_usuario.bind("<KeyRelease>", lambda e: cargar_imagen(entry_usuario.get()))

    # ------------------ CONTRASEÑA ------------------
    tk.Label(root, text="Contraseña:").pack(pady=(6, 0))
    entry_contra = tk.Entry(root, width=30, show="*")
    entry_contra.pack()

    # ------------------ VALIDAR ------------------
    def validar():
        usuario = entry_usuario.get().strip()
        contra = entry_contra.get().strip()

        if not usuario or not contra:
            messagebox.showwarning("Advertencia", "Debe llenar todos los campos")
            return

        try:
            login_sql_y_validar_tabla(usuario, contra)
            messagebox.showinfo("Éxito", "Acceso permitido al sistema.")
        except UsuarioNoRegistradoError as e:
            messagebox.showerror("Error", str(e))
        except AuthError as e:
            messagebox.showerror("Error", f"Credenciales incorrectas:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado:\n{e}")

    def cancelar():
        root.destroy()

    # ------------------ BOTONES ------------------
    frame_btn = tk.Frame(root)
    frame_btn.pack(pady=12)

    tk.Button(frame_btn, text="VALIDAR", width=12, command=validar).pack(side="left", padx=6)
    tk.Button(frame_btn, text="CANCELAR", width=12, command=cancelar).pack(side="left", padx=6)

    root.mainloop()
