import base64
import hashlib
import hmac
import re
import secrets
import threading


_VERIFIER_RE = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
_S256_CHALLENGE_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")


class MobileAuthFlow:
    def __init__(self, clients, redirect_allowlist, ttl=60):
        self.clients = clients
        self.redirect_allowlist = redirect_allowlist
        self.ttl = ttl
        self.codes = {}
        self._lock = threading.Lock()

    def authorize(self, client_id, redirect_uri, state, challenge, method="S256", now=0):
        if client_id not in self.clients:
            raise ValueError("unknown client")
        if not isinstance(redirect_uri, str) or redirect_uri not in self.redirect_allowlist:
            raise ValueError("redirect_uri is not allowed")
        if not isinstance(state, str) or not state.strip():
            raise ValueError("state must not be empty")

        self._validate_challenge(challenge, method)

        with self._lock:
            code = secrets.token_urlsafe(32)
            while code in self.codes:
                code = secrets.token_urlsafe(32)

            self.codes[code] = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "challenge": challenge,
                "method": method,
                "issued_at": now,
                "used": False,
            }
        return code

    def exchange(self, code, verifier, client_id, redirect_uri, now=0):
        if not isinstance(code, str):
            raise ValueError("unknown authorization code")

        with self._lock:
            record = self.codes.get(code)
            if record is None or record["used"]:
                raise ValueError("authorization code is unknown or already used")
            if now - record["issued_at"] > self.ttl:
                raise ValueError("authorization code has expired")
            if client_id != record["client_id"]:
                raise ValueError("client does not match authorization code")
            if redirect_uri != record["redirect_uri"]:
                raise ValueError("redirect_uri does not match authorization code")
            if not isinstance(verifier, str) or not _VERIFIER_RE.fullmatch(verifier):
                raise ValueError("invalid code verifier")

            if record["method"] == "S256":
                digest = hashlib.sha256(verifier.encode("ascii")).digest()
                expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
                matches = hmac.compare_digest(expected, record["challenge"])
            else:
                matches = hmac.compare_digest(verifier, record["challenge"])

            if not matches:
                raise ValueError("code verifier does not match challenge")

            record["used"] = True

        return {"client_id": record["client_id"]}

    @staticmethod
    def _validate_challenge(challenge, method):
        if method not in ("S256", "plain"):
            raise ValueError("unsupported challenge method")
        if not isinstance(challenge, str):
            raise ValueError("invalid code challenge")

        if method == "S256":
            if not _S256_CHALLENGE_RE.fullmatch(challenge):
                raise ValueError("invalid S256 code challenge")
            try:
                decoded = base64.urlsafe_b64decode(challenge + "=")
            except (ValueError, TypeError):
                raise ValueError("invalid S256 code challenge") from None
            if len(decoded) != hashlib.sha256().digest_size:
                raise ValueError("invalid S256 code challenge")
        elif not _VERIFIER_RE.fullmatch(challenge):
            raise ValueError("invalid plain code challenge")
