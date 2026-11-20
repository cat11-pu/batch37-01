import pytest

import match_spectator as ms


def hub(slots=4, delay=90):
    return ms.SpectatorHub(slots, delay)


def opened(slots=4, delay=90):
    game = hub(slots, delay)
    game.open_match("m1", 0)
    return game


def test_open_match_registers_room():
    assert "m1" in opened().state()["matches"]


def test_duplicate_match_rejected():
    game = opened()
    with pytest.raises(ValueError):
        game.open_match("m1", 5)


def test_negative_start_rejected():
    with pytest.raises(ValueError):
        hub().open_match("m1", -1)


def test_join_unknown_match_rejected():
    with pytest.raises(ValueError):
        hub().join("ghost", "viewer1")


def test_join_records_role():
    game = opened()
    game.join("m1", "viewer1")
    assert game.state()["matches"]["m1"]["viewers"]["viewer1"] == "viewer"


def test_duplicate_join_rejected():
    game = opened()
    game.join("m1", "viewer1")
    with pytest.raises(ValueError):
        game.join("m1", "viewer1", "referee")


def test_unknown_role_rejected():
    game = opened()
    with pytest.raises(ValueError):
        game.join("m1", "viewer1", "bot")


def test_viewer_slots_enforced():
    game = opened(slots=1)
    game.join("m1", "viewer1")
    with pytest.raises(ValueError):
        game.join("m1", "viewer2")


def test_referee_does_not_take_viewer_slot():
    game = opened(slots=1)
    game.join("m1", "ref1", "referee")
    game.join("m1", "viewer1")
    assert game.state()["matches"]["m1"]["viewers"]["viewer1"] == "viewer"


def test_viewer_delay_is_applied():
    game = opened()
    game.join("m1", "viewer1")
    assert game.visible_time("m1", "viewer1", 100) == 10


def test_viewer_delay_floor_is_zero():
    game = opened()
    game.join("m1", "viewer1")
    assert game.visible_time("m1", "viewer1", 30) == 0


def test_referee_sees_live_time():
    game = opened()
    game.join("m1", "ref1", "referee")
    assert game.visible_time("m1", "ref1", 100) == 100


def test_leave_removes_viewer():
    game = opened()
    game.join("m1", "viewer1")
    game.leave("m1", "viewer1")
    assert "viewer1" not in game.state()["matches"]["m1"]["viewers"]


def test_kick_requires_admin():
    game = opened()
    game.join("m1", "viewer1")
    game.join("m1", "viewer2")
    with pytest.raises(ValueError):
        game.kick("m1", "viewer1", "viewer2")


def test_admin_kick_removes_target():
    game = opened()
    game.join("m1", "admin1", "admin")
    game.join("m1", "viewer1")
    game.kick("m1", "admin1", "viewer1")
    assert "viewer1" not in game.state()["matches"]["m1"]["viewers"]
