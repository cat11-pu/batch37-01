import pytest

import world_boss as wb

PHASES = [
    {"threshold": 1.0, "multiplier": 1},
    {"threshold": 0.5, "multiplier": 2},
    {"threshold": 0.2, "multiplier": 3},
]


def boss(pool=1000):
    return wb.WorldBoss(1000, [dict(p) for p in PHASES], pool)


def test_initial_state():
    s = boss().state()
    assert s["hp"] == 1000
    assert s["phase"] == 0
    assert s["alive"] is True


def test_attack_reduces_hp():
    b = boss()
    b.attack("alice", 100, 0)
    assert b.state()["hp"] == 900


def test_contribution_accumulates():
    b = boss()
    b.attack("alice", 100, 0)
    b.attack("alice", 50, 1)
    assert b.state()["contributions"]["alice"] == 150


def test_overkill_counts_remaining_hp_only():
    b = boss()
    b.attack("alice", 900, 0)
    b.attack("bob", 500, 1)
    s = b.state()
    assert s["hp"] == 0
    assert s["contributions"]["bob"] == 100


def test_phase_advances_at_threshold():
    b = boss()
    b.attack("alice", 500, 0)
    assert b.state()["phase"] == 1


def test_phase_multiplier_applies():
    b = boss()
    b.attack("alice", 500, 0)
    b.attack("bob", 100, 1)
    s = b.state()
    assert s["hp"] == 300
    assert s["contributions"]["bob"] == 200


def test_phase_does_not_regress():
    b = boss()
    b.attack("alice", 800, 0)
    b.attack("alice", 1, 1)
    assert b.state()["phase"] == 2


def test_zero_damage_raises():
    b = boss()
    with pytest.raises(ValueError):
        b.attack("alice", 0, 0)


def test_negative_damage_raises():
    b = boss()
    with pytest.raises(ValueError):
        b.attack("alice", -5, 0)


def test_attack_after_death_raises():
    b = boss()
    b.attack("alice", 5000, 0)
    with pytest.raises(ValueError):
        b.attack("bob", 10, 1)


def test_settle_before_death_raises():
    b = boss()
    with pytest.raises(ValueError):
        b.settle()


def test_settle_splits_by_contribution():
    b = boss()
    b.attack("alice", 400, 0)
    b.attack("bob", 600, 0)
    rewards = b.settle()
    assert rewards == {"alice": 400, "bob": 600}
    assert b.reward("bob") == 600


def test_settle_twice_raises():
    b = boss()
    b.attack("alice", 1000, 0)
    b.settle()
    with pytest.raises(ValueError):
        b.settle()


def test_attack_after_settle_raises():
    b = boss()
    b.attack("alice", 1000, 0)
    b.settle()
    with pytest.raises(ValueError):
        b.attack("bob", 1, 1)


def test_state_is_copy():
    b = boss()
    b.attack("alice", 100, 0)
    snapshot = b.state()
    snapshot["contributions"]["alice"] = 9999
    assert b.state()["contributions"]["alice"] == 100
