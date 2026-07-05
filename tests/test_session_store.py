"""Unit tests for SessionStore — model storage, eviction, and per-session locks."""

import asyncio
import time

import pytest

from swipe.session import SessionStore
from model.thompson import ThompsonSamplingModel


@pytest.fixture
def store():
    s = SessionStore()
    return s


@pytest.mark.asyncio
async def test_get_model_unknown_session_returns_none(store):
    assert await store.get_model("nonexistent") is None


@pytest.mark.asyncio
async def test_set_and_get_model_round_trips(store):
    model = ThompsonSamplingModel()
    await store.set_model("s1", model)
    retrieved = await store.get_model("s1")
    assert retrieved is model


@pytest.mark.asyncio
async def test_get_model_different_sessions_isolated(store):
    m1 = ThompsonSamplingModel()
    await store.set_model("s1", m1)
    assert await store.get_model("s2") is None
    assert await store.get_model("s1") is m1


@pytest.mark.asyncio
async def test_evict_stale_removes_idle_sessions(store):
    model = ThompsonSamplingModel()
    await store.set_model("stale", model)
    # Backdate last_accessed beyond threshold
    store._last_accessed["stale"] = time.monotonic() - 3700
    store.evict_stale(max_idle_seconds=3600)
    # Check data removed before get_model (which would re-create the lock entry)
    assert "stale" not in store._models
    assert "stale" not in store._seen
    assert "stale" not in store._locks
    assert await store.get_model("stale") is None


@pytest.mark.asyncio
async def test_evict_stale_leaves_active_sessions(store):
    model = ThompsonSamplingModel()
    await store.set_model("active", model)
    store.evict_stale(max_idle_seconds=3600)
    assert await store.get_model("active") is model


@pytest.mark.asyncio
async def test_evict_called_on_mark(store):
    model = ThompsonSamplingModel()
    await store.set_model("old", model)
    store._last_accessed["old"] = time.monotonic() - 3700
    # mark on a different session triggers eviction
    await store.mark("new_session", 42)
    assert await store.get_model("old") is None


@pytest.mark.asyncio
async def test_per_session_locks_do_not_block_each_other(store):
    """Two concurrent marks on different sessions should both complete."""
    results = []

    async def do_mark(sid, item_id):
        await store.mark(sid, item_id)
        results.append(sid)

    await asyncio.gather(do_mark("s1", 1), do_mark("s2", 2))
    assert set(results) == {"s1", "s2"}


@pytest.mark.asyncio
async def test_reset_clears_model(store):
    model = ThompsonSamplingModel()
    await store.set_model("s1", model)
    await store.reset("s1")
    assert await store.get_model("s1") is None


@pytest.mark.asyncio
async def test_clear_all_wipes_everything(store):
    await store.set_model("s1", ThompsonSamplingModel())
    await store.mark("s1", 99)
    store.clear_all()
    assert store._models == {}
    assert store._seen == {}
    assert store._locks == {}
    assert store._last_accessed == {}


@pytest.mark.asyncio
async def test_empty_session_id_ignored(store):
    await store.set_model("", ThompsonSamplingModel())
    assert await store.get_model("") is None
    await store.mark("", 1)
    assert await store.seen("") == []


# ── consume() — single-use nonce for swipe replay (H1 residual) ────────────

@pytest.mark.asyncio
async def test_consume_returns_true_once_then_false(store):
    assert await store.consume("s1", "snap-a", 7) is True
    assert await store.consume("s1", "snap-a", 7) is False


@pytest.mark.asyncio
async def test_consume_isolated_per_session(store):
    assert await store.consume("s1", "snap-a", 7) is True
    assert await store.consume("s2", "snap-a", 7) is True


@pytest.mark.asyncio
async def test_consume_isolated_per_item(store):
    assert await store.consume("s1", "snap-a", 7) is True
    assert await store.consume("s1", "snap-a", 8) is True


@pytest.mark.asyncio
async def test_consume_empty_session_id_ignored(store):
    assert await store.consume("", "snap-a", 7) is True
    assert await store.consume("", "snap-a", 7) is True
