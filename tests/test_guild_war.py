import pytest

import guild_war as gw

NODES = {
    "north": {"value": 100, "defense": 50},
    "south": {"value": 40, "defense": 10},
}


def war():
    return gw.GuildWar({k: dict(v) for k, v in NODES.items()}, lock_seconds=100)


def test_initial_state():
    s = war().state()
    assert s["owners"] == {}
    assert s["settled"] is False


def test_attack_captures_node():
    game = war()
    game.attack("red", "north", 50, 0)
    assert game.state()["owners"]["north"] == "red"


def test_attack_below_defense_raises():
    game = war()
    with pytest.raises(ValueError):
        game.attack("red", "north", 49, 0)


def test_attack_unknown_node_raises():
    game = war()
    with pytest.raises(ValueError):
        game.attack("red", "east", 50, 0)


def test_attack_own_node_raises():
    game = war()
    game.attack("red", "north", 50, 0)
    with pytest.raises(ValueError):
        game.attack("red", "north", 80, 1)


def test_non_positive_power_raises():
    game = war()
    with pytest.raises(ValueError):
        game.attack("red", "north", 0, 0)


def test_score_sums_owned_values():
    game = war()
    game.attack("red", "north", 50, 0)
    game.attack("red", "south", 10, 1)
    assert game.score("red") == 140
    assert game.score("blue") == 0


def test_second_capture_adds_score():
    game = war()
    game.attack("red", "north", 50, 0)
    game.attack("blue", "south", 10, 0)
    assert game.score("red") == 100
    assert game.score("blue") == 40


def test_losing_node_removes_score():
    game = war()
    game.attack("red", "north", 50, 0)
    game.attack("blue", "north", 50, 100)
    assert game.score("red") == 0
    assert game.score("blue") == 100


def test_lock_blocks_rival():
    game = war()
    game.attack("red", "north", 50, 0)
    with pytest.raises(ValueError):
        game.attack("blue", "north", 50, 99)


def test_capture_extends_lock():
    game = war()
    game.attack("red", "north", 50, 0)
    game.attack("blue", "north", 50, 100)
    with pytest.raises(ValueError):
        game.attack("red", "north", 50, 150)
    assert game.state()["owners"]["north"] == "blue"


def test_settle_marks_state_and_scores():
    game = war()
    game.attack("red", "north", 50, 0)
    game.settle()
    s = game.state()
    assert s["settled"] is True
    assert game.score("red") == 100


def test_attack_after_settle_raises():
    game = war()
    game.attack("red", "north", 50, 0)
    game.settle()
    with pytest.raises(ValueError):
        game.attack("blue", "south", 10, 1)


def test_duplicate_settle_raises():
    game = war()
    game.settle()
    with pytest.raises(ValueError):
        game.settle()


def test_state_is_copy():
    game = war()
    game.attack("red", "north", 50, 0)
    snapshot = game.state()
    snapshot["owners"]["north"] = "blue"
    assert game.state()["owners"]["north"] == "red"
