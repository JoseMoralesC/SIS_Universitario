from __future__ import annotations

from datetime import datetime

from app.core import db as db_module
from app.core.exceptions import ValidationError
from app.repositories.security.usuario_security_repo import UsuarioSecurityRepository
from app.services.security.password_service import PasswordService


class UsuarioNoRegistradoError(ValidationError):
    """
    Se mantiene por compatibilidad con el flujo anterior.
    """
    pass


class CredencialesInvalidasError(ValidationError):
    pass


class UsuarioInactivoError(ValidationError):
    pass


class UsuarioBloqueadoError(ValidationError):
    pass


class RolNoAsignadoError(ValidationError):
    pass


class AuthService:
    """
    Servicio de autenticación del sistema.

    Nuevo flujo:
    1) Conecta con la cuenta técnica de la aplicación.
    2) Busca el usuario en el esquema de seguridad.
    3) Valida estado, bloqueo y contraseña hash.
    4) Carga rol principal y permisos.
    5) Actualiza intentos fallidos / último acceso.
    """

    MAX_INTENTOS_FALLIDOS = 5
    MINUTOS_BLOQUEO = 15

    def __init__(self) -> None:
        self.repo = UsuarioSecurityRepository()
        self.password_service = PasswordService()

    # =========================================================
    # Helpers internos
    # =========================================================
    def _connect_app(self):
        """
        Obtiene la conexión técnica de la aplicación.

        Este método queda preparado para el siguiente archivo,
        donde app.core.db expondrá connect_app().
        """
        connect_app = getattr(db_module, "connect_app", None)
        if connect_app is None:
            raise ValidationError(
                "La conexión técnica del sistema aún no está disponible. "
                "Falta actualizar app/core/db.py con connect_app()."
            )
        return connect_app()

    @staticmethod
    def _es_estado_activo(user_data: dict) -> bool:
        """
        Determina si el usuario se considera activo.

        Regla:
        - si el catálogo legacy tiene descripción, se evalúa por texto
        - si no, se usa fallback por código: 1 = activo
        """
        descripcion = (user_data.get("descripcion_estado") or "").strip().upper()
        estado_usuario = user_data.get("estado_usuario")

        if descripcion:
            if "ACTIV" in descripcion:
                return True
            if any(tag in descripcion for tag in ("INACT", "BLOQ", "SUSP", "ANUL")):
                return False

        return estado_usuario == 1

    @staticmethod
    def _esta_bloqueado(user_data: dict) -> bool:
        bloqueado_hasta = user_data.get("bloqueado_hasta")
        if bloqueado_hasta is None:
            return False
        return bloqueado_hasta > datetime.now()

    def _filtrar_permisos_por_rol(self, codigo_rol: str, permisos: list[str]) -> list[str]:
        """
        Aplica reglas de negocio para restringir permisos según el rol.
        Esto evita que errores en BD otorguen accesos indebidos.
        """
        rol = (codigo_rol or "").strip().upper()

        # ADMIN -> acceso total (no se filtra)
        if rol == "ADMIN":
            return permisos

        # DOCENTE -> solo asistencias
        if rol == "DOCENTE":
            return [
                p for p in permisos
                if (p or "").strip().upper().startswith("ASISTENCIA")
                or (p or "").strip().upper().startswith("ASISTENCIAS")
            ]

        # AUDITOR -> solo consulta / reportes
        if rol == "AUDITOR":
            return [
                p for p in permisos
                if any(x in (p or "").strip().upper() for x in ("VER", "CONSULTAR", "LISTAR", "REPORT"))
            ]

        # OPERADOR -> sin filtro (controlado por permisos BD)
        if rol == "OPERADOR":
            return permisos

        # default -> no tocar
        return permisos

    def _build_session_payload(
        self,
        user_data: dict,
        rol_principal: dict | None,
        permisos: list[str],
    ) -> dict:
        codigo_rol = rol_principal.get("codigo_rol") if rol_principal else None
        permisos_filtrados = self._filtrar_permisos_por_rol(codigo_rol, permisos)

        return {
            "usuario_seguridad_id": user_data.get("usuario_seguridad_id"),
            "codigo_usuario": user_data.get("codigo_usuario"),
            "id_usuario": user_data.get("id_usuario"),
            "usuario": user_data.get("usuario"),
            "nombre_usuario": user_data.get("nombre_usuario"),
            "correo": user_data.get("correo"),
            "tipo_usuario": user_data.get("tipo_usuario"),
            "descripcion_tipo": user_data.get("descripcion_tipo"),
            "estado_usuario": user_data.get("estado_usuario"),
            "descripcion_estado": user_data.get("descripcion_estado"),
            "rol_id": rol_principal.get("rol_id") if rol_principal else None,
            "codigo_rol": codigo_rol,
            "nombre_rol": rol_principal.get("nombre_rol") if rol_principal else None,
            "roles": [],
            "permisos": permisos_filtrados,
            "debe_cambiar_clave": user_data.get("debe_cambiar_clave", False),
            "ultimo_acceso": user_data.get("ultimo_acceso"),
        }

    # =========================================================
    # API principal
    # =========================================================
    def login(self, usuario: str, contra: str) -> dict:
        """
        Autentica al usuario contra dbo.Usuarios / vw_Usuarios_Seguridad.

        Retorna un dict con toda la información de sesión necesaria
        para la UI y el control de permisos.
        """
        usuario = (usuario or "").strip()
        contra = contra or ""

        if not usuario:
            raise ValidationError("Debe ingresar el nombre de usuario.")

        if not contra:
            raise ValidationError("Debe ingresar la contraseña.")

        conn = self._connect_app()
        try:
            user_data = self.repo.get_usuario_para_login(conn, usuario)

            if not user_data:
                raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

            if not self._es_estado_activo(user_data):
                raise UsuarioInactivoError("El usuario se encuentra inactivo.")

            if self._esta_bloqueado(user_data):
                raise UsuarioBloqueadoError(
                    "El usuario se encuentra bloqueado temporalmente. "
                    "Intente nuevamente más tarde."
                )

            password_ok = self.password_service.verify_password(
                plain_password=contra,
                stored_hash=user_data.get("clave_hash"),
                stored_salt=user_data.get("clave_salt"),
                stored_algorithm=user_data.get("clave_algoritmo"),
                stored_iterations=user_data.get("clave_iteraciones"),
            )

            if not password_ok:
                self.repo.incrementar_intentos_fallidos(
                    conn,
                    int(user_data["usuario_seguridad_id"]),
                )

                intentos_actuales = int(user_data.get("intentos_fallidos") or 0) + 1
                if intentos_actuales >= self.MAX_INTENTOS_FALLIDOS:
                    self.repo.bloquear_hasta(
                        conn,
                        int(user_data["usuario_seguridad_id"]),
                        self.MINUTOS_BLOQUEO,
                    )
                    raise UsuarioBloqueadoError(
                        "Se alcanzó el máximo de intentos fallidos. "
                        "El usuario ha sido bloqueado temporalmente."
                    )

                raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

            rol_principal = self.repo.get_rol_principal_usuario(
                conn,
                int(user_data["usuario_seguridad_id"]),
            )
            if not rol_principal:
                raise RolNoAsignadoError(
                    "El usuario no tiene un rol asignado para ingresar al sistema."
                )

            permisos = self.repo.get_permisos_usuario(
                conn,
                int(user_data["usuario_seguridad_id"]),
            )

            roles = self.repo.get_roles_usuario(
                conn,
                int(user_data["usuario_seguridad_id"]),
            )

            self.repo.resetear_intentos_fallidos(
                conn,
                int(user_data["usuario_seguridad_id"]),
            )
            self.repo.limpiar_bloqueo(
                conn,
                int(user_data["usuario_seguridad_id"]),
            )
            self.repo.actualizar_ultimo_acceso(
                conn,
                int(user_data["usuario_seguridad_id"]),
            )

            session_data = self._build_session_payload(
                user_data=user_data,
                rol_principal=rol_principal,
                permisos=permisos,
            )
            session_data["roles"] = roles

            return session_data

        finally:
            try:
                conn.close()
            except Exception:
                pass


# =========================================================
# Instancia reutilizable
# =========================================================
auth_service = AuthService()


# =========================================================
# Funciones públicas por compatibilidad
# =========================================================
def login_sistema(usuario: str, contra: str) -> dict:
    """
    Nuevo login del sistema.
    """
    return auth_service.login(usuario, contra)


def login_sql_y_validar_tabla(usuario: str, contra: str) -> dict:
    """
    Función legacy mantenida para no romper imports existentes.

    Antes:
    - validaba credenciales SQL Server
    - luego revisaba existencia en dbo.Usuarios

    Ahora:
    - autentica contra el sistema de usuarios propio
    - retorna datos de sesión
    """
    return auth_service.login(usuario, contra)