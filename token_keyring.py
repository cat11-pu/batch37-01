import base64
import binascii
import hashlib
import hmac
import json

SUPPORTED_ALGORITHM = "HS256"


class TokenKeyring:
    def __init__(self, keys=None):
        self._keys = {}
        for kid, secret in (keys or {}).items():
            self.add_key(kid, secret)

    def add_key(self, kid, secret, alg=SUPPORTED_ALGORITHM):
        if not isinstance(kid, str) or not kid:
            raise ValueError("key id must be a non-empty string")
        if not isinstance(secret, (str, bytes)) or not secret:
            raise ValueError("secret must be a non-empty string or bytes")
        if alg != SUPPORTED_ALGORITHM:
            raise ValueError(f"unsupported algorithm {alg!r}; only {SUPPORTED_ALGORITHM} is allowed")
        if kid in self._keys:
            raise ValueError(f"key id {kid!r} already exists")
        self._keys[kid] = secret.encode() if isinstance(secret, str) else secret

    def remove_key(self, kid):
        if kid not in self._keys:
            raise ValueError(f"unknown key id {kid!r}")
        del self._keys[kid]

    def verify(self, token, now, audience=None):
        if not isinstance(token, str):
            raise ValueError("token must be a string")
        parts = token.split(".")
        if len(parts) != 3 or not all(parts):
            raise ValueError("malformed token: expected header.payload.signature")

        header_segment, payload_segment, signature_segment = parts
        header = self._decode_json_segment(header_segment, "header")
        if not isinstance(header, dict):
            raise ValueError("token header must be a JSON object")
        if "alg" not in header:
            raise ValueError("missing alg in token header")
        if header["alg"] != SUPPORTED_ALGORITHM:
            raise ValueError(f"unsupported algorithm {header['alg']!r}; only {SUPPORTED_ALGORITHM} is allowed")
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise ValueError("missing or invalid kid in token header")

        secret = self._keys.get(kid)
        if secret is None:
            raise ValueError(f"unknown key id {kid!r}")

        payload = self._decode_json_segment(payload_segment, "payload")
        if not isinstance(payload, dict):
            raise ValueError("token payload must be a JSON object")

        self._verify_claims(payload, now, audience)

        expected_signature = hmac.new(
            secret,
            f"{header_segment}.{payload_segment}".encode(),
            hashlib.sha256,
        ).digest()
        actual_signature = self._decode_signature_segment(signature_segment)
        if not hmac.compare_digest(actual_signature, expected_signature):
            raise ValueError("invalid signature")

        return payload

    def _verify_claims(self, payload, now, audience):
        if "exp" not in payload:
            raise ValueError("missing required claim: exp")
        if "iat" not in payload:
            raise ValueError("missing required claim: iat")
        if "aud" not in payload:
            raise ValueError("missing required claim: aud")

        expires_at = self._numeric_claim(payload, "exp")
        issued_at = self._numeric_claim(payload, "iat")
        not_before = payload.get("nbf")
        if not_before is not None:
            not_before = self._numeric_claim(payload, "nbf")

        if now >= expires_at:
            raise ValueError("token has expired")
        if now < issued_at:
            raise ValueError("token issued in the future")
        if not_before is not None and now < not_before:
            raise ValueError("token is not yet valid")

        token_audience = payload["aud"]
        if isinstance(token_audience, list):
            if not all(isinstance(item, str) for item in token_audience) or not token_audience:
                raise ValueError("aud claim must be a non-empty string or list of strings")
            if audience is not None and audience not in token_audience:
                raise ValueError("audience mismatch")
        elif isinstance(token_audience, str):
            if audience is not None and token_audience != audience:
                raise ValueError("audience mismatch")
        else:
            raise ValueError("aud claim must be a string or list of strings")

    @staticmethod
    def _numeric_claim(payload, name):
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"claim {name!r} must be a numeric timestamp")
        return value

    @staticmethod
    def _b64url_decode(segment):
        try:
            return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        except (binascii.Error, TypeError) as exc:
            raise ValueError("invalid base64url segment") from exc

    def _decode_json_segment(self, segment, label):
        raw = self._b64url_decode(segment)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"token {label} is not valid UTF-8 JSON") from exc

    def _decode_signature_segment(self, segment):
        try:
            return self._b64url_decode(segment)
        except ValueError as exc:
            raise ValueError("invalid signature encoding") from exc
