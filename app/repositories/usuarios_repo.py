# app/repositories/usuarios_repo.py
# Repositorio para operaciones relacionadas con la tabla Usuarios



def existe_usuario_en_tabla(conn, usuario: str) -> bool:
    """
    Valida que exista un registro en dbo.Usuarios con Usuario = @usuario
    """
    sql = "SELECT 1 FROM dbo.Usuarios WHERE Usuario = ?;"
    cur = conn.cursor()
    cur.execute(sql, (usuario,))
    return cur.fetchone() is not None
