import pytest

import delegation_policy as dp

ROLES = {
    "member": {"parents": []},
    "officer": {"parents": ["member"]},
    "leader": {"parents": ["officer"]},
}


def policy(roles=None, max_depth=2):
    return dp.DelegationPolicy(ROLES if roles is None else roles, max_depth)


def test_direct_grant():
    game = policy()
    game.grant("member", "chat")
    assert game.can("member", "chat") is True


def test_inherited_grant():
    game = policy()
    game.grant("member", "chat")
    assert game.can("leader", "chat") is True


def test_deny_overrides_allow():
    game = policy()
    game.grant("member", "chat")
    assert game.can("member", "chat") is True
    game.deny("member", "chat")
    assert game.can("member", "chat") is False


def test_parent_deny_overrides_child_allow():
    game = policy()
    game.grant("officer", "bank")
    assert game.can("officer", "bank") is True
    game.deny("member", "bank")
    assert game.can("officer", "bank") is False


def test_delegate_grants_permission():
    game = policy()
    game.grant("leader", "approve")
    game.delegate("leader", "member", "approve", 1)
    assert game.can("member", "approve") is True


def test_delegation_chain_within_depth():
    game = policy(max_depth=2)
    game.grant("leader", "approve")
    game.delegate("leader", "officer", "approve", 2)
    game.delegate("officer", "member", "approve", 1)
    assert game.can("member", "approve") is True


def test_delegation_beyond_depth_is_denied():
    game = policy(max_depth=1)
    game.grant("leader", "approve")
    game.delegate("leader", "officer", "approve", 1)
    game.delegate("officer", "member", "approve", 1)
    assert len(game.state()["delegations"]) == 2
    assert game.can("member", "approve") is False


def test_delegation_cycle_is_denied():
    game = policy(max_depth=3)
    game.grant("leader", "approve")
    game.delegate("leader", "officer", "approve", 3)
    game.delegate("officer", "leader", "approve", 3)
    assert game.can("officer", "approve") is True


def test_delegator_must_have_permission():
    game = policy()
    game.delegate("leader", "member", "approve", 1)
    assert set(game.state()["roles"]) == {"member", "officer", "leader"}
    assert game.can("member", "approve") is False


def test_duplicate_delegation_raises():
    game = policy()
    game.grant("leader", "approve")
    game.delegate("leader", "member", "approve", 1)
    with pytest.raises(ValueError):
        game.delegate("leader", "member", "approve", 1)


def test_unknown_role_raises():
    with pytest.raises(ValueError):
        policy().grant("ghost", "chat")


def test_invalid_depth_raises():
    game = policy()
    game.grant("leader", "approve")
    with pytest.raises(ValueError):
        game.delegate("leader", "member", "approve", 0)


def test_cycle_in_roles_raises():
    with pytest.raises(ValueError):
        policy({"a": {"parents": ["b"]}, "b": {"parents": ["a"]}})


def test_state_returns_a_copy():
    game = policy()
    game.grant("member", "chat")
    snapshot = game.state()
    snapshot["allows"]["member"].append("hacked")
    assert "hacked" not in game.state()["allows"]["member"]


def test_no_permission_is_denied():
    game = policy()
    game.grant("member", "chat")
    assert game.can("member", "chat") is True
    assert game.can("member", "bank") is False
