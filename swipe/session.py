"""Per-Swipe-Session seen-set and guest Thompson model store. In-memory; cleared on /api/session/reset or process restart."""

from __future__ import annotations

import asyncio
import time

from model.thompson import ThompsonSamplingModel


class SessionStore:
    def __init__(self) -> None:
        self._seen: dict[str, set[int]] = {}
        self._models: dict[str, ThompsonSamplingModel] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._last_accessed: dict[str, float] = {}

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]

    def evict_stale(self, max_idle_seconds: int = 3600) -> None:
        now = time.monotonic()
        stale = [sid for sid, t in self._last_accessed.items() if now - t > max_idle_seconds]
        for sid in stale:
            self._seen.pop(sid, None)
            self._models.pop(sid, None)
            self._locks.pop(sid, None)
            self._last_accessed.pop(sid, None)

    async def seen(self, session_id: str) -> list[int]:
        if not session_id:
            return []
        async with self._get_lock(session_id):
            self._last_accessed[session_id] = time.monotonic()
            return list(self._seen.get(session_id, set()))

    async def mark(self, session_id: str, item_id: int) -> None:
        if not session_id:
            return
        self.evict_stale()
        async with self._get_lock(session_id):
            self._seen.setdefault(session_id, set()).add(item_id)
            self._last_accessed[session_id] = time.monotonic()

    async def count(self, session_id: str) -> int:
        if not session_id:
            return 0
        async with self._get_lock(session_id):
            return len(self._seen.get(session_id, set()))

    async def reset(self, session_id: str) -> None:
        async with self._get_lock(session_id):
            self._seen.pop(session_id, None)
            self._models.pop(session_id, None)
            self._last_accessed.pop(session_id, None)

    async def get_model(self, session_id: str) -> ThompsonSamplingModel | None:
        if not session_id:
            return None
        async with self._get_lock(session_id):
            return self._models.get(session_id)

    async def set_model(self, session_id: str, model: ThompsonSamplingModel) -> None:
        if not session_id:
            return
        async with self._get_lock(session_id):
            self._models[session_id] = model
            self._last_accessed[session_id] = time.monotonic()

    def clear_all(self) -> None:
        """Test-only: synchronous wipe."""
        self._seen.clear()
        self._models.clear()
        self._locks.clear()
        self._last_accessed.clear()
