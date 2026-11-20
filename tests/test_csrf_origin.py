import pytest

import csrf_origin as co

SECRET = "0123456789abcdef0123456789abcdef"


def guard():
    return co.CsrfGuard({"https://app.example"}, SECRET, ttl=100)


def test_issue_returns_token():
    token = guard().issue("s1", 0)
    assert isinstance(token, str) and token


def test_valid_post_is_accepted():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1, "POST") is True


def test_wrong_origin_is_rejected():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1) is True
    assert game.verify("s1", token, "https://evil.example", 1) is False


def test_origin_suffix_attack_is_rejected():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1) is True
    assert game.verify("s1", token, "https://evil-app.example", 1) is False


def test_token_bound_to_session():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1) is True
    assert game.verify("s2", token, "https://app.example", 1) is False


def test_expired_token_is_rejected():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1) is True
    assert game.verify("s1", token, "https://app.example", 101) is False


def test_tampered_token_is_rejected():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token + "x", "https://app.example", 1) is False


def test_safe_get_does_not_require_token():
    game = guard()
    assert game.verify("s1", "", "", 1, "GET") is True


def test_safe_head_does_not_require_token():
    game = guard()
    assert game.verify("s1", "", "", 1, "HEAD") is True


def test_options_is_safe():
    game = guard()
    assert game.verify("s1", "", "", 1, "OPTIONS") is True


def test_post_without_token_is_rejected():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1, "POST") is True
    assert game.verify("s1", "", "https://app.example", 1, "POST") is False


def test_unknown_session_is_rejected():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1) is True
    assert game.verify("ghost", token, "https://app.example", 1) is False


def test_empty_origin_is_rejected():
    game = guard()
    token = game.issue("s1", 0)
    assert game.verify("s1", token, "https://app.example", 1, "POST") is True
    assert game.verify("s1", token, "", 1, "POST") is False


def test_different_session_tokens_differ():
    game = guard()
    assert game.issue("s1", 0) != game.issue("s2", 0)


def test_token_is_not_plain_session():
    game = guard()
    token = game.issue("s1", 0)
    assert "s1" not in token
