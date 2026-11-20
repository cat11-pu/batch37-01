import pytest

import hitbox_sweep as hs


def world():
    game = hs.SweepWorld()
    game.add_box("player", 0, 0, 2, 2)
    return game


def test_horizontal_sweep_hits_wall():
    game = world()
    game.add_box("wall", 5, 0, 2, 2)
    result = game.sweep("player", 10, 0)
    assert result["id"] == "wall"
    assert result["time"] == pytest.approx(0.3)
    assert result["normal"] == (-1, 0)


def test_high_speed_does_not_tunnel():
    game = world()
    game.add_box("wall", 5, 0, 2, 2)
    result = game.sweep("player", 100, 0)
    assert result["id"] == "wall"
    assert result["time"] == pytest.approx(0.03)


def test_no_hit_returns_none():
    game = world()
    game.add_box("wall", 5, 50, 2, 2)
    assert game.sweep("player", 10, 0) is None


def test_initial_overlap_returns_zero_time():
    game = world()
    game.add_box("wall", 1, 0, 2, 2)
    result = game.sweep("player", 10, 0)
    assert result["id"] == "wall"
    assert result["time"] == 0.0


def test_vertical_sweep_hits_wall():
    game = world()
    game.add_box("wall", 0, 5, 2, 2)
    result = game.sweep("player", 0, 10)
    assert result["id"] == "wall"
    assert result["time"] == pytest.approx(0.3)
    assert result["normal"] == (0, -1)


def test_diagonal_hit_uses_first_axis():
    game = world()
    game.add_box("wall", 5, 5, 2, 2)
    result = game.sweep("player", 10, 10)
    assert result["id"] == "wall"
    assert result["time"] == pytest.approx(0.3)
    assert result["normal"] == (-1, 0)


def test_layer_filter_excludes_wall():
    game = world()
    game.add_box("wall", 5, 0, 2, 2, layer=1)
    assert game.sweep("player", 10, 0, layers=[0]) is None


def test_layer_filter_includes_wall():
    game = world()
    game.add_box("wall", 5, 0, 2, 2, layer=1)
    assert game.sweep("player", 10, 0, layers=[1])["id"] == "wall"


def test_earliest_hit_wins():
    game = world()
    game.add_box("far", 8, 0, 2, 2)
    game.add_box("near", 4, 0, 2, 2)
    result = game.sweep("player", 10, 0)
    assert result["id"] == "near"
    assert result["time"] == pytest.approx(0.2)


def test_same_time_tie_breaks_by_id():
    game = world()
    game.add_box("b", 5, 0, 2, 2)
    game.add_box("a", 5, 0, 2, 2)
    assert game.sweep("player", 10, 0)["id"] == "a"


def test_zero_velocity_overlap_returns_zero():
    game = world()
    game.add_box("wall", 1, 0, 2, 2)
    result = game.sweep("player", 0, 0)
    assert result["id"] == "wall"
    assert result["time"] == 0.0


def test_duplicate_box_id_raises():
    game = world()
    with pytest.raises(ValueError):
        game.add_box("player", 10, 10, 2, 2)


def test_negative_size_raises():
    game = world()
    with pytest.raises(ValueError):
        game.add_box("wall", 5, 0, -2, 2)


def test_non_finite_delta_raises():
    game = world()
    with pytest.raises(ValueError):
        game.sweep("player", float("nan"), 0)


def test_removed_box_is_ignored():
    game = world()
    game.add_box("wall", 5, 0, 2, 2)
    game.remove_box("wall")
    assert game.sweep("player", 10, 0) is None
