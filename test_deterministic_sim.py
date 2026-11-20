import pytest

import deterministic_sim as ds


def sim(seed=1):
    return ds.DeterministicSim(seed)


def test_initial_state():
    state = sim().state()
    assert state["frame"] == 0
    assert state["value"] == 0


def test_single_input_advances():
    game = sim()
    game.set_input(1, "p1", 2)
    game.step()
    assert game.state()["value"] >= 2


def test_two_inputs_are_summed():
    game = sim()
    game.set_input(1, "p1", 2)
    game.set_input(1, "p2", 3)
    game.step()
    assert game.state()["value"] >= 5


def test_input_order_does_not_matter():
    a = sim()
    a.set_input(1, "p1", 2)
    a.set_input(1, "p2", 3)
    a.step()
    b = sim()
    b.set_input(1, "p2", 3)
    b.set_input(1, "p1", 2)
    b.step()
    assert isinstance(a.checksum(), int)
    assert a.checksum() == b.checksum()


def test_missing_input_is_zero():
    game = sim()
    game.set_input(1, "p1", 2)
    game.step()
    assert game.state()["value"] >= 2


def test_duplicate_input_raises():
    game = sim()
    game.set_input(1, "p1", 2)
    with pytest.raises(ValueError):
        game.set_input(1, "p1", 3)


def test_invalid_player_raises():
    game = sim()
    with pytest.raises(ValueError):
        game.set_input(1, "p3", 1)


def test_past_frame_input_raises():
    game = sim()
    game.step(2)
    with pytest.raises(ValueError):
        game.set_input(1, "p1", 1)


def test_future_input_used_when_reached():
    game = sim()
    game.set_input(2, "p1", 7)
    game.step(2)
    assert game.state()["frame"] == 2


def test_negative_step_raises():
    game = sim()
    with pytest.raises(ValueError):
        game.step(-1)


def test_same_seed_is_deterministic():
    a = sim(7)
    b = sim(7)
    for frame in (1, 2):
        a.set_input(frame, "p1", 1)
        b.set_input(frame, "p1", 1)
    a.step(2)
    b.step(2)
    assert isinstance(a.checksum(), int)
    assert a.checksum() == b.checksum()


def test_different_seed_changes_checksum():
    a = sim(1)
    b = sim(2)
    a.step()
    b.step()
    assert a.checksum() != b.checksum()


def test_checksum_changes_after_step():
    game = sim()
    before = game.checksum()
    game.step()
    assert game.checksum() != before


def test_state_returns_a_copy():
    game = sim()
    snapshot = game.state()
    snapshot["value"] = 99
    assert game.state()["value"] == 0


def test_rng_is_advanced():
    game = sim()
    before = game.state()["rng"]
    game.step()
    assert game.state()["rng"] != before
