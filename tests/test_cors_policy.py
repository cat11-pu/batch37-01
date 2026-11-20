import pytest

import cors_policy as cp


def policy(credentials=False):
    return cp.CorsPolicy({"https://app.example"}, credentials)


def test_allowed_origin_is_echoed():
    headers = policy().headers("https://app.example", "GET")
    assert headers["Access-Control-Allow-Origin"] == "https://app.example"


def test_unknown_origin_has_no_allow_header():
    game = policy()
    assert game.headers("https://app.example", "GET")["Access-Control-Allow-Origin"] == "https://app.example"
    assert "Access-Control-Allow-Origin" not in game.headers("https://evil.example", "GET")


def test_suffix_origin_is_rejected():
    game = policy()
    assert game.headers("https://app.example", "GET")["Access-Control-Allow-Origin"] == "https://app.example"
    assert "Access-Control-Allow-Origin" not in game.headers("https://evil-app.example", "GET")


def test_vary_origin_is_always_set():
    headers = policy().headers("https://app.example", "GET")
    assert headers["Vary"] == "Origin"


def test_credentials_header_is_set():
    headers = policy(True).headers("https://app.example", "GET")
    assert headers["Access-Control-Allow-Credentials"] == "true"


def test_credentials_never_use_wildcard():
    game = policy(True)
    assert game.headers("https://app.example", "GET")["Access-Control-Allow-Origin"] == "https://app.example"
    headers = game.headers("*", "GET")
    assert headers.get("Access-Control-Allow-Origin") != "*"


def test_preflight_allows_method():
    headers = policy().headers("https://app.example", "OPTIONS", ["content-type"])
    assert "POST" in headers["Access-Control-Allow-Methods"]


def test_preflight_does_not_reflect_unknown_header():
    game = policy()
    allowed = game.headers("https://app.example", "OPTIONS", ["content-type"])
    assert "content-type" in allowed["Access-Control-Allow-Headers"].lower()
    headers = game.headers("https://app.example", "OPTIONS", ["x-evil"])
    assert "x-evil" not in headers.get("Access-Control-Allow-Headers", "")


def test_preflight_allows_content_type():
    headers = policy().headers("https://app.example", "OPTIONS", ["content-type"])
    assert "content-type" in headers["Access-Control-Allow-Headers"].lower()


def test_null_origin_is_rejected():
    game = policy()
    assert game.headers("https://app.example", "GET")["Access-Control-Allow-Origin"] == "https://app.example"
    headers = game.headers("null", "GET")
    assert "Access-Control-Allow-Origin" not in headers


def test_invalid_origin_raises():
    with pytest.raises(ValueError):
        policy().headers("not a url", "GET")


def test_invalid_allowed_origin_raises():
    with pytest.raises(ValueError):
        cp.CorsPolicy({"*"}, True)


def test_invalid_method_raises():
    with pytest.raises(ValueError):
        policy().headers("https://app.example", "TRACE")


def test_preflight_headers_are_sorted_or_stable():
    headers = policy().headers("https://app.example", "OPTIONS", ["content-type"])
    assert headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"


def test_no_allow_origin_for_disallowed_preflight():
    game = policy()
    assert game.headers("https://app.example", "OPTIONS")["Access-Control-Allow-Origin"] == "https://app.example"
    headers = game.headers("https://evil.example", "OPTIONS")
    assert "Access-Control-Allow-Origin" not in headers
