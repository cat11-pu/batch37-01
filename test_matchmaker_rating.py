import pytest

import matchmaker_rating as mr


def matchmaker(team_size=2, max_gap=100, wait_widen=10):
    return mr.Matchmaker(team_size, max_gap, wait_widen)


def enqueue_two(game, now=0):
    game.enqueue("a", 1000, now=now)
    game.enqueue("b", 1010, now=now)


def test_two_solo_players_match():
    game = matchmaker()
    enqueue_two(game)
    result = game.pop(0)
    assert result["teams"] == [["a"], ["b"]]
    assert result["rating_diff"] == pytest.approx(10)


def test_one_player_does_not_match():
    game = matchmaker()
    game.enqueue("a", 1000)
    assert len(game.state()) == 1
    assert game.pop(0) is None


def test_rating_gap_blocks_match():
    game = matchmaker(max_gap=10)
    game.enqueue("a", 1000)
    game.enqueue("b", 1200)
    assert len(game.state()) == 2
    assert game.pop(0) is None


def test_waiting_widens_rating_gap():
    game = matchmaker(max_gap=10, wait_widen=10)
    game.enqueue("a", 1000)
    game.enqueue("b", 1200)
    assert game.pop(20)["teams"] == [["a"], ["b"]]


def test_party_stays_on_same_team():
    game = matchmaker(team_size=4)
    game.enqueue("a", 1000, party="duo")
    game.enqueue("b", 1000, party="duo")
    game.enqueue("c", 1000)
    game.enqueue("d", 1000)
    result = game.pop(0)
    team = next(t for t in result["teams"] if "a" in t)
    assert set(team) == {"a", "b"}


def test_party_larger_than_team_raises():
    game = matchmaker(team_size=2)
    game.enqueue("a", 1000, party="trio")
    with pytest.raises(ValueError):
        game.enqueue("b", 1000, party="trio")
        game.enqueue("c", 1000, party="trio")


def test_party_must_include_player():
    game = matchmaker(team_size=4)
    with pytest.raises(ValueError):
        game.enqueue("a", 1000, party=["b"])


def test_duplicate_player_raises():
    game = matchmaker()
    game.enqueue("a", 1000)
    with pytest.raises(ValueError):
        game.enqueue("a", 1000)


def test_match_removes_players():
    game = matchmaker()
    enqueue_two(game)
    result = game.pop(0)
    assert result is not None
    assert game.state() == []


def test_older_players_are_selected_first():
    game = matchmaker(team_size=1)
    game.enqueue("old", 1000, now=0)
    game.enqueue("new", 1000, now=5)
    result = game.pop(10)
    assert result["teams"] == [["old"], ["new"]]


def test_tie_breaks_by_player_id():
    game = matchmaker(team_size=1)
    game.enqueue("b", 1000, now=0)
    game.enqueue("a", 1000, now=0)
    result = game.pop(0)
    assert result["teams"] == [["a"], ["b"]]


def test_state_returns_a_copy():
    game = matchmaker()
    game.enqueue("a", 1000)
    snapshot = game.state()
    snapshot[0]["player"] = "hacked"
    assert game.state()[0]["player"] == "a"


def test_invalid_rating_raises():
    game = matchmaker()
    with pytest.raises(ValueError):
        game.enqueue("a", float("nan"))


def test_invalid_team_size_raises():
    with pytest.raises(ValueError):
        mr.Matchmaker(0, 100, 10)


def test_exact_team_size_is_enforced():
    game = matchmaker(team_size=3)
    game.enqueue("a", 1000)
    game.enqueue("b", 1000)
    game.enqueue("c", 1000)
    game.enqueue("d", 1000)
    game.enqueue("e", 1000)
    game.enqueue("f", 1000)
    result = game.pop(0)
    assert sorted(len(t) for t in result["teams"]) == [3, 3]
