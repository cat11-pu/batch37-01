import pytest

import audio_event_queue as aq


def queue(budget=4, window=2):
    return aq.AudioEventQueue(budget, window)


def event(event_id="e1", kind="sfx", priority=0, volume=1.0):
    return {"id": event_id, "kind": kind, "priority": priority, "volume": volume}


def test_push_accepts_event():
    assert queue().push(event(), 0) is True


def test_drain_returns_event():
    game = queue()
    game.push(event(), 0)
    assert game.drain(0)[0]["id"] == "e1"


def test_budget_limits_drain():
    game = queue(budget=1)
    game.push(event("a"), 0)
    game.push(event("b", priority=5), 0)
    assert [e["id"] for e in game.drain(0)] == ["b"]


def test_priority_sort():
    game = queue()
    game.push(event("low", priority=0), 0)
    game.push(event("high", priority=5), 0)
    assert [e["id"] for e in game.drain(0)] == ["high", "low"]


def test_same_priority_sorts_by_id():
    game = queue()
    game.push(event("b"), 0)
    game.push(event("a"), 0)
    assert [e["id"] for e in game.drain(0)] == ["a", "b"]


def test_duplicate_within_window_is_dropped():
    game = queue(window=2)
    game.push(event(), 0)
    assert game.push(event(), 1) is False
    assert len(game.drain(1)) == 1


def test_duplicate_after_window_is_accepted():
    game = queue(window=1)
    game.push(event(), 0)
    assert game.push(event(), 2) is True


def test_expired_event_is_dropped():
    game = queue(window=2)
    game.push(event(), 0)
    assert game.drain(5) == []
    assert game.state()["events"] == []


def test_pause_blocks_drain():
    game = queue()
    game.push(event(), 0)
    game.pause()
    assert game.state()["paused"] is True
    assert game.drain(0) == []


def test_resume_drains_queued_events():
    game = queue()
    game.push(event(), 0)
    game.pause()
    game.resume()
    assert len(game.drain(0)) == 1


def test_invalid_id_raises():
    with pytest.raises(ValueError):
        queue().push(event(""), 0)


def test_invalid_priority_raises():
    with pytest.raises(ValueError):
        queue().push(event(priority=1.5), 0)


def test_invalid_volume_raises():
    with pytest.raises(ValueError):
        queue().push(event(volume=1.5), 0)


def test_state_returns_a_copy():
    game = queue()
    game.push(event(), 0)
    snapshot = game.state()
    snapshot["events"][0]["id"] = "hacked"
    assert game.state()["events"][0]["id"] == "e1"


def test_push_while_paused_is_queued():
    game = queue()
    game.pause()
    assert game.push(event(), 0) is True
    game.resume()
    assert len(game.drain(0)) == 1
