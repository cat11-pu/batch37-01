import pytest

import physics_island as pi


def manager():
    game = pi.IslandManager()
    for name in ["a", "b", "c", "d"]:
        game.add_body(name, sleeping=True)
    return game


def test_add_body_defaults_to_awake():
    game = pi.IslandManager()
    game.add_body("a")
    assert game.state()["a"] is False


def test_add_body_can_start_sleeping():
    game = pi.IslandManager()
    game.add_body("a", sleeping=True)
    assert game.state()["a"] is True


def test_wake_single_body():
    game = manager()
    game.wake("a")
    assert game.state()["a"] is False


def test_wake_propagates_through_contacts():
    game = manager()
    game.step([("a", "b"), ("b", "c")])
    game.wake("a")
    assert game.state()["b"] is False
    assert game.state()["c"] is False


def test_moving_body_wakes_its_island():
    game = manager()
    game.step([("a", "b"), ("b", "c")], moving=["b"])
    assert game.state()["a"] is False
    assert game.state()["c"] is False


def test_unrelated_island_stays_asleep():
    game = manager()
    game.step([("a", "b")], moving=["a"])
    assert game.state()["c"] is True
    assert game.state()["d"] is True


def test_transitive_island_wakes_all_members():
    game = manager()
    game.step([("a", "b"), ("b", "c"), ("c", "d")], moving=["d"])
    assert len(game.state()) == 4
    assert not any(game.state().values())


def test_no_contacts_wakes_only_moving_body():
    game = manager()
    game.step([], moving=["a"])
    assert game.state() == {"a": False, "b": True, "c": True, "d": True}


def test_remove_body_removes_it():
    game = manager()
    game.remove_body("a")
    assert len(game.state()) == 3
    assert "a" not in game.state()


def test_remove_body_clears_contacts():
    game = manager()
    game.step([("a", "b")])
    game.remove_body("a")
    game.wake("b")
    assert game.state()["b"] is False


def test_duplicate_body_raises():
    game = pi.IslandManager()
    game.add_body("a")
    with pytest.raises(ValueError):
        game.add_body("a")


def test_wake_unknown_body_raises():
    with pytest.raises(ValueError):
        manager().wake("ghost")


def test_invalid_contact_raises():
    game = manager()
    with pytest.raises(ValueError):
        game.step([("a", "ghost")])


def test_moving_unknown_body_raises():
    game = manager()
    with pytest.raises(ValueError):
        game.step([], moving=["ghost"])


def test_state_returns_a_copy():
    game = manager()
    snapshot = game.state()
    snapshot["a"] = False
    assert game.state()["a"] is True
