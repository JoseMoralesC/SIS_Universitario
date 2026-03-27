from __future__ import annotations

import pyodbc


# =========================================================
# Helpers internos
# =========================================================
def _row_to_perfil_dict(row) -> dict | None:
    """
    Convierte una fila del perfil a dict estándar para la capa superior.
    """
    if not row:
        return None

    return {
        "usuario_seguridad_id": int(row[0]) if row[0] is not None else None,
        "codigo_usuario": int(row[1]) if row[1] is not None else None,
        "id_usuario": int(row[2]) if row[2] is not None else None,
        "usuario": str(row[3]) if row[3] is not None else "",
        "nombre_usuario": str(row[4]) if row[4] is not None else "",
        "correo": str(row[5]) if row[5] is not None else None,
        "tipo_usuario": int(row[6]) if row[6] is not None else None,
        "descripcion_tipo": str(row[7]) if row[7] is not None else None,
        "estado_usuario": int(row[8]) if row[8] is not None else None,
        "descripcion_estado": str(row[9]) if row[9] is not None else None,
        "rol_id": int(row[10]) if row[10] is not None else None,
        "codigo_rol": str(row[11]) if row[11] is not None else None,
        "nombre_rol": str(row[12]) if row[12] is not None else None,
        "debe_cambiar_clave": bool(row[13]) if row[13] is not None else False,
        "intentos_fallidos": int(row[14]) if row[14] is not None else 0,
        "bloqueado_hasta": row[15],
        "ultimo_acceso": row[16],
        "ultimo_cambio_clave": row[17],
        "fecha_creacion": row[18],
        "fecha_modificacion": row[19],
    }


# =========================================================
# Lectura de perfil
# =========================================================
def get_perfil_usuario_by_usuario_seguridad_id(
    conn: pyodbc.Connection,
    usuario_seguridad_id: int,
) -> dict | None:
    """
    Obtiene el perfil completo del usuario usando su Usuario_Seguridad_Id.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Id_Usuario,
            Usuario,
            Nombre_Usuario,
            Correo,
            Tipo_Usuario,
            Descripcion_Tipo,
            Estado_Usuario,
            Descripcion_Estado,
            Rol_Id,
            Codigo_Rol,
            Nombre_Rol,
            Debe_Cambiar_Clave,
            Intentos_Fallidos,
            Bloqueado_Hasta,
            Ultimo_Acceso,
            Ultimo_Cambio_Clave,
            Fecha_Creacion,
            Fecha_Modificacion
        FROM dbo.vw_Usuarios_Seguridad
        WHERE Usuario_Seguridad_Id = ?;
        """,
        (int(usuario_seguridad_id),),
    )
    row = cur.fetchone()
    return _row_to_perfil_dict(row)


def get_perfil_usuario_by_codigo_usuario(
    conn: pyodbc.Connection,
    codigo_usuario: int,
) -> dict | None:
    """
    Obtiene el perfil completo del usuario usando su Codigo_Usuario.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Id_Usuario,
            Usuario,
            Nombre_Usuario,
            Correo,
            Tipo_Usuario,
            Descripcion_Tipo,
            Estado_Usuario,
            Descripcion_Estado,
            Rol_Id,
            Codigo_Rol,
            Nombre_Rol,
            Debe_Cambiar_Clave,
            Intentos_Fallidos,
            Bloqueado_Hasta,
            Ultimo_Acceso,
            Ultimo_Cambio_Clave,
            Fecha_Creacion,
            Fecha_Modificacion
        FROM dbo.vw_Usuarios_Seguridad
        WHERE Codigo_Usuario = ?;
        """,
        (int(codigo_usuario),),
    )
    row = cur.fetchone()
    return _row_to_perfil_dict(row)


# =========================================================
# Validaciones de unicidad
# =========================================================
def exists_usuario_login_excluding_current(
    conn: pyodbc.Connection,
    usuario: str,
    usuario_seguridad_id: int,
) -> bool:
    """
    Valida si el login ya existe en otro usuario.
    """
    usuario = (usuario or "").strip()

    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Usuarios
        WHERE Usuario = ?
          AND Usuario_Seguridad_Id <> ?;
        """,
        (
            usuario,
            int(usuario_seguridad_id),
        ),
    )
    return cur.fetchone() is not None


def exists_correo_excluding_current(
    conn: pyodbc.Connection,
    correo: str | None,
    usuario_seguridad_id: int,
) -> bool:
    """
    Valida si el correo ya existe en otro usuario.
    Si el correo viene vacío, no aplica unicidad.
    """
    correo = (correo or "").strip()
    if not correo:
        return False

    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Usuarios
        WHERE Correo = ?
          AND Usuario_Seguridad_Id <> ?;
        """,
        (
            correo,
            int(usuario_seguridad_id),
        ),
    )
    return cur.fetchone() is not None


# =========================================================
# Update de datos no sensibles
# =========================================================
def update_perfil_usuario_no_sensible(
    conn: pyodbc.Connection,
    *,
    usuario_seguridad_id: int,
    usuario: str,
    nombre_usuario: str,
    correo: str | None,
) -> None:
    """
    Actualiza únicamente datos no sensibles del usuario:
    - Usuario
    - Nombre_Usuario
    - Correo

    El resto de campos se mantiene intacto.
    """
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.Usuarios
        SET
            Usuario = ?,
            Nombre_Usuario = ?,
            Correo = ?,
            Fecha_Modificacion = SYSDATETIME()
        WHERE Usuario_Seguridad_Id = ?;
        """,
        (
            (usuario or "").strip(),
            (nombre_usuario or "").strip(),
            (correo or "").strip() or None,
            int(usuario_seguridad_id),
        ),
    )
    conn.commit()


# =========================================================
# Relectura post-update
# =========================================================
def get_perfil_actualizado(
    conn: pyodbc.Connection,
    usuario_seguridad_id: int,
) -> dict | None:
    """
    Helper semántico para recargar el perfil luego de actualizar.
    """
    return get_perfil_usuario_by_usuario_seguridad_id(
        conn,
        usuario_seguridad_id=usuario_seguridad_id,
    )