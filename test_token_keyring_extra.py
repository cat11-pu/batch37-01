import base64
import hashlib
import hmac
import json

import pytest

import token_keyring as tk

SECRET_A = "a" * 32
SECRET_B = "b" * 32


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sign(header, payload, secret):
    head = b64(json.dumps(header, separators=(",", ":")).encode())
    body = b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = b64(hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
    return f"{head}.{body}.{sig}"


def make_token(kid, secret, **payload_overrides):
    payload = {"sub": "u1", "exp": 100, "iat": 0, "aud": "api"}
    payload.update(payload_overrides)
    return sign({"alg": "HS256", "kid": kid}, payload, secret)


def multi_tenant_keyring():
    return tk.TokenKeyring({"tenant-a": SECRET_A, "tenant-b": SECRET_B})


def test_each_tenant_only_accepts_own_key():
    keyring = multi_tenant_keyring()
    token_a = make_token("tenant-a", SECRET_A)
    token_b = make_token("tenant-b", SECRET_B)
    assert keyring.verify(token_a, now=10, audience="api")["sub"] == "u1"
    assert keyring.verify(token_b, now=10, audience="api")["sub"] == "u1"

    cross = make_token("tenant-a", SECRET_B)
    with pytest.raises(ValueError):
        keyring.verify(cross, now=10, audience="api")


def test_sequential_verify_keeps_key_cache_isolated_per_kid():
    keyring = multi_tenant_keyring()
    for _ in range(3):
        keyring.verify(make_token("tenant-a", SECRET_A), now=10, audience="api")
        keyring.verify(make_token("tenant-b", SECRET_B), now=10, audience="api")
    with pytest.raises(ValueError):
        keyring.verify(make_token("tenant-b", SECRET_A), now=10, audience="api")


def test_rotation_window_rejects_old_and_accepts_new_kid():
    keyring = tk.TokenKeyring({"k-old": SECRET_A})
    old_token = make_token("k-old", SECRET_A)
    keyring.add_key("k-new", SECRET_B)
    new_token = make_token("k-new", SECRET_B)

    assert keyring.verify(new_token, now=10, audience="api")["sub"] == "u1"
    keyring.remove_key("k-old")
    with pytest.raises(ValueError):
        keyring.verify(old_token, now=10, audience="api")


def test_future_iat_raises():
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            make_token("tenant-a", SECRET_A, iat=50), now=10, audience="api"
        )


def test_nbf_boundary_is_inclusive():
    token = make_token("tenant-a", SECRET_A, nbf=10)
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(token, now=9, audience="api")
    assert multi_tenant_keyring().verify(token, now=10, audience="api")["sub"] == "u1"


def test_exp_boundary_is_exclusive():
    token = make_token("tenant-a", SECRET_A, exp=10)
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(token, now=10, audience="api")
    assert multi_tenant_keyring().verify(token, now=9, audience="api")["sub"] == "u1"


def test_missing_iat_and_aud_raise():
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            sign({"alg": "HS256", "kid": "tenant-a"},
                 {"sub": "u1", "exp": 100, "aud": "api"}, SECRET_A),
            now=10, audience="api",
        )
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            sign({"alg": "HS256", "kid": "tenant-a"},
                 {"sub": "u1", "exp": 100, "iat": 0}, SECRET_A),
            now=10, audience="api",
        )


def test_non_numeric_and_bool_claims_raise():
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            make_token("tenant-a", SECRET_A, exp="soon"), now=10, audience="api"
        )
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            make_token("tenant-a", SECRET_A, iat=True), now=10, audience="api"
        )


def test_invalid_aud_shapes_raise():
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            make_token("tenant-a", SECRET_A, aud=123), now=10, audience="api"
        )
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            make_token("tenant-a", SECRET_A, aud=[]), now=10, audience="api"
        )
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(
            make_token("tenant-a", SECRET_A, aud=["other"]), now=10, audience="api"
        )


def test_audience_skipped_when_not_requested():
    token = make_token("tenant-a", SECRET_A, aud="other")
    assert multi_tenant_keyring().verify(token, now=10)["sub"] == "u1"


def test_header_missing_alg_or_kid_raises():
    token = sign({"kid": "tenant-a"}, {"sub": "u1", "exp": 100, "iat": 0, "aud": "api"}, SECRET_A)
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(token, now=10)
    token = sign({"alg": "HS256"}, {"sub": "u1", "exp": 100, "iat": 0, "aud": "api"}, SECRET_A)
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(token, now=10)


def test_non_dict_header_raises():
    head = b64(json.dumps(["alg", "kid"]).encode())
    body = b64(json.dumps({"sub": "u1", "exp": 100, "iat": 0, "aud": "api"}).encode())
    sig = b64(hmac.new(SECRET_A.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(f"{head}.{body}.{sig}", now=10)


def test_bad_base64_and_wrong_segment_count_raise():
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify("###.###.###", now=10)
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify("a.b.c.d", now=10)
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify("a..c", now=10)
    with pytest.raises(ValueError):
        multi_tenant_keyring().verify(123, now=10)


def test_add_key_rejects_duplicate_bad_input_and_other_algs():
    keyring = tk.TokenKeyring()
    keyring.add_key("k1", SECRET_A)
    with pytest.raises(ValueError):
        keyring.add_key("k1", SECRET_B)
    with pytest.raises(ValueError):
        keyring.add_key("", SECRET_A)
    with pytest.raises(ValueError):
        keyring.add_key("k2", "")
    with pytest.raises(ValueError):
        keyring.add_key("k2", SECRET_A, alg="RS256")
    with pytest.raises(ValueError):
        keyring.add_key("k2", SECRET_A, alg="none")


def test_remove_unknown_kid_raises():
    with pytest.raises(ValueError):
        tk.TokenKeyring().remove_key("ghost")


def test_constructor_copies_keys_and_keeps_them_isolated():
    source = {"k1": SECRET_A}
    keyring = tk.TokenKeyring(source)
    source["k1"] = SECRET_B
    token = make_token("k1", SECRET_A)
    assert keyring.verify(token, now=10, audience="api")["sub"] == "u1"


def test_bytes_secret_is_supported():
    keyring = tk.TokenKeyring()
    keyring.add_key("k1", SECRET_A.encode())
    token = make_token("k1", SECRET_A)
    assert keyring.verify(token, now=10, audience="api")["sub"] == "u1"


def test_float_timestamps_are_accepted():
    token = make_token("tenant-a", SECRET_A, exp=10.5, iat=0.25, nbf=0.5)
    assert multi_tenant_keyring().verify(token, now=10, audience="api")["sub"] == "u1"


def test_signature_check_is_constant_time_primitive():
    assert tk.hmac.compare_digest is hmac.compare_digest
    keyring = multi_tenant_keyring()
    token = make_token("tenant-a", SECRET_A)
    head, body, sig = token.split(".")
    raw_sig = base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))
    flipped = bytes([raw_sig[0] ^ 0x01]) + raw_sig[1:]
    bad_sig = base64.urlsafe_b64encode(flipped).rstrip(b"=").decode()
    with pytest.raises(ValueError):
        keyring.verify(f"{head}.{body}.{bad_sig}", now=10, audience="api")
