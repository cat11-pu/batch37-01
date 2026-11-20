import base64
import hashlib
import hmac
import json

import pytest

import jwt_keyring as jk

SECRET = "0123456789abcdef0123456789abcdef"


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def token(header, payload, secret=SECRET):
    head = b64(json.dumps(header, separators=(",", ":")).encode())
    body = b64(json.dumps(payload, separators=(",", ":")).encode())
    signing = f"{head}.{body}".encode()
    sig = b64(hmac.new(secret.encode(), signing, hashlib.sha256).digest())
    return f"{head}.{body}.{sig}"


def payload(**overrides):
    value = {"sub": "u1", "exp": 100, "iat": 0, "aud": "api"}
    value.update(overrides)
    return value


def keyring():
    return jk.JwtKeyring({"k1": SECRET})


def test_valid_token_returns_payload():
    result = keyring().verify(token({"alg": "HS256", "kid": "k1"}, payload()), now=10, audience="api")
    assert result["sub"] == "u1"


def test_bad_signature_raises():
    bad = token({"alg": "HS256", "kid": "k1"}, payload(), "another-secret-0123456789abcdef")
    with pytest.raises(ValueError):
        keyring().verify(bad, now=10, audience="api")


def test_unknown_kid_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "HS256", "kid": "ghost"}, payload()), now=10)


def test_alg_none_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "none", "kid": "k1"}, payload()), now=10)


def test_alg_rs256_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "RS256", "kid": "k1"}, payload()), now=10)


def test_expired_token_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "HS256", "kid": "k1"}, payload(exp=5)), now=10)


def test_not_before_in_future_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "HS256", "kid": "k1"}, payload(nbf=20)), now=10)


def test_audience_mismatch_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "HS256", "kid": "k1"}, payload(aud="other")), now=10, audience="api")


def test_audience_list_matches():
    result = keyring().verify(token({"alg": "HS256", "kid": "k1"}, payload(aud=["api", "web"])), now=10, audience="api")
    assert result["sub"] == "u1"


def test_missing_exp_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "HS256", "kid": "k1"}, {"sub": "u1"}), now=10)


def test_malformed_token_raises():
    with pytest.raises(ValueError):
        keyring().verify("a.b", now=10)


def test_duplicate_kid_raises():
    game = keyring()
    with pytest.raises(ValueError):
        game.add_key("k1", "x" * 32)


def test_remove_key_rejects_old_token():
    game = keyring()
    old = token({"alg": "HS256", "kid": "k1"}, payload())
    game.remove_key("k1")
    with pytest.raises(ValueError):
        game.verify(old, now=10)


def test_non_object_payload_raises():
    with pytest.raises(ValueError):
        keyring().verify(token({"alg": "HS256", "kid": "k1"}, ["not", "dict"]), now=10)


def test_tampered_payload_raises():
    good = token({"alg": "HS256", "kid": "k1"}, payload())
    parts = good.split(".")
    parts[1] = b64(json.dumps(payload(sub="admin"), separators=(",", ":")).encode())
    with pytest.raises(ValueError):
        keyring().verify(".".join(parts), now=10)
