import pytest

import daily_streak as ds

T0 = 86400 * 20


def manager(grace_days=0, offset=0):
    return ds.DailyStreak(utc_offset_minutes=offset, grace_days=grace_days)


def test_local_day_respects_utc_offset():
    base = manager(offset=0)
    shifted = manager(offset=480)
    assert base.local_day(T0 - 1) == 19
    assert shifted.local_day(T0 - 1) == 20


def test_first_check_in_starts_streak():
    m = manager()
    out = m.check_in("alice", T0 + 10)
    assert out["streak"] == 1
    assert out["day"] == 20
    assert m.streak("alice") == 1


def test_same_day_check_in_is_rejected():
    m = manager()
    m.check_in("alice", T0 + 10)
    with pytest.raises(ValueError):
        m.check_in("alice", T0 + 3600)


def test_consecutive_day_extends_streak():
    m = manager()
    m.check_in("alice", T0 + 10)
    out = m.check_in("alice", T0 + 86400 + 10)
    assert out["streak"] == 2


def test_missed_day_resets_streak():
    m = manager()
    m.check_in("alice", T0 + 10)
    m.check_in("alice", T0 + 86400 + 10)
    out = m.check_in("alice", T0 + 3 * 86400 + 10)
    assert out["streak"] == 1


def test_grace_day_absorbs_one_skip():
    m = manager(grace_days=1)
    m.check_in("alice", T0 + 10)
    out = m.check_in("alice", T0 + 2 * 86400 + 10)
    assert out["streak"] == 2


def test_grace_does_not_absorb_two_skips():
    m = manager(grace_days=1)
    m.check_in("alice", T0 + 10)
    out = m.check_in("alice", T0 + 3 * 86400 + 10)
    assert out["streak"] == 1


def test_best_streak_keeps_historical_max():
    m = manager()
    m.check_in("alice", T0 + 10)
    m.check_in("alice", T0 + 86400 + 10)
    m.check_in("alice", T0 + 2 * 86400 + 10)
    m.check_in("alice", T0 + 5 * 86400 + 10)
    assert m.streak("alice") == 1
    assert m.best("alice") == 3


def test_total_check_ins_are_counted():
    m = manager(grace_days=1)
    m.check_in("alice", T0 + 10)
    m.check_in("alice", T0 + 2 * 86400 + 10)
    m.check_in("alice", T0 + 3 * 86400 + 10)
    assert m.state()["players"]["alice"]["total"] == 3


def test_streak_of_unknown_player_is_rejected():
    m = manager()
    with pytest.raises(ValueError):
        m.streak("ghost")


def test_negative_timestamp_is_rejected():
    m = manager()
    with pytest.raises(ValueError):
        m.check_in("alice", -1)


def test_offset_out_of_range_is_rejected():
    m = manager()
    with pytest.raises(ValueError):
        m.set_offset(2000)


def test_negative_grace_days_are_rejected():
    with pytest.raises(ValueError):
        ds.DailyStreak(utc_offset_minutes=0, grace_days=-2)


def test_same_instant_duplicate_survives_offset_change():
    m = manager(offset=0)
    m.check_in("alice", T0 + 80000)
    m.set_offset(480)
    with pytest.raises(ValueError):
        m.check_in("alice", T0 + 80000)
    assert m.streak("alice") == 1


def test_state_is_a_detached_snapshot():
    m = manager()
    m.check_in("alice", T0 + 10)
    snap = m.state()
    snap["players"]["alice"]["streak"] = 99
    assert m.streak("alice") == 1
