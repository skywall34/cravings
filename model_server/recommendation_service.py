"""Business logic for recommendation, swipe recording, status, and onboarding.

Separated from the gRPC binding so it can be tested and called without a gRPC server.
The ModelServiceServicer in server.py is a thin adapter over this class.
"""

from __future__ import annotations

import numpy as np

from db.database import (
    get_connection, get_user_swipes_with_cuisine,
    get_recent_likes, push_recent_like, get_embeddings_for_items,
)
from model.features import FeatureSchema


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


class RecommendationService:
    def __init__(self, store, schema: FeatureSchema | None = None):
        self.store = store
        self.schema = schema or FeatureSchema()

    def recommend(
        self,
        user_id: int,
        candidates: list[dict],
        context: dict,
        top_n: int = 1,
    ) -> list[dict]:
        """Score candidates for user and return top_n as [{id, name, score, rank}]."""
        model = self.store.get(user_id)
        decayed_days = model.maybe_apply_decay()
        if decayed_days > 0:
            self.store.persist(user_id)
        scores = model.score_items(candidates, context)

        liked_embeddings: list[np.ndarray] = []
        try:
            conn = get_connection(self.store.db_path)
            like_ids = get_recent_likes(conn, user_id)
            conn.close()
            if like_ids:
                conn = get_connection(self.store.db_path)
                blobs = get_embeddings_for_items(conn, like_ids)
                conn.close()
                liked_embeddings = [np.frombuffer(b, dtype=np.float32) for b in blobs]
        except Exception as e:
            print(f"Warning: failed to load liked embeddings for user {user_id}: {e}")

        lam = 0.0 if not liked_embeddings else (0.3 if model.total_swipes < 20 else 0.1)
        scores = _boost_with_similarity(scores, candidates, liked_embeddings, lam)

        results = []
        for rank, (idx, score) in enumerate(scores[:top_n]):
            item = candidates[idx]
            results.append({
                "id": item["id"],
                "name": item["name"],
                "score": float(score),
                "rank": rank + 1,
            })
        return results

    def record_swipe(self, user_id: int, item: dict, context: dict, reward: float) -> int:
        """Update model with swipe signal. Returns total_swipes after update."""
        model = self.store.get(user_id)
        model.record_swipe(item, context, reward)

        if reward == 1:
            try:
                conn = get_connection(self.store.db_path)
                push_recent_like(conn, user_id, item["id"])
                conn.close()
            except Exception as e:
                print(f"Warning: push_recent_like failed for user {user_id}: {e}")

        if model.total_swipes == 5:
            try:
                conn = get_connection(self.store.db_path)
                swipes = get_user_swipes_with_cuisine(conn, user_id, limit=5)
                conn.close()
                model.seed_cuisine_prior_from_swipes(swipes)
            except Exception as e:
                print(f"Warning: cuisine prior seed failed for user {user_id}: {e}")

        try:
            self.store.persist(user_id)
        except Exception as e:
            print(f"Warning: failed to persist user {user_id} model: {e}")
        return model.total_swipes

    def get_status(self, user_id: int) -> dict:
        model = self.store.get(user_id)
        return {
            "total_swipes": model.total_swipes,
            "current_alpha": model._get_alpha(),
            "drift_active": model._drift_active,
        }

    def set_onboarding(self, user_id: int, preferences: dict) -> None:
        model = self.store.get(user_id)
        model.set_prior_from_onboarding(preferences)
        self.store.persist(user_id)
