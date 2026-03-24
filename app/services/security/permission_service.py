from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.core.exceptions import ValidationError
from app.core.session import (
    get_permisos,
    has_permission,
    is_admin,
)


class PermissionDeniedError(ValidationError):
    """
    Error funcional cuando el usuario autenticado no posee autorización
    para acceder a un módulo o ejecutar una acción.
    """
    pass


@dataclass(frozen=True)
class PermissionCheckResult:
    allowed: bool
    matched_code: str | None
    candidates: tuple[str, ...]


class PermissionService:
    """
    Servicio centralizado para validación de permisos del sistema.

    Objetivos:
    - Unificar las reglas de autorización para UI y endpoints.
    - Soportar ADMIN como bypass global.
    - Tolerar variaciones razonables en nombres de permisos
      (singular/plural, prefijos de módulo, alias históricos).
    - Exponer helpers listos para módulos y tabs de mantenimientos.
    """

    MODULE_ALIASES: dict[str, tuple[str, ...]] = {
        "mantenimientos": ("MANTENIMIENTOS", "MANTENIMIENTO"),
        "matriculas": ("MATRICULAS", "MATRICULA"),
        "matricula_materias": (
            "MATRICULA_MATERIAS",
            "MATRICULAS_MATERIAS",
            "MATRICULA_POR_MATERIAS",
            "MATRICULA_MATERIA",
        ),
        "asistencias": ("ASISTENCIAS", "ASISTENCIA"),
    }

    MAINTENANCE_RESOURCE_ALIASES: dict[str, tuple[str, ...]] = {
        "programas": ("PROGRAMAS", "PROGRAMA", "CURSOS_PROGRAMAS", "CURSO_PROGRAMA"),
        "cursos": ("CURSOS", "CURSO"),
        "docentes": ("DOCENTES", "DOCENTE"),
        "estudiantes": ("ESTUDIANTES", "ESTUDIANTE"),
        "becas": ("BECAS", "BECA"),
        "becados": ("BECADOS", "BECADO"),
        "periodos": ("PERIODOS", "PERIODO"),
        "asignacion": (
            "ASIGNACION",
            "ASIGNACIONES",
            "ASIGNACION_DOCENTES",
            "ASIGNACIONES_DOCENTES",
            "CURSO_DOCENTE",
        ),
    }

    ACTION_ALIASES: dict[str, tuple[str, ...]] = {
        "access": ("ACCESO", "VER", "CONSULTAR", "LISTAR"),
        "create": ("CREAR", "NUEVO", "GUARDAR", "REGISTRAR", "INSERTAR"),
        "update": ("ACTUALIZAR", "EDITAR", "MODIFICAR"),
        "delete": ("ELIMINAR", "BORRAR"),
    }

    @staticmethod
    def _normalize_token(value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().upper().replace(" ", "_").replace("-", "_")

    def _normalize_key(self, key: str) -> str:
        normalized = self._normalize_token(key)
        if not normalized:
            return ""
        return normalized.lower()

    def _permission_set(self) -> set[str]:
        return {self._normalize_token(code) for code in get_permisos() if self._normalize_token(code)}

    def _module_aliases(self, module_key: str) -> tuple[str, ...]:
        key = self._normalize_key(module_key)
        aliases = self.MODULE_ALIASES.get(key, ())
        if aliases:
            return aliases

        token = self._normalize_token(module_key)
        return (token,) if token else ()

    def _resource_aliases(self, resource_key: str) -> tuple[str, ...]:
        key = self._normalize_key(resource_key)
        aliases = self.MAINTENANCE_RESOURCE_ALIASES.get(key, ())
        if aliases:
            return aliases

        token = self._normalize_token(resource_key)
        return (token,) if token else ()

    def _action_aliases(self, action_key: str) -> tuple[str, ...]:
        key = self._normalize_key(action_key)
        aliases = self.ACTION_ALIASES.get(key, ())
        if aliases:
            return aliases

        token = self._normalize_token(action_key)
        return (token,) if token else ()

    @staticmethod
    def _unique_ordered(values: Iterable[str]) -> tuple[str, ...]:
        seen: set[str] = set()
        result: list[str] = []

        for value in values:
            current = str(value or "").strip().upper()
            if not current or current in seen:
                continue
            seen.add(current)
            result.append(current)

        return tuple(result)

    def _build_module_candidates(self, module_key: str) -> tuple[str, ...]:
        module_aliases = self._module_aliases(module_key)
        candidates: list[str] = []

        for module in module_aliases:
            candidates.extend(
                [
                    f"{module}.ACCESO",
                    f"{module}.VER",
                    f"{module}.CONSULTAR",
                    f"{module}.LISTAR",
                ]
            )

        return self._unique_ordered(candidates)

    def _build_maintenance_candidates(self, resource_key: str, action_key: str) -> tuple[str, ...]:
        action_key = self._normalize_key(action_key)
        if not action_key:
            return ()

        module_aliases = self._module_aliases("mantenimientos")
        resource_aliases = self._resource_aliases(resource_key)
        action_aliases = self._action_aliases(action_key)

        candidates: list[str] = []

        if action_key == "access":
            for module in module_aliases:
                candidates.append(f"{module}.ACCESO")

        for resource in resource_aliases:
            for action in action_aliases:
                candidates.append(f"{resource}.{action}")
                for module in module_aliases:
                    candidates.append(f"{module}.{resource}.{action}")

        # Fallbacks globales de mantenimiento para escenarios donde exista
        # permiso transversal del módulo completo por operación.
        if action_key != "access":
            for module in module_aliases:
                for action in action_aliases:
                    candidates.append(f"{module}.{action}")

        return self._unique_ordered(candidates)

    def _check_candidates(self, candidates: Iterable[str], *, admin_bypass: bool = True) -> PermissionCheckResult:
        normalized_candidates = self._unique_ordered(candidates)

        if admin_bypass and is_admin():
            return PermissionCheckResult(True, "ADMIN", normalized_candidates)

        permisos = self._permission_set()
        for code in normalized_candidates:
            if code in permisos or has_permission(code):
                return PermissionCheckResult(True, code, normalized_candidates)

        return PermissionCheckResult(False, None, normalized_candidates)

    # =========================================================
    # API genérica
    # =========================================================
    def has_permission_code(self, codigo_permiso: str, *, admin_bypass: bool = True) -> bool:
        result = self._check_candidates((self._normalize_token(codigo_permiso),), admin_bypass=admin_bypass)
        return result.allowed

    def check_module_access(self, module_key: str, *, admin_bypass: bool = True) -> PermissionCheckResult:
        candidates = self._build_module_candidates(module_key)
        return self._check_candidates(candidates, admin_bypass=admin_bypass)

    def can_access_module(self, module_key: str, *, admin_bypass: bool = True) -> bool:
        return self.check_module_access(module_key, admin_bypass=admin_bypass).allowed

    def check_maintenance_permission(
        self,
        resource_key: str,
        action_key: str,
        *,
        admin_bypass: bool = True,
    ) -> PermissionCheckResult:
        candidates = self._build_maintenance_candidates(resource_key, action_key)
        return self._check_candidates(candidates, admin_bypass=admin_bypass)

    def can_access_maintenance(self, resource_key: str, *, admin_bypass: bool = True) -> bool:
        return self.check_maintenance_permission(resource_key, "access", admin_bypass=admin_bypass).allowed

    def can_create_maintenance(self, resource_key: str, *, admin_bypass: bool = True) -> bool:
        return self.check_maintenance_permission(resource_key, "create", admin_bypass=admin_bypass).allowed

    def can_update_maintenance(self, resource_key: str, *, admin_bypass: bool = True) -> bool:
        return self.check_maintenance_permission(resource_key, "update", admin_bypass=admin_bypass).allowed

    def can_delete_maintenance(self, resource_key: str, *, admin_bypass: bool = True) -> bool:
        return self.check_maintenance_permission(resource_key, "delete", admin_bypass=admin_bypass).allowed

    def get_maintenance_permissions_state(self, resource_key: str, *, admin_bypass: bool = True) -> dict:
        access_result = self.check_maintenance_permission(resource_key, "access", admin_bypass=admin_bypass)
        create_result = self.check_maintenance_permission(resource_key, "create", admin_bypass=admin_bypass)
        update_result = self.check_maintenance_permission(resource_key, "update", admin_bypass=admin_bypass)
        delete_result = self.check_maintenance_permission(resource_key, "delete", admin_bypass=admin_bypass)

        return {
            "resource": self._normalize_key(resource_key),
            "is_admin": is_admin(),
            "access": access_result.allowed,
            "create": create_result.allowed,
            "update": update_result.allowed,
            "delete": delete_result.allowed,
            "matched": {
                "access": access_result.matched_code,
                "create": create_result.matched_code,
                "update": update_result.matched_code,
                "delete": delete_result.matched_code,
            },
            "candidates": {
                "access": list(access_result.candidates),
                "create": list(create_result.candidates),
                "update": list(update_result.candidates),
                "delete": list(delete_result.candidates),
            },
        }

    # =========================================================
    # Reglas require_* para endpoints / UI
    # =========================================================
    def require_permission_code(
        self,
        codigo_permiso: str,
        *,
        message: str | None = None,
        admin_bypass: bool = True,
    ) -> None:
        result = self._check_candidates((self._normalize_token(codigo_permiso),), admin_bypass=admin_bypass)
        if result.allowed:
            return

        raise PermissionDeniedError(
            message or f"No tienes permiso para ejecutar esta acción ({self._normalize_token(codigo_permiso)})."
        )

    def require_module_access(
        self,
        module_key: str,
        *,
        message: str | None = None,
        admin_bypass: bool = True,
    ) -> None:
        result = self.check_module_access(module_key, admin_bypass=admin_bypass)
        if result.allowed:
            return

        module_name = self._normalize_token(module_key) or "MODULO"
        raise PermissionDeniedError(
            message or f"No tienes permiso para acceder al módulo {module_name}."
        )

    def require_maintenance_access(
        self,
        resource_key: str,
        *,
        message: str | None = None,
        admin_bypass: bool = True,
    ) -> None:
        result = self.check_maintenance_permission(resource_key, "access", admin_bypass=admin_bypass)
        if result.allowed:
            return

        resource_name = self._normalize_token(resource_key) or "RECURSO"
        raise PermissionDeniedError(
            message or f"No tienes permiso para acceder a {resource_name}."
        )

    def require_maintenance_action(
        self,
        resource_key: str,
        action_key: str,
        *,
        message: str | None = None,
        admin_bypass: bool = True,
    ) -> None:
        result = self.check_maintenance_permission(resource_key, action_key, admin_bypass=admin_bypass)
        if result.allowed:
            return

        resource_name = self._normalize_token(resource_key) or "RECURSO"
        action_name = self._normalize_token(action_key) or "ACCION"

        action_labels = {
            "ACCESS": "acceder",
            "CREATE": "crear",
            "UPDATE": "actualizar",
            "DELETE": "eliminar",
        }
        action_label = action_labels.get(action_name, action_name.lower())

        raise PermissionDeniedError(
            message or f"No tienes permiso para {action_label} en {resource_name}."
        )


permission_service = PermissionService()


# =========================================================
# Funciones helper para imports directos
# =========================================================

def can_access_module(module_key: str, *, admin_bypass: bool = True) -> bool:
    return permission_service.can_access_module(module_key, admin_bypass=admin_bypass)


def can_access_maintenance(resource_key: str, *, admin_bypass: bool = True) -> bool:
    return permission_service.can_access_maintenance(resource_key, admin_bypass=admin_bypass)


def can_create_maintenance(resource_key: str, *, admin_bypass: bool = True) -> bool:
    return permission_service.can_create_maintenance(resource_key, admin_bypass=admin_bypass)


def can_update_maintenance(resource_key: str, *, admin_bypass: bool = True) -> bool:
    return permission_service.can_update_maintenance(resource_key, admin_bypass=admin_bypass)


def can_delete_maintenance(resource_key: str, *, admin_bypass: bool = True) -> bool:
    return permission_service.can_delete_maintenance(resource_key, admin_bypass=admin_bypass)


def get_maintenance_permissions_state(resource_key: str, *, admin_bypass: bool = True) -> dict:
    return permission_service.get_maintenance_permissions_state(resource_key, admin_bypass=admin_bypass)


def require_module_access(module_key: str, *, message: str | None = None, admin_bypass: bool = True) -> None:
    permission_service.require_module_access(module_key, message=message, admin_bypass=admin_bypass)


def require_maintenance_access(resource_key: str, *, message: str | None = None, admin_bypass: bool = True) -> None:
    permission_service.require_maintenance_access(resource_key, message=message, admin_bypass=admin_bypass)


def require_maintenance_action(
    resource_key: str,
    action_key: str,
    *,
    message: str | None = None,
    admin_bypass: bool = True,
) -> None:
    permission_service.require_maintenance_action(
        resource_key,
        action_key,
        message=message,
        admin_bypass=admin_bypass,
    )