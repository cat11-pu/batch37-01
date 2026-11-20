import pytest

import server_transfer as st

SERVERS = {
    "s1": {"capacity": 3, "players": ["alice", "bob"]},
    "s2": {"capacity": 3, "players": []},
    "s3": {"capacity": 3, "players": ["cara"]},
}


def service(**overrides):
    params = {
        "weights": {"sword": 5, "ore": 2, "relic": 1},
        "bound": {"relic"},
        "max_weight": 50,
        "cooldown": 100,
    }
    params.update(overrides)
    servers = {
        name: {"capacity": data["capacity"], "players": list(data["players"])}
        for name, data in SERVERS.items()
    }
    return st.ServerTransfer(servers, **params)


def test_request_creates_pending_transfer():
    game = service()
    game.request("t1", "alice", "s1", "s2", {"sword": 2}, 0)
    state = game.state()
    assert state["transfers"]["t1"]["status"] == "pending"
    assert "alice" in state["servers"]["s1"]["players"]


def test_unknown_source_is_rejected():
    game = service()
    with pytest.raises(ValueError):
        game.request("t1", "alice", "nope", "s2", {"sword": 1}, 0)


def test_unknown_target_is_rejected():
    game = service()
    with pytest.raises(ValueError):
        game.request("t1", "alice", "s1", "nope", {"sword": 1}, 0)


def test_same_server_is_rejected():
    game = service()
    with pytest.raises(ValueError):
        game.request("t1", "alice", "s1", "s1", {"sword": 1}, 0)


def test_player_must_be_on_source():
    game = service()
    with pytest.raises(ValueError):
        game.request("t1", "cara", "s1", "s2", {"sword": 1}, 0)


def test_full_target_is_rejected():
    servers = {
        "s1": {"capacity": 3, "players": ["alice"]},
        "s2": {"capacity": 1, "players": ["cara"]},
    }
    game = st.ServerTransfer(servers, weights={"sword": 1}, bound=set())
    with pytest.raises(ValueError):
        game.request("t1", "alice", "s1", "s2", {"sword": 1}, 0)


def test_commit_moves_player_between_servers():
    game = service()
    game.request("t1", "alice", "s1", "s2", {"sword": 2, "ore": 3}, 0)
    game.commit("t1", "alice", 5)
    state = game.state()
    assert "alice" in state["servers"]["s2"]["players"]
    assert "alice" not in state["servers"]["s1"]["players"]


def test_commit_preserves_inventory():
    game = service()
    game.request("t1", "alice", "s1", "s2", {"sword": 2, "ore": 3}, 0)
    game.commit("t1", "alice", 5)
    assert game.state()["inventories"]["alice"] == {"sword": 2, "ore": 3}


def test_commit_fails_when_target_filled_meanwhile():
    servers = {
        "s1": {"capacity": 3, "players": ["alice", "bob"]},
        "s2": {"capacity": 2, "players": ["cara"]},
    }
    game = st.ServerTransfer(servers, weights={"sword": 1, "ore": 1}, bound=set())
    game.request("t1", "alice", "s1", "s2", {"sword": 1}, 0)
    game.request("t2", "bob", "s1", "s2", {"ore": 1}, 0)
    game.commit("t1", "alice", 1)
    with pytest.raises(ValueError):
        game.commit("t2", "bob", 2)
    assert game.state()["transfers"]["t2"]["status"] == "pending"


def test_cooldown_blocks_second_request():
    game = service()
    game.request("t1", "alice", "s1", "s2", {"sword": 1}, 0)
    game.commit("t1", "alice", 10)
    with pytest.raises(ValueError):
        game.request("t2", "alice", "s2", "s1", {"sword": 1}, 50)


def test_cooldown_expires():
    game = service()
    game.request("t1", "alice", "s1", "s2", {"sword": 1}, 0)
    game.commit("t1", "alice", 10)
    game.request("t2", "alice", "s2", "s1", {"sword": 1}, 110)
    assert game.state()["transfers"]["t2"]["status"] == "pending"


def test_cancel_allows_immediate_new_request():
    game = service()
    game.request("t1", "alice", "s1", "s2", {"sword": 1}, 0)
    game.cancel("t1", "alice", 1)
    game.request("t2", "alice", "s1", "s2", {"sword": 1}, 2)
    assert game.state()["transfers"]["t2"]["status"] == "pending"


def test_commit_after_cancel_is_rejected():
    game = service()
    game.request("t1", "alice", "s1", "s2", {"sword": 1}, 0)
    game.cancel("t1", "alice", 1)
    with pytest.raises(ValueError):
        game.commit("t1", "alice", 2)


def test_overweight_inventory_is_rejected():
    game = service()
    with pytest.raises(ValueError):
        game.request("t1", "alice", "s1", "s2", {"sword": 11}, 0)


def test_bound_item_is_rejected():
    game = service()
    with pytest.raises(ValueError):
        game.request("t1", "alice", "s1", "s2", {"relic": 1}, 0)
