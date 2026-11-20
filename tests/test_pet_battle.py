import pytest

import pet_battle as pb

PETS = {
    "flame": {"hp": 60, "atk": 12, "def": 4, "speed": 9},
    "tide": {"hp": 70, "atk": 10, "def": 6, "speed": 7},
    "leaf": {"hp": 50, "atk": 8, "def": 3, "speed": 9},
    "rock": {"hp": 45, "atk": 2, "def": 40, "speed": 1},
    "spark": {"hp": 10, "atk": 10, "def": 0, "speed": 5},
    "moss": {"hp": 10, "atk": 3, "def": 0, "speed": 4},
}
SKILLS = {
    "strike": {"power": 4, "cooldown": 0},
    "heavy": {"power": 10, "cooldown": 2},
}


def arena():
    return pb.PetBattle(
        {k: dict(v) for k, v in PETS.items()},
        {k: dict(v) for k, v in SKILLS.items()},
    )


def test_start_sets_full_hp_and_first_turn():
    b = arena()
    assert b.start("flame", "tide") == "b1"
    assert b.hp("b1", "flame") == 60
    assert b.hp("b1", "tide") == 70
    assert b.turn("b1") == "flame"
    assert b.state()["battles"]["b1"]["round"] == 1


def test_start_rejects_same_pet():
    b = arena()
    with pytest.raises(ValueError):
        b.start("flame", "flame")


def test_start_rejects_unknown_pet():
    b = arena()
    with pytest.raises(ValueError):
        b.start("flame", "ghost")


def test_out_of_turn_and_unknown_skill_are_rejected():
    b = arena()
    b.start("flame", "tide")
    with pytest.raises(ValueError):
        b.act("b1", "tide", "strike")
    with pytest.raises(ValueError):
        b.act("b1", "flame", "meteor")
    assert b.turn("b1") == "flame"


def test_strike_uses_stats_and_skill_power():
    b = arena()
    b.start("flame", "tide")
    got = b.act("b1", "flame", "strike")
    assert got["damage"] == 10
    assert got["target"] == "tide"
    assert got["hp"] == 60
    assert got["winner"] is None
    assert got["next"] == "tide"
    assert b.hp("b1", "tide") == 60


def test_damage_never_drops_below_one():
    b = arena()
    b.start("rock", "tide")
    assert b.turn("b1") == "tide"
    got = b.act("b1", "tide", "strike")
    assert got["damage"] == 1
    assert b.hp("b1", "rock") == 44


def test_turn_order_alternates_by_speed():
    b = arena()
    b.start("flame", "tide")
    b.act("b1", "flame", "strike")
    assert b.turn("b1") == "tide"
    b.act("b1", "tide", "strike")
    assert b.turn("b1") == "flame"
    assert b.state()["battles"]["b1"]["round"] == 2


def test_heavy_skill_starts_cooldown():
    b = arena()
    b.start("flame", "tide")
    got = b.act("b1", "flame", "heavy")
    assert got["damage"] == 16
    assert b.hp("b1", "tide") == 54
    assert b.cooldown("b1", "flame", "heavy") == 2


def test_skill_on_cooldown_is_rejected():
    b = arena()
    b.start("flame", "tide")
    b.act("b1", "flame", "heavy")
    b.act("b1", "tide", "strike")
    with pytest.raises(ValueError):
        b.act("b1", "flame", "heavy")
    assert b.hp("b1", "tide") == 54
    assert b.cooldown("b1", "flame", "heavy") == 2


def test_cooldown_counts_down_after_own_turn():
    b = arena()
    b.start("flame", "tide")
    b.act("b1", "flame", "heavy")
    b.act("b1", "tide", "strike")
    b.act("b1", "flame", "strike")
    assert b.cooldown("b1", "flame", "heavy") == 1
    b.act("b1", "tide", "strike")
    assert b.cooldown("b1", "flame", "heavy") == 1


def test_cooldown_expires_on_third_own_turn():
    b = arena()
    b.start("flame", "tide")
    b.act("b1", "flame", "heavy")
    b.act("b1", "tide", "strike")
    b.act("b1", "flame", "strike")
    b.act("b1", "tide", "strike")
    with pytest.raises(ValueError):
        b.act("b1", "flame", "heavy")
    assert b.cooldown("b1", "flame", "heavy") == 1
    b.act("b1", "flame", "strike")
    assert b.cooldown("b1", "flame", "heavy") == 0
    b.act("b1", "tide", "strike")
    got = b.act("b1", "flame", "heavy")
    assert got["damage"] == 16
    assert b.hp("b1", "tide") == 18


def test_battle_ends_when_hp_reaches_zero():
    b = arena()
    b.start("spark", "moss")
    assert b.turn("b1") == "spark"
    got = b.act("b1", "spark", "strike")
    assert got["damage"] == 14
    assert got["winner"] == "spark"
    assert b.hp("b1", "moss") == 0
    assert b.turn("b1") is None
    assert b.state()["battles"]["b1"]["status"] == "finished"


def test_actions_after_finish_are_rejected():
    b = arena()
    b.start("spark", "moss")
    b.act("b1", "spark", "strike")
    with pytest.raises(ValueError):
        b.act("b1", "moss", "strike")


def test_pet_cannot_join_two_battles():
    b = arena()
    b.start("flame", "tide")
    with pytest.raises(ValueError):
        b.start("flame", "leaf")


def test_state_is_a_copy():
    b = arena()
    b.start("flame", "tide")
    b.act("b1", "flame", "strike")
    snap = b.state()
    snap["battles"]["b1"]["hp"]["tide"] = 1
    snap["battles"]["b1"]["round"] = 99
    assert b.hp("b1", "tide") == 60
    assert b.state()["battles"]["b1"]["round"] == 1
