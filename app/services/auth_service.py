from __future__ import annotations

from datetime import datetime

from app.core import db as db_module
from app.core.exceptions import ValidationError
from app.repositories.security.usuario_security_repo import UsuarioSecurityRepository
from app.repositories.security.bitacora_acceso_repo import bitacora_acceso_repo
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

    Flujo actual:
    1) Conecta con la cuenta técnica de la aplicación.
    2) Busca el usuario en el esquema de seguridad.
    3) Valida estado, bloqueo y contraseña hash.
    4) Carga rol principal y permisos.
    5) Actualiza intentos fallidos / último acceso.
    6) Registra login exitoso o fallido en dbo.Bitacora_Acceso.
    """

    MAX_INTENTOS_FALLIDOS = 5
    MINUTOS_BLOQUEO = 15

    def __init__(self) -> None:
        self.repo = UsuarioSecurityRepository()
        self.password_service = PasswordService()
        self.bitacora_repo = bitacora_acceso_repo

    # =========================================================
    # Helpers internos
    # =========================================================
    def _connect_app(self):
        """
        Obtiene la conexión técnica de la aplicación.

        Este método depende de app.core.db.connect_app().
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

    @staticmethod
    def _safe_user_text(value: object | None) -> str:
        if value is None:
            return ""
        return str(value).strip()

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
        bitacora_acceso_id: int | None = None,
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
            "bitacora_acceso_id": bitacora_acceso_id,
        }

    def _registrar_login_fallido_si_posible(
        self,
        conn,
        *,
        usuario_login: str,
        motivo_fallo: str,
        user_data: dict | None = None,
    ) -> None:
        """
        Registra intento fallido en la bitácora.
        Nunca debe romper el flujo principal del login.
        """
        try:
            self.bitacora_repo.registrar_login_fallido(
                conn,
                usuario_login=self._safe_user_text(usuario_login),
                motivo_fallo=self._safe_user_text(motivo_fallo) or "Credenciales inválidas.",
                usuario_seguridad_id=(user_data or {}).get("usuario_seguridad_id"),
                codigo_usuario=(user_data or {}).get("codigo_usuario"),
                nombre_usuario=(user_data or {}).get("nombre_usuario"),
                origen_aplicacion="SIS_Universitario",
                modulo_origen="LOGIN",
                observacion="Registro automático desde AuthService.",
            )
        except Exception:
            pass

    def _cerrar_sesion_previa_si_existe(
        self,
        conn,
        *,
        usuario_seguridad_id: int,
    ) -> None:
        """
        Cierra una sesión abierta previa si existe.
        Esto evita dejar múltiples sesiones abiertas en bitácora
        para un mismo usuario en el flujo de escritorio.
        """
        try:
            self.bitacora_repo.cerrar_sesion_abierta_por_usuario(
                conn,
                usuario_seguridad_id=int(usuario_seguridad_id),
                observacion="Cierre automático por nuevo inicio de sesión.",
            )
        except Exception:
            pass

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
                self._registrar_login_fallido_si_posible(
                    conn,
                    usuario_login=usuario,
                    motivo_fallo="Usuario no encontrado o credenciales inválidas.",
                    user_data=None,
                )
                raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

            if not self._es_estado_activo(user_data):
                self._registrar_login_fallido_si_posible(
                    conn,
                    usuario_login=usuario,
                    motivo_fallo="Usuario inactivo.",
                    user_data=user_data,
                )
                raise UsuarioInactivoError("El usuario se encuentra inactivo.")

            if self._esta_bloqueado(user_data):
                self._registrar_login_fallido_si_posible(
                    conn,
                    usuario_login=usuario,
                    motivo_fallo="Usuario bloqueado temporalmente.",
                    user_data=user_data,
                )
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

                    self._registrar_login_fallido_si_posible(
                        conn,
                        usuario_login=usuario,
                        motivo_fallo=(
                            "Máximo de intentos fallidos alcanzado. "
                            "Usuario bloqueado temporalmente."
                        ),
                        user_data=user_data,
                    )
                    raise UsuarioBloqueadoError(
                        "Se alcanzó el máximo de intentos fallidos. "
                        "El usuario ha sido bloqueado temporalmente."
                    )

                self._registrar_login_fallido_si_posible(
                    conn,
                    usuario_login=usuario,
                    motivo_fallo="Contraseña incorrecta.",
                    user_data=user_data,
                )
                raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

            rol_principal = self.repo.get_rol_principal_usuario(
                conn,
                int(user_data["usuario_seguridad_id"]),
            )
            if not rol_principal:
                self._registrar_login_fallido_si_posible(
                    conn,
                    usuario_login=usuario,
                    motivo_fallo="Usuario sin rol asignado para ingresar.",
                    user_data=user_data,
                )
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

            self._cerrar_sesion_previa_si_existe(
                conn,
                usuario_seguridad_id=int(user_data["usuario_seguridad_id"]),
            )

            bitacora_acceso_id = self.bitacora_repo.registrar_login_exitoso(
                conn,
                usuario_seguridad_id=int(user_data["usuario_seguridad_id"]),
                codigo_usuario=user_data.get("codigo_usuario"),
                usuario_login=user_data.get("usuario") or usuario,
                nombre_usuario=user_data.get("nombre_usuario"),
                origen_aplicacion="SIS_Universitario",
                modulo_origen="LOGIN",
                observacion="Login exitoso registrado desde AuthService.",
            )

            session_data = self._build_session_payload(
                user_data=user_data,
                rol_principal=rol_principal,
                permisos=permisos,
                bitacora_acceso_id=bitacora_acceso_id,
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