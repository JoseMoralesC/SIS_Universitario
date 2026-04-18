from __future__ import annotations

import socket
from typing import Any

import pyodbc


class BitacoraAccesoRepository:
    """
    Repositorio para dbo.Bitacora_Acceso.

    Responsabilidades:
    - Registrar login exitoso
    - Registrar login fallido
    - Consultar sesiones abiertas
    - Cerrar sesiones
    - Consultar registros de bitácora por id
    """

    # =========================================================
    # Helpers internos
    # =========================================================
    @staticmethod
    def _safe_str(value: object | None, max_len: int | None = None) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        if max_len is not None:
            return text[:max_len]

        return text

    @staticmethod
    def _safe_int(value: object | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_equipo_default() -> str:
        """
        Obtiene un nombre de equipo razonable para registrar en bitácora.
        """
        try:
            return socket.gethostname() or "DESCONOCIDO"
        except Exception:
            return "DESCONOCIDO"

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any] | None:
        if not row:
            return None

        return {
            "bitacora_acceso_id": int(row[0]) if row[0] is not None else None,
            "usuario_seguridad_id": int(row[1]) if row[1] is not None else None,
            "codigo_usuario": int(row[2]) if row[2] is not None else None,
            "usuario_login": str(row[3]) if row[3] is not None else "",
            "nombre_usuario": str(row[4]) if row[4] is not None else None,
            "fecha_login": row[5],
            "fecha_logout": row[6],
            "resultado_login": str(row[7]) if row[7] is not None else None,
            "estado_sesion": str(row[8]) if row[8] is not None else None,
            "intento_fallido": bool(row[9]) if row[9] is not None else False,
            "origen_aplicacion": str(row[10]) if row[10] is not None else None,
            "modulo_origen": str(row[11]) if row[11] is not None else None,
            "equipo": str(row[12]) if row[12] is not None else None,
            "ip_cliente": str(row[13]) if row[13] is not None else None,
            "motivo_fallo": str(row[14]) if row[14] is not None else None,
            "observacion": str(row[15]) if row[15] is not None else None,
        }

    # =========================================================
    # Lectura
    # =========================================================
    def get_by_id(
        self,
        conn: pyodbc.Connection,
        bitacora_acceso_id: int,
    ) -> dict[str, Any] | None:
        sql = """
        SELECT TOP 1
            Bitacora_Acceso_Id,
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Usuario_Login,
            Nombre_Usuario,
            Fecha_Login,
            Fecha_Logout,
            Resultado_Login,
            Estado_Sesion,
            Intento_Fallido,
            Origen_Aplicacion,
            Modulo_Origen,
            Equipo,
            IP_Cliente,
            Motivo_Fallo,
            Observacion
        FROM dbo.Bitacora_Acceso
        WHERE Bitacora_Acceso_Id = ?;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(bitacora_acceso_id),))
        row = cur.fetchone()
        return self._row_to_dict(row)

    def get_sesion_abierta_por_usuario(
        self,
        conn: pyodbc.Connection,
        usuario_seguridad_id: int,
    ) -> dict[str, Any] | None:
        """
        Retorna la sesión ABIERTA más reciente para el usuario.
        """
        sql = """
        SELECT TOP 1
            Bitacora_Acceso_Id,
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Usuario_Login,
            Nombre_Usuario,
            Fecha_Login,
            Fecha_Logout,
            Resultado_Login,
            Estado_Sesion,
            Intento_Fallido,
            Origen_Aplicacion,
            Modulo_Origen,
            Equipo,
            IP_Cliente,
            Motivo_Fallo,
            Observacion
        FROM dbo.Bitacora_Acceso
        WHERE Usuario_Seguridad_Id = ?
          AND Estado_Sesion = 'ABIERTA'
          AND Resultado_Login = 'EXITOSO'
        ORDER BY Bitacora_Acceso_Id DESC;
        """
        cur = conn.cursor()
        cur.execute(sql, (int(usuario_seguridad_id),))
        row = cur.fetchone()
        return self._row_to_dict(row)

    # =========================================================
    # Escritura: login exitoso
    # =========================================================
    def registrar_login_exitoso(
        self,
        conn: pyodbc.Connection,
        *,
        usuario_seguridad_id: int,
        codigo_usuario: int | None,
        usuario_login: str,
        nombre_usuario: str | None = None,
        origen_aplicacion: str = "SIS_Universitario",
        modulo_origen: str | None = "LOGIN",
        equipo: str | None = None,
        ip_cliente: str | None = None,
        observacion: str | None = None,
    ) -> int:
        """
        Inserta un login exitoso y retorna el id generado.
        """
        sql = """
        INSERT INTO dbo.Bitacora_Acceso
        (
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Usuario_Login,
            Nombre_Usuario,
            Fecha_Login,
            Fecha_Logout,
            Resultado_Login,
            Estado_Sesion,
            Intento_Fallido,
            Origen_Aplicacion,
            Modulo_Origen,
            Equipo,
            IP_Cliente,
            Motivo_Fallo,
            Observacion
        )
        OUTPUT INSERTED.Bitacora_Acceso_Id
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            SYSDATETIME(),
            NULL,
            'EXITOSO',
            'ABIERTA',
            0,
            ?,
            ?,
            ?,
            ?,
            NULL,
            ?
        );
        """

        cur = conn.cursor()
        cur.execute(
            sql,
            (
                int(usuario_seguridad_id),
                self._safe_int(codigo_usuario),
                self._safe_str(usuario_login, 50),
                self._safe_str(nombre_usuario, 120),
                self._safe_str(origen_aplicacion, 100) or "SIS_Universitario",
                self._safe_str(modulo_origen, 100),
                self._safe_str(equipo, 100) or self._get_equipo_default(),
                self._safe_str(ip_cliente, 50),
                self._safe_str(observacion, 250),
            ),
        )
        row = cur.fetchone()
        conn.commit()

        if not row or row[0] is None:
            raise RuntimeError("No fue posible obtener el id de la bitácora de acceso.")

        return int(row[0])

    # =========================================================
    # Escritura: login fallido
    # =========================================================
    def registrar_login_fallido(
        self,
        conn: pyodbc.Connection,
        *,
        usuario_login: str,
        motivo_fallo: str,
        usuario_seguridad_id: int | None = None,
        codigo_usuario: int | None = None,
        nombre_usuario: str | None = None,
        origen_aplicacion: str = "SIS_Universitario",
        modulo_origen: str | None = "LOGIN",
        equipo: str | None = None,
        ip_cliente: str | None = None,
        observacion: str | None = None,
    ) -> int:
        """
        Inserta un login fallido y retorna el id generado.

        Se permite registrar:
        - solo el usuario digitado
        - o bien también enlazar al usuario real si ya fue identificado
        """
        sql = """
        INSERT INTO dbo.Bitacora_Acceso
        (
            Usuario_Seguridad_Id,
            Codigo_Usuario,
            Usuario_Login,
            Nombre_Usuario,
            Fecha_Login,
            Fecha_Logout,
            Resultado_Login,
            Estado_Sesion,
            Intento_Fallido,
            Origen_Aplicacion,
            Modulo_Origen,
            Equipo,
            IP_Cliente,
            Motivo_Fallo,
            Observacion
        )
        OUTPUT INSERTED.Bitacora_Acceso_Id
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            SYSDATETIME(),
            NULL,
            'FALLIDO',
            'FALLIDA',
            1,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        );
        """

        cur = conn.cursor()
        cur.execute(
            sql,
            (
                self._safe_int(usuario_seguridad_id),
                self._safe_int(codigo_usuario),
                self._safe_str(usuario_login, 50),
                self._safe_str(nombre_usuario, 120),
                self._safe_str(origen_aplicacion, 100) or "SIS_Universitario",
                self._safe_str(modulo_origen, 100),
                self._safe_str(equipo, 100) or self._get_equipo_default(),
                self._safe_str(ip_cliente, 50),
                self._safe_str(motivo_fallo, 250) or "Credenciales inválidas.",
                self._safe_str(observacion, 250),
            ),
        )
        row = cur.fetchone()
        conn.commit()

        if not row or row[0] is None:
            raise RuntimeError("No fue posible obtener el id de la bitácora de acceso.")

        return int(row[0])

    # =========================================================
    # Escritura: cierre de sesión
    # =========================================================
    def cerrar_sesion_por_bitacora_id(
        self,
        conn: pyodbc.Connection,
        *,
        bitacora_acceso_id: int,
        observacion: str | None = None,
    ) -> bool:
        """
        Cierra una sesión específica que esté ABIERTA.
        """
        sql = """
        UPDATE dbo.Bitacora_Acceso
        SET
            Fecha_Logout = SYSDATETIME(),
            Estado_Sesion = 'CERRADA',
            Observacion = CASE
                WHEN ? IS NULL OR LTRIM(RTRIM(?)) = '' THEN Observacion
                ELSE ?
            END
        WHERE Bitacora_Acceso_Id = ?
          AND Estado_Sesion = 'ABIERTA';
        """

        cur = conn.cursor()
        observacion_limpia = self._safe_str(observacion, 250)

        cur.execute(
            sql,
            (
                observacion_limpia,
                observacion_limpia,
                observacion_limpia,
                int(bitacora_acceso_id),
            ),
        )
        affected = cur.rowcount
        conn.commit()
        return affected > 0

    def cerrar_sesion_abierta_por_usuario(
        self,
        conn: pyodbc.Connection,
        *,
        usuario_seguridad_id: int,
        observacion: str | None = None,
    ) -> bool:
        """
        Busca la sesión ABIERTA más reciente del usuario y la cierra.
        """
        sesion = self.get_sesion_abierta_por_usuario(conn, int(usuario_seguridad_id))
        if not sesion:
            return False

        bitacora_acceso_id = sesion.get("bitacora_acceso_id")
        if not bitacora_acceso_id:
            return False

        return self.cerrar_sesion_por_bitacora_id(
            conn,
            bitacora_acceso_id=int(bitacora_acceso_id),
            observacion=observacion,
        )


# =========================================================
# Instancia reutilizable
# =========================================================
bitacora_acceso_repo = BitacoraAccesoRepository()