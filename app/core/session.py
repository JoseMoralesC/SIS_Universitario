# app/core/session.py
from app.ui.login_window import run_login_window
from app.ui.main_menu import run_main_menu

if __name__ == "__main__":
    creds = run_login_window()
    if creds:
        run_main_menu(usuario=creds["usuario"], db_user=creds["usuario"], db_pass=creds["contra"])