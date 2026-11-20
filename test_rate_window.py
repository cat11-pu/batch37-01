import pytest

import rate_window as rw


def limiter(limit=3, window=10):
    return rw.SlidingWindowLimiter(limit, window)


def test_first_request_is_allowed():
    assert limiter().allow("ip", 0) is True


def test_limit_is_reached():
    game = limiter(limit=2)
    assert game.allow("ip", 0) is True
    assert game.allow("ip", 1) is True
    assert game.allow("ip", 2) is False


def test_window_slides():
    game = limiter(limit=1, window=10)
    assert game.allow("ip", 0) is True
    assert game.allow("ip", 10) is True


def test_exact_boundary_is_excluded():
    game = limiter(limit=1, window=10)
    game.allow("ip", 0)
    assert game.allow("ip", 10) is True


def test_cost_is_counted():
    game = limiter(limit=5)
    assert game.allow("ip", 0, cost=3) is True
    assert game.allow("ip", 1, cost=3) is False


def test_cost_over_limit_is_rejected():
    game = limiter(limit=2)
    assert game.allow("ip", 0, cost=2) is True
    assert game.allow("ip", 1, cost=3) is False


def test_keys_are_isolated():
    game = limiter(limit=1)
    assert game.allow("a", 0) is True
    assert game.allow("b", 0) is True


def test_negative_cost_raises():
    with pytest.raises(ValueError):
        limiter().allow("ip", 0, cost=-1)


def test_zero_cost_raises():
    with pytest.raises(ValueError):
        limiter().allow("ip", 0, cost=0)


def test_invalid_limit_raises():
    with pytest.raises(ValueError):
        rw.SlidingWindowLimiter(0, 10)


def test_invalid_window_raises():
    with pytest.raises(ValueError):
        rw.SlidingWindowLimiter(1, 0)


def test_time_backwards_raises():
    game = limiter()
    game.allow("ip", 5)
    with pytest.raises(ValueError):
        game.allow("ip", 4)


def test_remaining_decreases():
    game = limiter(limit=3)
    game.allow("ip", 0, cost=2)
    assert game.remaining("ip", 0) == 1


def test_remaining_after_window():
    game = limiter(limit=3, window=10)
    game.allow("ip", 0, cost=3)
    assert game.remaining("ip", 10) == 3


def test_remaining_returns_zero_not_negative():
    game = limiter(limit=1)
    game.allow("ip", 0, cost=1)
    assert game.remaining("ip", 1) == 0
