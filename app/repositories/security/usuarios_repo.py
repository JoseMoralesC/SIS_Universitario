from __future__ import annotations

import pyodbc


# =========================================================
# Lookups de seguridad
# =========================================================

def fetch_roles_activos(conn: pyodbc.Connection) -> list[tuple[int, str, str]]:
    """
    Retorna roles activos para combos o validaciones:
    (rol_id, codigo_rol, nombre_rol)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            Rol_Id,
            Codigo_Rol,
            Nombre_Rol
        FROM dbo.Roles
        WHERE Estado = 1
        ORDER BY Nombre_Rol ASC;
        """
    )
    return [
        (int(r[0]), str(r[1]), str(r[2]))
        for r in cur.fetchall()
    ]


def fetch_tipos_usuario_activos(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    """
    Retorna tipos de usuario activos:
    (tipo_usuario, descripcion_tipo)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            Tipo_Usuario,
            Descripcion_Tipo
        FROM dbo.Tipo_Usuario
        WHERE Estado_Tipo = 1
        ORDER BY Tipo_Usuario ASC;
        """
    )
    return [
        (int(r[0]), str(r[1]))
        for r in cur.fetchall()
    ]


def fetch_estados_usuario(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    """
    Retorna estados de usuario:
    (estado_usuario, descripcion_estado)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            Estado_Usuario,
            Descripcion_Estado
        FROM dbo.Estado_Usuario
        ORDER BY Estado_Usuario ASC;
        """
    )
    return [
        (int(r[0]), str(r[1]))
        for r in cur.fetchall()
    ]


# =========================================================
# Validaciones de existencia
# =========================================================

def exists_usuario_login(
    conn: pyodbc.Connection,
    usuario: str,
    exclude_usuario_seguridad_id: int | None = None,
) -> bool:
    """
    Valida si ya existe un login de usuario.
    """
    usuario = (usuario or "").strip()

    cur = conn.cursor()
    if exclude_usuario_seguridad_id is None:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Usuarios
            WHERE Usuario = ?;
            """,
            usuario,
        )
    else:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Usuarios
            WHERE Usuario = ?
              AND Usuario_Seguridad_Id <> ?;
            """,
            (
                usuario,
                int(exclude_usuario_seguridad_id),
            ),
        )

    return cur.fetchone() is not None


def exists_id_usuario(
    conn: pyodbc.Connection,
    id_usuario: int,
    exclude_usuario_seguridad_id: int | None = None,
) -> bool:
    """
    Valida si ya existe un Id_Usuario en dbo.Usuarios.
    """
    cur = conn.cursor()
    if exclude_usuario_seguridad_id is None:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Usuarios
            WHERE Id_Usuario = ?;
            """,
            int(id_usuario),
        )
    else:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Usuarios
            WHERE Id_Usuario = ?
              AND Usuario_Seguridad_Id <> ?;
            """,
            (
                int(id_usuario),
                int(exclude_usuario_seguridad_id),
            ),
        )

    return cur.fetchone() is not None


def exists_correo_usuario(
    conn: pyodbc.Connection,
    correo: str | None,
    exclude_usuario_seguridad_id: int | None = None,
) -> bool:
    """
    Valida si el correo ya está registrado.
    Si el correo viene vacío o None, no valida unicidad.
    """
    correo = (correo or "").strip()
    if not correo:
        return False

    cur = conn.cursor()
    if exclude_usuario_seguridad_id is None:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Usuarios
            WHERE Correo = ?;
            """,
            correo,
        )
    else:
        cur.execute(
            """
            SELECT TOP 1 1
            FROM dbo.Usuarios
            WHERE Correo = ?
              AND Usuario_Seguridad_Id <> ?;
            """,
            (
                correo,
                int(exclude_usuario_seguridad_id),
            ),
        )

    return cur.fetchone() is not None


def exists_rol_activo(conn: pyodbc.Connection, rol_id: int) -> bool:
    """
    Valida que el rol exista y esté activo.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Roles
        WHERE Rol_Id = ?
          AND Estado = 1;
        """,
        int(rol_id),
    )
    return cur.fetchone() is not None


def exists_tipo_usuario_activo(conn: pyodbc.Connection, tipo_usuario: int) -> bool:
    """
    Valida que el tipo de usuario exista y esté activo.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Tipo_Usuario
        WHERE Tipo_Usuario = ?
          AND Estado_Tipo = 1;
        """,
        int(tipo_usuario),
    )
    return cur.fetchone() is not None


def exists_estado_usuario(conn: pyodbc.Connection, estado_usuario: int) -> bool:
    """
    Valida que el estado de usuario exista.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 1
        FROM dbo.Estado_Usuario
        WHERE Estado_Usuario = ?;
        """,
        int(estado_usuario),
    )
    return cur.fetchone() is not None


# =========================================================
# Lectura de apoyo
# =========================================================

def get_rol_by_id(conn: pyodbc.Connection, rol_id: int) -> dict | None:
    """
    Retorna un rol por ID.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            Rol_Id,
            Codigo_Rol,
            Nombre_Rol,
            Descripcion,
            Es_Sistema,
            Estado,
            Fecha_Creacion
        FROM dbo.Roles
        WHERE Rol_Id = ?;
        """,
        int(rol_id),
    )
    row = cur.fetchone()
    if not row:
        return None

    return {
        "rol_id": int(row[0]),
        "codigo_rol": str(row[1]),
        "nombre_rol": str(row[2]),
        "descripcion": str(row[3]) if row[3] is not None else None,
        "es_sistema": bool(row[4]),
        "estado": bool(row[5]),
        "fecha_creacion": row[6],
    }


def get_usuario_seguridad_by_id(
    conn: pyodbc.Connection,
    usuario_seguridad_id: int,
) -> dict | None:
    """
    Retorna el usuario de seguridad desde la vista consolidada.
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
        int(usuario_seguridad_id),
    )
    row = cur.fetchone()
    if not row:
        return None

    return {
        "usuario_seguridad_id": int(row[0]),
        "codigo_usuario": int(row[1]),
        "id_usuario": int(row[2]),
        "usuario": str(row[3]),
        "nombre_usuario": str(row[4]),
        "correo": str(row[5]) if row[5] is not None else None,
        "tipo_usuario": int(row[6]),
        "descripcion_tipo": str(row[7]) if row[7] is not None else None,
        "estado_usuario": int(row[8]),
        "descripcion_estado": str(row[9]) if row[9] is not None else None,
        "rol_id": int(row[10]) if row[10] is not None else None,
        "codigo_rol": str(row[11]) if row[11] is not None else None,
        "nombre_rol": str(row[12]) if row[12] is not None else None,
        "debe_cambiar_clave": bool(row[13]),
        "intentos_fallidos": int(row[14]),
        "bloqueado_hasta": row[15],
        "ultimo_acceso": row[16],
        "ultimo_cambio_clave": row[17],
        "fecha_creacion": row[18],
        "fecha_modificacion": row[19],
    }


