from __future__ import annotations

import pyodbc


class UsuarioSecurityRepository:
    """
    Repositorio de seguridad para autenticación, roles y permisos.

    Este repositorio asume la existencia de la vista:
        dbo.vw_Usuarios_Seguridad

    Y las tablas:
        dbo.Usuario_Rol
        dbo.Roles
        dbo.Permisos
        dbo.Rol_Permiso
        dbo.Usuarios
    """

    # =========================================================
    # Helpers privados
    # =========================================================
    @staticmethod
    def _row_to_user_dict(row) -> dict | None:
        if not row:
            return None

        return {
            "usuario_seguridad_id": int(row[0]) if row[0] is not None else None,
            "codigo_usuario": int(row[1]) if row[1] is not None else None,
            "id_usuario": int(row[2]) if row[2] is not None else None,
            "usuario": str(row[3]) if row[3] is not None else "",
            "nombre_usuario": str(row[4]) if row[4] is not None else "",
            "correo": str(row[5]) if row[5] is not None else None,
            "clave_hash": str(row[6]) if row[6] is not None else None,
            "clave_salt": str(row[7]) if row[7] is not None else None,
            "clave_algoritmo": str(row[8]) if row[8] is not None else None,
            "clave_iteraciones": int(row[9]) if row[9] is not None else None,
            "debe_cambiar_clave": bool(row[10]) if row[10] is not None else False,
            "intentos_fallidos": int(row[11]) if row[11] is not None else 0,
            "bloqueado_hasta": row[12],
            "ultimo_acceso": row[13],
            "ultimo_cambio_clave": row[14],
            "fecha_creacion": row[15],
            "fecha_modificacion": row[16],
            "tipo_usuario": int(row[17]) if row[17] is not None else None,
            "descripcion_tipo": str(row[18]) if row[18] is not None else None,
            "estado_usuario": int(row[19]) if row[19] is not None else None,
            "descripcion_estado": str(row[20]) if row[20] is not None else None,
            "rol_id": int(row[21]) if row[21] is not None else None,
            "codigo_rol": str(row[22]) if row[22] is not None else None,
            "nombre_rol": str(row[23]) if row[23] is not None else None,
        }

    # =========================================================
    # Lectura principal de usuario para login
    # =========================================================
    def get_usuario_para_login(
        self,
        conn: pyodbc.Connection,
        usuario: str,
    ) -> dict | None:
        """
        Busca el usuario principal para autenticación desde la vista de seguridad.
        """
        sql = """
        SELECT TOP 1
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Id_Usuario,
            Usuario,
            Nombre_Usuario,
            Correo,
            Clave_Hash,
            Clave_Salt,
            Clave_Algoritmo,
            Clave_Iteraciones,
            Debe_Cambiar_Clave,
            Intentos_Fallidos,
            Bloqueado_Hasta,
            Ultimo_Acceso,
            Ultimo_Cambio_Clave,
            Fecha_Creacion,
            Fecha_Modificacion,
            Tipo_Usuario,
            Descripcion_Tipo,
            Estado_Usuario,
            Descripcion_Estado,
            Rol_Id,
            Codigo_Rol,
            Nombre_Rol
        FROM dbo.vw_Usuarios_Seguridad
        WHERE Usuario = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (usuario,))
        row = cur.fetchone()
        return self._row_to_user_dict(row)

    def exists_usuario(
        self,
        conn: pyodbc.Connection,
        usuario: str,
    ) -> bool:
        """
        Valida si existe un usuario registrado en el esquema de seguridad.
        """
        sql = """
        SELECT TOP 1 1
        FROM dbo.Usuarios
        WHERE Usuario = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (usuario,))
        return cur.fetchone() is not None

    # =========================================================
    # Permisos
    # =========================================================
    def get_permisos_usuario(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> list[str]:
        """
        Retorna la lista de códigos de permiso activos del usuario.
        """
        sql = """
        SELECT DISTINCT
            p.Codigo_Permiso
        FROM dbo.Usuario_Rol ur
        INNER JOIN dbo.Roles r
            ON r.Rol_Id = ur.Rol_Id
        INNER JOIN dbo.Rol_Permiso rp
            ON rp.Rol_Id = r.Rol_Id
           AND rp.Estado = 1
        INNER JOIN dbo.Permisos p
            ON p.Permiso_Id = rp.Permiso_Id
           AND p.Estado = 1
        WHERE ur.Usuario_Seguridad_Id = ?
          AND ur.Estado = 1
          AND r.Estado = 1
        ORDER BY p.Codigo_Permiso;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        rows = cur.fetchall()
        return [str(r[0]) for r in rows]

    def get_roles_usuario(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> list[dict]:
        """
        Retorna todos los roles activos del usuario.
        """
        sql = """
        SELECT
            r.Rol_Id,
            r.Codigo_Rol,
            r.Nombre_Rol,
            ur.Es_Principal
        FROM dbo.Usuario_Rol ur
        INNER JOIN dbo.Roles r
            ON r.Rol_Id = ur.Rol_Id
        WHERE ur.Usuario_Seguridad_Id = ?
          AND ur.Estado = 1
          AND r.Estado = 1
        ORDER BY ur.Es_Principal DESC, r.Nombre_Rol ASC;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        rows = cur.fetchall()

        return [
            {
                "rol_id": int(r[0]),
                "codigo_rol": str(r[1]),
                "nombre_rol": str(r[2]),
                "es_principal": bool(r[3]),
            }
            for r in rows
        ]

    def get_rol_principal_usuario(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> dict | None:
        """
        Retorna el rol principal activo del usuario.
        """
        sql = """
        SELECT TOP 1
            r.Rol_Id,
            r.Codigo_Rol,
            r.Nombre_Rol,
            ur.Es_Principal
        FROM dbo.Usuario_Rol ur
        INNER JOIN dbo.Roles r
            ON r.Rol_Id = ur.Rol_Id
        WHERE ur.Usuario_Seguridad_Id = ?
          AND ur.Estado = 1
          AND r.Estado = 1
        ORDER BY ur.Es_Principal DESC, r.Rol_Id ASC;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        row = cur.fetchone()

        if not row:
            return None

        return {
            "rol_id": int(row[0]),
            "codigo_rol": str(row[1]),
            "nombre_rol": str(row[2]),
            "es_principal": bool(row[3]),
        }

    # =========================================================
    # Estado de acceso
    # =========================================================
    def incrementar_intentos_fallidos(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> None:
        """
        Incrementa en 1 los intentos fallidos del usuario.
        """
        sql = """
        UPDATE dbo.Usuarios
        SET Intentos_Fallidos = ISNULL(Intentos_Fallidos, 0) + 1
        WHERE Usuario_Seguridad_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        conn.commit()

    def resetear_intentos_fallidos(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> None:
        """
        Reinicia el contador de intentos fallidos.
        """
        sql = """
        UPDATE dbo.Usuarios
        SET Intentos_Fallidos = 0
        WHERE Usuario_Seguridad_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        conn.commit()

    def actualizar_ultimo_acceso(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> None:
        """
        Actualiza la fecha/hora del último acceso exitoso.
        """
        sql = """
        UPDATE dbo.Usuarios
        SET Ultimo_Acceso = SYSDATETIME()
        WHERE Usuario_Seguridad_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        conn.commit()

    def bloquear_hasta(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
        minutos: int,
    ) -> None:
        """
        Bloquea temporalmente al usuario por N minutos.
        """
        sql = """
        UPDATE dbo.Usuarios
        SET Bloqueado_Hasta = DATEADD(MINUTE, ?, SYSDATETIME())
        WHERE Usuario_Seguridad_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(minutos), int(usuario_seguridad_id)))
        conn.commit()

    def limpiar_bloqueo(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> None:
        """
        Limpia el bloqueo temporal del usuario.
        """
        sql = """
        UPDATE dbo.Usuarios
        SET Bloqueado_Hasta = NULL
        WHERE Usuario_Seguridad_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        conn.commit()

    # =========================================================
    # Contraseña
    # =========================================================
    def actualizar_password_hash(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
        clave_hash: str,
        clave_salt: str,
        clave_algoritmo: str,
        clave_iteraciones: int,
        debe_cambiar_clave: bool = False,
    ) -> None:
        """
        Actualiza los datos de contraseña del usuario.
        """
        sql = """
        UPDATE dbo.Usuarios
        SET
            Clave_Hash = ?,
            Clave_Salt = ?,
            Clave_Algoritmo = ?,
            Clave_Iteraciones = ?,
            Debe_Cambiar_Clave = ?,
            Ultimo_Cambio_Clave = SYSDATETIME()
        WHERE Usuario_Seguridad_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(
            sql,
            (
                clave_hash,
                clave_salt,
                clave_algoritmo,
                int(clave_iteraciones),
                1 if debe_cambiar_clave else 0,
                int(usuario_seguridad_id),
            ),
        )
        conn.commit()

    # =========================================================
    # Consultas auxiliares
    # =========================================================
    def get_usuario_por_id(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> dict | None:
        """
        Busca un usuario por Usuario_Seguridad_Id usando la vista de seguridad.
        """
        sql = """
        SELECT TOP 1
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Id_Usuario,
            Usuario,
            Nombre_Usuario,
            Correo,
            Clave_Hash,
            Clave_Salt,
            Clave_Algoritmo,
            Clave_Iteraciones,
            Debe_Cambiar_Clave,
            Intentos_Fallidos,
            Bloqueado_Hasta,
            Ultimo_Acceso,
            Ultimo_Cambio_Clave,
            Fecha_Creacion,
            Fecha_Modificacion,
            Tipo_Usuario,
            Descripcion_Tipo,
            Estado_Usuario,
            Descripcion_Estado,
            Rol_Id,
            Codigo_Rol,
            Nombre_Rol
        FROM dbo.vw_Usuarios_Seguridad
        WHERE Usuario_Seguridad_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        row = cur.fetchone()
        return self._row_to_user_dict(row)

    def get_codigo_usuario(
        self,
        conn: pyodbc.Connection,
        usuario: str,
    ) -> int | None:
        """
        Retorna Codigo_Usuario a partir del nombre de usuario.
        Se mantiene por compatibilidad con auditoría y lógica legacy.
        """
        sql = """
        SELECT TOP 1 Codigo_Usuario
        FROM dbo.Usuarios
        WHERE Usuario = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (usuario,))
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else None