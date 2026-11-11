import pytest

from app.rate_limiter import FixedWindowRateLimiter


def test_allows_up_to_limit_then_blocks(clock):
    limiter = FixedWindowRateLimiter(limit=3, window_seconds=60, clock=clock)
    results = [limiter.check("a").allowed for _ in range(4)]
    assert results == [True, True, True, False]


def test_clients_have_separate_counters(clock):
    limiter = FixedWindowRateLimiter(limit=1, window_seconds=60, clock=clock)
    assert limiter.check("a").allowed
    assert not limiter.check("a").allowed
    assert limiter.check("b").allowed


def test_new_window_overwrites_old_entry(clock):
    limiter = FixedWindowRateLimiter(limit=1, window_seconds=60, clock=clock)
    limiter.check("a")
    clock.advance(60)
    assert limiter.check("a").allowed
    assert limiter._clients["a"] == (1, 1)


@pytest.mark.parametrize("limit, window", [(0, 60), (-1, 60), (10, 0)])
def test_invalid_config_is_rejected(limit, window):
    with pytest.raises(ValueError):
        FixedWindowRateLimiter(limit=limit, window_seconds=window)