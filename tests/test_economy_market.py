import pytest

import economy_market as em


def book(*orders):
    book_obj = em.OrderBook()
    for order in orders:
        book_obj.submit(*order)
    return book_obj


def test_submit_records_bid():
    book_obj = em.OrderBook()
    book_obj.submit("b1", "buy", 100, 5, 0)
    bid = book_obj.book()["bids"][0]
    assert (bid["id"], bid["price"], bid["qty"]) == ("b1", 100, 5)


def test_duplicate_order_id_is_rejected():
    book_obj = book(("b1", "buy", 100, 5, 0))
    with pytest.raises(ValueError):
        book_obj.submit("b1", "sell", 101, 1, 1)


def test_invalid_side_is_rejected():
    with pytest.raises(ValueError):
        em.OrderBook().submit("b1", "hold", 100, 1, 0)


def test_price_must_be_positive_integer():
    with pytest.raises(ValueError):
        em.OrderBook().submit("b1", "buy", 0, 1, 0)
    with pytest.raises(ValueError):
        em.OrderBook().submit("b2", "buy", 10.5, 1, 0)


def test_quantity_must_be_positive_integer():
    with pytest.raises(ValueError):
        em.OrderBook().submit("b1", "buy", 100, 0, 0)


def test_time_must_be_non_negative_integer():
    with pytest.raises(ValueError):
        em.OrderBook().submit("b1", "buy", 100, 1, -1)


def test_no_trade_when_spread_is_positive():
    book_obj = book(("b1", "buy", 100, 5, 0), ("s1", "sell", 101, 5, 1))
    assert book_obj.match() == []
    assert len(book_obj.book()["bids"]) == 1
    assert len(book_obj.book()["asks"]) == 1


def test_buy_maker_sets_trade_price():
    book_obj = book(("b1", "buy", 110, 5, 0), ("s1", "sell", 90, 5, 1))
    assert book_obj.match() == [{"buy": "b1", "sell": "s1", "price": 110, "qty": 5}]
    assert book_obj.book() == {"bids": [], "asks": []}


def test_sell_maker_sets_trade_price():
    book_obj = book(("s1", "sell", 100, 5, 0), ("b1", "buy", 120, 5, 1))
    trades = book_obj.match()
    assert len(trades) == 1
    assert trades[0]["price"] == 100


def test_partial_fill_keeps_remainder():
    book_obj = book(("s1", "sell", 100, 10, 0), ("b1", "buy", 100, 4, 1))
    trades = book_obj.match()
    assert trades[0]["qty"] == 4
    assert book_obj.book()["asks"][0]["qty"] == 6
    assert book_obj.book()["bids"] == []


def test_price_priority_chooses_highest_bid():
    book_obj = book(
        ("b1", "buy", 100, 5, 0),
        ("b2", "buy", 105, 5, 1),
        ("s1", "sell", 95, 5, 2),
    )
    trades = book_obj.match()
    assert len(trades) == 1
    assert trades[0]["buy"] == "b2"
    assert trades[0]["price"] == 105
    assert book_obj.book()["bids"][0]["id"] == "b1"


def test_time_priority_at_same_price():
    book_obj = book(
        ("b1", "buy", 100, 5, 0),
        ("b2", "buy", 100, 5, 1),
        ("s1", "sell", 100, 5, 2),
    )
    trades = book_obj.match()
    assert trades[0]["buy"] == "b1"
    assert book_obj.book()["bids"][0]["id"] == "b2"


def test_large_order_sweeps_multiple_asks():
    book_obj = book(
        ("a1", "sell", 100, 3, 0),
        ("a2", "sell", 101, 3, 1),
        ("b1", "buy", 102, 5, 2),
    )
    trades = book_obj.match()
    assert [(t["price"], t["qty"]) for t in trades] == [(100, 3), (101, 2)]
    remaining = book_obj.book()["asks"]
    assert remaining[0]["id"] == "a2"
    assert remaining[0]["qty"] == 1


def test_cancel_removes_order():
    book_obj = book(("b1", "buy", 100, 5, 0))
    book_obj.cancel("b1")
    assert book_obj.book()["bids"] == []
    with pytest.raises(ValueError):
        book_obj.cancel("b1")


def test_state_snapshot_is_independent():
    book_obj = book(("s1", "sell", 100, 10, 0), ("b1", "buy", 100, 4, 1))
    book_obj.match()
    snapshot = book_obj.state()
    snapshot["trades"][0]["qty"] = 99
    snapshot["asks"][0]["qty"] = 99
    assert book_obj.state()["trades"][0]["qty"] == 4
    assert book_obj.state()["asks"][0]["qty"] == 6
