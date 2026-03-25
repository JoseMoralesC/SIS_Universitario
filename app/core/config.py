# app/core/config.py

# =========================================================
# Configuración de base de datos
# =========================================================

DB_SERVER = r"TACHER-THR\SQLEXPRESS02"
DB_NAME = "Universidad"
DB_DRIVER = "ODBC Driver 17 for SQL Server"

# Cuenta técnica de la aplicación
# Esta cuenta será la que use el sistema para conectarse siempre a SQL Server.
DB_APP_USER = "Administrador"
DB_APP_PASS = "1234"


# =========================================================
# Recursos de interfaz
# =========================================================

# carpeta imágenes de usuarios
USER_IMAGES_DIR = "app/assets/users"
DEFAULT_USER_IMAGE = "default.png"