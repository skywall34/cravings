"""Thread-safe per-user model cache backed by the sqlite users table."""

import io
import logging
import threading
from pathlib import Path

import numpy as np

from db.database import db_connection, get_user, update_user_model_state, DEFAULT_DB_PATH
from model.features import FeatureSchema
from model.thompson import ThompsonSamplingModel, ModelConfig

logger = logging.getLogger(__name__)


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
                # Self-heal stale blobs (e.g. after a cuisine-enum/dim change):
                # fall back to a fresh prior instead of crashing scoring.
                if not FeatureSchema().validate_model(model):
                    logger.warning(
                        "user_id %s has stale model blob (dim=%d, expected=%d) — resetting to fresh prior",
                        user_id, len(model.mu), FeatureSchema().total_dim,
                    )
                    model.reset()
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


