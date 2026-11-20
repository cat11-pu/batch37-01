import pytest

import constraint_solver as cs


def solver(iterations=4):
    return cs.ConstraintSolver(iterations)


def pair(restitution=0.0):
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0, vx=1.0)
    game.add_body("b", 1.0, 1.0, 0.0, vx=-1.0)
    game.add_contact("a", "b", 1.0, 0.0, 0.0, restitution=restitution)
    return game


def test_head_on_inelastic_stops():
    game = pair(0.0)
    game.step(0.016)
    assert game.state()["a"]["vx"] == pytest.approx(0.0)
    assert game.state()["b"]["vx"] == pytest.approx(0.0)


def test_elastic_swaps_velocity():
    game = pair(1.0)
    game.step(0.016)
    assert game.state()["a"]["vx"] == pytest.approx(-1.0)
    assert game.state()["b"]["vx"] == pytest.approx(1.0)


def test_momentum_is_conserved():
    game = pair(0.0)
    before = game.state()["a"]["vx"] + game.state()["b"]["vx"]
    game.step(0.016)
    after = game.state()["a"]["vx"] + game.state()["b"]["vx"]
    assert after == pytest.approx(before)


def test_static_body_does_not_move():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0, vx=1.0)
    game.add_body("floor", 0.0, 1.0, 0.0, static=True)
    game.add_contact("a", "floor", 1.0, 0.0, 0.0, restitution=0.0)
    game.step(0.016)
    assert game.state()["a"]["vx"] == pytest.approx(0.0)
    assert game.state()["floor"]["vx"] == pytest.approx(0.0)


def test_penetration_is_corrected():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0)
    game.add_body("b", 1.0, 1.0, 0.0)
    game.add_contact("a", "b", 1.0, 0.0, 1.0)
    game.step(0.016)
    assert game.state()["a"]["x"] < 0.0
    assert game.state()["b"]["x"] > 1.0


def test_static_body_does_not_move_in_correction():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0)
    game.add_body("floor", 0.0, 1.0, 0.0, static=True)
    game.add_contact("a", "floor", 1.0, 0.0, 1.0)
    game.step(0.016)
    assert game.state()["floor"]["x"] == pytest.approx(1.0)


def test_friction_reduces_tangent():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0, vx=0.0, vy=2.0)
    game.add_body("floor", 0.0, 1.0, 0.0, static=True)
    game.add_contact("a", "floor", 1.0, 0.0, 0.0, friction=0.5)
    game.step(0.016)
    assert abs(game.state()["a"]["vy"]) < 2.0


def test_zero_friction_keeps_tangent():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0, vx=1.0, vy=2.0)
    game.add_body("floor", 0.0, 1.0, 0.0, static=True)
    game.add_contact("a", "floor", 1.0, 0.0, 0.0, friction=0.0)
    game.step(0.016)
    assert game.state()["a"]["vy"] == pytest.approx(2.0)
    assert game.state()["a"]["vx"] == pytest.approx(0.0)


def test_invalid_restitution_raises():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0)
    game.add_body("b", 1.0, 1.0, 0.0)
    with pytest.raises(ValueError):
        game.add_contact("a", "b", 1.0, 0.0, 0.0, restitution=2.0)


def test_invalid_mass_raises():
    game = solver()
    with pytest.raises(ValueError):
        game.add_body("a", -1.0, 0.0, 0.0)


def test_unknown_body_contact_raises():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        game.add_contact("a", "ghost", 1.0, 0.0, 0.0)


def test_duplicate_body_raises():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        game.add_body("a", 1.0, 0.0, 0.0)


def test_multiple_contacts_are_processed():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0, vx=1.0)
    game.add_body("b", 1.0, 1.0, 0.0, vx=-1.0)
    game.add_body("c", 1.0, 2.0, 0.0, vx=-1.0)
    game.add_contact("a", "b", 1.0, 0.0, 0.0)
    game.add_contact("b", "c", 1.0, 0.0, 0.0)
    game.step(0.016)
    assert game.state()["c"]["vx"] != pytest.approx(-1.0)


def test_more_iterations_keep_elastic_result():
    game = pair(1.0)
    game.iterations = 8
    game.step(0.016)
    assert game.state()["a"]["vx"] == pytest.approx(-1.0)


def test_state_returns_a_copy():
    game = solver()
    game.add_body("a", 1.0, 0.0, 0.0)
    snapshot = game.state()
    snapshot["a"]["x"] = 99.0
    assert game.state()["a"]["x"] == 0.0
