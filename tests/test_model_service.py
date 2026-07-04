"""Tests for the model server layer."""

import tempfile
from pathlib import Path

import pytest

from db.database import init_db, insert_user, get_connection, record_swipe as db_record_swipe, get_swiped_cuisines
from model_server.model_service import UserModelStore
from model_server.recommendation_service import ModelServer


def _insert_item_with_cuisine(conn, item_id: int, cuisine: str) -> dict:
    """Insert a tagged food item with a given cuisine_type, return item dict."""
    conn.execute(
        "INSERT OR IGNORE INTO food_items "
        "(id, name, description, cuisine_type, protein_type, carb_base, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "veggie_density, dairy_content, smell_intensity, nausea_trigger, "
        "safety_risk_bitmask, dietary_flags_bitmask, tagging_status) "
        "VALUES (?, ?, '', ?, 'chicken', 'rice', "
        "0.5, 0.3, 0.2, 0.6, 0.4, 0.1, 0.8, 0.5, 0.6, 0.5, 0.2, 0.3, 0.4, 0.1, "
        "0, 0, 'tagged')",
        [item_id, f"Item_{cuisine}_{item_id}", cuisine],
    )
    conn.commit()
    return {
        "id": item_id, "name": f"Item_{cuisine}_{item_id}",
        "cuisine_type": cuisine, "protein_type": "chicken", "carb_base": "rice",
        "spice_level": 0.5, "sweetness": 0.3, "sourness": 0.2, "savory_umami": 0.6,
        "saltiness": 0.4, "bitterness": 0.1, "temperature": 0.8,
        "texture_softness": 0.5, "sauce_heaviness": 0.6, "richness": 0.5,
        "veggie_density": 0.2, "dairy_content": 0.3, "smell_intensity": 0.4,
        "nausea_trigger": 0.1, "embedding": None,
    }


def make_item_dict(**kwargs) -> dict:
    defaults = {
        "id": 1, "name": "Test Item",
        "spice_level": 0.5, "sweetness": 0.3, "sourness": 0.2,
        "savory_umami": 0.6, "saltiness": 0.4, "bitterness": 0.1,
        "temperature": 0.8, "texture_softness": 0.5,
        "sauce_heaviness": 0.6, "richness": 0.5,
        "protein_type": "chicken", "cuisine_type": "indian", "carb_base": "rice",
        "veggie_density": 0.2, "dairy_content": 0.3,
        "smell_intensity": 0.4, "nausea_trigger": 0.1,
    }
    defaults.update(kwargs)
    return defaults


