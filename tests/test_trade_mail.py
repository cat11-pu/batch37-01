import pytest

import trade_mail as tm

WALLETS = {
    "alice": {"gold": 100, "items": {"sword": 2, "gem": 1}},
    "bob": {"gold": 50, "items": {"shield": 1}},
    "eve": {"gold": 0, "items": {}},
}


def mailbox():
    wallets = {
        name: {"gold": data["gold"], "items": dict(data["items"])}
        for name, data in WALLETS.items()
    }
    return tm.TradeMail(wallets)


def test_send_escrows_attachment():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 0, 0, 100)
    state = mail.state()
    assert state["mails"]["m1"]["status"] == "pending"
    assert state["wallets"]["alice"]["items"]["sword"] == 1


def test_unknown_recipient_is_rejected():
    mail = mailbox()
    with pytest.raises(ValueError):
        mail.send("m1", "alice", "ghost", {"sword": 1}, 0, 0, 100)


def test_empty_attachment_is_rejected():
    mail = mailbox()
    with pytest.raises(ValueError):
        mail.send("m1", "alice", "bob", {}, 0, 0, 100)


def test_negative_price_is_rejected():
    mail = mailbox()
    with pytest.raises(ValueError):
        mail.send("m1", "alice", "bob", {"sword": 1}, -5, 0, 100)


def test_duplicate_mail_id_is_rejected():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 0, 0, 100)
    with pytest.raises(ValueError):
        mail.send("m1", "alice", "bob", {"gem": 1}, 0, 1, 100)


def test_zero_ttl_is_rejected():
    mail = mailbox()
    with pytest.raises(ValueError):
        mail.send("m1", "alice", "bob", {"sword": 1}, 0, 0, 0)


def test_sender_cannot_claim_own_mail():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 0, 0, 100)
    with pytest.raises(PermissionError):
        mail.claim("m1", "alice", 1)


def test_outsider_cannot_claim():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 0, 0, 100)
    with pytest.raises(PermissionError):
        mail.claim("m1", "eve", 1)


def test_cod_claim_transfers_gold_and_item():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 30, 0, 100)
    mail.claim("m1", "bob", 5)
    state = mail.state()
    assert state["mails"]["m1"]["status"] == "claimed"
    assert state["wallets"]["bob"]["gold"] == 20
    assert state["wallets"]["alice"]["gold"] == 130
    assert state["wallets"]["bob"]["items"]["sword"] == 1
    assert state["wallets"]["alice"]["items"]["sword"] == 1


def test_insufficient_gold_keeps_mail_pending():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 80, 0, 100)
    with pytest.raises(ValueError):
        mail.claim("m1", "bob", 5)
    state = mail.state()
    assert state["mails"]["m1"]["status"] == "pending"
    assert state["wallets"]["bob"]["gold"] == 50
    assert state["wallets"]["alice"]["items"]["sword"] == 1


def test_free_mail_does_not_move_gold():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"gem": 1}, 0, 0, 100)
    mail.claim("m1", "bob", 5)
    state = mail.state()
    assert state["wallets"]["bob"]["gold"] == 50
    assert state["wallets"]["alice"]["gold"] == 100
    assert state["wallets"]["bob"]["items"]["gem"] == 1


def test_second_claim_is_rejected():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 30, 0, 100)
    mail.claim("m1", "bob", 5)
    with pytest.raises(ValueError):
        mail.claim("m1", "bob", 6)


def test_expired_mail_returns_item_to_sender():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 0, 0, 10)
    expired = mail.expire(10)
    state = mail.state()
    assert expired == ["m1"]
    assert state["mails"]["m1"]["status"] == "expired"
    assert state["wallets"]["alice"]["items"]["sword"] == 2


def test_expired_mail_cannot_be_claimed():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"sword": 1}, 0, 0, 10)
    with pytest.raises(ValueError):
        mail.claim("m1", "bob", 10)


def test_inbox_lists_pending_mail_only():
    mail = mailbox()
    mail.send("m1", "alice", "bob", {"gem": 1}, 0, 0, 100)
    mail.send("m2", "alice", "bob", {"sword": 1}, 0, 0, 100)
    mail.claim("m1", "bob", 1)
    assert mail.inbox("bob") == ["m2"]
    assert mail.inbox("alice") == []
