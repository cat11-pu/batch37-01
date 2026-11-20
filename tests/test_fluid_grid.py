import math

import pytest

import fluid_grid as fg


def grid(width=5, height=1, **kw):
    return fg.FluidGrid(width, height, **kw)


def test_width_must_be_positive():
    with pytest.raises(ValueError):
        fg.FluidGrid(0, 1)


def test_height_must_be_positive():
    with pytest.raises(ValueError):
        fg.FluidGrid(3, -1)


def test_diffusion_must_not_be_negative():
    with pytest.raises(ValueError):
        fg.FluidGrid(3, 3, diffusion=-0.1)


def test_iterations_must_be_positive():
    with pytest.raises(ValueError):
        fg.FluidGrid(3, 3, iterations=0)


def test_new_grid_is_empty_and_still():
    g = grid(3, 2)
    assert g.density_at(1, 1) == 0.0
    assert g.velocity_at(1, 1) == (0.0, 0.0)


def test_density_sources_accumulate():
    g = grid()
    g.add_density(2, 0, 0.5)
    g.add_density(2, 0, 0.5)
    assert g.density_at(2, 0) == 1.0


def test_density_never_goes_negative():
    g = grid()
    g.add_density(2, 0, 0.5)
    g.add_density(2, 0, -3.0)
    assert g.density_at(2, 0) == 0.0


def test_out_of_range_density_source_is_rejected():
    g = grid()
    with pytest.raises(ValueError):
        g.add_density(5, 0, 1.0)


def test_velocity_roundtrip():
    g = grid()
    g.add_velocity(1, 0, 0.25, -0.5)
    assert g.velocity_at(1, 0) == (0.25, -0.5)


def test_advance_with_zero_dt_is_rejected():
    g = grid()
    with pytest.raises(ValueError):
        g.step(0)


def test_constant_wind_carries_density_downstream():
    g = grid(9, 1)
    for x in range(9):
        g.add_velocity(x, 0, 1.0, 0.0)
    g.add_density(1, 0, 1.0)
    for _ in range(5):
        g.step(1.0)
    assert g.density_at(6, 0) > 0.3
    assert g.density_at(1, 0) < 0.1


def test_diffusion_spreads_density_to_neighbour():
    g = grid(5, 1, diffusion=0.5)
    g.add_density(2, 0, 1.0)
    for _ in range(5):
        g.step(1.0)
    assert 0.0 < g.density_at(1, 0) < 1.0
    assert g.density_at(2, 0) < 1.0


def test_diffusion_keeps_most_of_the_total():
    g = grid(5, 1, diffusion=0.5)
    g.add_density(2, 0, 1.0)
    for _ in range(5):
        g.step(1.0)
    total = sum(g.density_at(x, 0) for x in range(5))
    assert 0.9 <= total <= 1.1


def test_viscosity_softens_the_velocity_peak():
    g = grid(5, 1, viscosity=0.5)
    g.add_velocity(2, 0, 1.0, 0.0)
    for _ in range(5):
        g.step(1.0)
    assert g.velocity_at(2, 0)[0] < 0.99
    assert g.velocity_at(1, 0)[0] > 0.0


def test_long_run_stays_finite():
    g = grid(6, 3, diffusion=0.2, viscosity=0.2)
    g.add_density(2, 1, 2.0)
    g.add_velocity(2, 1, 0.4, -0.3)
    for _ in range(20):
        g.step(0.5)
    values = [g.density_at(x, y) for x in range(6) for y in range(3)]
    speeds = [g.velocity_at(x, y) for x in range(6) for y in range(3)]
    assert all(math.isfinite(v) and v >= 0.0 for v in values)
    assert all(math.isfinite(a) and math.isfinite(b) for a, b in speeds)