@pytest.fixture
def db_with_user():
    """Tmp DB pre-populated with one user; yields (db_path, user_id)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    conn = init_db(db_path)
    uid, _ = insert_user(conn, "testuser")
    conn.close()
    yield db_path, uid
    db_path.unlink(missing_ok=True)


class TestModelServer:
    """Tests for ModelServer — Thompson Sampling recommend/swipe/status/onboarding."""

    @pytest.fixture
    def service(self, db_with_user):
        db_path, _ = db_with_user
        return ModelServer(UserModelStore(db_path))

    def test_recommend_returns_scored_items(self, service, db_with_user):
        _, uid = db_with_user
        candidates = [
            make_item_dict(id=1, name="Curry"),
            make_item_dict(id=2, name="Salad", spice_level=0.0),
        ]
        ctx = {"hour": 12.0}
        results = service.recommend(uid, candidates, ctx, top_n=2)
        assert len(results) == 2
        assert results[0]["rank"] == 1
        assert results[1]["rank"] == 2
        for r in results:
            assert 0.0 <= r["score"] <= 1.0

    def test_recommend_respects_top_n(self, service, db_with_user):
        _, uid = db_with_user
        candidates = [make_item_dict(id=i) for i in range(5)]
        ctx = {"hour": 12.0}
        results = service.recommend(uid, candidates, ctx, top_n=1)
        assert len(results) == 1

    def test_record_swipe_increments_total(self, service, db_with_user):
        _, uid = db_with_user
        item = make_item_dict()
        ctx = {"hour": 12.0}
        total = service.record_swipe(uid, item, ctx, reward=1)
        assert total == 1
        total = service.record_swipe(uid, item, ctx, reward=0)
        assert total == 2

    def test_get_status_initial(self, service, db_with_user):
        _, uid = db_with_user
        status = service.get_status(uid)
        assert status["total_swipes"] == 0
        assert status["current_alpha"] > 0
        assert not status["drift_active"]

    def test_swipe_then_status(self, service, db_with_user):
        _, uid = db_with_user
        item = make_item_dict()
        ctx = {"hour": 12.0}
        for _ in range(3):
            service.record_swipe(uid, item, ctx, reward=1)
        status = service.get_status(uid)
        assert status["total_swipes"] == 3

    def test_persist_and_reload(self, db_with_user):
        db_path, uid = db_with_user
        svc1 = ModelServer(UserModelStore(db_path))
        item = make_item_dict()
        ctx = {"hour": 12.0}
        svc1.record_swipe(uid, item, ctx, reward=1)
        svc2 = ModelServer(UserModelStore(db_path))
        status = svc2.get_status(uid)
        assert status["total_swipes"] == 1

    def test_similarity_boost_applied_with_liked_embeddings(self, service, db_with_user):
        """A right-swiped item with an embedding feeds the liked-centroid boost
        on the next recommend() call (_boost_with_similarity / _get_liked_embeddings)."""
        import numpy as np
        from db.database import db_connection, insert_food_item, update_food_item_embedding

        db_path, uid = db_with_user
        liked_emb = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32).tobytes()
        similar_emb = np.array([0.9, 0.1, 0.0, 0.0], dtype=np.float32).tobytes()
        with db_connection(db_path) as conn:
            liked_id = insert_food_item(conn, {"name": "Liked", "description": "", "tagging_status": "tagged"})
            update_food_item_embedding(conn, liked_id, liked_emb)

        ctx = {"hour": 12.0}
        # Right-swipe pushes this item onto the user's recent-likes list.
        service.record_swipe(uid, make_item_dict(id=liked_id, name="Liked"), ctx, reward=1)

        candidates = [
            make_item_dict(id=liked_id + 1, name="Similar", embedding=similar_emb),
            make_item_dict(id=liked_id + 2, name="NoEmbedding", embedding=None),
        ]
        results = service.recommend(uid, candidates, ctx, top_n=2)
        assert len(results) == 2
        assert {r["id"] for r in results} == {liked_id + 1, liked_id + 2}

    def test_apply_decay_runs_and_persists_after_interval(self, service, db_with_user):
        """apply_decay() only actually decays (and persists) once the min interval
        has elapsed — force last_decay_ts into the past to hit that branch."""
        import time as _time

        _, uid = db_with_user
        model = service.store.get(uid)
        model.last_decay_ts = _time.time() - 7 * 3600  # past the 6h min interval
        assert service.apply_decay(uid) is True
        # Too soon immediately after — idempotent within the interval.
        assert service.apply_decay(uid) is False

    def test_long_tail_injection_at_multiple_of_7_past_20(self, service, db_with_user):
        """At total_swipes == 21 (>= 20 and a multiple of 7), the least-impressed
        candidate is forced to rank 1 (`_thompson_recommend`'s long-tail branch)."""
        db_path, uid = db_with_user
        ctx = {"hour": 12.0}
        item = make_item_dict()
        for _ in range(21):
            service.record_swipe(uid, item, ctx, reward=1)
        assert service.get_status(uid)["total_swipes"] == 21

        candidates = [make_item_dict(id=i) for i in range(1, 6)]
        # Give every candidate but #3 lots of impressions, so #3 is least-impressed
        # and must be forced to rank 1 regardless of its Thompson score. The FK on
        # user_item_impressions needs real food_items rows for ids 1-5 first.
        from db.database import db_connection, record_impression
        with db_connection(db_path) as conn:
            for c in candidates:
                _insert_item_with_cuisine(conn, c["id"], "indian")
            for cid in (1, 2, 4, 5):
                for _ in range(5):
                    record_impression(conn, uid, cid)

        # Cold-start stratification only ends once every eligible cuisine has been
        # swiped; force the normal Thompson path (where long-tail injection lives)
        # by reporting "indian" as already covered.
        results = service.recommend(uid, candidates, ctx, top_n=3, swiped_cuisines={"indian"})
        assert len(results) == 3
        assert results[0]["id"] == 3

    def test_recommend_survives_db_failures(self, service, db_with_user, monkeypatch):
        """record_impression/get_least_impressed failures must not crash recommend()
        — they're best-effort side channels, logged and swallowed."""
        import model_server.recommendation_service as rs

        def _boom(*a, **kw):
            raise RuntimeError("db down")

        monkeypatch.setattr(rs, "record_impression", _boom)
        monkeypatch.setattr(rs, "get_least_impressed", _boom)

        _, uid = db_with_user
        candidates = [make_item_dict(id=i) for i in range(1, 4)]
        ctx = {"hour": 12.0}
        results = service.recommend(uid, candidates, ctx, top_n=2)
        assert len(results) == 2

    def test_record_swipe_survives_persist_failure(self, service, db_with_user, monkeypatch):
        """A persist() failure must not crash record_swipe() — total_swipes is
        already updated in memory and returned regardless."""
        monkeypatch.setattr(service.store, "persist", lambda uid: (_ for _ in ()).throw(RuntimeError("disk full")))
        _, uid = db_with_user
        item = make_item_dict()
        ctx = {"hour": 12.0}
        total = service.record_swipe(uid, item, ctx, reward=1)
        assert total == 1

    def test_stale_dim_blob_self_heals(self, db_with_user):
        """A blob from a smaller feature dim (e.g. pre cuisine-enum expansion)
        must reset to a fresh prior at the current dim instead of crashing scoring."""
        import numpy as np
        from db.database import db_connection, update_user_model_state
        from model.features import FeatureSchema
        from model_server.model_service import _serialize_array

        db_path, uid = db_with_user
        stale_dim = FeatureSchema().total_dim - 14  # old enum had fewer cuisines
        with db_connection(db_path) as conn:
            update_user_model_state(
                conn, uid,
                _serialize_array(np.ones(stale_dim)),
                _serialize_array(np.eye(stale_dim)),
                total_swipes=42,
                last_decay_ts=0.0,
                drift_active=False,
            )

        store = UserModelStore(db_path)
        model = store.get(uid)
        assert model.mu.shape == (FeatureSchema().total_dim,)
        assert np.allclose(model.mu, 0.0)  # fresh prior
        assert model.total_swipes == 0

        # Scoring must work after the heal (this is what used to crash).
        svc = ModelServer(store)
        scored = svc.recommend(uid, [make_item_dict()], {"hour": 12.0})
        assert len(scored) == 1


class TestModelServerIsolation:
    """Per-user model isolation via ModelServer."""

    def test_per_user_isolation(self, db_with_user):
        db_path, uid1 = db_with_user
        conn = get_connection(db_path)
        uid2, _ = insert_user(conn, "u2")
        conn.close()

        svc = ModelServer(UserModelStore(db_path))
        item = make_item_dict()
        ctx = {"hour": 12.0}

        for _ in range(3):
            svc.record_swipe(uid1, item, ctx, reward=1)
        svc.record_swipe(uid2, item, ctx, reward=0)

        assert svc.get_status(uid1)["total_swipes"] == 3
        assert svc.get_status(uid2)["total_swipes"] == 1


class TestStratifiedColdStart:
    """Stratified cuisine rotation for cold-start users."""

    CUISINES = ["american", "korean", "italian", "japanese", "mexican"]

    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        conn = init_db(db_path)
        uid, _ = insert_user(conn, "colduser")
        items = [_insert_item_with_cuisine(conn, i + 1, c) for i, c in enumerate(self.CUISINES)]
        conn.close()
        svc = ModelServer(UserModelStore(db_path))
        yield db_path, uid, items, svc
        db_path.unlink(missing_ok=True)

    def test_cold_start_returns_distinct_cuisines(self, setup):
        _, uid, items, svc = setup
        ctx = {"hour": 12.0}
        results = svc.recommend(uid, items, ctx, top_n=3)
        assert len(results) == 3
        cuisines = [next(it["cuisine_type"] for it in items if it["id"] == r["id"]) for r in results]
        assert len(set(cuisines)) == 3, "all 3 slots must be distinct cuisines"
        assert "other" not in cuisines

    def test_cold_start_excludes_other_cuisine(self, setup):
        db_path, uid, items, svc = setup
        conn = get_connection(db_path)
        fusion_item = _insert_item_with_cuisine(conn, 99, "other")
        conn.close()
        ctx = {"hour": 12.0}
        results = svc.recommend(uid, items + [fusion_item], ctx, top_n=3)
        result_ids = {r["id"] for r in results}
        assert 99 not in result_ids, "other-cuisine item must not appear in stratified phase"

    def test_stratified_ends_after_all_cuisines_swiped(self, setup):
        db_path, uid, items, svc = setup
        conn = get_connection(db_path)
        # Record one swipe per cuisine to mark all cuisines as seen
        for item in items:
            db_record_swipe(conn, uid, item["id"], "right", 12.0, 0.0, 0.0)
        swiped = get_swiped_cuisines(conn, uid)
        conn.close()

        ctx = {"hour": 12.0}
        # Should now use normal Thompson path (all cuisines covered → unseen_cuisines empty)
        results = svc.recommend(uid, items, ctx, top_n=1, swiped_cuisines=swiped)
        assert len(results) == 1

    def test_stratified_skips_already_swiped_cuisines(self, setup):
        db_path, uid, items, svc = setup
        conn = get_connection(db_path)
        # Swipe on the first item (american)
        db_record_swipe(conn, uid, items[0]["id"], "right", 12.0, 0.0, 0.0)
        swiped = get_swiped_cuisines(conn, uid)
        conn.close()

        ctx = {"hour": 12.0}
        results = svc.recommend(uid, items, ctx, top_n=3, swiped_cuisines=swiped)
        result_item_ids = {r["id"] for r in results}
        # american item should not appear (already swiped, american = covered)
        assert items[0]["id"] not in result_item_ids, "already-covered cuisine must not appear"
