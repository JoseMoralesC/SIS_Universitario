# app/repositories/profesiones_repo.py
def listar_profesiones(conn):
    sql = """
        SELECT Profesion_Cod, Descripcion, Estado_Codigo
        FROM dbo.Profesiones
        ORDER BY Profesion_Cod;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()