import math

import pytest

import projectile_ballistics as pb


def solver(gravity=0.0, drag=0.0):
    return pb.Ballistics(gravity, drag)


def test_stationary_target_without_gravity():
    result = solver().solve((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 0.0), 10.0)
    assert result["aim"] == pytest.approx((10.0, 0.0, 0.0))
    assert result["flight_time"] == pytest.approx(1.0)
    assert result["converged"] is True


def test_flight_time_without_drag():
    assert solver().flight_time(20.0, 10.0) == pytest.approx(2.0)


def test_flight_time_grows_with_drag():
    b = solver(drag=0.05)
    t = b.flight_time(10.0, 10.0)
    assert t == pytest.approx(-math.log(0.95) / 0.05)
    assert t > 1.0


def test_flight_time_is_monotonic():
    b = solver(drag=0.02)
    times = [b.flight_time(d, 10.0) for d in (1.0, 5.0, 10.0, 20.0)]
    assert times == sorted(times)
    assert len(set(times)) == 4


def test_gravity_lifts_the_aim_point():
    result = solver(gravity=9.81).solve((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 0.0), 10.0)
    t = result["flight_time"]
    assert result["aim"][1] == pytest.approx(0.5 * 9.81 * t * t)


def test_leading_moving_target_along_x():
    result = solver().solve((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (2.0, 0.0, 0.0), 10.0)
    assert result["aim"][0] == pytest.approx(12.5)
    assert result["flight_time"] == pytest.approx(1.25)


def test_leading_moving_target_along_z():
    result = solver().solve((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 3.0), 10.0)
    assert result["aim"][2] == pytest.approx(3.0 * result["flight_time"])
    assert result["aim"][2] > 0.0


def test_iterations_are_reported():
    result = solver().solve((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (1.0, 0.0, 0.0), 10.0)
    assert result["iterations"] >= 1
    assert result["iterations"] <= 10


def test_iterations_respect_limit():
    result = solver().solve(
        (0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (5.0, 0.0, 0.0), 10.0, max_iterations=3
    )
    assert result["iterations"] <= 3


def test_solution_is_deterministic():
    args = ((0.0, 1.0, 0.0), (10.0, 2.0, 3.0), (1.0, -0.5, 0.7), 12.0)
    first = solver(gravity=9.81, drag=0.01).solve(*args)
    second = solver(gravity=9.81, drag=0.01).solve(*args)
    assert first["aim"] == pytest.approx(second["aim"])
    assert first["flight_time"] == pytest.approx(second["flight_time"])
    assert first["iterations"] == second["iterations"]
    assert first["converged"] == second["converged"]


def test_invalid_speed_raises():
    with pytest.raises(ValueError):
        solver().solve((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0)


def test_negative_drag_raises():
    with pytest.raises(ValueError):
        pb.Ballistics(9.81, -0.1)


def test_negative_gravity_raises():
    with pytest.raises(ValueError):
        pb.Ballistics(-1.0, 0.0)


def test_unreachable_distance_raises():
    with pytest.raises(ValueError):
        solver(drag=0.2).flight_time(100.0, 10.0)


def test_invalid_iteration_limit_raises():
    with pytest.raises(ValueError):
        solver().solve(
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), 10.0, max_iterations=0
        )
