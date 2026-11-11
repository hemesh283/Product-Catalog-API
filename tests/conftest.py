import pytest
from fastapi.testclient import TestClient

from app import main
from app.cache import TTLCache
from app.rate_limiter import FixedWindowRateLimiter


class FakeClock:
    """A controllable clock for tests: time only moves when the test says so."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def client(clock, monkeypatch):
    monkeypatch.setattr(
        main, "cache", TTLCache(ttl_seconds=main.CACHE_TTL_SECONDS, clock=clock)
    )
    monkeypatch.setattr(
        main,
        "rate_limiter",
        FixedWindowRateLimiter(
            limit=main.RATE_LIMIT,
            window_seconds=main.RATE_LIMIT_WINDOW_SECONDS,
            clock=clock,
        ),
    )
    return TestClient(main.app)