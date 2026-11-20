import pytest

import aoi_scheduler as aoi


def make_scheduler(budget=5):
    scheduler = aoi.AoiScheduler(cell_size=10, view_radius=10, budget=budget)
    scheduler.update_observer("o", 0, 0)
    return scheduler


def test_plan_sends_visible_entities():
    scheduler = make_scheduler()
    scheduler.add_entity("a", 3, 0, priority=1)
    scheduler.add_entity("b", 4, 0, priority=0)
    assert scheduler.plan(1) == {"o": {"send": ["a", "b"], "defer": []}}


def test_view_radius_boundary_is_inclusive():
    scheduler = make_scheduler()
    scheduler.add_entity("near", 10, 0, priority=0)
    scheduler.add_entity("far", 10.001, 0, priority=0)
    assert scheduler.plan(1)["o"]["send"] == ["near"]


def test_order_is_priority_then_distance_then_id():
    scheduler = make_scheduler()
    scheduler.add_entity("c", 2, 0, priority=0)
    scheduler.add_entity("a", 5, 0, priority=1)
    scheduler.add_entity("b", 1, 0, priority=1)
    assert scheduler.plan(1)["o"]["send"] == ["b", "a", "c"]


def test_budget_defers_the_rest():
    scheduler = make_scheduler(budget=1)
    scheduler.add_entity("a", 3, 0, priority=1)
    scheduler.add_entity("b", 4, 0, priority=0)
    assert scheduler.plan(1) == {"o": {"send": ["a"], "defer": ["b"]}}


def test_ack_clears_pending():
    scheduler = make_scheduler()
    scheduler.add_entity("a", 3, 0)
    scheduler.plan(1)
    scheduler.ack("o", ["a"])
    assert scheduler.pending() == {"o": []}


def test_lost_entity_is_resent_first():
    scheduler = make_scheduler(budget=2)
    scheduler.add_entity("a", 3, 0, priority=2)
    scheduler.add_entity("b", 4, 0, priority=1)
    first = scheduler.plan(1, loss={"o": ["a"]})
    assert first == {"o": {"send": ["b"], "defer": ["a"]}}
    assert scheduler.pending() == {"o": ["a"]}
    assert scheduler.plan(2)["o"]["send"] == ["a", "b"]


def test_unacked_entities_stay_pending():
    scheduler = make_scheduler(budget=2)
    scheduler.add_entity("a", 3, 0, priority=1)
    scheduler.add_entity("b", 4, 0, priority=0)
    scheduler.plan(1)
    scheduler.ack("o", ["a"])
    assert scheduler.pending() == {"o": ["b"]}


def test_ack_unknown_entity_raises():
    scheduler = make_scheduler()
    scheduler.add_entity("a", 3, 0)
    scheduler.plan(1)
    with pytest.raises(ValueError):
        scheduler.ack("o", ["missing"])


def test_duplicate_entity_id_raises():
    scheduler = make_scheduler()
    scheduler.add_entity("a", 3, 0)
    with pytest.raises(ValueError):
        scheduler.add_entity("a", 4, 0)


def test_invalid_observer_coordinate_raises():
    scheduler = make_scheduler()
    with pytest.raises(ValueError):
        scheduler.update_observer("o2", float("inf"), 0)


def test_invalid_entity_priority_raises():
    scheduler = make_scheduler()
    with pytest.raises(ValueError):
        scheduler.add_entity("a", 3, 0, priority=1.5)


def test_moving_entity_out_of_view_stops_sending():
    scheduler = make_scheduler()
    scheduler.add_entity("a", 3, 0)
    scheduler.plan(1)
    scheduler.ack("o", ["a"])
    scheduler.add_entity("a", 300, 0)
    assert scheduler.plan(2)["o"]["send"] == []


def test_duplicate_tick_raises():
    scheduler = make_scheduler()
    scheduler.plan(1)
    with pytest.raises(ValueError):
        scheduler.plan(1)


def test_pending_returns_a_copy():
    scheduler = make_scheduler()
    scheduler.add_entity("a", 3, 0)
    scheduler.plan(1)
    snapshot = scheduler.pending()
    snapshot["o"].append("x")
    assert scheduler.pending()["o"] == ["a"]


def test_pending_entity_out_of_view_is_dropped():
    scheduler = make_scheduler()
    scheduler.add_entity("a", 3, 0)
    scheduler.plan(1)
    scheduler.add_entity("a", 300, 0)
    assert scheduler.plan(2) == {"o": {"send": [], "defer": []}}
    assert scheduler.pending() == {"o": []}
