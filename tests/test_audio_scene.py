import pytest

import audio_scene as au

BUSES = {
    "master": {"parent": None, "volume": 1.0},
    "sfx": {"parent": "master", "volume": 0.8},
    "music": {"parent": "master", "volume": 0.5},
    "voice": {"parent": "master", "volume": 1.0},
}


def scene(**cfg):
    base = {
        "max_channels": 2,
        "occlusion_floor": 0.2,
        "duck_source": "voice",
        "duck_target": "music",
        "duck_db": -6.0,
    }
    base.update(cfg)
    return au.AudioScene({k: dict(v) for k, v in BUSES.items()}, base)


def test_bus_gains_follow_hierarchy():
    s = scene()
    assert s.mix()["buses"] == {"master": 1.0, "sfx": 0.8, "music": 0.5, "voice": 1.0}


def test_mute_zeroes_subtree():
    s = scene()
    s.set_bus("sfx", mute=True)
    buses = s.mix()["buses"]
    assert buses["sfx"] == 0.0
    assert buses["master"] == 1.0


def test_distance_attenuation():
    s = scene()
    s.play("a", "sfx", (10, 0))
    assert s.mix()["active"]["a"]["gain"] == pytest.approx(0.0727)


def test_listener_move_recalculates():
    s = scene()
    s.play("a", "sfx", (10, 0))
    s.update((5, 0), [])
    assert s.mix()["active"]["a"]["gain"] == pytest.approx(0.1333)


def test_wall_occludes():
    s = scene()
    s.play("a", "sfx", (10, 0))
    s.update((0, 0), [((5, -1), (5, 1))])
    assert s.mix()["active"]["a"]["gain"] == pytest.approx(0.0145)


def test_wall_off_path_does_not_occlude():
    s = scene()
    s.play("a", "sfx", (10, 0))
    s.update((0, 0), [((5, 3), (5, 6))])
    assert s.mix()["active"]["a"]["gain"] == pytest.approx(0.0727)


def test_voice_ducks_music():
    s = scene()
    s.play("v", "voice", (10, 0))
    assert s.mix()["buses"]["music"] == pytest.approx(0.2506)
    assert s.mix()["buses"]["sfx"] == 0.8


def test_stop_voice_restores_music():
    s = scene()
    s.play("v", "voice", (10, 0))
    s.stop("v")
    assert s.mix()["buses"]["music"] == pytest.approx(0.5)


def test_channel_limit_evicts_lowest_priority():
    s = scene(max_channels=2)
    s.play("a", "sfx", None, priority=1)
    s.play("b", "sfx", None, priority=2)
    s.play("c", "sfx", None, priority=3)
    active = s.mix()["active"]
    assert "a" not in active
    assert set(active) == {"b", "c"}


def test_low_priority_rejected_when_full():
    s = scene(max_channels=1)
    s.play("a", "sfx", None, priority=1)
    with pytest.raises(ValueError):
        s.play("b", "sfx", None, priority=1)
    s.play("c", "sfx", None, priority=2)
    assert set(s.mix()["active"]) == {"c"}


def test_duplicate_sound_id_rejected():
    s = scene()
    s.play("a", "sfx", None)
    with pytest.raises(ValueError):
        s.play("a", "music", None)


def test_stop_removes_sound():
    s = scene()
    s.play("a", "sfx", None)
    s.stop("a")
    assert s.mix()["active"] == {}


def test_unknown_bus_rejected():
    s = scene()
    with pytest.raises(ValueError):
        s.play("a", "ui", None)


def test_ui_sound_is_not_attenuated():
    s = scene()
    s.play("a", "sfx", None)
    assert s.mix()["active"]["a"]["gain"] == pytest.approx(0.8)


def test_state_is_a_copy():
    s = scene()
    s.play("a", "sfx", (10, 0))
    st = s.state()
    st["buses"]["sfx"]["volume"] = 9.0
    st["active"]["a"]["loudness"] = 9.0
    assert s.mix()["buses"]["sfx"] == 0.8
    assert s.mix()["active"]["a"]["gain"] == pytest.approx(0.0727)
