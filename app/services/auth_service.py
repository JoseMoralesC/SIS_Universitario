# app/services/auth_service.py
# Servicio de autenticación para validar credenciales SQL y permisos en la tabla Usuarios

import pyodbc
from app.core.db import connect
from app.repositories.usuarios_repo import existe_usuario_en_tabla

class AuthError(Exception):
    pass

class UsuarioNoRegistradoError(AuthError):
    pass

def login_sql_y_validar_tabla(usuario: str, contra: str) -> None:
    """
    1) Intenta conectar a SQL Server con SQL Authentication.
    2) Si conecta, valida que el usuario exista en dbo.Usuarios.
       Si no existe: levantar UsuarioNoRegistradoError con el mensaje exacto requerido.
    """
    try:
        conn = connect(usuario, contra)
    except pyodbc.Error as e:
        # credenciales malas / server / driver / etc.
        raise AuthError(str(e))

    try:
        if not existe_usuario_en_tabla(conn, usuario):
            raise UsuarioNoRegistradoError(
                "Usuario con permiso en SQL, pero, no registrado en la tabla de la Base de Datos"
            )
    finally:
        try:
            conn.close()
        except Exception:
            pass
