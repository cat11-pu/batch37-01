from collections import deque

import pytest

import dungeon_edit as de


def editor(seed=7):
    game = de.DungeonEditor(seed, width=24, height=18)
    game.generate()
    return game


def test_same_seed_is_deterministic():
    first = editor(7)
    second = editor(7)
    a = first.snapshot()
    b = second.snapshot()
    assert a is not None
    assert a == b


def test_different_seed_changes_layout():
    a = editor(7).snapshot()
    b = editor(8).snapshot()
    assert a is not None and b is not None
    assert a != b


def test_rooms_stay_inside_bounds():
    game = editor()
    assert game.rooms
    for room in game.rooms:
        assert room["x"] >= 0
        assert room["y"] >= 0
        assert room["x"] + room["w"] <= game.width
        assert room["y"] + room["h"] <= game.height


def test_rooms_do_not_overlap():
    game = editor()
    rooms = game.rooms
    assert len(rooms) >= 2
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            overlap_x = a["x"] < b["x"] + b["w"] + 1 and b["x"] < a["x"] + a["w"] + 1
            overlap_y = a["y"] < b["y"] + b["h"] + 1 and b["y"] < a["y"] + a["h"] + 1
            assert not (overlap_x and overlap_y)


def test_generate_places_multiple_rooms():
    game = editor()
    assert len(game.rooms) >= 2


def test_all_floor_tiles_are_connected():
    game = editor()
    grid = game.snapshot()
    floors = {(x, y) for y, row in enumerate(grid) for x, tile in enumerate(row) if tile == "."}
    assert floors
    start = next(iter(floors))
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in floors and (nx, ny) not in seen:
                seen.add((nx, ny))
                queue.append((nx, ny))
    assert seen == floors


def test_paint_changes_tile_and_version():
    game = editor()
    old_version = game.version
    game.paint(1, 1, ".")
    assert game.snapshot()[1][1] == "."
    assert game.version == old_version + 1


def test_paint_out_of_bounds_raises():
    game = editor()
    with pytest.raises(ValueError):
        game.paint(-1, 0, ".")


def test_paint_invalid_tile_raises():
    game = editor()
    with pytest.raises(ValueError):
        game.paint(1, 1, "X")


def test_apply_is_atomic_and_bumps_once():
    game = editor()
    old_version = game.version
    game.apply([{"x": 1, "y": 1, "tile": "."}, {"x": 2, "y": 1, "tile": "."}])
    grid = game.snapshot()
    assert grid[1][1] == "." and grid[1][2] == "."
    assert game.version == old_version + 1


def test_apply_invalid_batch_changes_nothing():
    game = editor()
    before = game.snapshot()
    old_version = game.version
    with pytest.raises(ValueError):
        game.apply([{"x": 1, "y": 1, "tile": "."}, {"x": -1, "y": 1, "tile": "."}])
    assert game.snapshot() == before
    assert game.version == old_version


def test_rollback_restores_old_snapshot():
    game = editor()
    old_version = game.version
    before = game.snapshot()
    game.paint(1, 1, ".")
    new_version = game.version
    game.rollback(old_version)
    assert game.snapshot() == before
    assert game.version == new_version + 1


def test_rollback_unknown_version_raises():
    game = editor()
    with pytest.raises(ValueError):
        game.rollback(999)


def test_rollback_current_version_creates_new_version():
    game = editor()
    current = game.version
    before = game.snapshot()
    game.rollback(current)
    assert game.snapshot() == before
    assert game.version == current + 1


def test_snapshot_is_a_copy():
    game = editor()
    snapshot = game.snapshot()
    snapshot[0] = "X" * game.width
    assert game.snapshot()[0] != "X" * game.width
