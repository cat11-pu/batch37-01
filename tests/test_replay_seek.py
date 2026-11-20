import pytest

import replay_seek as rs


def sample_states():
    return [
        {"p1": {"hp": 100, "x": 0, "items": ["sword"]}},
        {"p1": {"hp": 90, "x": 1, "items": ["sword"]}},
        {"p1": {"hp": 90, "x": 2, "items": ["sword", "potion"]}, "p2": {"hp": 50}},
        {"p1": {"hp": 80, "x": 3, "items": ["sword", "potion"]}, "p2": {"hp": 40}},
        {"p1": {"hp": 80, "x": 4, "items": ["sword", "potion"]}, "p2": {"hp": 30}},
    ]


def buffer(interval=2):
    b = rs.ReplayBuffer(interval)
    for state in sample_states():
        b.append(state)
    return b


def test_empty_buffer_seek_raises():
    with pytest.raises(IndexError):
        rs.ReplayBuffer(4).seek(0)


def test_append_returns_frame_index():
    b = rs.ReplayBuffer(4)
    assert b.append({"a": 1}) == 0
    assert b.append({"a": 2}) == 1


def test_seek_first_frame():
    assert buffer().seek(0) == sample_states()[0]


def test_seek_last_frame():
    assert buffer().seek(4) == sample_states()[4]


def test_backward_and_forward_seek_are_stable():
    b = buffer()
    before = b.seek(3)
    assert before == sample_states()[3]
    b.seek(1)
    assert b.seek(3) == before


def test_keyframes_follow_interval():
    b = rs.ReplayBuffer(5)
    for i in range(12):
        b.append({"i": i})
    assert b.stats()["keyframes"] == [0, 5, 10]


def test_interval_one_keeps_every_frame():
    b = rs.ReplayBuffer(1)
    for i in range(4):
        b.append({"i": i})
    assert b.stats()["keyframes"] == [0, 1, 2, 3]


def test_removed_key_is_deleted():
    b = rs.ReplayBuffer(3)
    b.append({"hp": 10, "buff": "haste"})
    b.append({"hp": 10})
    assert b.seek(1) == {"hp": 10}
    assert "buff" not in b.seek(1)


def test_nested_value_is_replaced():
    b = rs.ReplayBuffer(3)
    b.append({"p": {"hp": 10, "pos": [0, 0]}})
    b.append({"p": {"hp": 10, "pos": [1, 2]}})
    assert b.seek(1) == {"p": {"hp": 10, "pos": [1, 2]}}


def test_cache_miss_then_hit():
    b = buffer()
    first = b.seek(3)
    after_miss = b.cache_info()
    second = b.seek(3)
    after_hit = b.cache_info()
    assert first == second
    assert after_miss["misses"] >= 1
    assert after_hit["hits"] >= 1


def test_stats_reports_frame_count_and_cache():
    b = buffer()
    b.seek(4)
    stats = b.stats()
    assert stats["frames"] == 5
    assert b.cache_info()["size"] >= 1


def test_returned_state_is_isolated():
    b = buffer()
    state = b.seek(0)
    state["p1"]["hp"] = 1
    state["p1"]["items"].append("hack")
    fresh = b.seek(0)
    assert fresh["p1"]["hp"] == 100
    assert fresh["p1"]["items"] == ["sword"]


def test_two_buffers_reconstruct_identically():
    a = buffer()
    b = buffer()
    assert a.seek(2) == sample_states()[2]
    assert a.seek(2) == b.seek(2)
    assert a.seek(4) == b.seek(4)


def test_invalid_interval_and_state_raise():
    with pytest.raises(ValueError):
        rs.ReplayBuffer(0)
    with pytest.raises(ValueError):
        rs.ReplayBuffer(2).append([1, 2, 3])


def test_out_of_range_seek_raises():
    b = buffer()
    with pytest.raises(IndexError):
        b.seek(-1)
    with pytest.raises(IndexError):
        b.seek(5)
