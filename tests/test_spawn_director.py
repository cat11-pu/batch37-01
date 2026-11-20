import random

import pytest

import spawn_director as sd

ENTRIES = [
    {"type": "grunt", "cost": 2, "weight": 6},
    {"type": "archer", "cost": 3, "weight": 3},
    {"type": "brute", "cost": 5, "weight": 1},
]


def director(seed=7):
    return sd.SpawnDirector(seed)


def plan(seed=7, entries=None, budget=100, count=10, duration=10.0):
    pool = [dict(e) for e in ENTRIES] if entries is None else entries
    return director(seed).plan_wave("w1", pool, budget, count, duration)


def test_same_seed_same_plan():
    first = plan(seed=3)
    assert len(first["spawns"]) == 10
    assert first == plan(seed=3)


def test_different_seeds_change_order():
    a = [s["type"] for s in plan(seed=1, count=30, duration=30.0)["spawns"]]
    b = [s["type"] for s in plan(seed=2, count=30, duration=30.0)["spawns"]]
    assert a != b


def test_budget_is_never_exceeded():
    result = plan(budget=20, count=50)
    assert result["spent"] <= 20
    assert result["remaining"] == 20 - result["spent"]


def test_count_is_respected_when_budget_allows():
    result = plan(budget=1000, count=10)
    assert len(result["spawns"]) == 10
    assert result["finished"] is True


def test_stops_when_no_entry_is_affordable():
    entries = [{"type": "brute", "cost": 6, "weight": 1}]
    result = plan(entries=entries, budget=10, count=10)
    assert len(result["spawns"]) == 1
    assert result["spent"] == 6
    assert result["remaining"] == 4
    assert result["finished"] is True


def test_zero_budget_spawns_nothing():
    result = plan(budget=0, count=5)
    assert result["spawns"] == []
    assert result["spent"] == 0
    assert result["remaining"] == 0
    assert result["finished"] is True


def test_only_affordable_types_are_chosen():
    result = plan(budget=4, count=20)
    types = {s["type"] for s in result["spawns"]}
    assert types <= {"grunt", "archer"}
    assert "brute" not in types


def test_spawn_times_are_sorted_inside_duration():
    result = plan(budget=1000, count=9, duration=12.0)
    times = [s["at"] for s in result["spawns"]]
    assert times == sorted(times)
    assert times[0] >= 0.0
    assert times[-1] <= 12.0


def test_spawn_times_are_evenly_paced():
    result = plan(budget=1000, count=4, duration=8.0)
    times = [s["at"] for s in result["spawns"]]
    gaps = [times[i + 1] - times[i] for i in range(len(times) - 1)]
    assert len(gaps) == 3
    assert all(abs(g - gaps[0]) < 1e-9 for g in gaps)


def test_spent_matches_spawn_costs():
    result = plan(budget=50, count=7)
    assert result["spent"] == sum(s["cost"] for s in result["spawns"])


def test_global_random_state_does_not_leak():
    random.seed(123)
    first = plan(seed=11, count=12)
    random.seed(999)
    second = plan(seed=11, count=12)
    assert len(first["spawns"]) == 12
    assert first == second


def test_negative_budget_raises():
    with pytest.raises(ValueError):
        plan(budget=-1)


def test_empty_entries_raises():
    with pytest.raises(ValueError):
        plan(entries=[], budget=10, count=2)


def test_invalid_cost_or_weight_raises():
    with pytest.raises(ValueError):
        plan(entries=[{"type": "x", "cost": 0, "weight": 1}], budget=10, count=2)
    with pytest.raises(ValueError):
        plan(entries=[{"type": "x", "cost": 1, "weight": 0}], budget=10, count=2)


def test_invalid_count_duration_and_seed_raise():
    with pytest.raises(ValueError):
        plan(count=0)
    with pytest.raises(ValueError):
        plan(duration=0.0)
    with pytest.raises(ValueError):
        sd.SpawnDirector("seed")
