import math
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after: int  # whole seconds until the next window; 0 when allowed


class FixedWindowRateLimiter:
    """Allows at most `limit` requests per client in each fixed time window."""

    def __init__(self, limit, window_seconds, clock=time.monotonic):
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._clients = {}

    def check(self, client_id):
        now = self._clock()
        window_id = int(now // self._window)

        entry = self._clients.get(client_id)
        if entry is None or entry[0] != window_id:
            self._clients[client_id] = (window_id, 1)
            return RateLimitResult(allowed=True, retry_after=0)

        _, count = entry
        count += 1
        self._clients[client_id] = (window_id, count)

        if count <= self._limit:
            return RateLimitResult(allowed=True, retry_after=0)

        window_end = (window_id + 1) * self._window
        retry_after = math.ceil(window_end - now)
        return RateLimitResult(allowed=False, retry_after=retry_after)

    def clear(self):
        self._clients.clear()