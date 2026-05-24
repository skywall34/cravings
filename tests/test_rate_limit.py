"""TokenBucket rate limiter — burst, refill, lazy sweep, concurrency."""

import asyncio
import pytest

from rate_limit import RateLimiter, _SWEEP_INTERVAL


class FakeClock:
    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@pytest.mark.asyncio
async def test_burst_then_throttle():
    clock = FakeClock()
    limiter = RateLimiter(capacity=10, refill_seconds=30.0, clock=clock)
    for _ in range(10):
        allowed, retry = await limiter.consume("u:1")
        assert allowed is True
        assert retry == 0.0
    allowed, retry = await limiter.consume("u:1")
    assert allowed is False
    assert retry > 0


@pytest.mark.asyncio
async def test_refill_restores_one_token_per_refill_seconds():
    clock = FakeClock()
    limiter = RateLimiter(capacity=10, refill_seconds=30.0, clock=clock)
    for _ in range(10):
        await limiter.consume("u:1")
    # Drained. Advance 30s → exactly 1 token back.
    clock.advance(30.0)
    allowed, _ = await limiter.consume("u:1")
    assert allowed is True
    allowed, retry = await limiter.consume("u:1")
    assert allowed is False
    assert retry == pytest.approx(30.0, abs=0.01)


@pytest.mark.asyncio
async def test_refill_caps_at_capacity():
    clock = FakeClock()
    limiter = RateLimiter(capacity=10, refill_seconds=30.0, clock=clock)
    await limiter.consume("u:1")
    clock.advance(10_000)  # huge gap → would refill past capacity
    bucket = limiter._buckets["u:1"]
    # Trigger refill via another consume.
    await limiter.consume("u:1")
    assert bucket.tokens == pytest.approx(9.0)  # capacity 10 minus the consume just made


@pytest.mark.asyncio
async def test_per_key_isolation():
    clock = FakeClock()
    limiter = RateLimiter(capacity=2, refill_seconds=30.0, clock=clock)
    await limiter.consume("u:1")
    await limiter.consume("u:1")
    blocked, _ = await limiter.consume("u:1")
    assert blocked is False
    # Different key — fresh bucket.
    allowed, _ = await limiter.consume("u:2")
    assert allowed is True


@pytest.mark.asyncio
async def test_lazy_sweep_drops_stale_saturated_entries():
    clock = FakeClock()
    limiter = RateLimiter(capacity=2, refill_seconds=10.0, clock=clock)
    # Touch many keys to build dict.
    for i in range(50):
        await limiter.consume(f"u:{i}")
    assert len(limiter._buckets) == 50
    # Advance past stale_threshold = capacity * refill_seconds = 20s.
    clock.advance(100.0)
    # Trigger sweep — need _SWEEP_INTERVAL more consumes.
    for _ in range(_SWEEP_INTERVAL):
        await limiter.consume("active")
    # All u:* entries were stale + saturated → swept.
    assert "active" in limiter._buckets
    for i in range(50):
        assert f"u:{i}" not in limiter._buckets


@pytest.mark.asyncio
async def test_concurrent_consume_no_overspend():
    clock = FakeClock()
    limiter = RateLimiter(capacity=5, refill_seconds=30.0, clock=clock)
    results = await asyncio.gather(*[limiter.consume("u:1") for _ in range(20)])
    allowed_count = sum(1 for ok, _ in results if ok)
    assert allowed_count == 5


def test_invalid_capacity_raises():
    with pytest.raises(ValueError):
        RateLimiter(capacity=0, refill_seconds=1.0)


def test_invalid_refill_raises():
    with pytest.raises(ValueError):
        RateLimiter(capacity=1, refill_seconds=0.0)
