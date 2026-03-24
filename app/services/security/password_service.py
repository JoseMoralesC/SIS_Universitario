from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


class PasswordService:
    """
    Servicio de manejo de contraseñas.

    Implementa hashing con PBKDF2-HMAC-SHA256 usando:
    - salt aleatoria
    - cantidad configurable de iteraciones
    - comparación segura en tiempo constante
    """

    DEFAULT_ALGORITHM = "pbkdf2_sha256"
    DEFAULT_ITERATIONS = 390_000
    DEFAULT_SALT_BYTES = 16

    # =========================================================
    # Helpers internos
    # =========================================================
    @staticmethod
    def _to_bytes(text: str) -> bytes:
        return text.encode("utf-8")

    @staticmethod
    def _b64encode(raw: bytes) -> str:
        return base64.b64encode(raw).decode("utf-8")

    @staticmethod
    def _b64decode(value: str) -> bytes:
        return base64.b64decode(value.encode("utf-8"))

    # =========================================================
    # Generación de salt
    # =========================================================
    def generate_salt(self, nbytes: int = DEFAULT_SALT_BYTES) -> str:
        """
        Genera una salt criptográficamente segura y la retorna en base64.
        """
        if nbytes <= 0:
            raise ValueError("La cantidad de bytes para la salt debe ser mayor que cero.")

        raw_salt = secrets.token_bytes(nbytes)
        return self._b64encode(raw_salt)

    # =========================================================
    # Hashing
    # =========================================================
    def hash_password(
        self,
        plain_password: str,
        salt: str | None = None,
        algorithm: str = DEFAULT_ALGORITHM,
        iterations: int = DEFAULT_ITERATIONS,
    ) -> dict:
        """
        Genera el hash de una contraseña y retorna todos los datos requeridos
        para persistirla en base de datos.
        """
        if not plain_password:
            raise ValueError("La contraseña no puede estar vacía.")

        if algorithm != self.DEFAULT_ALGORITHM:
            raise ValueError(f"Algoritmo no soportado: {algorithm}")

        if iterations <= 0:
            raise ValueError("La cantidad de iteraciones debe ser mayor que cero.")

        if salt is None:
            salt = self.generate_salt()

        salt_bytes = self._b64decode(salt)
        password_bytes = self._to_bytes(plain_password)

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password_bytes,
            salt_bytes,
            iterations,
        )

        return {
            "clave_hash": self._b64encode(digest),
            "clave_salt": salt,
            "clave_algoritmo": algorithm,
            "clave_iteraciones": iterations,
        }

    # =========================================================
    # Verificación
    # =========================================================
    def verify_password(
        self,
        plain_password: str,
        stored_hash: str | None,
        stored_salt: str | None,
        stored_algorithm: str | None,
        stored_iterations: int | None,
    ) -> bool:
        """
        Verifica si la contraseña ingresada coincide con la almacenada.
        """
        if not plain_password:
            return False

        if not stored_hash or not stored_salt or not stored_algorithm or not stored_iterations:
            return False

        if stored_algorithm != self.DEFAULT_ALGORITHM:
            return False

        try:
            generated = self.hash_password(
                plain_password=plain_password,
                salt=stored_salt,
                algorithm=stored_algorithm,
                iterations=int(stored_iterations),
            )
        except Exception:
            return False

        return hmac.compare_digest(
            generated["clave_hash"],
            stored_hash,
        )

    # =========================================================
    # Utilidad para creación/actualización
    # =========================================================
    def build_password_payload(
        self,
        plain_password: str,
        debe_cambiar_clave: bool = False,
    ) -> dict:
        """
        Genera un payload listo para guardar en base de datos.
        """
        result = self.hash_password(
            plain_password=plain_password,
            salt=None,
            algorithm=self.DEFAULT_ALGORITHM,
            iterations=self.DEFAULT_ITERATIONS,
        )

        result["debe_cambiar_clave"] = bool(debe_cambiar_clave)
        return result

    # =========================================================
    # Validaciones básicas
    # =========================================================
    def validate_password_policy(self, plain_password: str) -> tuple[bool, str]:
        """
        Valida una política básica de contraseña.

        Regla actual:
        - mínimo 8 caracteres
        - al menos una letra
        - al menos un número

        Esta política luego se puede endurecer sin tocar el resto del login.
        """
        if not plain_password:
            return False, "La contraseña es obligatoria."

        if len(plain_password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres."

        has_letter = any(ch.isalpha() for ch in plain_password)
        has_digit = any(ch.isdigit() for ch in plain_password)

        if not has_letter:
            return False, "La contraseña debe incluir al menos una letra."

        if not has_digit:
            return False, "La contraseña debe incluir al menos un número."

        return True, "OK"