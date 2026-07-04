"""Recommender seam — one interface, two adapters for the two User Identity classes.

A Recommender owns the full per-request flow behind /api/recommend and /api/swipe
for a single identity:

  recommend() — intake (filter + snapshot) → score → shape_results
  record()    — verify snapshot → update model → session-complete check

RegisteredRecommender drives the DB-backed Local Model via ModelServer.
GuestRecommender drives a session-scoped Local Model (SessionStore), falling back
to Global Popularity ordering when the guest supplied no taste prefs.

The route resolves identity once via make_recommender() and then speaks only this
interface — it never branches on Guest vs Registered again. Reward policy, model
lazy-init, and result shaping live here, not smeared across the routes, so the two
paths cannot drift (e.g. the old guest Left-Swipe reward hardcoded to 0.0).

Adapters are request-scoped and cheap to construct. They raise domain errors
(swipe.SnapshotError, swipe.SwipeError); HTTP mapping stays in the route. An empty
recommend() result means "no eligible food items" — the route maps it to 404.
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Protocol

import db.database as db
import swipe
from model.thompson import ThompsonSamplingModel
from swipe.session import SessionStore


class Recommender(Protocol):
    async def recommend(
        self,
        *,
        hour: float | None,
        top_n: int,
        excluded_ids: list[int],
    ) -> list[dict]:
        """Shaped, ready-to-return results. Empty list ⇒ no eligible items (404)."""
        ...

    async def record(self, *, item: dict, direction: str, token: str) -> dict:
        """Record a swipe. Returns {total_swipes, session_complete}.

        Raises swipe.SnapshotError (bad/expired token) or swipe.SwipeError
        (bad direction / identity mismatch) — the route maps both to 400."""
        ...


class RegisteredRecommender:
    """Recommender for a Registered user — DB-backed Local Model via ModelServer."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        sessions: SessionStore,
        model_service,
        base_path: str,
        session_max_swipes: int,
        user: dict,
        session_id: str,
    ) -> None:
        self._conn = conn
        self._sessions = sessions
        self._model_service = model_service
        self._base_path = base_path
        self._session_max = session_max_swipes
        self._user = user
        self._session_id = session_id

    async def recommend(self, *, hour, top_n, excluded_ids) -> list[dict]:
        snapshot, candidates = await swipe.build_intake(
            self._conn, self._sessions, self._user, hour, self._session_id,
            extra_excluded=excluded_ids,
        )
        if not candidates:
            return []
        await asyncio.to_thread(self._model_service.apply_decay, self._user["id"])
        swiped_cuisines = db.get_swiped_cuisines(self._conn, self._user["id"])
        results = await asyncio.to_thread(
            self._model_service.recommend,
            self._user["id"], candidates, snapshot.to_context(), top_n, swiped_cuisines,
        )
        if not results:
            return []
        return swipe.shape_results(results, candidates, snapshot, self._base_path)

    async def record(self, *, item, direction, token) -> dict:
        snapshot = swipe.verify(token, self._user["id"])
        total = await swipe.record_swipe(
            self._conn, self._model_service, self._sessions,
            self._user, item, snapshot, direction, self._session_id,
        )
        seen = await self._sessions.count(self._session_id)
        return {"total_swipes": total, "session_complete": seen >= self._session_max}


class GuestRecommender:
    """Recommender for a stateless Guest — session-scoped Local Model, no DB writes.

    Falls back to Global Popularity ordering (score 0.0) when no taste prefs given."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        sessions: SessionStore,
        base_path: str,
        session_max_swipes: int,
        session_id: str,
        dietary_restrictions: list[str],
        safety_overrides: list[str],
        taste_prefs: dict,
    ) -> None:
        self._conn = conn
        self._sessions = sessions
        self._base_path = base_path
        self._session_max = session_max_swipes
        self._session_id = session_id
        self._dietary_restrictions = dietary_restrictions
        self._safety_overrides = safety_overrides
        self._taste_prefs = taste_prefs

    async def _ensure_model(self) -> ThompsonSamplingModel | None:
        """Lazily seed a session model from taste prefs; None ⇒ Global Popularity path."""
        model = await self._sessions.get_model(self._session_id)
        if model is None and self._taste_prefs:
            model = ThompsonSamplingModel()
            model.set_prior_from_onboarding(self._taste_prefs)
            await self._sessions.set_model(self._session_id, model)
        return model

    async def recommend(self, *, hour, top_n, excluded_ids) -> list[dict]:
        snapshot, candidates = await swipe.build_guest_intake(
            self._conn, self._sessions, self._session_id,
            self._dietary_restrictions, self._safety_overrides,
            hour, top_n, extra_excluded=excluded_ids,
        )
        if not candidates:
            return []
        model = await self._ensure_model()
        if model is not None:
            raw_scores = await asyncio.to_thread(
                model.score_items, candidates, snapshot.to_context()
            )
            results = [
                {"id": candidates[idx]["id"], "name": candidates[idx]["name"],
                 "score": score, "rank": rank + 1}
                for rank, (idx, score) in enumerate(raw_scores[:top_n])
            ]
        else:
            results = [
                {"id": c["id"], "name": c["name"], "score": 0.0, "rank": i + 1}
                for i, c in enumerate(candidates[:top_n])
            ]
        return swipe.shape_results(results, candidates, snapshot, self._base_path)

    async def record(self, *, item, direction, token) -> dict:
        snapshot = swipe.verify_guest(token, self._session_id)
        swipe.check_item(snapshot, item["id"])  # swipe must target a served item (H1)
        await self._sessions.mark(self._session_id, item["id"])
        seen = await self._sessions.count(self._session_id)
        model = await self._ensure_model()
        if model is not None:
            reward = swipe.reward_for_direction(direction)
            await asyncio.to_thread(model.record_swipe, item, snapshot.to_context(), reward)
        return {"total_swipes": 0, "session_complete": seen >= self._session_max}


def make_recommender(
    *,
    conn: sqlite3.Connection,
    user: dict | None,
    sessions: SessionStore,
    model_service,
    base_path: str,
    session_max_swipes: int,
    session_id: str,
    dietary_restrictions: list[str] | None = None,
    safety_overrides: list[str] | None = None,
    taste_prefs: dict | None = None,
) -> Recommender:
    """Resolve the Recommender for an identity. user is None ⇒ Guest."""
    if user is not None:
        return RegisteredRecommender(
            conn, sessions, model_service, base_path, session_max_swipes, user, session_id
        )
    return GuestRecommender(
        conn, sessions, base_path, session_max_swipes, session_id,
        dietary_restrictions or [], safety_overrides or [], taste_prefs or {},
    )
