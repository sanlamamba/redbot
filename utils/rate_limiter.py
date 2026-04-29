"""Simple sliding-window rate limiter."""
import time
from collections import defaultdict, deque


class RateLimiter:
    """Allow at most `max_calls` events per `window_seconds` per key."""

    def __init__(self, max_calls: int, window_seconds: float):
        self._max = max_calls
        self._window = window_seconds
        self._history: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        dq = self._history[key]
        # Drop events outside the window
        while dq and dq[0] < now - self._window:
            dq.popleft()
        if len(dq) >= self._max:
            return False
        dq.append(now)
        return True
