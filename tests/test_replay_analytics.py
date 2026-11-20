import pytest

import replay_analytics as ra

REPLAYS = {
    "r1": {
        "duration": 100,
        "keyframes": [0, 20, 40, 60, 80, 100],
        "events": [
            {"t": 5, "type": "kill", "x": 3, "y": 7},
            {"t": 25, "type": "kill", "x": 12, "y": 7},
            {"t": 30, "type": "chat"},
            {"t": 55, "type": "death", "x": 3, "y": 7},
        ],
    },
    "r2": {
        "duration": 60,
        "keyframes": [0, 30, 60],
        "events": [{"t": 10, "type": "kill", "x": 3, "y": 7}],
    },
}


def analytics(**cfg):
    base = {"bucket": 10, "max_bookmarks": 2}
    base.update(cfg)
    replays = {}
    for rid, data in REPLAYS.items():
        replays[rid] = {
            "duration": data["duration"],
            "keyframes": list(data["keyframes"]),
            "events": [dict(e) for e in data["events"]],
        }
    return ra.ReplayAnalytics(replays, base)


def test_seek_finds_previous_keyframe():
    res = analytics().seek("r1", 30)
    assert res["keyframe"] == 20
    assert res["t"] == 30
    assert res["replay_cost"] == 10
    assert res["clamped"] is False


def test_seek_exact_keyframe_has_zero_cost():
    res = analytics().seek("r1", 40)
    assert res["keyframe"] == 40
    assert res["replay_cost"] == 0


def test_seek_clamps_past_duration():
    res = analytics().seek("r1", 150)
    assert res["t"] == 100
    assert res["keyframe"] == 100
    assert res["replay_cost"] == 0
    assert res["clamped"] is True


def test_seek_rejects_bad_input():
    a = analytics()
    with pytest.raises(ValueError):
        a.seek("r1", -1)
    with pytest.raises(ValueError):
        a.seek("nope", 10)


def test_bookmarks_sorted_by_time():
    a = analytics()
    a.bookmark("r1", "b1", 50, "late", "alice")
    a.bookmark("r1", "b2", 10, "early", "alice")
    assert [x["bookmark_id"] for x in a.bookmarks("r1")] == ["b2", "b1"]


def test_duplicate_bookmark_id_rejected():
    a = analytics()
    a.bookmark("r1", "b1", 10, "one", "alice")
    with pytest.raises(ValueError):
        a.bookmark("r2", "b1", 20, "two", "alice")


def test_bookmark_time_out_of_range_rejected():
    a = analytics()
    with pytest.raises(ValueError):
        a.bookmark("r1", "b1", 101, "late", "alice")
    with pytest.raises(ValueError):
        a.bookmark("r1", "b2", -5, "early", "alice")


def test_bookmark_cap_per_player():
    a = analytics()
    a.bookmark("r1", "b1", 10, "one", "alice")
    a.bookmark("r1", "b2", 20, "two", "alice")
    with pytest.raises(ValueError):
        a.bookmark("r1", "b3", 30, "three", "alice")
    a.bookmark("r1", "b4", 40, "other", "bob")


def test_remove_bookmark_requires_owner():
    a = analytics()
    a.bookmark("r1", "b1", 10, "one", "alice")
    with pytest.raises(ValueError):
        a.remove_bookmark("r1", "b1", "bob")


def test_remove_frees_capacity():
    a = analytics()
    a.bookmark("r1", "b1", 10, "one", "alice")
    a.bookmark("r1", "b2", 20, "two", "alice")
    a.remove_bookmark("r1", "b1", "alice")
    a.bookmark("r1", "b3", 30, "three", "alice")
    assert len(a.bookmarks("r1")) == 2


def test_heatmap_buckets_positions():
    assert analytics().heatmap("r1") == {"0,0": 2, "1,0": 1}


def test_heatmap_filters_time_window():
    assert analytics().heatmap("r1", window=(20, 60)) == {"0,0": 1, "1,0": 1}


def test_heatmap_all_replays_aggregate():
    assert analytics().heatmap() == {"0,0": 3, "1,0": 1}


def test_heatmap_rejects_bad_parameters():
    a = analytics()
    with pytest.raises(ValueError):
        a.heatmap("r1", bucket=0)
    with pytest.raises(ValueError):
        a.heatmap("r1", window=(60, 20))
    with pytest.raises(ValueError):
        a.heatmap("nope")


def test_state_is_a_copy():
    a = analytics()
    a.bookmark("r1", "b1", 10, "one", "alice")
    st = a.state()
    st["bookmarks"]["r1"][0]["note"] = "changed"
    assert a.bookmarks("r1")[0]["note"] == "one"
