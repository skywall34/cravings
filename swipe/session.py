"""Per-Swipe-Session seen-set. In-memory; cleared on /api/session/reset or process restart."""

from __future__ import annotations

import asyncio


class SessionStore:
    def __init__(self) -> None:
        self._seen: dict[str, set[int]] = {}
        self._lock = asyncio.Lock()

    async def seen(self, session_id: str) -> list[int]:
        if not session_id:
            return []
        async with self._lock:
            return list(self._seen.get(session_id, set()))

    async def mark(self, session_id: str, item_id: int) -> None:
        if not session_id:
            return
        async with self._lock:
            self._seen.setdefault(session_id, set()).add(item_id)

    async def count(self, session_id: str) -> int:
        if not session_id:
            return 0
        async with self._lock:
            return len(self._seen.get(session_id, set()))

    async def reset(self, session_id: str) -> None:
        async with self._lock:
            self._seen.pop(session_id, None)

    def clear_all(self) -> None:
        """Test-only: synchronous wipe."""
        self._seen.clear()
