import pytest

import mail_auction as ma

WALLET = {"alice": 200, "bob": 150, "cara": 150, "dave": 10}
ITEMS = {"alice": ["sword"], "bob": ["shield"], "cara": [], "dave": []}


def house():
    return ma.MailAuction(
        {k: v for k, v in WALLET.items()},
        {k: list(v) for k, v in ITEMS.items()},
    )


def test_list_item_moves_item_into_auction():
    h = house()
    assert h.list_item("alice", "sword", 50, now=0) == "a1"
    assert h.inventory("alice") == []
    s = h.state()
    assert s["auctions"]["a1"]["status"] == "open"
    assert s["auctions"]["a1"]["item"] == "sword"
    assert s["auctions"]["a1"]["deadline"] == 10


def test_bad_listing_is_rejected():
    h = house()
    with pytest.raises(ValueError):
        h.list_item("alice", "axe", 50, now=0)
    with pytest.raises(ValueError):
        h.list_item("alice", "sword", 0, now=0)
    with pytest.raises(ValueError):
        h.list_item("ghost", "sword", 50, now=0)
    assert h.inventory("alice") == ["sword"]


def test_bid_below_start_price_is_rejected():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    with pytest.raises(ValueError):
        h.bid("a1", "bob", 40, now=1)
    assert h.state()["auctions"]["a1"]["bids"] == []


def test_bid_must_exceed_current_high():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    assert h.bid("a1", "bob", 50, now=1) == 50
    with pytest.raises(ValueError):
        h.bid("a1", "cara", 50, now=2)
    assert h.bid("a1", "cara", 60, now=3) == 60


def test_seller_cannot_bid():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    with pytest.raises(ValueError):
        h.bid("a1", "alice", 80, now=1)


def test_bid_after_deadline_is_rejected():
    h = house()
    h.list_item("alice", "sword", 50, now=0, duration=5)
    assert h.bid("a1", "bob", 50, now=4) == 50
    with pytest.raises(ValueError):
        h.bid("a1", "cara", 70, now=5)


def test_close_before_deadline_is_rejected():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    with pytest.raises(ValueError):
        h.close("a1", now=9)


def test_tick_closes_auction_and_creates_cod_mail():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    h.bid("a1", "bob", 80, now=1)
    assert h.tick(10) == ["a1"]
    s = h.state()
    assert s["auctions"]["a1"]["status"] == "closed"
    mails = h.mailbox("bob")
    assert len(mails) == 1
    assert mails[0]["kind"] == "cod"
    assert mails[0]["amount"] == 80
    assert mails[0]["status"] == "unpaid"


def test_winner_cod_pays_seller_through_payout_mail():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    h.bid("a1", "bob", 80, now=1)
    h.tick(10)
    mail_id = h.mailbox("bob")[0]["id"]
    got = h.claim("bob", mail_id, now=11)
    assert got["kind"] == "cod"
    assert got["item"] == "sword"
    assert h.balance("bob") == 70
    assert h.inventory("bob") == ["shield", "sword"]
    payout = h.mailbox("alice")[0]
    assert payout["kind"] == "payout"
    received = h.claim("alice", payout["id"], now=12)
    assert received["amount"] == 80
    assert h.balance("alice") == 280


def test_cod_claim_without_funds_is_rejected():
    h = house()
    h.send_cod("bob", "dave", "shield", 80, now=0)
    mail_id = h.mailbox("dave")[0]["id"]
    with pytest.raises(ValueError):
        h.claim("dave", mail_id, now=1)
    assert h.balance("dave") == 10
    assert h.inventory("dave") == []
    assert h.mailbox("dave")[0]["status"] == "unpaid"


def test_bad_cod_send_is_rejected():
    h = house()
    with pytest.raises(ValueError):
        h.send_cod("alice", "bob", "axe", 20, now=0)
    with pytest.raises(ValueError):
        h.send_cod("bob", "bob", "shield", 20, now=0)
    with pytest.raises(ValueError):
        h.send_cod("bob", "cara", "shield", 0, now=0)
    assert h.inventory("bob") == ["shield"]


def test_expired_cod_returns_item_to_sender():
    h = house()
    h.send_cod("bob", "cara", "shield", 10, now=0, ttl=5)
    mail_id = h.mailbox("cara")[0]["id"]
    with pytest.raises(ValueError):
        h.claim("cara", mail_id, now=9)
    assert h.inventory("bob") == ["shield"]
    assert h.inventory("cara") == []
    assert h.mailbox("cara")[0]["status"] == "expired"


def test_expired_auction_without_bids_returns_item():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    assert h.tick(10) == ["a1"]
    assert h.state()["auctions"]["a1"]["status"] == "expired"
    back = h.mailbox("alice")[0]
    assert back["kind"] == "return"
    h.claim("alice", back["id"], now=11)
    assert h.inventory("alice") == ["sword"]


def test_cod_mail_cannot_be_claimed_twice():
    h = house()
    h.send_cod("bob", "cara", "shield", 30, now=0)
    mail_id = h.mailbox("cara")[0]["id"]
    h.claim("cara", mail_id, now=1)
    assert h.balance("cara") == 120
    with pytest.raises(ValueError):
        h.claim("cara", mail_id, now=2)
    assert h.balance("cara") == 120


def test_state_is_a_copy():
    h = house()
    h.list_item("alice", "sword", 50, now=0)
    snap = h.state()
    snap["wallet"]["alice"] = 99999
    snap["auctions"]["a1"]["status"] = "hacked"
    assert h.balance("alice") == 200
    assert h.state()["auctions"]["a1"]["status"] == "open"
