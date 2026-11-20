import pytest

import session_lifecycle as sl


def store():
    return sl.SessionStore(100, 1000)


def test_create_returns_session():
    assert store().create("alice", 0)


def test_validate_returns_user():
    game = store()
    sid = game.create("alice", 0)
    assert game.validate(sid, 1) == "alice"


def test_idle_timeout_expires():
    game = store()
    sid = game.create("alice", 0)
    with pytest.raises(ValueError):
        game.validate(sid, 101)


def test_absolute_timeout_expires():
    game = sl.SessionStore(100, 50)
    sid = game.create("alice", 0)
    with pytest.raises(ValueError):
        game.validate(sid, 51)


def test_touch_extends_idle():
    game = store()
    sid = game.create("alice", 0)
    game.touch(sid, 90)
    assert game.validate(sid, 150) == "alice"


def test_touch_does_not_extend_absolute():
    game = sl.SessionStore(100, 120)
    sid = game.create("alice", 0)
    game.touch(sid, 100)
    with pytest.raises(ValueError):
        game.validate(sid, 121)


def test_revoke_invalidates():
    game = store()
    sid = game.create("alice", 0)
    game.revoke(sid)
    with pytest.raises(ValueError):
        game.validate(sid, 1)


def test_rotate_returns_new_id():
    game = store()
    sid = game.create("alice", 0)
    new_sid = game.rotate(sid, 1)
    assert new_sid != sid


def test_rotate_invalidates_old_id():
    game = store()
    sid = game.create("alice", 0)
    new_sid = game.rotate(sid, 1)
    with pytest.raises(ValueError):
        game.validate(sid, 2)
    assert game.validate(new_sid, 2) == "alice"


def test_unknown_session_raises():
    with pytest.raises(ValueError):
        store().validate("ghost", 0)


def test_unknown_revoke_raises():
    with pytest.raises(ValueError):
        store().revoke("ghost")


def test_time_backwards_raises():
    game = store()
    sid = game.create("alice", 10)
    with pytest.raises(ValueError):
        game.validate(sid, 9)


def test_invalid_ttls_raise():
    with pytest.raises(ValueError):
        sl.SessionStore(0, 100)


def test_session_ids_are_unique():
    game = store()
    assert game.create("alice", 0) != game.create("alice", 0)


def test_rotate_unknown_session_raises():
    with pytest.raises(ValueError):
        store().rotate("ghost", 0)
