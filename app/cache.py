import time


class TTLCache:
    """In-memory key-value cache where every entry expires after a fixed TTL."""

    def __init__(self, ttl_seconds, clock=time.monotonic):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._ttl = ttl_seconds
        self._clock = clock
        self._store = {}

    def get(self, key):
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if self._clock() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key, value):
        expires_at = self._clock() + self._ttl
        self._store[key] = (value, expires_at)

    def clear(self):
        self._store.clear()