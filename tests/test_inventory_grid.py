import pytest

import inventory_grid as ig


def grid():
    return ig.GridInventory(10, 10)


def test_place_registers_footprint():
    g = grid()
    g.place("sword", 1, 2, 0, 0)
    item = g.state()["items"]["sword"]
    assert (item["x"], item["y"], item["w"], item["h"]) == (0, 0, 1, 2)


def test_place_out_of_bounds_raises():
    with pytest.raises(ValueError):
        grid().place("crate", 3, 1, 8, 0)


def test_place_negative_origin_raises():
    with pytest.raises(ValueError):
        grid().place("crate", 1, 1, -1, 0)


def test_overlap_is_rejected():
    g = grid()
    g.place("a", 2, 2, 0, 0)
    with pytest.raises(ValueError):
        g.place("b", 1, 1, 1, 1)


def test_rotation_swaps_dimensions():
    g = grid()
    g.place("pike", 1, 3, 7, 0, rotated=True)
    item = g.state()["items"]["pike"]
    assert item["w"] == 3
    assert item["h"] == 1
    assert item["rotated"] is True


def test_rotated_footprint_out_of_bounds_is_false():
    g = grid()
    assert g.can_place(1, 3, 8, 0, rotated=True) is False


def test_can_place_true_does_not_mutate():
    g = grid()
    g.place("a", 2, 2, 0, 0)
    before = g.state()
    assert g.can_place(1, 1, 5, 5) is True
    assert g.state() == before


def test_can_place_false_on_overlap():
    g = grid()
    g.place("a", 2, 2, 0, 0)
    assert g.can_place(1, 1, 0, 0) is False


def test_remove_releases_space():
    g = grid()
    g.place("a", 2, 2, 0, 0)
    g.remove("a")
    assert g.state()["items"] == {}
    assert g.can_place(2, 2, 0, 0) is True


def test_remove_more_than_held_raises():
    g = grid()
    g.place("a", 1, 1, 0, 0)
    g.stack("a", 2)
    with pytest.raises(ValueError):
        g.remove("a", 4)


def test_remove_unknown_item_raises():
    g = grid()
    with pytest.raises(ValueError):
        g.remove("ghost")


def test_stack_increases_quantity():
    g = grid()
    g.place("a", 1, 1, 0, 0)
    g.stack("a", 3)
    assert g.state()["items"]["a"]["qty"] == 4


def test_stack_overflow_keeps_quantity():
    g = grid()
    g.place("a", 1, 1, 0, 0)
    g.stack("a", 4)
    with pytest.raises(ValueError):
        g.stack("a", 1)
    assert g.state()["items"]["a"]["qty"] == 5


def test_move_updates_position():
    g = grid()
    g.place("a", 2, 2, 0, 0)
    g.move("a", 5, 5)
    assert g.state()["items"]["a"]["x"] == 5
    assert g.state()["items"]["a"]["y"] == 5


def test_move_into_overlap_raises():
    g = grid()
    g.place("a", 2, 2, 0, 0)
    g.place("b", 2, 2, 5, 5)
    with pytest.raises(ValueError):
        g.move("b", 1, 1)
