import pytest

import currency_exchange as cx

WALLETS = {
    "alice": {"USD": 500, "JPY": 0},
    "bob": {"USD": 100, "JPY": 0},
}


def exchange(**overrides):
    params = {
        "fee_rate": 0.02,
        "min_amount": 10,
        "max_amount": 1000,
        "daily_limit": 2000,
        "rate_ttl": 60,
    }
    params.update(overrides)
    wallets = {name: dict(balances) for name, balances in WALLETS.items()}
    return cx.CurrencyExchange(wallets, **params)


def test_quote_reports_rate_fee_and_credit():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    result = game.quote(100, "USD", "JPY", 1)
    assert result["rate"] == pytest.approx(150.0)
    assert result["fee"] == pytest.approx(300.0)
    assert result["credited"] == pytest.approx(14700.0)


def test_quote_without_rate_raises():
    game = exchange()
    with pytest.raises(ValueError):
        game.quote(100, "USD", "JPY", 1)


def test_non_positive_amount_raises():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    with pytest.raises(ValueError):
        game.quote(0, "USD", "JPY", 1)


def test_amount_below_minimum_raises():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    with pytest.raises(ValueError):
        game.quote(5, "USD", "JPY", 1)


def test_amount_above_maximum_raises():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    with pytest.raises(ValueError):
        game.quote(1001, "USD", "JPY", 1)


def test_inverse_pair_is_derived():
    game = exchange()
    game.set_rate("JPY", "USD", 0.5, 0)
    result = game.quote(1000, "USD", "JPY", 1)
    assert result["rate"] == pytest.approx(2.0)
    assert result["credited"] == pytest.approx(1960.0)


def test_stale_rate_is_rejected():
    game = exchange(rate_ttl=10)
    game.set_rate("USD", "JPY", 150, 0)
    with pytest.raises(ValueError):
        game.quote(100, "USD", "JPY", 11)


def test_non_positive_rate_is_rejected():
    game = exchange()
    with pytest.raises(ValueError):
        game.set_rate("USD", "JPY", 0, 0)


def test_same_currency_rate_is_rejected():
    game = exchange()
    with pytest.raises(ValueError):
        game.set_rate("USD", "USD", 1, 0)


def test_convert_moves_funds():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    result = game.convert("alice", 100, "USD", "JPY", 1)
    state = game.state()
    assert result["credited"] == pytest.approx(14700.0)
    assert state["wallets"]["alice"]["USD"] == pytest.approx(400)
    assert state["wallets"]["alice"]["JPY"] == pytest.approx(14700.0)


def test_convert_with_insufficient_balance_raises():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    with pytest.raises(ValueError):
        game.convert("bob", 200, "USD", "JPY", 1)
    state = game.state()
    assert state["wallets"]["bob"]["USD"] == 100
    assert state["wallets"]["bob"]["JPY"] == 0


def test_daily_limit_blocks_second_conversion():
    game = exchange(daily_limit=200)
    game.set_rate("USD", "JPY", 150, 0)
    game.convert("alice", 150, "USD", "JPY", 10)
    assert game.used_today("alice", 10) == pytest.approx(150)
    with pytest.raises(ValueError):
        game.convert("alice", 100, "USD", "JPY", 20)


def test_daily_limit_resets_on_next_day():
    game = exchange(daily_limit=200, rate_ttl=1000000)
    game.set_rate("USD", "JPY", 150, 0)
    game.convert("alice", 150, "USD", "JPY", 10)
    game.convert("alice", 100, "USD", "JPY", 86410)
    assert game.used_today("alice", 86410) == pytest.approx(100)
    assert game.used_today("alice", 10) == pytest.approx(150)


def test_repeated_request_id_is_idempotent():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    first = game.convert("alice", 100, "USD", "JPY", 1, request_id="r-1")
    second = game.convert("alice", 100, "USD", "JPY", 1, request_id="r-1")
    assert first["credited"] == pytest.approx(14700.0)
    assert second["credited"] == pytest.approx(14700.0)
    state = game.state()
    assert state["wallets"]["alice"]["USD"] == pytest.approx(400)
    assert game.used_today("alice", 1) == pytest.approx(100)


def test_state_returns_detached_copy():
    game = exchange()
    game.set_rate("USD", "JPY", 150, 0)
    snapshot = game.state()
    snapshot["wallets"]["alice"]["USD"] = 999999
    assert game.state()["wallets"]["alice"]["USD"] == 500
