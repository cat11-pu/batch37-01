import pytest

import tournament_bracket as tb


def bracket(size=4):
    return tb.TournamentBracket(size)


def seeded():
    game = bracket(4)
    game.seed(["p1", "p2", "p3", "p4"])
    return game


def test_size_must_be_power_of_two():
    with pytest.raises(ValueError):
        tb.TournamentBracket(3)


def test_too_few_players_rejected():
    with pytest.raises(ValueError):
        bracket(4).seed(["p1"])


def test_duplicate_players_rejected():
    with pytest.raises(ValueError):
        bracket(4).seed(["p1", "p2", "p1"])


def test_first_round_pairs_top_with_bottom():
    rounds = seeded().state()["rounds"]
    assert len(rounds[0]) == 2
    assert rounds[0][0]["a"] == "p1"
    assert rounds[0][0]["b"] == "p4"


def test_odd_count_creates_bye():
    game = bracket(4)
    game.seed(["p1", "p2", "p3"])
    rounds = game.state()["rounds"]
    assert rounds[0][0]["b"] is None
    assert rounds[1][0]["a"] == "p1"


def test_bye_cannot_be_reported():
    game = bracket(4)
    game.seed(["p1", "p2", "p3"])
    with pytest.raises(ValueError):
        game.report(0, 0, "p1")


def test_report_records_winner():
    game = seeded()
    game.report(0, 0, "p1")
    assert game.state()["rounds"][0][0]["winner"] == "p1"


def test_winner_must_be_participant():
    game = seeded()
    with pytest.raises(ValueError):
        game.report(0, 0, "p3")


def test_report_wrong_round_rejected():
    game = seeded()
    with pytest.raises(ValueError):
        game.report(1, 0, "p1")


def test_double_report_rejected():
    game = seeded()
    game.report(0, 0, "p1")
    with pytest.raises(ValueError):
        game.report(0, 0, "p2")


def test_winners_fill_next_round():
    game = seeded()
    game.report(0, 0, "p1")
    game.report(0, 1, "p2")
    final = game.state()["rounds"][1][0]
    assert final["a"] == "p1"
    assert final["b"] == "p2"


def test_current_round_advances():
    game = seeded()
    game.report(0, 0, "p1")
    assert game.current_round() == 0
    game.report(0, 1, "p2")
    assert game.current_round() == 1


def test_champion_after_final():
    game = seeded()
    game.report(0, 0, "p1")
    game.report(0, 1, "p2")
    game.report(1, 0, "p1")
    assert game.champion() == "p1"
    assert game.current_round() is None


def test_champion_none_before_final():
    game = seeded()
    game.report(0, 0, "p1")
    game.report(0, 1, "p2")
    assert game.current_round() == 1
    assert game.champion() is None


def test_state_returns_a_copy():
    game = seeded()
    snapshot = game.state()
    snapshot["rounds"][0][0]["winner"] = "p4"
    assert game.state()["rounds"][0][0]["winner"] is None
