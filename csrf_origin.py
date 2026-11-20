import hashlib
import hmac
import os


class CsrfGuard:
    SAFE_METHODS = frozenset(("GET", "HEAD", "OPTIONS"))

    def __init__(self, allowed_origins, secret, ttl=300):
        self.allowed_origins = frozenset(allowed_origins)
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        self.secret = secret
        self.ttl = ttl
        # session_id -> {nonce: expiry_timestamp}; one entry per issued token,
        # so tokens for different tabs can be revoked independently.
        self.sessions = {}

    def issue(self, session_id, now):
        nonce = os.urandom(32).hex()
        expires_at = now + self.ttl
        self.sessions.setdefault(session_id, {})[nonce] = expires_at
        signature = self._sign(session_id, nonce, expires_at)
        return ".".join((nonce, str(expires_at), signature))

    def verify(self, session_id, token, origin, now, method="POST"):
        if method.upper() in self.SAFE_METHODS:
            return True

        if not token or not origin:
            return False

        # Exact whitelist match: no suffix/prefix matching.
        if origin not in self.allowed_origins:
            return False

        parsed = self._parse(token)
        if parsed is None:
            return False
        nonce, expires_at, signature = parsed

        # Signature binds the token to its session; compare in constant time
        # before touching the session store so timing cannot leak state.
        expected_signature = self._sign(session_id, nonce, expires_at)
        if not hmac.compare_digest(signature, expected_signature):
            return False

        issued = self.sessions.get(session_id)
        if not issued or nonce not in issued:
            return False

        if now >= expires_at or now >= issued[nonce]:
            issued.pop(nonce, None)
            return False

        return True

    def revoke(self, session_id, token):
        """Invalidate a single tab's token without touching other tokens."""
        parsed = self._parse(token)
        if parsed is None:
            return False
        nonce = parsed[0]
        issued = self.sessions.get(session_id)
        if not issued:
            return False
        return issued.pop(nonce, None) is not None

    def logout(self, session_id):
        """Drop every token issued to the session (user logout)."""
        return self.sessions.pop(session_id, None) is not None

    invalidate = revoke
    invalidate_session = logout

    def _sign(self, session_id, nonce, expires_at):
        message = ".".join((str(session_id), nonce, str(expires_at)))
        return hmac.new(
            self.secret, message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _parse(token):
        if not isinstance(token, str):
            return None
        parts = token.split(".")
        if len(parts) != 3:
            return None
        nonce, expires_text, signature = parts
        if not nonce or not expires_text or not signature:
            return None
        try:
            expires_at = int(expires_text)
        except ValueError:
            return None
        if expires_at < 0:
            return None
        return nonce, expires_at, signature
