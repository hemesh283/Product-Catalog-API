import pytest

from app.cache import TTLCache


def test_get_missing_key_returns_none(clock):
    cache = TTLCache(ttl_seconds=30, clock=clock)
    assert cache.get("missing") is None


def test_set_then_get_returns_value(clock):
    cache = TTLCache(ttl_seconds=30, clock=clock)
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_expired_entry_is_removed_on_get(clock):
    cache = TTLCache(ttl_seconds=30, clock=clock)
    cache.set("k", "v")
    clock.advance(31)
    assert cache.get("k") is None
    assert "k" not in cache._store


def test_set_again_refreshes_expiry(clock):
    cache = TTLCache(ttl_seconds=30, clock=clock)
    cache.set("k", "old")
    clock.advance(20)
    cache.set("k", "new")
    clock.advance(20)
    assert cache.get("k") == "new"


def test_clear_removes_everything(clock):
    cache = TTLCache(ttl_seconds=30, clock=clock)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


@pytest.mark.parametrize("ttl", [0, -1])
def test_non_positive_ttl_is_rejected(ttl):
    with pytest.raises(ValueError):
        TTLCache(ttl_seconds=ttl)