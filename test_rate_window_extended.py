import pytest

import rate_window as rw


def test_cost_over_limit_is_rejected_without_consuming_quota():
    limiter = rw.SlidingWindowLimiter(limit=2, window=10)
    assert limiter.allow("ip", 0, cost=3) is False
    assert limiter.remaining("ip", 0) == 2
    assert limiter.allow("ip", 1, cost=2) is True


def test_each_event_slides_out_exactly_at_its_own_boundary():
    limiter = rw.SlidingWindowLimiter(limit=2, window=10)
    assert limiter.allow("ip", 0) is True
    assert limiter.allow("ip", 5) is True
    assert limiter.allow("ip", 9) is False
    assert limiter.allow("ip", 10) is True
    assert limiter.remaining("ip", 10) == 0
    assert limiter.remaining("ip", 15) == 1
    assert limiter.remaining("ip", 20) == 2


def test_remaining_is_stable_and_does_not_consume_quota():
    limiter = rw.SlidingWindowLimiter(limit=3, window=10)
    assert limiter.allow("ip", 0, cost=2) is True
    assert limiter.remaining("ip", 0) == 1
    assert limiter.remaining("ip", 0) == 1
    assert limiter.allow("ip", 0, cost=1) is True


def test_time_cannot_move_backwards_through_remaining():
    limiter = rw.SlidingWindowLimiter(limit=3, window=10)
    limiter.allow("ip", 5)
    with pytest.raises(ValueError):
        limiter.remaining("ip", 4)


@pytest.mark.parametrize("limit", [-1, 0, 1.5, True, "1", None])
def test_invalid_limits_are_rejected(limit):
    with pytest.raises(ValueError):
        rw.SlidingWindowLimiter(limit, 10)


@pytest.mark.parametrize("window", [-1, 0, float("inf"), float("nan"), True, None])
def test_invalid_windows_are_rejected(window):
    with pytest.raises(ValueError):
        rw.SlidingWindowLimiter(1, window)


@pytest.mark.parametrize("cost", [-1, 0, 1.5, True, "1", None])
def test_invalid_costs_are_rejected(cost):
    limiter = rw.SlidingWindowLimiter(1, 10)
    with pytest.raises(ValueError):
        limiter.allow("ip", 0, cost=cost)


def test_shared_storage_is_atomic_and_survives_restart(tmp_path):
    path = tmp_path / "rate-window.sqlite3"
    first = rw.SlidingWindowLimiter(3, 10, storage_path=path)
    assert first.allow("ip", 0, cost=2) is True
    assert first.allow("ip", 1) is True
    first.close()

    second = rw.SlidingWindowLimiter(3, 10, storage_path=path)
    assert second.remaining("ip", 1) == 0
    assert second.allow("ip", 2) is False
    assert second.allow("ip", 10) is True
    second.close()


def test_shared_storage_rejects_clock_regression(tmp_path):
    path = tmp_path / "rate-window.sqlite3"
    first = rw.SlidingWindowLimiter(3, 10, storage_path=path)
    second = rw.SlidingWindowLimiter(3, 10, storage_path=path)
    first.allow("ip", 5)
    with pytest.raises(ValueError):
        second.allow("ip", 4)
    first.close()
    second.close()


def test_tenant_and_endpoint_are_part_of_the_bucket_key():
    limiter = rw.SlidingWindowLimiter(1, 10)
    assert limiter.allow("user", 0, tenant="t1", endpoint="/login") is True
    assert limiter.allow("user", 0, tenant="t2", endpoint="/login") is True
    assert limiter.allow("user", 0, tenant="t1", endpoint="/sms") is True
    assert limiter.allow("user", 0, tenant="t1", endpoint="/login") is False
