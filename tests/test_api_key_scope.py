import pytest

import api_key_scope as ak


def store():
    game = ak.ApiKeyStore()
    game.issue("k1", ["read:users", "write:posts"], 0, ttl=100)
    return game


def test_exact_scope_is_allowed():
    assert store().authorize("k1", "read:users", 1) is True


def test_missing_scope_is_denied():
    game = store()
    assert game.authorize("k1", "read:users", 1) is True
    assert game.authorize("k1", "delete:users", 1) is False


def test_wildcard_scope_matches():
    game = ak.ApiKeyStore()
    game.issue("k1", ["read:*"], 0)
    assert game.authorize("k1", "read:users", 1) is True


def test_wildcard_does_not_cross_action():
    game = ak.ApiKeyStore()
    game.issue("k1", ["read:*"], 0)
    assert game.authorize("k1", "read:users", 1) is True
    assert game.authorize("k1", "write:users", 1) is False


def test_global_wildcard_matches_all():
    game = ak.ApiKeyStore()
    game.issue("k1", ["*"], 0)
    assert game.authorize("k1", "delete:users", 1) is True


def test_expired_key_is_denied():
    game = store()
    assert game.authorize("k1", "read:users", 1) is True
    assert game.authorize("k1", "read:users", 101) is False


def test_revoked_key_is_denied():
    game = store()
    assert game.authorize("k1", "read:users", 1) is True
    game.revoke("k1")
    assert game.authorize("k1", "read:users", 1) is False


def test_unknown_key_is_denied():
    game = store()
    assert game.authorize("k1", "read:users", 1) is True
    assert game.authorize("ghost", "read:users", 1) is False


def test_duplicate_key_id_raises():
    game = store()
    with pytest.raises(ValueError):
        game.issue("k1", ["read:users"], 0)


def test_invalid_scope_raises():
    game = ak.ApiKeyStore()
    with pytest.raises(ValueError):
        game.issue("k1", [""], 0)


def test_invalid_ttl_raises():
    game = ak.ApiKeyStore()
    with pytest.raises(ValueError):
        game.issue("k1", ["read:users"], 0, ttl=0)


def test_revoke_unknown_raises():
    with pytest.raises(ValueError):
        ak.ApiKeyStore().revoke("ghost")


def test_authorize_does_not_mutate():
    game = store()
    before = game.keys["k1"]["scopes"][:]
    game.authorize("k1", "read:users", 1)
    assert game.keys["k1"]["scopes"] == before


def test_scope_prefix_must_be_exact():
    game = ak.ApiKeyStore()
    game.issue("k1", ["read:user"], 0)
    assert game.authorize("k1", "read:user", 1) is True
    assert game.authorize("k1", "read:users", 1) is False


def test_multiple_scopes_work():
    assert store().authorize("k1", "write:posts", 1) is True
