import pytest

import friend_gift as fg

DAY = 86400
T = DAY * 30


def manager(limit=5, ttl=3600):
    m = fg.GiftManager(daily_limit=limit, ttl=ttl)
    m.add_friend("alice", "bob")
    return m


def test_send_between_friends_shows_as_pending():
    m = manager()
    rec = m.send("alice", "bob", "g1", now=T + 100, count=2)
    assert rec["count"] == 2
    assert rec["expires"] == T + 100 + 3600
    assert m.pending("bob", T + 200) == ["g1"]


def test_send_to_stranger_is_rejected():
    m = manager()
    with pytest.raises(ValueError):
        m.send("alice", "carol", "g1", now=T + 100)


def test_adding_self_as_friend_is_rejected():
    m = manager()
    with pytest.raises(ValueError):
        m.add_friend("alice", "alice")


def test_blank_friend_name_is_rejected():
    m = manager()
    with pytest.raises(ValueError):
        m.add_friend("alice", "  ")


def test_daily_limit_counts_gift_units():
    m = manager(limit=3)
    m.send("alice", "bob", "g1", now=T + 100, count=2)
    with pytest.raises(ValueError):
        m.send("alice", "bob", "g2", now=T + 200, count=2)


def test_daily_limit_resets_next_day():
    m = manager(limit=1, ttl=10 * DAY)
    m.send("alice", "bob", "g1", now=T + 100)
    m.send("alice", "bob", "g2", now=T + DAY + 100)
    assert m.pending("bob", T + DAY + 200) == ["g1", "g2"]


def test_duplicate_gift_id_same_day_is_rejected():
    m = manager()
    m.send("alice", "bob", "g1", now=T + 100)
    with pytest.raises(ValueError):
        m.send("alice", "bob", "g1", now=T + 500)


def test_duplicate_gift_id_next_day_is_allowed():
    m = manager()
    m.send("alice", "bob", "g1", now=T + 100)
    rec = m.send("alice", "bob", "g1", now=T + DAY + 100)
    assert rec["gift_id"] == "g1"
    assert rec["sent_at"] == T + DAY + 100


def test_claim_without_reciprocal_gift_is_rejected():
    m = manager()
    m.send("alice", "bob", "g1", now=T + 100)
    with pytest.raises(ValueError):
        m.claim("bob", "alice", "g1", now=T + 200)


def test_claim_after_reciprocal_gift_succeeds():
    m = manager()
    m.send("alice", "bob", "g1", now=T + 100)
    m.send("bob", "alice", "g2", now=T + 150)
    out = m.claim("bob", "alice", "g1", now=T + 200)
    assert out["gift_id"] == "g1"
    assert m.pending("bob", T + 300) == []


def test_claiming_same_gift_twice_is_rejected():
    m = manager()
    m.send("alice", "bob", "g1", now=T + 100)
    m.send("bob", "alice", "g2", now=T + 150)
    m.claim("bob", "alice", "g1", now=T + 200)
    with pytest.raises(ValueError):
        m.claim("bob", "alice", "g1", now=T + 250)


def test_claim_by_non_receiver_is_rejected():
    m = manager()
    m.send("alice", "bob", "g1", now=T + 100)
    m.add_friend("bob", "carol")
    with pytest.raises(ValueError):
        m.claim("carol", "alice", "g1", now=T + 200)


def test_expired_gift_cannot_be_claimed():
    m = manager(ttl=100)
    m.send("alice", "bob", "g1", now=T + 100)
    m.send("bob", "alice", "g2", now=T + 150)
    with pytest.raises(ValueError):
        m.claim("bob", "alice", "g1", now=T + 300)


def test_pending_skips_expired_gifts():
    m = manager(ttl=100)
    m.send("alice", "bob", "g1", now=T + 100)
    m.send("alice", "bob", "g2", now=T + 250)
    assert m.pending("bob", T + 260) == ["g2"]


def test_state_is_a_detached_snapshot():
    m = manager()
    m.send("alice", "bob", "g1", now=T + 100)
    snap = m.state()
    snap["gifts"][0]["count"] = 99
    assert m.pending("bob", T + 200) == ["g1"]
    assert m.state()["gifts"][0]["count"] == 1
