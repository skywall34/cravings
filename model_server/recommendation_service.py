"""Thompson Sampling model server: recommendation, swipe recording, status, and onboarding."""

from __future__ import annotations

import logging
import random

import numpy as np

from db.database import (
    db_connection, get_recent_likes, push_recent_like, get_embeddings_for_items,
    record_impression, get_least_impressed,
)

from model.features import FeatureSchema

logger = logging.getLogger(__name__)


def _boost_with_similarity(
    scores: list[tuple[int, float]],
    items: list[dict],
    liked_embeddings: list[np.ndarray],
    lam: float,
) -> list[tuple[int, float]]:
    if not liked_embeddings or lam == 0.0:
        return scores
    centroid = np.mean(liked_embeddings, axis=0)
    centroid /= np.linalg.norm(centroid) + 1e-8
    out = []
    for idx, thompson_score in scores:
        emb_bytes = items[idx].get("embedding")
        if emb_bytes is None:
            out.append((idx, thompson_score))
            continue
        emb = np.frombuffer(emb_bytes, dtype=np.float32)
        cos = float(emb @ centroid)
        out.append((idx, thompson_score + lam * cos))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


class ModelServer:
    def __init__(self, store, schema: FeatureSchema | None = None):
        self.store = store
        self.schema = schema or FeatureSchema()

    def _get_liked_embeddings(self, user_id: int, model) -> tuple[list[np.ndarray], float]:
        liked_embeddings: list[np.ndarray] = []
        try:
            with db_connection(self.store.db_path) as conn:
                like_ids = get_recent_likes(conn, user_id)
                if like_ids:
                    blobs = get_embeddings_for_items(conn, like_ids)
                    liked_embeddings = [np.frombuffer(b, dtype=np.float32) for b in blobs]
        except Exception as e:
            logger.warning("failed to load liked embeddings for user %d: %s", user_id, e)
        lam = 0.0 if not liked_embeddings else (0.3 if model.total_swipes < 20 else 0.1)
        return liked_embeddings, lam

    def recommend(
        self,
        user_id: int,
        candidates: list[dict],
        context: dict,
        top_n: int = 1,
        swiped_cuisines: set[str] | None = None,
    ) -> list[dict]:
        """Score candidates for user and return top_n as [{id, name, score, rank}].

        swiped_cuisines: set of cuisine_types already seen by this user (for stratified
        cold-start). Compute via db.get_swiped_cuisines before calling. Defaults to empty
        set (treats user as new) when not provided.
        """
        model = self.store.get(user_id)
        decayed_days = model.maybe_apply_decay()
        if decayed_days > 0:
            self.store.persist(user_id)

        liked_embeddings, lam = self._get_liked_embeddings(user_id, model)

        # Stratified cold-start: cover each cuisine before model exploits preferences.
        # Active until user has swiped at least one item from every eligible cuisine
        # (cuisine_type != "other"). State derived from swipe_events — self-healing
        # across sessions and dietary filter changes.
        eligible_cuisines = {
            c["cuisine_type"]
            for c in candidates
            if c.get("cuisine_type") and c["cuisine_type"] != "other"
        }
        unseen_cuisines = eligible_cuisines - (swiped_cuisines or set())

        if unseen_cuisines:
            return self._stratified_recommend(
                user_id, candidates, context, top_n,
                unseen_cuisines, model, liked_embeddings, lam,
            )

        return self._thompson_recommend(
            user_id, candidates, context, top_n, model, liked_embeddings, lam,
        )

    def _stratified_recommend(
        self,
        user_id: int,
        candidates: list[dict],
        context: dict,
        top_n: int,
        unseen_cuisines: set[str],
        model,
        liked_embeddings: list[np.ndarray],
        lam: float,
    ) -> list[dict]:
        """Pick one item per unseen cuisine (up to top_n), scored by Thompson + embedding boost."""
        chosen_cuisines = random.sample(sorted(unseen_cuisines), min(top_n, len(unseen_cuisines)))

        results: list[dict] = []
        used_ids: set[int] = set()

        for cuisine in chosen_cuisines:
            cuisine_items = [c for c in candidates if c.get("cuisine_type") == cuisine]
            if not cuisine_items:
                continue
            scores = model.score_items(cuisine_items, context)
            scores = _boost_with_similarity(scores, cuisine_items, liked_embeddings, lam)
            top_idx, top_score = scores[0]
            item = cuisine_items[top_idx]
            results.append({
                "id": item["id"],
                "name": item["name"],
                "score": float(top_score),
                "rank": len(results) + 1,
            })
            used_ids.add(item["id"])

        # Fill remaining slots (tail of stratified phase: fewer unseen cuisines than top_n)
        if len(results) < top_n:
            remaining = [c for c in candidates if c["id"] not in used_ids]
            if remaining:
                fill_scores = model.score_items(remaining, context)
                fill_scores = _boost_with_similarity(fill_scores, remaining, liked_embeddings, lam)
                id_to_fill = {c["id"]: c for c in remaining}
                fill_ids = [remaining[idx]["id"] for idx, _ in fill_scores]
                for item_id in fill_ids[: top_n - len(results)]:
                    item = id_to_fill[item_id]
                    score_val = float(next(s for i, s in fill_scores if remaining[i]["id"] == item_id))
                    results.append({
                        "id": item["id"],
                        "name": item["name"],
                        "score": score_val,
                        "rank": len(results) + 1,
                    })

        if results:
            try:
                with db_connection(self.store.db_path) as conn:
                    record_impression(conn, user_id, results[0]["id"])
            except Exception as e:
                logger.warning("record_impression failed for user %d: %s", user_id, e)

        return results

    def _thompson_recommend(
        self,
        user_id: int,
        candidates: list[dict],
        context: dict,
        top_n: int,
        model,
        liked_embeddings: list[np.ndarray],
        lam: float,
    ) -> list[dict]:
        """Normal Thompson Sampling path with embedding boost and long-tail injection."""
        if not candidates:
            return []

        scores = model.score_items(candidates, context)
        scores = _boost_with_similarity(scores, candidates, liked_embeddings, lam)

        candidate_ids = [candidates[idx]["id"] for idx, _ in scores]

        # Every 7th swipe after 20: force least-impressed item to front
        chosen_id = None
        if model.total_swipes >= 20 and model.total_swipes % 7 == 0:
            try:
                with db_connection(self.store.db_path) as conn:
                    chosen_id = get_least_impressed(conn, user_id, candidate_ids)
            except Exception as e:
                logger.warning("long-tail injection failed for user %d: %s", user_id, e)

        if chosen_id is not None:
            ordered_ids = [chosen_id] + [i for i in candidate_ids if i != chosen_id]
        else:
            ordered_ids = candidate_ids

        id_to_candidate = {c["id"]: c for c in candidates}

        try:
            with db_connection(self.store.db_path) as conn:
                record_impression(conn, user_id, ordered_ids[0])
        except Exception as e:
            logger.warning("record_impression failed for user %d: %s", user_id, e)

        results = []
        for rank, item_id in enumerate(ordered_ids[:top_n]):
            item = id_to_candidate[item_id]
            results.append({
                "id": item["id"],
                "name": item["name"],
                "score": float(next(s for i, s in scores if candidates[i]["id"] == item_id)),
                "rank": rank + 1,
            })
        return results

    def record_swipe(self, user_id: int, item: dict, context: dict, reward: float) -> int:
        """Update model with swipe signal. Returns total_swipes after update."""
        model = self.store.get(user_id)
        model.record_swipe(item, context, reward)

        if reward == 1:
            try:
                with db_connection(self.store.db_path) as conn:
                    push_recent_like(conn, user_id, item["id"])
            except Exception as e:
                logger.warning("push_recent_like failed for user %d: %s", user_id, e)

        try:
            self.store.persist(user_id)
        except Exception as e:
            logger.warning("failed to persist user %d model: %s", user_id, e)
        return model.total_swipes

    def get_status(self, user_id: int) -> dict:
        model = self.store.get(user_id)
        return {
            "total_swipes": model.total_swipes,
            "current_alpha": model._get_alpha(),
            "drift_active": model._drift_active,
        }

    def set_onboarding(self, user_id: int, preferences: dict, reset: bool = False) -> None:
        model = self.store.get(user_id)
        if reset:
            model.reset()
        model.set_prior_from_onboarding(preferences)
        self.store.persist(user_id)