# =========================================================
# CRUD usuarios de seguridad
# =========================================================

def insert_usuario_seguridad(
    conn: pyodbc.Connection,
    *,
    id_usuario: int,
    usuario: str,
    nombre_usuario: str,
    tipo_usuario: int,
    estado_usuario: int,
    correo: str | None,
    clave_hash: str,
    clave_salt: str,
    clave_algoritmo: str = "pbkdf2_sha256",
    clave_iteraciones: int = 390000,
    debe_cambiar_clave: bool = True,
) -> dict:
    """
    Inserta un usuario de seguridad en dbo.Usuarios.

    Usa los defaults de BD para:
    - Codigo_Usuario
    - Usuario_Seguridad_Id
    - Fecha_Creacion
    - Fecha_Modificacion
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Usuarios (
            Id_Usuario,
            Usuario,
            Nombre_Usuario,
            Tipo_Usuario,
            Estado_Usuario,
            Correo,
            Clave_Hash,
            Clave_Salt,
            Clave_Algoritmo,
            Clave_Iteraciones,
            Debe_Cambiar_Clave,
            Intentos_Fallidos
        )
        OUTPUT
            INSERTED.Codigo_Usuario,
            INSERTED.Usuario_Seguridad_Id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
        """,
        (
            int(id_usuario),
            (usuario or "").strip(),
            (nombre_usuario or "").strip(),
            int(tipo_usuario),
            int(estado_usuario),
            (correo or "").strip() or None,
            clave_hash,
            clave_salt,
            (clave_algoritmo or "").strip(),
            int(clave_iteraciones),
            1 if debe_cambiar_clave else 0,
        ),
    )
    row = cur.fetchone()
    conn.commit()

    return {
        "codigo_usuario": int(row[0]),
        "usuario_seguridad_id": int(row[1]),
    }


def insert_usuario_rol(
    conn: pyodbc.Connection,
    *,
    usuario_seguridad_id: int,
    rol_id: int,
    es_principal: bool = True,
    estado: bool = True,
) -> None:
    """
    Asigna un rol al usuario en dbo.Usuario_Rol.
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.Usuario_Rol (
            Usuario_Seguridad_Id,
            Rol_Id,
            Es_Principal,
            Estado
        )
        VALUES (?, ?, ?, ?);
        """,
        (
            int(usuario_seguridad_id),
            int(rol_id),
            1 if es_principal else 0,
            1 if estado else 0,
        ),
    )
    conn.commit()


def create_usuario_con_rol_principal(
    conn: pyodbc.Connection,
    *,
    id_usuario: int,
    usuario: str,
    nombre_usuario: str,
    tipo_usuario: int,
    estado_usuario: int,
    correo: str | None,
    clave_hash: str,
    clave_salt: str,
    clave_algoritmo: str = "pbkdf2_sha256",
    clave_iteraciones: int = 390000,
    debe_cambiar_clave: bool = True,
    rol_id: int,
) -> dict:
    """
    Crea el usuario y asigna un único rol principal.

    Este método encapsula el flujo base del módulo de registro:
    1) inserta en dbo.Usuarios
    2) inserta en dbo.Usuario_Rol
    3) retorna resumen del usuario creado
    """
    usuario_creado = insert_usuario_seguridad(
        conn,
        id_usuario=id_usuario,
        usuario=usuario,
        nombre_usuario=nombre_usuario,
        tipo_usuario=tipo_usuario,
        estado_usuario=estado_usuario,
        correo=correo,
        clave_hash=clave_hash,
        clave_salt=clave_salt,
        clave_algoritmo=clave_algoritmo,
        clave_iteraciones=clave_iteraciones,
        debe_cambiar_clave=debe_cambiar_clave,
    )

    insert_usuario_rol(
        conn,
        usuario_seguridad_id=usuario_creado["usuario_seguridad_id"],
        rol_id=rol_id,
        es_principal=True,
        estado=True,
    )

    data = get_usuario_seguridad_by_id(
        conn,
        usuario_creado["usuario_seguridad_id"],
    )

    return data if data is not None else usuario_creado