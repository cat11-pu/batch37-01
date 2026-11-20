import pytest

import ping_compensation as pc


def buffer(max_samples=8, max_ticks=64):
    return pc.NetcodeBuffer(max_samples, max_ticks)


def test_record_keeps_sample():
    game = buffer()
    game.record(1, 40, 0)
    assert game.state()["samples"][0]["rtt"] == 40


def test_sequence_must_increase():
    game = buffer()
    game.record(2, 40, 0)
    with pytest.raises(ValueError):
        game.record(2, 50, 1)


def test_rtt_must_be_positive():
    with pytest.raises(ValueError):
        buffer().record(1, 0, 0)


def test_sample_time_must_not_go_backwards():
    game = buffer()
    game.record(1, 40, 10)
    with pytest.raises(ValueError):
        game.record(2, 50, 9)


def test_first_smoothed_equals_sample():
    game = buffer()
    game.record(1, 40, 0)
    assert game.smoothed_rtt() == 40.0


def test_ewma_blends_samples():
    game = buffer()
    game.record(1, 40, 0)
    game.record(2, 80, 1)
    assert game.smoothed_rtt() == 50.0


def test_window_keeps_recent_samples():
    game = buffer(3, 64)
    for seq in range(1, 6):
        game.record(seq, 40, seq)
    samples = game.state()["samples"]
    assert len(samples) == 3
    assert samples[0]["seq"] == 3


def test_jitter_is_mean_difference():
    game = buffer()
    game.record(1, 40, 0)
    game.record(2, 60, 1)
    game.record(3, 50, 2)
    assert game.jitter() == 15.0


def test_jitter_single_sample_is_zero():
    game = buffer()
    game.record(1, 40, 0)
    assert game.jitter() == 0.0


def test_compensation_formula():
    game = buffer()
    game.record(1, 40, 0)
    game.record(2, 80, 1)
    assert game.compensation_ms() == 130.0


def test_compensation_is_capped():
    game = buffer()
    game.record(1, 400, 0)
    game.record(2, 400, 1)
    assert game.compensation_ms() == 250.0


def test_duplicate_input_tick_rejected():
    game = buffer()
    game.push_input(10, "move")
    with pytest.raises(ValueError):
        game.push_input(10, "jump")


def test_replay_returns_sorted_range():
    game = buffer()
    game.push_input(12, "c")
    game.push_input(10, "a")
    game.push_input(11, "b")
    assert game.replay(10, 12) == [(10, "a"), (11, "b"), (12, "c")]


def test_replay_invalid_range_rejected():
    with pytest.raises(ValueError):
        buffer().replay(5, 4)


def test_state_returns_a_copy():
    game = buffer()
    game.record(1, 40, 0)
    game.push_input(3, "move")
    snapshot = game.state()
    snapshot["samples"][0]["rtt"] = 999
    snapshot["inputs"][3] = "hack"
    assert game.state()["samples"][0]["rtt"] == 40
    assert game.state()["inputs"][3] == "move"
