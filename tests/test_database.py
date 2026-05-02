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
