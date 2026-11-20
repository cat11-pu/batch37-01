import pytest

import camera_replay as cr


def make(colliders=None, **cfg):
    base = {"distance": 6.0, "min_distance": 1.0, "padding": 0.2, "smooth": 0.5}
    base.update(cfg)
    return cr.CameraReplay([dict(c) for c in (colliders or [])], base)


def test_solve_without_collider():
    c = make()
    assert c.solve((0, 0, 0), (0, 0, -1)) == pytest.approx((0.0, 0.0, -6.0))
    assert c.solve((0, 0, 0), (0, 0, -2)) == pytest.approx((0.0, 0.0, -6.0))


def test_solve_stops_before_sphere():
    c = make([{"x": 0, "y": 0, "z": -3, "r": 1}])
    assert c.solve((0, 0, 0), (0, 0, -1)) == pytest.approx((0.0, 0.0, -1.8))


def test_collider_behind_is_ignored():
    c = make([{"x": 0, "y": 0, "z": 3, "r": 1}])
    assert c.solve((0, 0, 0), (0, 0, -1)) == pytest.approx((0.0, 0.0, -6.0))


def test_origin_inside_sphere_uses_min_distance():
    c = make([{"x": 0, "y": 0, "z": -0.5, "r": 1}])
    assert c.solve((0, 0, 0), (0, 0, -1)) == pytest.approx((0.0, 0.0, -1.0))


def test_solve_respects_min_distance():
    c = make([{"x": 0, "y": 0, "z": -1.1, "r": 1}])
    assert c.solve((0, 0, 0), (0, 0, -1)) == pytest.approx((0.0, 0.0, -1.0))


def test_solve_rejects_bad_direction():
    c = make()
    with pytest.raises(ValueError):
        c.solve((0, 0, 0), (0, 0, 0))
    with pytest.raises(ValueError):
        c.solve((0, 0, 0), (0, 0, -1), distance=0)


def test_snap_is_immediate():
    c = make()
    pos = c.snap("cam", (0, 0, 0), (0, 0, -1), 1.0)
    assert pos == pytest.approx((0.0, 0.0, -6.0))
    assert len(c.timeline("cam")) == 1
    assert c.timeline("cam")[0]["t"] == 1.0


def test_first_step_snaps():
    c = make()
    c.step("cam", (0, 0, 0), (0, 0, -1), 1.0)
    assert c.timeline("cam")[0]["position"] == pytest.approx([0.0, 0.0, -6.0])


def test_step_smooths_toward_desired():
    c = make()
    c.step("cam", (0, 0, 0), (0, 0, -1), 1.0)
    c.step("cam", (0, 0, 10), (0, 0, -1), 2.0)
    assert c.timeline("cam")[-1]["position"] == pytest.approx([0.0, 0.0, -1.0])


def test_repeated_steps_converge():
    c = make()
    c.step("cam", (0, 0, 0), (0, 0, -1), 1.0)
    for i in range(20):
        c.step("cam", (0, 0, 10), (0, 0, -1), 2.0 + i)
    assert c.timeline("cam")[-1]["position"] == pytest.approx([0.0, 0.0, 4.0], abs=1e-3)


def test_smooth_one_snaps():
    c = make(smooth=1.0)
    c.step("cam", (0, 0, 0), (0, 0, -1), 1.0)
    c.step("cam", (0, 0, 10), (0, 0, -1), 2.0)
    assert c.timeline("cam")[-1]["position"] == pytest.approx([0.0, 0.0, 4.0])


def test_smooth_zero_holds():
    c = make(smooth=0.0)
    c.step("cam", (0, 0, 0), (0, 0, -1), 1.0)
    c.step("cam", (0, 0, 10), (0, 0, -1), 2.0)
    assert c.timeline("cam")[-1]["position"] == pytest.approx([0.0, 0.0, -6.0])


def test_timeline_filters_by_time():
    c = make()
    for i in range(3):
        c.step("cam", (0, 0, i), (0, 0, -1), float(i + 1))
    entries = c.timeline("cam", 1.5, 2.5)
    assert [e["t"] for e in entries] == [2.0]
    assert [e["t"] for e in c.timeline("cam")] == [1.0, 2.0, 3.0]


def test_replay_seek_uses_recorded_position():
    c = make()
    c.step("cam", (0, 0, 0), (0, 0, -1), 1.0)
    c.step("cam", (0, 0, 10), (0, 0, -1), 2.0)
    pos = c.replay_seek("cam", 1.5)
    assert pos == pytest.approx([0.0, 0.0, -6.0])
    assert c.replay_seek("cam", 99) == pytest.approx([0.0, 0.0, -1.0])
    with pytest.raises(ValueError):
        c.replay_seek("cam", 0.5)


def test_state_is_a_copy():
    c = make()
    c.snap("cam", (0, 0, 0), (0, 0, -1), 1.0)
    st = c.state()
    st["rigs"]["cam"]["position"][2] = 99.0
    assert c.state()["rigs"]["cam"]["position"][2] == pytest.approx(-6.0)
