import threading

import pytest

import trade_escrow as te

INV = {"alice": {"sword": 1, "gold": 100}, "bob": {"shield": 1, "gold": 50}}


def escrow():
    return te.TradeEscrow({k: dict(v) for k, v in INV.items()})


def test_offer_creates_pending_trade():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    s = e.state()
    assert s["trades"]["t1"]["status"] == "pending"
    assert s["trades"]["t1"]["confirmed"] == []
    assert s["inventories"] == INV


def test_unknown_player_is_rejected():
    e = escrow()
    with pytest.raises(ValueError):
        e.offer("t1", "ghost", "bob", {"sword": 1}, {"gold": 20}, now=0)


def test_missing_item_is_rejected():
    e = escrow()
    with pytest.raises(ValueError):
        e.offer("t1", "alice", "bob", {"sword": 2}, {"gold": 20}, now=0)


def test_duplicate_trade_id_is_rejected():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    with pytest.raises(ValueError):
        e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)


def test_one_confirm_stays_pending():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    e.confirm("t1", "alice", now=1)
    assert e.state()["trades"]["t1"]["status"] == "pending"


def test_both_confirm_commits_atomically():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    e.confirm("t1", "alice", now=1)
    e.confirm("t1", "bob", now=2)
    s = e.state()
    assert s["trades"]["t1"]["status"] == "completed"
    assert s["inventories"]["alice"] == {"sword": 0, "gold": 120}
    assert s["inventories"]["bob"] == {"shield": 1, "gold": 30}


def test_duplicate_confirm_is_idempotent():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    e.confirm("t1", "alice", now=1)
    e.confirm("t1", "bob", now=2)
    e.confirm("t1", "bob", now=3)
    assert e.state()["inventories"]["alice"]["gold"] == 120


def test_cancel_pending_restores_nothing():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    e.cancel("t1", "alice", now=1)
    s = e.state()
    assert s["trades"]["t1"]["status"] == "cancelled"
    assert s["inventories"] == INV


def test_confirm_after_cancel_is_rejected():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    e.cancel("t1", "alice", now=1)
    with pytest.raises(ValueError):
        e.confirm("t1", "bob", now=2)


def test_expired_trade_cannot_confirm():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0, ttl=5)
    with pytest.raises(ValueError):
        e.confirm("t1", "alice", now=6)


def test_concurrent_confirm_only_one_commit():
    e = escrow()
    e.offer("t1", "alice", "bob", {"sword": 1}, {"gold": 20}, now=0)
    e.confirm("t1", "alice", now=1)
    results = []

    def worker():
        try:
            e.confirm("t1", "bob", now=2)
            results.append(True)
        except ValueError:
            results.append(False)

    ts = [threading.Thread(target=worker) for _ in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert results.count(True) == 1
    assert e.state()["inventories"]["alice"]["gold"] == 120


def test_state_is_a_copy():
    e = escrow()
    s = e.state()
    s["inventories"]["alice"]["gold"] = 999
    assert e.state()["inventories"]["alice"]["gold"] == 100


def test_empty_items_is_rejected():
    e = escrow()
    with pytest.raises(ValueError):
        e.offer("t1", "alice", "bob", {}, {"gold": 20}, now=0)


def test_same_player_is_rejected():
    e = escrow()
    with pytest.raises(ValueError):
        e.offer("t1", "alice", "alice", {"sword": 1}, {"gold": 20}, now=0)


def test_recover_replays_committed_trade():
    e = escrow()
    journal = [
        {"type": "offer", "trade_id": "t1", "a": "alice", "b": "bob", "items_a": {"sword": 1}, "items_b": {"gold": 20}},
        {"type": "confirm", "trade_id": "t1", "player": "alice"},
        {"type": "confirm", "trade_id": "t1", "player": "bob"},
    ]
    e.recover(journal)
    s = e.state()
    assert s["trades"]["t1"]["status"] == "completed"
    assert s["inventories"]["alice"]["gold"] == 120
