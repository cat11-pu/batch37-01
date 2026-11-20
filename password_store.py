import hashlib
import hmac
import os


class PasswordStore:
    PREFIX = "pbkdf2"
    HASH_ALGORITHM = "sha256"
    SALT_BYTES = 16
    KEY_BYTES = 32
    MIN_PASSWORD_LENGTH = 8

    def __init__(self, pepper=b"", iterations=1000):
        if isinstance(pepper, str):
            pepper = pepper.encode("utf-8")
        if not isinstance(pepper, bytes):
            raise ValueError("pepper must be bytes")
        if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations <= 0:
            raise ValueError("iterations must be a positive integer")
        self.pepper = pepper
        self.iterations = iterations

    def _validate_password(self, password):
        if not isinstance(password, str):
            raise ValueError("password must be a string")
        if not password:
            raise ValueError("password must not be empty")
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValueError(
                "password must be at least %d characters" % self.MIN_PASSWORD_LENGTH
            )
        return password.encode("utf-8")

    def _key_material(self, password_bytes):
        if not self.pepper:
            return password_bytes
        return hmac.new(self.pepper, password_bytes, hashlib.sha256).digest()

    def _derive(self, password_bytes, salt, iterations):
        return hashlib.pbkdf2_hmac(
            self.HASH_ALGORITHM,
            self._key_material(password_bytes),
            salt,
            iterations,
            self.KEY_BYTES,
        )

    def hash(self, password):
        password_bytes = self._validate_password(password)
        salt = os.urandom(self.SALT_BYTES)
        derived = self._derive(password_bytes, salt, self.iterations)
        return "$".join(
            (
                self.PREFIX,
                str(self.iterations),
                salt.hex(),
                derived.hex(),
            )
        )

    def _parse(self, stored):
        if not isinstance(stored, str):
            return None
        parts = stored.split("$")
        if len(parts) != 4 or parts[0] != self.PREFIX:
            return None
        try:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected = bytes.fromhex(parts[3])
        except (ValueError, TypeError):
            return None
        if (
            iterations <= 0
            or len(salt) != self.SALT_BYTES
            or len(expected) != self.KEY_BYTES
        ):
            return None
        return iterations, salt, expected

    def verify(self, password, stored):
        if not isinstance(password, str) or not password:
            return False
        parsed = self._parse(stored)
        if parsed is None:
            return False
        iterations, salt, expected = parsed
        try:
            derived = self._derive(password.encode("utf-8"), salt, iterations)
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(derived, expected)

    def needs_upgrade(self, stored):
        parsed = self._parse(stored)
        if parsed is None:
            return True
        iterations, _salt, _expected = parsed
        return iterations < self.iterations

    def verify_and_upgrade(self, password, stored):
        """Verify first; only produce a replacement hash on success.

        The caller is expected to swap the persisted value for the returned
        hash in a single atomic write so a failed verification never touches
        the existing record.
        """
        if not self.verify(password, stored):
            return False, stored
        if not self.needs_upgrade(stored):
            return True, stored
        return True, self.hash(password)
