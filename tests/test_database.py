"""Tests for database initialization and CRUD operations."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from db.database import (
    init_db,
    insert_food_item,
    insert_restaurant,
    insert_user,
    get_user,
    get_user_by_token,
    get_untagged_items,
    update_food_item_tags,
    update_user_model_state,
    update_user_onboarding,
    get_embeddings_for_items,
    record_impression,
    get_least_impressed,
    get_eligible_food_items,
)


@pytest.fixture
def db_conn():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    conn = init_db(db_path)
    yield conn
    conn.close()
    db_path.unlink(missing_ok=True)


class TestInitDB:
    def test_creates_tables(self, db_conn):
        tables = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        assert "food_items" in table_names
        assert "restaurants" in table_names
        assert "swipe_events" in table_names
        assert "users" in table_names

    def test_image_columns_exist_on_fresh_db(self, db_conn):
        cols = {r["name"] for r in db_conn.execute("PRAGMA table_info(food_items)").fetchall()}
        for col in ("image_slug", "image_hash", "image_author", "image_license",
                    "image_source_url", "image_review_status"):
            assert col in cols, f"missing column: {col}"

    def test_migration_adds_image_columns_to_existing_db(self):
        import sqlite3
        import tempfile
        from pathlib import Path
        from db.database import SCHEMA_PATH, _migrate

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        # Create table without image columns (simulate old schema)
        conn.executescript(
            "CREATE TABLE food_items ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  name TEXT NOT NULL,"
            "  tagging_status TEXT NOT NULL DEFAULT 'pending'"
            ");"
            "CREATE TABLE users ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  name TEXT NOT NULL,"
            "  api_token TEXT NOT NULL UNIQUE,"
            "  dietary_flags_bitmask INTEGER NOT NULL DEFAULT 0,"
            "  safety_overrides_bitmask INTEGER NOT NULL DEFAULT 0,"
            "  total_swipes INTEGER NOT NULL DEFAULT 0,"
            "  drift_active INTEGER NOT NULL DEFAULT 0,"
            "  onboarding_complete INTEGER NOT NULL DEFAULT 0"
            ");"
            "CREATE TABLE swipe_events ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  user_id INTEGER NOT NULL,"
            "  food_item_id INTEGER NOT NULL,"
            "  direction TEXT NOT NULL"
            ");"
        )
        _migrate(conn)

        cols = {r["name"] for r in conn.execute("PRAGMA table_info(food_items)").fetchall()}
        for col in ("image_slug", "image_hash", "image_author", "image_license",
                    "image_source_url", "image_review_status"):
            assert col in cols, f"migration missing column: {col}"

        conn.close()
        db_path.unlink(missing_ok=True)

    def test_creates_indexes(self, db_conn):
        indexes = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()
        index_names = [i["name"] for i in indexes]
        assert "idx_food_items_restaurant" in index_names
        assert "idx_food_items_safety" in index_names
        assert "idx_swipe_events_food_item" in index_names


class TestRestaurants:
    def test_insert_restaurant(self, db_conn):
        rid = insert_restaurant(db_conn, {
            "name": "Test Restaurant",
            "cuisine_type": "italian",
            "source_type": "manual",
        })
        assert rid > 0

        row = db_conn.execute("SELECT * FROM restaurants WHERE id = ?", [rid]).fetchone()
        assert row["name"] == "Test Restaurant"
        assert row["cuisine_type"] == "italian"


class TestFoodItems:
    def test_insert_food_item(self, db_conn):
        fid = insert_food_item(db_conn, {
            "name": "Test Pizza",
            "description": "A test pizza",
        })
        assert fid > 0

        row = db_conn.execute("SELECT * FROM food_items WHERE id = ?", [fid]).fetchone()
        assert row["name"] == "Test Pizza"
        assert row["tagging_status"] == "pending"

    def test_insert_with_restaurant(self, db_conn):
        rid = insert_restaurant(db_conn, {"name": "R1", "source_type": "manual"})
        fid = insert_food_item(db_conn, {
            "name": "Pizza",
            "restaurant_id": rid,
        })
        row = db_conn.execute("SELECT * FROM food_items WHERE id = ?", [fid]).fetchone()
        assert row["restaurant_id"] == rid

    def test_get_untagged_items(self, db_conn):
        insert_food_item(db_conn, {"name": "Untagged 1"})
        insert_food_item(db_conn, {"name": "Untagged 2"})
        items = get_untagged_items(db_conn)
        assert len(items) == 2
        assert items[0]["name"] == "Untagged 1"

    def test_update_food_item_tags(self, db_conn):
        fid = insert_food_item(db_conn, {"name": "To Tag"})
        tags = {
            "spice_level": 0.5,
            "sweetness": 0.3,
            "protein_type": "chicken",
            "cuisine_type": "thai",
            "carb_base": "rice",
            "safety_risk_bitmask": 0,
            "dietary_flags_bitmask": 0,
        }
        update_food_item_tags(db_conn, fid, tags)

        row = db_conn.execute("SELECT * FROM food_items WHERE id = ?", [fid]).fetchone()
        assert row["tagging_status"] == "tagged"
        assert row["spice_level"] == 0.5
        assert row["protein_type"] == "chicken"

    def test_untagged_excludes_tagged(self, db_conn):
        fid1 = insert_food_item(db_conn, {"name": "Item 1"})
        insert_food_item(db_conn, {"name": "Item 2"})
        update_food_item_tags(db_conn, fid1, {"spice_level": 0.5})

        items = get_untagged_items(db_conn)
        assert len(items) == 1
        assert items[0]["name"] == "Item 2"


class TestUsers:
    def test_insert_user_returns_id_and_token(self, db_conn):
        uid, token = insert_user(db_conn, "alice")
        assert uid > 0
        assert len(token) >= 16

    def test_get_user_by_token(self, db_conn):
        uid, token = insert_user(db_conn, "bob", dietary_flags_bitmask=2)
        user = get_user_by_token(db_conn, token)
        assert user is not None
        assert user["id"] == uid
        assert user["name"] == "bob"
        assert user["dietary_flags_bitmask"] == 2
        assert user["onboarding_complete"] == 0

    def test_get_user_by_id(self, db_conn):
        uid, _ = insert_user(db_conn, "carol")
        user = get_user(db_conn, uid)
        assert user is not None
        assert user["name"] == "carol"

    def test_unknown_token_returns_none(self, db_conn):
        assert get_user_by_token(db_conn, "no-such-token") is None

    def test_token_is_unique(self, db_conn):
        _, t1 = insert_user(db_conn, "u1")
        _, t2 = insert_user(db_conn, "u2")
        assert t1 != t2

    def test_update_model_state(self, db_conn):
        uid, _ = insert_user(db_conn, "dave")
        update_user_model_state(db_conn, uid, b"mu_bytes", b"b_bytes",
                                 total_swipes=5, last_decay_ts=1234.5,
                                 drift_active=True)
        user = get_user(db_conn, uid)
        assert user["mu_blob"] == b"mu_bytes"
        assert user["b_blob"] == b"b_bytes"
        assert user["total_swipes"] == 5
        assert user["last_decay_ts"] == 1234.5
        assert user["drift_active"] == 1

    def test_update_onboarding(self, db_conn):
        uid, _ = insert_user(db_conn, "eve")
        update_user_onboarding(db_conn, uid, dietary_flags_bitmask=3,
                               safety_overrides_bitmask=1)
        user = get_user(db_conn, uid)
        assert user["dietary_flags_bitmask"] == 3
        assert user["safety_overrides_bitmask"] == 1
        assert user["onboarding_complete"] == 1


def _tagged_item(db_conn, name: str, cuisine: str = "italian", safety: int = 0, dietary: int = 0) -> int:
    fid = insert_food_item(db_conn, {"name": name})
    update_food_item_tags(db_conn, fid, {
        "cuisine_type": cuisine,
        "safety_risk_bitmask": safety,
        "dietary_flags_bitmask": dietary,
    })
    return fid


class TestEmbeddings:
    def test_returns_blobs_for_items_with_embedding(self, db_conn):
        fid = _tagged_item(db_conn, "Sushi Roll")
        blob = bytes(range(16))
        db_conn.execute("UPDATE food_items SET embedding = ? WHERE id = ?", [blob, fid])
        db_conn.commit()

        result = get_embeddings_for_items(db_conn, [fid])
        assert result == [blob]

    def test_skips_items_without_embedding(self, db_conn):
        fid = _tagged_item(db_conn, "Plain Rice")
        result = get_embeddings_for_items(db_conn, [fid])
        assert result == []

    def test_empty_id_list_returns_empty(self, db_conn):
        assert get_embeddings_for_items(db_conn, []) == []

    def test_preserves_order_of_ids_with_embeddings(self, db_conn):
        blob_a = b"\x01" * 8
        blob_b = b"\x02" * 8
        fid_a = _tagged_item(db_conn, "Item A")
        fid_b = _tagged_item(db_conn, "Item B")
        db_conn.execute("UPDATE food_items SET embedding = ? WHERE id = ?", [blob_a, fid_a])
        db_conn.execute("UPDATE food_items SET embedding = ? WHERE id = ?", [blob_b, fid_b])
        db_conn.commit()

        result = get_embeddings_for_items(db_conn, [fid_b, fid_a])
        assert result == [blob_b, blob_a]


class TestImpressions:
    def test_record_impression_creates_row(self, db_conn):
        uid, _ = insert_user(db_conn, "user1")
        fid = _tagged_item(db_conn, "Pizza")

        record_impression(db_conn, uid, fid)

        row = db_conn.execute(
            "SELECT count FROM user_item_impressions WHERE user_id = ? AND food_item_id = ?",
            [uid, fid],
        ).fetchone()
        assert row is not None
        assert row["count"] == 1

    def test_record_impression_increments_on_conflict(self, db_conn):
        uid, _ = insert_user(db_conn, "user2")
        fid = _tagged_item(db_conn, "Tacos")

        record_impression(db_conn, uid, fid)
        record_impression(db_conn, uid, fid)
        record_impression(db_conn, uid, fid)

        row = db_conn.execute(
            "SELECT count FROM user_item_impressions WHERE user_id = ? AND food_item_id = ?",
            [uid, fid],
        ).fetchone()
        assert row["count"] == 3

    def test_get_least_impressed_returns_item_with_fewest_impressions(self, db_conn):
        uid, _ = insert_user(db_conn, "user3")
        fid_a = _tagged_item(db_conn, "A")
        fid_b = _tagged_item(db_conn, "B")
        fid_c = _tagged_item(db_conn, "C")

        record_impression(db_conn, uid, fid_a)
        record_impression(db_conn, uid, fid_a)
        record_impression(db_conn, uid, fid_b)

        result = get_least_impressed(db_conn, uid, [fid_a, fid_b, fid_c])
        assert result == fid_c  # fid_c has 0 impressions

    def test_get_least_impressed_tie_breaks_to_first_in_list(self, db_conn):
        uid, _ = insert_user(db_conn, "user4")
        fid_a = _tagged_item(db_conn, "X")
        fid_b = _tagged_item(db_conn, "Y")

        result = get_least_impressed(db_conn, uid, [fid_a, fid_b])
        assert result in (fid_a, fid_b)  # both 0 impressions

    def test_get_least_impressed_empty_raises(self, db_conn):
        uid, _ = insert_user(db_conn, "user5")
        with pytest.raises(ValueError):
            get_least_impressed(db_conn, uid, [])


class TestEligibleFoodItems:
    def test_excludes_unsafe_items(self, db_conn):
        safe_fid = _tagged_item(db_conn, "Safe", safety=0)
        unsafe_fid = _tagged_item(db_conn, "Unsafe", safety=0b00001)  # raw_fish bit

        results = get_eligible_food_items(db_conn, safety_mask=0b00001, dietary_restrictions=[])
        ids = [r["id"] for r in results]
        assert safe_fid in ids
        assert unsafe_fid not in ids

    def test_excludes_allergen_items(self, db_conn):
        safe_fid = _tagged_item(db_conn, "No Nuts", dietary=0b0000000000)
        nut_fid = _tagged_item(db_conn, "Has Nuts", dietary=0b1000000)  # contains_nuts bit 6

        results = get_eligible_food_items(db_conn, safety_mask=0, dietary_restrictions=["contains_nuts"])
        ids = [r["id"] for r in results]
        assert safe_fid in ids
        assert nut_fid not in ids

    def test_excludes_by_id(self, db_conn):
        fid_a = _tagged_item(db_conn, "Exclude Me")
        fid_b = _tagged_item(db_conn, "Keep Me")

        results = get_eligible_food_items(db_conn, safety_mask=0, dietary_restrictions=[], exclude_ids=[fid_a])
        ids = [r["id"] for r in results]
        assert fid_a not in ids
        assert fid_b in ids

    def test_includes_embedding_column(self, db_conn):
        fid = _tagged_item(db_conn, "With Embedding")
        blob = b"\xff" * 4
        db_conn.execute("UPDATE food_items SET embedding = ? WHERE id = ?", [blob, fid])
        db_conn.commit()

        results = get_eligible_food_items(db_conn, safety_mask=0, dietary_restrictions=[])
        item = next(r for r in results if r["id"] == fid)
        assert item["embedding"] == blob
