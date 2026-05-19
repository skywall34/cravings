"""Direct Python interface to the Thompson Sampling model, replacing the gRPC adapter."""

import io
import threading
from pathlib import Path

import numpy as np

from db.database import db_connection, get_user, update_user_model_state, DEFAULT_DB_PATH
from model.features import FeatureSchema
from model.thompson import ThompsonSamplingModel, ModelConfig
from model_server.recommendation_service import RecommendationService


def _serialize_array(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, arr, allow_pickle=False)
    return buf.getvalue()


def _deserialize_array(blob: bytes) -> np.ndarray:
    return np.load(io.BytesIO(blob), allow_pickle=False)


class UserModelStore:
    """Thread-safe per-user model cache backed by the sqlite users table."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._cache: dict[int, ThompsonSamplingModel] = {}
        self._locks: dict[int, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def _user_lock(self, user_id: int) -> threading.Lock:
        with self._global_lock:
            if user_id not in self._locks:
                self._locks[user_id] = threading.Lock()
            return self._locks[user_id]

    def get(self, user_id: int) -> ThompsonSamplingModel:
        if user_id in self._cache:
            return self._cache[user_id]
        with self._user_lock(user_id):
            if user_id in self._cache:
                return self._cache[user_id]
            model = self._load_or_create(user_id)
            self._cache[user_id] = model
            return model

    def _load_or_create(self, user_id: int) -> ThompsonSamplingModel:
        with db_connection(self.db_path) as conn:
            user = get_user(conn, user_id)
            if user is None:
                raise ValueError(f"user_id {user_id} not found")
            model = ThompsonSamplingModel(ModelConfig())
            if user["mu_blob"] and user["b_blob"]:
                model.mu = _deserialize_array(user["mu_blob"])
                model.B = _deserialize_array(user["b_blob"])
                model.total_swipes = user["total_swipes"]
                model.last_decay_ts = user["last_decay_ts"] or model.last_decay_ts
                model._drift_active = bool(user["drift_active"])
                FeatureSchema().validate_model(model)
        return model

    def persist(self, user_id: int) -> None:
        model = self._cache.get(user_id)
        if model is None:
            return
        with db_connection(self.db_path) as conn:
            update_user_model_state(
                conn, user_id,
                _serialize_array(model.mu),
                _serialize_array(model.B),
                model.total_swipes,
                model.last_decay_ts,
                model._drift_active,
            )


class ModelService:
    """Synchronous façade over RecommendationService. Call from asyncio via asyncio.to_thread."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self._svc = RecommendationService(UserModelStore(db_path))

    def get_recommendation(
        self, user_id: int, candidates: list[dict], context: dict, top_n: int = 1
    ) -> list[dict]:
        return self._svc.recommend(user_id, candidates, context, top_n)

    def record_swipe(self, user_id: int, item: dict, context: dict, reward: int) -> int:
        return self._svc.record_swipe(user_id, item, context, reward)

    def get_status(self, user_id: int) -> dict:
        return self._svc.get_status(user_id)

    def set_onboarding(self, user_id: int, preferences: dict) -> None:
        self._svc.set_onboarding(user_id, preferences)
