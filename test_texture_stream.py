import pytest

import texture_stream as ts


def streamer(budget=10):
    return ts.TextureStreamer(budget)


def test_loads_texture_within_budget():
    game = streamer()
    game.request("a", 3, priority=1)
    result = game.tick()
    assert result["loaded"] == ["a"]
    assert game.resident() == ["a"]


def test_loads_higher_priority_first():
    game = streamer()
    game.request("low", 2, priority=0)
    game.request("high", 2, priority=5)
    assert game.tick()["loaded"] == ["high", "low"]


def test_evicts_low_priority_to_fit_high():
    game = streamer(4)
    game.request("low", 3, priority=0)
    game.tick()
    game.request("high", 3, priority=5)
    result = game.tick()
    assert result["evicted"] == ["low"]
    assert game.resident() == ["high"]


def test_pinned_texture_is_not_evicted():
    game = streamer(4)
    game.request("ui", 3, priority=0, pinned=True)
    game.tick()
    game.request("high", 3, priority=5)
    result = game.tick()
    assert result["evicted"] == []
    assert result["deferred"] == ["high"]


def test_oversized_texture_is_deferred():
    game = streamer(2)
    game.request("huge", 3)
    assert game.tick()["deferred"] == ["huge"]


def test_request_updates_priority():
    game = streamer(4)
    game.request("a", 3, priority=0)
    game.tick()
    game.request("b", 3, priority=1)
    game.request("a", 3, priority=9)
    result = game.tick()
    assert result["evicted"] == ["b"]
    assert game.resident() == ["a"]


def test_cancel_before_tick_removes_request():
    game = streamer()
    game.request("a", 3)
    game.cancel("a")
    assert game.tick()["loaded"] == []


def test_cancel_unknown_raises():
    with pytest.raises(ValueError):
        streamer().cancel("missing")


def test_budget_exact_fit_loads():
    game = streamer(3)
    game.request("a", 3)
    assert game.tick()["loaded"] == ["a"]


def test_eviction_tie_breaks_by_id():
    game = streamer(3)
    game.request("b", 2, priority=0)
    game.request("a", 2, priority=0)
    game.tick()
    game.request("c", 2, priority=5)
    result = game.tick()
    assert result["evicted"] == ["a"]


def test_resident_returns_a_copy():
    game = streamer()
    game.request("a", 3)
    game.tick()
    snapshot = game.resident()
    snapshot.append("x")
    assert game.resident() == ["a"]


def test_invalid_size_raises():
    with pytest.raises(ValueError):
        streamer().request("a", 0)


def test_invalid_priority_raises():
    with pytest.raises(ValueError):
        streamer().request("a", 1, priority=1.5)


def test_duplicate_request_does_not_double_count():
    game = streamer(5)
    game.request("a", 3)
    game.request("a", 3)
    game.tick()
    assert game.resident() == ["a"]


def test_tick_reports_loaded_evicted_and_deferred():
    game = streamer(4)
    game.request("a", 3, priority=0)
    game.tick()
    game.request("b", 3, priority=5)
    game.request("c", 9, priority=9)
    result = game.tick()
    assert result["loaded"] == ["b"]
    assert result["evicted"] == ["a"]
    assert result["deferred"] == ["c"]
