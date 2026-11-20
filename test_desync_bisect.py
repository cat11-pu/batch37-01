import math

import pytest

import desync_bisect as db


def frame(tick, **entities):
    return {"tick": tick, "entities": entities}


def test_identical_frames_have_no_divergence():
    server = [frame(0, a={"hp": 10}), frame(1, a={"hp": 9})]
    client = [frame(0, a={"hp": 10}), frame(1, a={"hp": 9})]
    assert db.DesyncBisect(server, client).first_divergence() is None


def test_divergence_at_first_tick():
    server = [frame(0, a={"hp": 10})]
    client = [frame(0, a={"hp": 9})]
    assert db.DesyncBisect(server, client).first_divergence() == 0


def test_divergence_at_last_tick():
    server = [frame(0, a={"hp": 10}), frame(1, a={"hp": 9}), frame(2, a={"hp": 8})]
    client = [frame(0, a={"hp": 10}), frame(1, a={"hp": 9}), frame(2, a={"hp": 7})]
    assert db.DesyncBisect(server, client).first_divergence() == 2


def test_first_divergence_is_earliest():
    server = [frame(0, a={"hp": 10}), frame(1, a={"hp": 9}), frame(2, a={"hp": 8})]
    client = [frame(0, a={"hp": 10}), frame(1, a={"hp": 8}), frame(2, a={"hp": 9})]
    assert db.DesyncBisect(server, client).first_divergence() == 1


def test_float_epsilon_is_tolerated():
    server = [frame(0, a={"hp": 1.0000000001})]
    client = [frame(0, a={"hp": 1.0})]
    assert db.DesyncBisect(server, client, epsilon=1e-9).first_divergence() is None


def test_float_beyond_epsilon_is_detected():
    server = [frame(0, a={"hp": 1.0001})]
    client = [frame(0, a={"hp": 1.0})]
    assert db.DesyncBisect(server, client, epsilon=1e-9).first_divergence() == 0


def test_two_nan_values_are_equal():
    server = [frame(0, a={"hp": float("nan")})]
    client = [frame(0, a={"hp": float("nan")})]
    assert db.DesyncBisect(server, client).first_divergence() is None


def test_nan_and_number_diverge():
    server = [frame(0, a={"hp": float("nan")})]
    client = [frame(0, a={"hp": 0.0})]
    assert db.DesyncBisect(server, client).first_divergence() == 0


def test_added_entity_is_classified():
    server = [frame(0, a={"hp": 1}, b={"hp": 2})]
    client = [frame(0, a={"hp": 1})]
    bisect = db.DesyncBisect(server, client)
    assert bisect.first_divergence() == 0
    assert bisect.diff(0) == {"tick": 0, "added": ["b"], "removed": [], "changed": {}}


def test_removed_entity_is_classified():
    server = [frame(0, a={"hp": 1})]
    client = [frame(0, a={"hp": 1}, c={"hp": 3})]
    assert db.DesyncBisect(server, client).diff(0) == {
        "tick": 0,
        "added": [],
        "removed": ["c"],
        "changed": {},
    }


def test_changed_field_reports_both_values():
    server = [frame(0, a={"hp": 10, "mp": 3})]
    client = [frame(0, a={"hp": 9, "mp": 3})]
    assert db.DesyncBisect(server, client).diff(0) == {
        "tick": 0,
        "added": [],
        "removed": [],
        "changed": {"a": {"hp": {"server": 10, "client": 9}}},
    }


def test_diff_unknown_tick_raises():
    bisect = db.DesyncBisect([frame(0, a={"hp": 1})], [frame(0, a={"hp": 2})])
    with pytest.raises(ValueError):
        bisect.diff(5)


def test_mismatched_tick_sequence_raises():
    with pytest.raises(ValueError):
        db.DesyncBisect([frame(0), frame(1)], [frame(0), frame(2)])


def test_reconcile_operations_are_sorted():
    server = [frame(0, a={"hp": 10}, b={"x": 1})]
    client = [frame(0, a={"hp": 9}, c={"y": 2})]
    assert db.DesyncBisect(server, client).reconcile(0) == [
        {"op": "set", "entity": "a", "field": "hp", "value": 10},
        {"op": "add", "entity": "b", "value": {"x": 1}},
        {"op": "remove", "entity": "c"},
    ]


def test_divergences_returns_all_ticks_and_a_copy():
    server = [frame(0, a={"hp": 10}), frame(1, a={"hp": 9}), frame(2, a={"hp": 8})]
    client = [frame(0, a={"hp": 9}), frame(1, a={"hp": 9}), frame(2, a={"hp": 7})]
    bisect = db.DesyncBisect(server, client)
    found = bisect.divergences()
    found.append(99)
    assert bisect.divergences() == [0, 2]
