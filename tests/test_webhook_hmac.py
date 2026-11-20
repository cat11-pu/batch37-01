import pytest

import webhook_hmac as wh

SECRET = b"0123456789abcdef0123456789abcdef"


def verifier(tolerance=300):
    return wh.WebhookVerifier(SECRET, tolerance)


def test_sign_returns_hex():
    sig = verifier().sign(b"{}", 100)
    assert isinstance(sig, str) and len(sig) == 64
    int(sig, 16)


def test_valid_signature_is_accepted():
    game = verifier()
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True


def test_body_change_is_rejected():
    game = verifier()
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True
    assert game.verify(b'{"x":1}', 100, sig, 100) is False


def test_timestamp_change_is_rejected():
    game = verifier()
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True
    assert game.verify(b"{}", 101, sig, 101) is False


def test_old_timestamp_is_rejected():
    game = verifier(tolerance=10)
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True
    game2 = verifier(tolerance=10)
    sig2 = game2.sign(b"{}", 100)
    assert game2.verify(b"{}", 100, sig2, 111) is False


def test_future_timestamp_is_rejected():
    game = verifier(tolerance=10)
    sig = game.sign(b"{}", 200)
    assert game.verify(b"{}", 200, sig, 200) is True
    game2 = verifier(tolerance=10)
    sig2 = game2.sign(b"{}", 200)
    assert game2.verify(b"{}", 200, sig2, 189) is False


def test_replay_is_rejected():
    game = verifier()
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True
    assert game.verify(b"{}", 100, sig, 100) is False


def test_uppercase_hex_is_accepted():
    game = verifier()
    sig = game.sign(b"{}", 100).upper()
    assert game.verify(b"{}", 100, sig, 100) is True


def test_invalid_hex_is_rejected():
    game = verifier()
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True
    game2 = verifier()
    assert game2.verify(b"{}", 100, "zz" * 32, 100) is False


def test_short_signature_is_rejected():
    game = verifier()
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True
    game2 = verifier()
    assert game2.verify(b"{}", 100, "ab", 100) is False


def test_non_bytes_body_raises():
    with pytest.raises(ValueError):
        verifier().sign("{}", 100)


def test_non_int_timestamp_raises():
    with pytest.raises(ValueError):
        verifier().sign(b"{}", "100")


def test_invalid_tolerance_raises():
    with pytest.raises(ValueError):
        wh.WebhookVerifier(SECRET, -1)


def test_wrong_secret_is_rejected():
    sig = verifier().sign(b"{}", 100)
    assert verifier().verify(b"{}", 100, sig, 100) is True
    other = wh.WebhookVerifier(b"ffffffffffffffffffffffffffffffff", 300)
    assert other.verify(b"{}", 100, sig, 100) is False


def test_verify_does_not_consume_on_failure():
    game = verifier()
    assert game.verify(b"{}", 100, "00" * 32, 100) is False
    sig = game.sign(b"{}", 100)
    assert game.verify(b"{}", 100, sig, 100) is True
