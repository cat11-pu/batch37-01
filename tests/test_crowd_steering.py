import pytest

import crowd_steering as cs


def test_neighbor_grid_excludes_far_pair():
    assert cs.neighbor_grid([(0.0, 0.0), (2.0, 0.0), (5.0, 0.0)], 2.5) == [[1], [0], []]


def test_neighbor_grid_matches_brute_force():
    positions = [(0.0, 0.0), (1.5, 0.0), (0.0, 1.5), (5.0, 5.0)]
    assert cs.neighbor_grid(positions, 2.0) == [[1, 2], [0], [0], []]


def test_cell_size_does_not_change_neighbors():
    positions = [(0.0, 0.0), (1.5, 0.0), (0.0, 1.5), (5.0, 5.0)]
    fine = cs.neighbor_grid(positions, 2.0, cell_size=0.5)
    coarse = cs.neighbor_grid(positions, 2.0, cell_size=3.0)
    assert fine == coarse == [[1, 2], [0], [0], []]


def test_neighbor_across_cell_boundary_is_found():
    assert cs.neighbor_grid([(0.9, 0.0), (1.1, 0.0)], 0.5, cell_size=1.0) == [[1], [0]]


def test_separation_pushes_boids_apart():
    forces = cs.boids_forces(
        [(0.0, 0.0), (2.0, 0.0)],
        [(0.0, 0.0), (0.0, 0.0)],
        separation=1.0,
        alignment=0.0,
        cohesion=0.0,
        radius=3.0,
        max_force=10.0,
    )
    assert forces == [(-0.5, 0.0), (0.5, 0.0)]


def test_cohesion_pulls_toward_neighbor():
    forces = cs.boids_forces(
        [(0.0, 0.0), (2.0, 0.0)],
        [(0.0, 0.0), (0.0, 0.0)],
        separation=0.0,
        alignment=0.0,
        cohesion=1.0,
        radius=3.0,
        max_force=10.0,
    )
    assert forces == [(2.0, 0.0), (-2.0, 0.0)]


def test_alignment_matches_neighbor_velocity():
    forces = cs.boids_forces(
        [(0.0, 0.0), (1.0, 0.0)],
        [(0.0, 0.0), (2.0, 0.0)],
        separation=0.0,
        alignment=1.0,
        cohesion=0.0,
        radius=3.0,
        max_force=10.0,
    )
    assert forces == [(2.0, 0.0), (-2.0, 0.0)]


def test_combined_force_is_clamped():
    forces = cs.boids_forces(
        [(0.0, 0.0), (2.0, 0.0)],
        [(0.0, 0.0), (0.0, 0.0)],
        separation=1.0,
        alignment=1.0,
        cohesion=1.0,
        radius=3.0,
        max_force=1.0,
    )
    assert forces == [(1.0, 0.0), (-1.0, 0.0)]


def test_far_apart_boids_feel_no_force():
    forces = cs.boids_forces(
        [(0.0, 0.0), (10.0, 0.0)],
        [(0.0, 0.0), (0.0, 0.0)],
        separation=1.0,
        alignment=1.0,
        cohesion=1.0,
        radius=3.0,
        max_force=5.0,
    )
    assert forces == [(0.0, 0.0), (0.0, 0.0)]


def test_coincident_boids_have_zero_separation():
    forces = cs.boids_forces(
        [(1.0, 1.0), (1.0, 1.0)],
        [(0.0, 0.0), (0.0, 0.0)],
        separation=1.0,
        alignment=0.0,
        cohesion=0.0,
        radius=3.0,
        max_force=5.0,
    )
    assert forces == [(0.0, 0.0), (0.0, 0.0)]


def test_step_integrates_velocity():
    positions, velocities = cs.step(
        [(0.0, 0.0)],
        [(1.0, 0.0)],
        dt=0.5,
        separation=1.0,
        alignment=1.0,
        cohesion=1.0,
        radius=3.0,
        max_force=1.0,
        max_speed=2.0,
    )
    assert positions == [(0.5, 0.0)]
    assert velocities == [(1.0, 0.0)]


def test_step_clamps_speed():
    positions, velocities = cs.step(
        [(0.0, 0.0)],
        [(10.0, 0.0)],
        dt=0.5,
        separation=1.0,
        alignment=1.0,
        cohesion=1.0,
        radius=3.0,
        max_force=1.0,
        max_speed=2.0,
    )
    assert velocities == [(2.0, 0.0)]
    assert positions == [(1.0, 0.0)]


def test_step_rejects_non_positive_dt():
    with pytest.raises(ValueError):
        cs.step([(0.0, 0.0)], [(0.0, 0.0)], dt=0.0)


def test_positions_and_velocities_must_match():
    with pytest.raises(ValueError):
        cs.boids_forces([(0.0, 0.0)], [(0.0, 0.0), (1.0, 0.0)])


def test_radius_must_be_positive():
    with pytest.raises(ValueError):
        cs.neighbor_grid([(0.0, 0.0)], 0.0)
