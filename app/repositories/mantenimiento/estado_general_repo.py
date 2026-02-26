# app/repositories/estado_general_repo.py
def listar_estados(conn):
    sql = """
        SELECT Estado_Codigo, Estado_Desc
        FROM dbo.Estado_General
        ORDER BY Estado_Codigo;
    """
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()