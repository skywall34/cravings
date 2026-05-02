"""Async API tests ported from the Go backend test suite."""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Must set env before importing main so lifespan picks up the test DB.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
TEST_DB = _tmp.name
os.environ["CRAVINGS_DB"] = TEST_DB

import main  # noqa: E402 — env set above
import db.database as _db  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    """Re-initialize DB and reset in-memory state before each test."""
    main._db_path = Path(TEST_DB)
    Path(TEST_DB).unlink(missing_ok=True)
    _db.init_db(Path(TEST_DB))
    main._sessions.clear_all()
    yield


@pytest_asyncio.fixture
async def client(reset_db):
    """HTTP client with lifespan triggered."""
    async with main.lifespan(main.app):
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture
async def auth_client(client):
    """Client with a created user; yields (client, token, user_id)."""
    resp = await client.post("/api/users", json={"name": "Alice"})
    assert resp.status_code == 201
    data = resp.json()
    token = data["api_token"]
    user_id = data["id"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client, token, user_id


def _insert_food_item(db_path: str, name: str = "Spicy Ramen") -> int:
    """Insert a tagged food item directly into the test DB."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "INSERT INTO food_items (name, description, tagging_status, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "protein_type, cuisine_type, carb_base, veggie_density, dairy_content, "
        "smell_intensity, nausea_trigger, safety_risk_bitmask, dietary_flags_bitmask) "
        "VALUES (?, 'A test food item', 'tagged', "
        "0.8, 0.2, 0.3, 0.9, 0.5, 0.1, "
        "0.7, 0.4, 0.6, 0.8, "
        "'chicken', 'japanese', 'noodles_pasta', 0.2, 0.1, "
        "0.5, 0.0, 0, 0)",
        [name],
    )
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# User creation
# ---------------------------------------------------------------------------

async def test_create_user(client):
    resp = await client.post("/api/users", json={"name": "Bob"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Bob"
    assert "api_token" in data
    assert isinstance(data["id"], int)
    assert data["dietary_restrictions"] == []
    assert data["safety_overrides"] == []


async def test_create_user_with_restrictions(client):
    resp = await client.post("/api/users", json={
        "name": "Vegan User",
        "dietary_restrictions": ["vegan"],
        "safety_overrides": ["raw_fish"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "vegan" in data["dietary_restrictions"]
    assert "raw_fish" in data["safety_overrides"]


async def test_create_user_missing_name(client):
    resp = await client.post("/api/users", json={"name": ""})
    assert resp.status_code == 400


async def test_create_user_no_name_field(client):
    resp = await client.post("/api/users", json={})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

async def test_auth_missing_token(client):
    resp = await client.get("/api/users/me")
    assert resp.status_code in (401, 403)  # HTTPBearer returns 401/403 when header absent


async def test_auth_invalid_token(client):
    resp = await client.get("/api/users/me", headers={"Authorization": "Bearer badtoken"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /api/users/me
# ---------------------------------------------------------------------------

async def test_get_me(auth_client):
    client, token, user_id = auth_client
    resp = await client.get("/api/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user_id
    assert data["name"] == "Alice"
    assert data["onboarding_complete"] is False


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

async def test_onboarding(auth_client):
    client, _, _ = auth_client
    resp = await client.post("/api/onboarding", json={
        "preferences": {"spice_level": 0.8, "sweetness": -0.5}
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    me = await client.get("/api/users/me")
    assert me.json()["onboarding_complete"] is True


async def test_onboarding_empty_prefs(auth_client):
    client, _, _ = auth_client
    resp = await client.post("/api/onboarding", json={"preferences": {}})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Recommend
# ---------------------------------------------------------------------------

async def test_recommend_no_items(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/recommend?session_id=s1")
    assert resp.status_code == 404


async def test_recommend_returns_item(auth_client):
    client, _, _ = auth_client
    _insert_food_item(TEST_DB)
    resp = await client.get("/api/recommend?session_id=s1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert "id" in data[0]
    assert "name" in data[0]
    assert "score" in data[0]
    assert "snapshot_token" in data[0]


async def _recommend_and_token(client, session_id="s1"):
    resp = await client.get(f"/api/recommend?session_id={session_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()[0]["snapshot_token"]


async def test_recommend_session_dedup(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)

    # First recommend returns the item with a snapshot token
    resp1 = await client.get("/api/recommend?session_id=s1")
    assert resp1.status_code == 200
    token = resp1.json()[0]["snapshot_token"]

    # Swipe on it to add to session seen-set
    await client.post("/api/swipe", json={
        "food_item_id": item_id,
        "direction": "left",
        "session_id": "s1",
        "snapshot_token": token,
    })

    # Second recommend with same session → item excluded → 404 (only 1 item)
    resp2 = await client.get("/api/recommend?session_id=s1")
    assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# Swipe
# ---------------------------------------------------------------------------

async def test_swipe_right(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)
    token = await _recommend_and_token(client)
    resp = await client.post("/api/swipe", json={
        "food_item_id": item_id,
        "direction": "right",
        "session_id": "s1",
        "snapshot_token": token,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["total_swipes"] == 1


async def test_swipe_invalid_direction(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)
    token = await _recommend_and_token(client)
    resp = await client.post("/api/swipe", json={
        "food_item_id": item_id,
        "direction": "up",
        "session_id": "s1",
        "snapshot_token": token,
    })
    assert resp.status_code == 400


async def test_swipe_unknown_item(auth_client):
    client, _, _ = auth_client
    resp = await client.post("/api/swipe", json={
        "food_item_id": 99999,
        "direction": "right",
        "session_id": "s1",
        "snapshot_token": "x.y",
    })
    assert resp.status_code == 404


async def test_swipe_missing_token(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)
    resp = await client.post("/api/swipe", json={
        "food_item_id": item_id,
        "direction": "right",
        "session_id": "s1",
    })
    assert resp.status_code == 400


async def test_swipe_tampered_token(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)
    resp = await client.post("/api/swipe", json={
        "food_item_id": item_id,
        "direction": "right",
        "session_id": "s1",
        "snapshot_token": "bogus.payload",
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Session reset
# ---------------------------------------------------------------------------

async def test_session_reset(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)
    token = await _recommend_and_token(client)

    await client.post("/api/swipe", json={
        "food_item_id": item_id, "direction": "left", "session_id": "s1", "snapshot_token": token,
    })

    reset_resp = await client.post("/api/session/reset", json={"session_id": "s1"})
    assert reset_resp.status_code == 200

    # After reset, item appears again
    rec = await client.get("/api/recommend?session_id=s1")
    assert rec.status_code == 200


# ---------------------------------------------------------------------------
# Food items
# ---------------------------------------------------------------------------

async def test_list_food_items_empty(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/food-items")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_food_items(auth_client):
    client, _, _ = auth_client
    _insert_food_item(TEST_DB)
    resp = await client.get("/api/food-items")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_food_item(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB, name="Sushi")
    resp = await client.get(f"/api/food-items/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Sushi"


async def test_get_food_item_not_found(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/food-items/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Restaurants
# ---------------------------------------------------------------------------

async def test_list_restaurants_empty(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/restaurants")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Model status
# ---------------------------------------------------------------------------

async def test_model_status(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/model/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_swipes" in data
    assert data["total_swipes"] == 0


async def test_model_status_after_swipe(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)
    token = await _recommend_and_token(client)
    await client.post("/api/swipe", json={
        "food_item_id": item_id, "direction": "right",
        "session_id": "s1", "snapshot_token": token,
    })
    resp = await client.get("/api/model/status")
    assert resp.json()["total_swipes"] == 1


# ---------------------------------------------------------------------------
# Nearby (stub mode — no API key)
# ---------------------------------------------------------------------------

async def test_nearby_stub(auth_client):
    client, _, _ = auth_client
    item_id = _insert_food_item(TEST_DB)
    resp = await client.get(f"/api/nearby?food_item_id={item_id}&lat=37.77&lng=-122.41")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "name" in data[0]
    assert "address" in data[0]


async def test_nearby_missing_params(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/nearby?food_item_id=1")
    assert resp.status_code == 422  # FastAPI validation error


async def test_nearby_unknown_item(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/nearby?food_item_id=99999&lat=37.77&lng=-122.41")
    assert resp.status_code == 404
