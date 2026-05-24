"""In-process token-bucket rate limiter. Per-key buckets, asyncio-safe, lazy GC."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Callable

_SWEEP_INTERVAL = 100


@dataclass
class TokenBucket:
    tokens: float
    last_refill: float


class RateLimiter:
    """Token bucket per string key. Buckets start full; refill linearly over time.

    consume() returns (allowed, retry_after_seconds). Caller raises 429 if denied.
    """

    def __init__(
        self,
        capacity: int,
        refill_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if refill_seconds <= 0:
            raise ValueError("refill_seconds must be > 0")
        self.capacity = capacity
        self.refill_seconds = refill_seconds
        self._clock = clock
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
        self._consume_count = 0

    async def consume(self, key: str, cost: float = 1.0) -> tuple[bool, float]:
        async with self._lock:
            now = self._clock()
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(tokens=float(self.capacity), last_refill=now)
                self._buckets[key] = bucket
            else:
                elapsed = now - bucket.last_refill
                refilled = elapsed / self.refill_seconds
                bucket.tokens = min(float(self.capacity), bucket.tokens + refilled)
                bucket.last_refill = now

            self._consume_count += 1
            if self._consume_count % _SWEEP_INTERVAL == 0:
                self._sweep(now)

            if bucket.tokens >= cost:
                bucket.tokens -= cost
                return True, 0.0
            deficit = cost - bucket.tokens
            return False, deficit * self.refill_seconds

    def _sweep(self, now: float) -> None:
        """Drop saturated stale entries — they would be full anyway, lazy GC."""
        stale_threshold = self.capacity * self.refill_seconds
        stale = [k for k, b in self._buckets.items() if now - b.last_refill > stale_threshold]
        for k in stale:
            del self._buckets[k]

    def reset(self) -> None:
        """Test-only: synchronous wipe."""
        self._buckets.clear()
        self._consume_count = 0
