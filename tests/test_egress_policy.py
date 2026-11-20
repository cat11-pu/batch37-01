import pytest

import egress_policy as ep


def policy():
    return ep.EgressPolicy([
        {"host": "api.example.com", "ports": [443], "schemes": ["https"], "paths": ["/v1/*"], "methods": ["GET"], "effect": "allow"},
        {"host": "*.internal", "effect": "deny"},
    ])


def req(**overrides):
    value = {"host": "api.example.com", "port": 443, "scheme": "https", "path": "/v1/users", "method": "GET"}
    value.update(overrides)
    return value


def test_exact_allow():
    assert policy().check(req()) is True


def test_wildcard_subdomain_allowed():
    game = ep.EgressPolicy([{"host": "*.example.com", "effect": "allow"}])
    assert game.check(req(host="a.example.com")) is True


def test_wildcard_does_not_match_apex():
    game = ep.EgressPolicy([{"host": "*.example.com", "effect": "allow"}])
    assert game.check(req(host="a.example.com")) is True
    assert game.check(req(host="example.com")) is False


def test_deny_rule_wins_after_allow():
    game = ep.EgressPolicy([
        {"host": "*.example.com", "effect": "allow"},
        {"host": "evil.example.com", "effect": "deny"},
    ])
    assert game.check(req(host="ok.example.com")) is True
    assert game.check(req(host="evil.example.com")) is False


def test_port_mismatch_is_denied():
    assert policy().check(req()) is True
    assert policy().check(req(port=8443)) is False


def test_path_mismatch_is_denied():
    assert policy().check(req()) is True
    assert policy().check(req(path="/v2/users")) is False


def test_method_mismatch_is_denied():
    assert policy().check(req()) is True
    assert policy().check(req(method="POST")) is False


def test_default_deny():
    assert policy().check(req()) is True
    assert ep.EgressPolicy([]).check(req()) is False


def test_host_is_case_insensitive():
    assert policy().check(req(host="API.EXAMPLE.COM")) is True


def test_trailing_dot_is_normalized():
    assert policy().check(req(host="api.example.com.")) is True


def test_invalid_request_raises():
    with pytest.raises(ValueError):
        policy().check({"host": "api.example.com"})


def test_invalid_rule_effect_raises():
    with pytest.raises(ValueError):
        ep.EgressPolicy([{"host": "a", "effect": "maybe"}])


def test_invalid_port_raises():
    with pytest.raises(ValueError):
        ep.EgressPolicy([{"host": "a", "ports": [0], "effect": "allow"}])


def test_path_prefix_matches():
    game = ep.EgressPolicy([{"host": "a", "paths": ["/api/*"], "effect": "allow"}])
    assert game.check(req(host="a", path="/api/v1")) is True


def test_rule_order_is_stable():
    game = ep.EgressPolicy([
        {"host": "a", "effect": "deny"},
        {"host": "a", "effect": "allow"},
        {"host": "b", "effect": "allow"},
    ])
    assert game.check(req(host="b")) is True
    assert game.check(req(host="a")) is False
