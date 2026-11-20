import pytest

import hit_rewind as hr


def rewind(history=8):
    return hr.HitRewind(history)


def test_static_hit():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (3.0, 4.0)})
    result = game.register(1, "a", "b", 100.0, 5.0)
    assert result["hit"] is True


def test_static_miss():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (3.0, 4.0)})
    result = game.register(1, "a", "b", 100.0, 4.9)
    assert result["hit"] is False


def test_travel_tick_reported():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (10.0, 0.0)})
    result = game.register(1, "a", "b", 5.0, 1.0)
    assert result["tick"] == 3


def test_moving_target_uses_hit_tick_position():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (10.0, 0.0)})
    game.record(3, {"a": (0.0, 0.0), "b": (20.0, 0.0)})
    result = game.register(1, "a", "b", 5.0, 1.0)
    assert result["hit"] is False


def test_moving_target_can_be_hit():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (10.0, 0.0)})
    game.record(3, {"a": (0.0, 0.0), "b": (10.0, 0.0)})
    assert game.register(1, "a", "b", 5.0, 1.0)["hit"] is True


def test_blocked_tick_misses():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (10.0, 0.0)}, blocked=[3])
    result = game.register(1, "a", "b", 5.0, 1.0)
    assert result["hit"] is False


def test_missing_hit_tick_uses_latest_prior():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (10.0, 0.0)})
    game.record(2, {"a": (0.0, 0.0), "b": (10.0, 0.0)})
    assert game.register(1, "a", "b", 5.0, 1.0)["hit"] is True


def test_missing_attacker_raises():
    game = rewind()
    game.record(1, {"b": (10.0, 0.0)})
    with pytest.raises(ValueError):
        game.register(1, "a", "b", 5.0, 1.0)


def test_missing_target_raises():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0)})
    with pytest.raises(ValueError):
        game.register(1, "a", "b", 5.0, 1.0)


def test_invalid_speed_raises():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (1.0, 0.0)})
    with pytest.raises(ValueError):
        game.register(1, "a", "b", 0.0, 1.0)


def test_negative_radius_raises():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (1.0, 0.0)})
    with pytest.raises(ValueError):
        game.register(1, "a", "b", 1.0, -1.0)


def test_duplicate_tick_raises():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0)})
    with pytest.raises(ValueError):
        game.record(1, {"a": (0.0, 0.0)})


def test_history_is_pruned():
    game = rewind(history=1)
    game.record(1, {"a": (0.0, 0.0), "b": (1.0, 0.0)})
    game.record(2, {"a": (0.0, 0.0), "b": (1.0, 0.0)})
    with pytest.raises(ValueError):
        game.register(1, "a", "b", 1.0, 1.0)


def test_state_returns_a_copy():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0)})
    snapshot = game.state()
    snapshot["frames"][1]["a"] = (99.0, 99.0)
    assert game.state()["frames"][1]["a"] == (0.0, 0.0)


def test_register_does_not_mutate_history():
    game = rewind()
    game.record(1, {"a": (0.0, 0.0), "b": (1.0, 0.0)})
    before = game.state()
    assert before["frames"][1]["a"] == (0.0, 0.0)
    game.register(1, "a", "b", 1.0, 1.0)
    assert game.state() == before
