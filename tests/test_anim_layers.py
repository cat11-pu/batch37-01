import math

import pytest

import anim_layers as al


def graph():
    game = al.AnimationGraph()
    game.add_clip("walk", 2.0, [(0.0, 0.0), (1.0, 10.0), (2.0, 20.0)])
    return game


def test_sample_exact_key():
    game = graph()
    assert game.sample("walk", 1.0) == 10.0


def test_sample_interpolates():
    game = graph()
    assert game.sample("walk", 0.5) == 5.0


def test_sample_loops_at_duration():
    game = al.AnimationGraph()
    game.add_clip("cycle", 2.0, [(0.0, 0.0), (2.0, 10.0)])
    assert game.sample("cycle", 2.5) == 2.5


def test_non_loop_clamps_at_end():
    game = al.AnimationGraph()
    game.add_clip("once", 2.0, [(0.0, 0.0), (2.0, 10.0)], loop=False)
    assert game.sample("once", 3.0) == 10.0


def test_negative_sample_time_raises():
    game = graph()
    with pytest.raises(ValueError):
        game.sample("walk", -0.1)


def test_unsorted_keys_raise():
    game = al.AnimationGraph()
    with pytest.raises(ValueError):
        game.add_clip("bad", 2.0, [(1.0, 1.0), (0.0, 0.0)])


def test_duplicate_key_time_raises():
    game = al.AnimationGraph()
    with pytest.raises(ValueError):
        game.add_clip("bad", 2.0, [(1.0, 1.0), (1.0, 2.0)])


def test_invalid_duration_raises():
    game = al.AnimationGraph()
    with pytest.raises(ValueError):
        game.add_clip("bad", 0.0, [(0.0, 1.0)])


def test_override_layers_blend_in_order():
    game = al.AnimationGraph()
    game.add_clip("a", 1.0, [(0.0, 10.0), (1.0, 10.0)])
    game.add_clip("b", 1.0, [(0.0, 20.0), (1.0, 20.0)])
    game.add_layer("base", "a", mode="override", weight=1.0)
    game.add_layer("top", "b", mode="override", weight=0.5)
    assert game.evaluate(0.0) == 15.0


def test_additive_layer_adds_weighted_value():
    game = al.AnimationGraph()
    game.add_clip("a", 1.0, [(0.0, 10.0), (1.0, 10.0)])
    game.add_clip("b", 1.0, [(0.0, 5.0), (1.0, 5.0)])
    game.add_layer("base", "a", mode="override", weight=1.0)
    game.add_layer("extra", "b", mode="additive", weight=0.5)
    assert game.evaluate(0.0) == 12.5


def test_weights_override_layer_weight():
    game = al.AnimationGraph()
    game.add_clip("a", 1.0, [(0.0, 10.0), (1.0, 10.0)])
    game.add_clip("b", 1.0, [(0.0, 20.0), (1.0, 20.0)])
    game.add_layer("base", "a", mode="override", weight=1.0)
    game.add_layer("top", "b", mode="override", weight=1.0)
    assert game.evaluate(0.0, weights={"top": 0.0}) == 10.0


def test_lod_skips_high_detail_layer():
    game = al.AnimationGraph()
    game.add_clip("a", 1.0, [(0.0, 10.0), (1.0, 10.0)])
    game.add_clip("b", 1.0, [(0.0, 20.0), (1.0, 20.0)])
    game.add_layer("base", "a", mode="override", weight=1.0)
    game.add_layer("top", "b", mode="override", weight=0.5, min_lod=2)
    assert game.evaluate(0.0, lod=1) == 10.0
    assert game.evaluate(0.0, lod=2) == 15.0


def test_invalid_layer_weight_raises():
    game = graph()
    with pytest.raises(ValueError):
        game.add_layer("bad", "walk", weight=1.5)


def test_root_delta_is_weighted_sum():
    game = al.AnimationGraph()
    game.add_clip("a", 1.0, [(0.0, 0.0), (1.0, 0.0)], root=2.0)
    game.add_clip("b", 1.0, [(0.0, 0.0), (1.0, 0.0)], root=4.0)
    game.add_layer("base", "a", weight=1.0)
    game.add_layer("extra", "b", mode="additive", weight=0.5)
    assert game.root_delta(0.0) == 4.0


def test_solve_ik_clamps_step():
    game = al.AnimationGraph()
    assert game.solve_ik((0.0, 0.0), (10.0, 0.0), 3.0) == (3.0, 0.0)
    assert game.solve_ik((0.0, 0.0), (1.0, 0.0), 3.0) == (1.0, 0.0)
