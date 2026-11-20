import base64
import hashlib

import pytest

import oauth_pkce as op

VERIFIER = "a" * 50
CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).rstrip(b"=").decode()


def flow():
    return op.PkceFlow({"client1"}, {"https://app.example/cb"}, ttl=60)


def authorize(game, **overrides):
    args = {
        "client_id": "client1",
        "redirect_uri": "https://app.example/cb",
        "state": "state-1",
        "challenge": CHALLENGE,
        "method": "S256",
        "now": 0,
    }
    args.update(overrides)
    return game.authorize(**args)


def test_authorize_returns_code():
    code = authorize(flow())
    assert isinstance(code, str) and code


def test_valid_exchange_returns_client():
    game = flow()
    code = authorize(game)
    result = game.exchange(code, VERIFIER, "client1", "https://app.example/cb", now=1)
    assert result["client_id"] == "client1"


def test_wrong_verifier_raises():
    game = flow()
    code = authorize(game)
    with pytest.raises(ValueError):
        game.exchange(code, "b" * 50, "client1", "https://app.example/cb", now=1)


def test_code_cannot_be_reused():
    game = flow()
    code = authorize(game)
    game.exchange(code, VERIFIER, "client1", "https://app.example/cb", now=1)
    with pytest.raises(ValueError):
        game.exchange(code, VERIFIER, "client1", "https://app.example/cb", now=2)


def test_expired_code_raises():
    game = flow()
    code = authorize(game)
    with pytest.raises(ValueError):
        game.exchange(code, VERIFIER, "client1", "https://app.example/cb", now=61)


def test_unknown_code_raises():
    with pytest.raises(ValueError):
        flow().exchange("ghost", VERIFIER, "client1", "https://app.example/cb")


def test_wrong_client_raises():
    game = flow()
    code = authorize(game)
    with pytest.raises(ValueError):
        game.exchange(code, VERIFIER, "client2", "https://app.example/cb")


def test_wrong_redirect_raises():
    game = flow()
    code = authorize(game)
    with pytest.raises(ValueError):
        game.exchange(code, VERIFIER, "client1", "https://evil.example/cb")


def test_unknown_client_raises():
    with pytest.raises(ValueError):
        authorize(flow(), client_id="ghost")


def test_redirect_not_allowlisted_raises():
    with pytest.raises(ValueError):
        authorize(flow(), redirect_uri="https://evil.example/cb")


def test_empty_state_raises():
    with pytest.raises(ValueError):
        authorize(flow(), state="")


def test_short_challenge_raises():
    with pytest.raises(ValueError):
        authorize(flow(), challenge="short")


def test_invalid_method_raises():
    with pytest.raises(ValueError):
        authorize(flow(), method="MD5")


def test_plain_method_works():
    import hashlib
    plain = "c" * 50
    game = flow()
    code = authorize(game, challenge=plain, method="plain")
    result = game.exchange(code, plain, "client1", "https://app.example/cb", now=1)
    assert result["client_id"] == "client1"


def test_short_verifier_raises():
    game = flow()
    code = authorize(game)
    with pytest.raises(ValueError):
        game.exchange(code, "short", "client1", "https://app.example/cb")
