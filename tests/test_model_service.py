"""Tests for the model service layer (previously gRPC server, now direct Python calls)."""

import tempfile
from pathlib import Path

import pytest

from db.database import init_db, insert_user, get_connection, record_swipe as db_record_swipe
from model_server.model_service import ModelService, UserModelStore
from model_server.recommendation_service import RecommendationService


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


class TestRecommendationServiceDirect:
    """Tests that drive RecommendationService directly (no gRPC machinery)."""

    @pytest.fixture
    def service(self, db_with_user):
        db_path, _ = db_with_user
        return RecommendationService(UserModelStore(db_path))

    def test_recommend_returns_scored_items(self, service, db_with_user):
        _, uid = db_with_user
        candidates = [
            make_item_dict(id=1, name="Curry"),
            make_item_dict(id=2, name="Salad", spice_level=0.0),
        ]
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        results = service.recommend(uid, candidates, ctx, top_n=2)
        assert len(results) == 2
        assert results[0]["rank"] == 1
        assert results[1]["rank"] == 2
        for r in results:
            assert 0.0 <= r["score"] <= 1.0

    def test_recommend_respects_top_n(self, service, db_with_user):
        _, uid = db_with_user
        candidates = [make_item_dict(id=i) for i in range(5)]
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        results = service.recommend(uid, candidates, ctx, top_n=1)
        assert len(results) == 1

    def test_record_swipe_increments_total(self, service, db_with_user):
        _, uid = db_with_user
        item = make_item_dict()
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
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
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        for _ in range(3):
            service.record_swipe(uid, item, ctx, reward=1)
        status = service.get_status(uid)
        assert status["total_swipes"] == 3

    def test_persist_and_reload(self, db_with_user):
        db_path, uid = db_with_user
        svc1 = RecommendationService(UserModelStore(db_path))
        item = make_item_dict()
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        svc1.record_swipe(uid, item, ctx, reward=1)
        svc2 = RecommendationService(UserModelStore(db_path))
        status = svc2.get_status(uid)
        assert status["total_swipes"] == 1


class TestModelService:
    """Tests for the ModelService façade used by the FastAPI app."""

    @pytest.fixture
    def svc(self, db_with_user):
        db_path, _ = db_with_user
        return ModelService(db_path)

    def test_get_recommendation(self, svc, db_with_user):
        _, uid = db_with_user
        candidates = [make_item_dict(id=1), make_item_dict(id=2)]
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        results = svc.get_recommendation(uid, candidates, ctx, top_n=1)
        assert len(results) == 1
        assert "id" in results[0]
        assert "score" in results[0]

    def test_record_swipe(self, svc, db_with_user):
        _, uid = db_with_user
        item = make_item_dict()
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        total = svc.record_swipe(uid, item, ctx, reward=1)
        assert total == 1

    def test_get_status(self, svc, db_with_user):
        _, uid = db_with_user
        status = svc.get_status(uid)
        assert status["total_swipes"] == 0

    def test_set_onboarding(self, svc, db_with_user):
        _, uid = db_with_user
        svc.set_onboarding(uid, {"spice_level": 0.8, "sweetness": -0.5})
        status = svc.get_status(uid)
        assert status["total_swipes"] == 0

    def test_per_user_isolation(self, db_with_user):
        db_path, uid1 = db_with_user
        conn = get_connection(db_path)
        uid2, _ = insert_user(conn, "u2")
        conn.close()

        svc = ModelService(db_path)
        item = make_item_dict()
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}

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
        svc = RecommendationService(UserModelStore(db_path))
        yield db_path, uid, items, svc
        db_path.unlink(missing_ok=True)

    def test_cold_start_returns_distinct_cuisines(self, setup):
        _, uid, items, svc = setup
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
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
        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        results = svc.recommend(uid, items + [fusion_item], ctx, top_n=3)
        result_ids = {r["id"] for r in results}
        assert 99 not in result_ids, "other-cuisine item must not appear in stratified phase"

    def test_stratified_ends_after_all_cuisines_swiped(self, setup):
        db_path, uid, items, svc = setup
        conn = get_connection(db_path)
        # Record one swipe per cuisine to mark all cuisines as seen
        for item in items:
            db_record_swipe(conn, uid, item["id"], "right", "standard", 12.0, "no_preference", 0.0, 0.0)
        conn.close()

        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        # Should now use normal Thompson path (all cuisines covered → unseen_cuisines empty)
        results = svc.recommend(uid, items, ctx, top_n=1)
        assert len(results) == 1

    def test_stratified_skips_already_swiped_cuisines(self, setup):
        db_path, uid, items, svc = setup
        conn = get_connection(db_path)
        # Swipe on the first item (american)
        db_record_swipe(conn, uid, items[0]["id"], "right", "standard", 12.0, "no_preference", 0.0, 0.0)
        conn.close()

        ctx = {"dietary_mode": "standard", "hour": 12.0, "mood": "no_preference"}
        results = svc.recommend(uid, items, ctx, top_n=3)
        result_item_ids = {r["id"] for r in results}
        # american item should not appear (already swiped, american = covered)
        assert items[0]["id"] not in result_item_ids, "already-covered cuisine must not appear"
