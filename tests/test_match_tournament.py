import pytest

import match_tournament as mt


def tourney():
    return mt.MatchTournament(window=100)


def queue_four(t):
    t.enqueue("a", 1000)
    t.enqueue("b", 1010)
    t.enqueue("c", 1020)
    t.enqueue("d", 1030)


def test_duplicate_enqueue_is_rejected():
    t = tourney()
    t.enqueue("a", 1000)
    with pytest.raises(ValueError):
        t.enqueue("a", 1000)
    assert t.state()["queue"] == ["a"]


def test_negative_rating_and_blank_name_are_rejected():
    t = tourney()
    with pytest.raises(ValueError):
        t.enqueue("a", -1)
    with pytest.raises(ValueError):
        t.enqueue(" ", 1000)
    assert t.state()["queue"] == []


def test_pair_respects_rating_window():
    t = tourney()
    t.enqueue("a", 1000)
    t.enqueue("b", 1050)
    t.enqueue("c", 1400)
    assert t.pair() == [("a", "b")]
    assert t.state()["queue"] == ["c"]


def test_window_boundary_is_inclusive():
    t = tourney()
    t.enqueue("a", 1000)
    t.enqueue("b", 1100)
    t.enqueue("c", 1201)
    assert t.pair() == [("a", "b")]
    assert t.state()["queue"] == ["c"]


def test_leave_removes_queued_player():
    t = tourney()
    t.enqueue("a", 1000)
    t.enqueue("b", 1010)
    t.leave("a")
    assert t.pair() == []
    assert t.state()["queue"] == ["b"]


def test_pair_creates_distinct_match_ids():
    t = tourney()
    queue_four(t)
    pairs = t.pair()
    assert pairs == [("a", "b"), ("c", "d")]
    ids = list(t.state()["matches"].keys())
    assert ids == ["m1", "m2"]


def test_start_requires_power_of_two_bracket():
    t = tourney()
    for name, rating in [("a", 1000), ("b", 1001), ("c", 1002), ("d", 1003), ("e", 1004), ("f", 1005)]:
        t.enqueue(name, rating)
    pairs = t.pair()
    assert len(pairs) == 3
    with pytest.raises(ValueError):
        t.start()


def test_start_rejects_unpaired_queue():
    t = tourney()
    t.enqueue("a", 1000)
    t.enqueue("b", 1001)
    with pytest.raises(ValueError):
        t.start()


def test_start_builds_bracket_rounds():
    t = tourney()
    queue_four(t)
    t.pair()
    info = t.start()
    assert info == {"size": 4, "rounds": 2}
    assert t.state()["bracket"]["rounds"] == [["m1", "m2"], []]


def test_report_before_start_is_rejected():
    t = tourney()
    queue_four(t)
    t.pair()
    with pytest.raises(ValueError):
        t.report("m1", "a")


def test_report_with_unknown_winner_is_rejected():
    t = tourney()
    queue_four(t)
    t.pair()
    t.start()
    with pytest.raises(ValueError):
        t.report("m1", "ghost")
    assert t.state()["matches"]["m1"]["winner"] is None


def test_match_cannot_be_reported_twice():
    t = tourney()
    queue_four(t)
    t.pair()
    t.start()
    t.report("m1", "a")
    with pytest.raises(ValueError):
        t.report("m1", "b")


def test_winners_advance_and_final_is_created():
    t = tourney()
    queue_four(t)
    t.pair()
    t.start()
    t.report("m1", "a")
    assert sorted(t.state()["matches"]) == ["m1", "m2"]
    t.report("m2", "c")
    s = t.state()
    assert s["bracket"]["rounds"] == [["m1", "m2"], ["m3"]]
    assert (s["matches"]["m3"]["a"], s["matches"]["m3"]["b"]) == ("a", "c")


def test_champion_and_placement_rewards():
    t = tourney()
    queue_four(t)
    t.pair()
    t.start()
    t.report("m1", "a")
    t.report("m2", "c")
    t.report("m3", "a")
    s = t.state()
    assert s["bracket"]["champion"] == "a"
    assert s["bracket"]["finished"] is True
    assert t.reward("a") == 100
    assert t.reward("c") == 50
    assert t.reward("b") == 20
    assert t.reward("d") == 20


def test_state_is_a_copy():
    t = tourney()
    queue_four(t)
    t.pair()
    snap = t.state()
    snap["queue"].append("zz")
    snap["matches"]["m1"]["winner"] = "zz"
    assert t.state()["queue"] == []
    assert t.state()["matches"]["m1"]["winner"] is None
