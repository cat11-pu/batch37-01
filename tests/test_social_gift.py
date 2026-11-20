import pytest

import social_gift as sg

PLAYERS = {
    "alice": {"online": True, "items": {"cake": 3, "tea": 1}},
    "bob": {"online": False, "items": {}},
    "carol": {"online": True, "items": {"cake": 1}},
}


def social(**cfg):
    base = {"daily_gifts": 2, "mail_ttl": 50}
    base.update(cfg)
    players = {
        pid: {"online": v["online"], "items": dict(v["items"])}
        for pid, v in PLAYERS.items()
    }
    return sg.SocialGift(players, base)


def befriend(s, a, b, now=0):
    s.request_friend(a, b, now)
    s.accept_friend(a, b, now + 1)


def test_friend_request_and_accept():
    s = social()
    befriend(s, "alice", "bob")
    assert s.friends("alice") == ["bob"]
    assert s.friends("bob") == ["alice"]


def test_accept_without_request_rejected():
    s = social()
    with pytest.raises(ValueError):
        s.accept_friend("alice", "bob")


def test_duplicate_request_rejected():
    s = social()
    s.request_friend("alice", "bob", 0)
    with pytest.raises(ValueError):
        s.request_friend("alice", "bob", 1)


def test_unfriend_removes_both_sides():
    s = social()
    befriend(s, "alice", "bob")
    assert s.friends("alice") == ["bob"]
    s.unfriend("alice", "bob")
    assert s.friends("alice") == []
    assert s.friends("bob") == []


def test_gift_requires_friendship():
    s = social()
    with pytest.raises(ValueError):
        s.send_gift("g1", "alice", "carol", {"cake": 1}, 0)


def test_gift_to_self_rejected():
    s = social()
    with pytest.raises(ValueError):
        s.send_gift("g1", "alice", "alice", {"cake": 1}, 0)


def test_gift_to_online_receiver_is_immediate():
    s = social()
    befriend(s, "alice", "carol")
    s.send_gift("g1", "alice", "carol", {"cake": 1}, 5)
    st = s.state()
    assert st["players"]["alice"]["items"]["cake"] == 2
    assert st["players"]["carol"]["items"]["cake"] == 2
    assert s.inbox("carol") == []


def test_gift_to_offline_receiver_creates_mail():
    s = social()
    befriend(s, "alice", "bob")
    s.send_gift("g1", "alice", "bob", {"cake": 1}, 5)
    st = s.state()
    assert st["players"]["alice"]["items"]["cake"] == 2
    assert st["players"]["bob"]["items"] == {}
    mail = s.inbox("bob")[0]
    assert mail["items"] == {"cake": 1}
    assert mail["expires"] == 55
    assert mail["status"] == "unread"


def test_claim_delivers_mail():
    s = social()
    befriend(s, "alice", "bob")
    s.send_gift("g1", "alice", "bob", {"cake": 1}, 5)
    mail_id = s.inbox("bob")[0]["mail_id"]
    s.claim("bob", mail_id, 6)
    assert s.state()["players"]["bob"]["items"]["cake"] == 1
    assert s.inbox("bob")[0]["status"] == "claimed"


def test_claim_twice_rejected():
    s = social()
    befriend(s, "alice", "bob")
    s.send_gift("g1", "alice", "bob", {"cake": 1}, 5)
    mail_id = s.inbox("bob")[0]["mail_id"]
    s.claim("bob", mail_id, 6)
    with pytest.raises(ValueError):
        s.claim("bob", mail_id, 7)


def test_claim_by_other_player_rejected():
    s = social()
    befriend(s, "alice", "bob")
    s.send_gift("g1", "alice", "bob", {"cake": 1}, 5)
    mail_id = s.inbox("bob")[0]["mail_id"]
    with pytest.raises(ValueError):
        s.claim("carol", mail_id, 6)


def test_expired_mail_cannot_be_claimed():
    s = social()
    befriend(s, "alice", "bob")
    s.send_gift("g1", "alice", "bob", {"cake": 1}, 5)
    mail_id = s.inbox("bob")[0]["mail_id"]
    s.expire(60)
    with pytest.raises(ValueError):
        s.claim("bob", mail_id, 61)


def test_daily_gift_limit():
    s = social()
    befriend(s, "alice", "bob")
    s.send_gift("g1", "alice", "bob", {"cake": 1}, 0)
    s.send_gift("g2", "alice", "bob", {"cake": 1}, 1)
    with pytest.raises(ValueError):
        s.send_gift("g3", "alice", "bob", {"tea": 1}, 2)
    s.send_gift("g4", "alice", "bob", {"tea": 1}, 86400)


def test_failed_gift_does_not_consume_quota():
    s = social()
    befriend(s, "alice", "bob")
    with pytest.raises(ValueError):
        s.send_gift("g1", "alice", "bob", {"cake": 5}, 0)
    s.send_gift("g2", "alice", "bob", {"cake": 1}, 1)
    s.send_gift("g3", "alice", "bob", {"cake": 1}, 2)


def test_state_is_a_copy():
    s = social()
    befriend(s, "alice", "bob")
    s.send_gift("g1", "alice", "bob", {"cake": 1}, 5)
    st = s.state()
    st["players"]["bob"]["mail"][0]["status"] = "claimed"
    st["players"]["alice"]["items"]["cake"] = 99
    assert s.inbox("bob")[0]["status"] == "unread"
    assert s.state()["players"]["alice"]["items"]["cake"] == 2
