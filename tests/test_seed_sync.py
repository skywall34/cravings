"""Tests for content sync from seed DB into live DB.

The seed sync is the replacement for the legacy `rsync cravings.db` deploy
step. It must upsert food_items + restaurants by id while leaving user data
(users, swipe_events, user_item_impressions) untouched.
"""

import tempfile
from pathlib import Path

import pytest

from db.database import (
    init_db,
    insert_food_item,
    insert_user,
    record_impression,
)
from db.seed_sync import sync_content_from_seed


@pytest.fixture
def live_and_seed():
    with tempfile.NamedTemporaryFile(suffix="-live.db", delete=False) as f:
        live_path = Path(f.name)
    with tempfile.NamedTemporaryFile(suffix="-seed.db", delete=False) as f:
        seed_path = Path(f.name)
    live = init_db(live_path)
    seed = init_db(seed_path)
    yield live, seed, live_path, seed_path
    live.close()
    seed.close()
    live_path.unlink(missing_ok=True)
    seed_path.unlink(missing_ok=True)


class TestSeedSync:
    def test_skipped_when_seed_missing(self, live_and_seed):
        live, _, _, _ = live_and_seed
        result = sync_content_from_seed(live, Path("/nonexistent/seed.db"))
        assert result == {"skipped": True}

    def test_inserts_new_food_items(self, live_and_seed):
        live, seed, _, seed_path = live_and_seed
        insert_food_item(seed, {"name": "Pho", "cuisine_type": "vietnamese"})
        insert_food_item(seed, {"name": "Pad Thai", "cuisine_type": "thai"})

        result = sync_content_from_seed(live, seed_path)
        assert result["food_items"] == 2

        names = [r["name"] for r in live.execute("SELECT name FROM food_items ORDER BY id")]
        assert names == ["Pho", "Pad Thai"]

    def test_updates_existing_food_items_by_id(self, live_and_seed):
        live, seed, _, seed_path = live_and_seed
        insert_food_item(live, {"name": "Old Name", "cuisine_type": "thai"})
        insert_food_item(seed, {"name": "New Name", "cuisine_type": "thai"})
        seed.execute("UPDATE food_items SET image_slug='new_slug' WHERE id=1")
        seed.commit()

        sync_content_from_seed(live, seed_path)

        row = live.execute("SELECT name, image_slug FROM food_items WHERE id=1").fetchone()
        assert row["name"] == "New Name"
        assert row["image_slug"] == "new_slug"

    def test_preserves_user_data(self, live_and_seed):
        live, seed, _, seed_path = live_and_seed
        uid, token = insert_user(live, "alice")
        fid = insert_food_item(seed, {"name": "Sushi"})

        sync_content_from_seed(live, seed_path)

        user = live.execute("SELECT id, name, api_token FROM users WHERE id=?", [uid]).fetchone()
        assert user["api_token"] == token
        assert user["name"] == "alice"
        assert live.execute("SELECT COUNT(*) c FROM food_items").fetchone()["c"] == 1

    def test_preserves_swipes_and_impressions(self, live_and_seed):
        live, seed, _, seed_path = live_and_seed
        uid, _ = insert_user(live, "bob")
        fid = insert_food_item(live, {"name": "Curry", "cuisine_type": "indian"})
        record_impression(live, uid, fid)
        # seed has the same item id (after update) plus a new one
        insert_food_item(seed, {"name": "Curry Updated", "cuisine_type": "indian"})
        insert_food_item(seed, {"name": "Naan"})

        sync_content_from_seed(live, seed_path)

        impressions = live.execute(
            "SELECT user_id, food_item_id FROM user_item_impressions"
        ).fetchall()
        assert len(impressions) == 1
        assert impressions[0]["food_item_id"] == fid

    def test_idempotent_on_repeat(self, live_and_seed):
        live, seed, _, seed_path = live_and_seed
        insert_food_item(seed, {"name": "Tacos"})

        r1 = sync_content_from_seed(live, seed_path)
        r2 = sync_content_from_seed(live, seed_path)

        assert r1 == r2
        assert live.execute("SELECT COUNT(*) c FROM food_items").fetchone()["c"] == 1

    def test_same_file_short_circuits(self, live_and_seed):
        live, _, live_path, _ = live_and_seed
        insert_food_item(live, {"name": "Existing"})
        result = sync_content_from_seed(live, live_path)
        assert result == {"skipped": True}
