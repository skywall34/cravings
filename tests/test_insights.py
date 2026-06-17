"""Tests for GET /api/insights — axis math, premium gate, thin-data gate."""

import math
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
TEST_DB = _tmp.name
os.environ["CRAVINGS_DB"] = TEST_DB
os.environ.setdefault("CRAVINGS_BILLING_WEBHOOK_SECRET", "test-secret-insights")
os.environ.pop("CRAVINGS_BILLING_PROVIDER", None)

import main  # noqa: E402
import db.database as _db  # noqa: E402
from db.swipe_events import get_insights  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    os.environ["CRAVINGS_DB"] = TEST_DB
    main._db_path = Path(TEST_DB)
    Path(TEST_DB).unlink(missing_ok=True)
    _db.init_db(Path(TEST_DB))
    main._sessions.clear_all()
    yield


@pytest_asyncio.fixture
async def client(reset_db):
    async with main.lifespan(main.app):
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture
async def premium_client(client):
    """Registered premium user; yields (client, user_id)."""
    resp = await client.post("/api/auth/register", json={
        "email": "insights_test@example.com",
        "password": "securepass1",
        "name": "Tester",
    })
    assert resp.status_code == 201
    data = resp.json()
    user_id = data["id"]
    client.headers["Authorization"] = f"Bearer {data['api_token']}"

    # Grant premium via DB directly
    with _db.db_connection(Path(TEST_DB)) as conn:
        _db.set_premium(conn, user_id)

    yield client, user_id


def _insert_food_item(
    conn: sqlite3.Connection,
    name: str,
    cuisine: str = "japanese",
    spice: float = 0.5,
    richness: float = 0.5,
    dairy: float = 0.5,
    sauce: float = 0.5,
    texture_soft: float = 0.5,
) -> int:
    cursor = conn.execute(
        "INSERT INTO food_items (name, description, tagging_status, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "protein_type, cuisine_type, carb_base, veggie_density, dairy_content, "
        "smell_intensity, nausea_trigger, safety_risk_bitmask, dietary_flags_bitmask) "
        "VALUES (?, 'test food', 'tagged', "
        "?, 0.2, 0.1, 0.5, 0.3, 0.0, "
        "0.5, ?, ?, ?, "
        "'chicken', ?, 'rice', 0.2, ?, "
        "0.2, 0.0, 0, 0)",
        [name, spice, texture_soft, sauce, richness, cuisine, dairy],
    )
    conn.commit()
    return cursor.lastrowid


def _insert_swipe(
    conn: sqlite3.Connection,
    user_id: int,
    food_item_id: int,
    direction: str = "right",
    time_of_day: float = 12.0,
    timestamp: str = "2026-06-01T12:00:00",
) -> None:
    conn.execute(
        "INSERT INTO swipe_events (user_id, food_item_id, direction, time_of_day, "
        "recent_rejection_rate, days_since_last_session, timestamp) "
        "VALUES (?, ?, ?, ?, 0.0, 0.0, ?)",
        [user_id, food_item_id, direction, time_of_day, timestamp],
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Gate tests
# ---------------------------------------------------------------------------

async def test_insights_requires_auth(client):
    resp = await client.get("/api/insights")
    assert resp.status_code == 401


async def test_insights_requires_premium(client):
    resp = await client.post("/api/auth/register", json={
        "email": "free@example.com", "password": "securepass1", "name": "Free",
    })
    data = resp.json()
    client.headers["Authorization"] = f"Bearer {data['api_token']}"
    resp = await client.get("/api/insights")
    assert resp.status_code == 403
    assert "premium" in resp.json()["detail"]


async def test_insights_premium_200(premium_client):
    client, _ = premium_client
    resp = await client.get("/api/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert "axes" in data
    assert "ready" in data
    assert "total_right_swipes" in data


async def test_insights_admin_bypass(client, monkeypatch):
    """Admin email bypasses premium gate without payment."""
    monkeypatch.setenv("CRAVINGS_ADMIN_EMAILS", "admin@example.com")
    resp = await client.post("/api/auth/register", json={
        "email": "admin@example.com", "password": "securepass1", "name": "Admin",
    })
    data = resp.json()
    client.headers["Authorization"] = f"Bearer {data['api_token']}"
    resp = await client.get("/api/insights")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Thin-data gate
# ---------------------------------------------------------------------------

async def test_insights_thin_data_not_ready(premium_client):
    client, user_id = premium_client
    with _db.db_connection(Path(TEST_DB)) as conn:
        item_id = _insert_food_item(conn, "Ramen")
        for i in range(5):
            _insert_swipe(conn, user_id, item_id, "right", 12.0)

    resp = await client.get("/api/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is False
    assert data["total_right_swipes"] == 5


async def test_insights_ready_at_20(premium_client):
    client, user_id = premium_client
    with _db.db_connection(Path(TEST_DB)) as conn:
        item_id = _insert_food_item(conn, "Curry")
        for i in range(20):
            _insert_swipe(conn, user_id, item_id, "right", 12.0)

    resp = await client.get("/api/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["total_right_swipes"] == 20


# ---------------------------------------------------------------------------
# Axis math unit tests (direct function call)
# ---------------------------------------------------------------------------

def _make_conn() -> sqlite3.Connection:
    Path(TEST_DB).unlink(missing_ok=True)
    _db.init_db(Path(TEST_DB))
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    return conn


def test_heat_axis():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Spicy", spice=0.8)
    _insert_swipe(conn, user_id, item_id, "right", 12.0)
    data = get_insights(conn, user_id)
    assert data["axes"]["Heat"] == 80  # 0.8 * 100


def test_indulgence_axis():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Rich", richness=0.6, dairy=0.3, sauce=0.9)
    _insert_swipe(conn, user_id, item_id, "right", 12.0)
    data = get_insights(conn, user_id)
    expected = round((0.6 + 0.3 + 0.9) / 3 * 100)
    assert data["axes"]["Indulgence"] == expected


def test_texture_axis():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Crunchy", texture_soft=0.2)
    _insert_swipe(conn, user_id, item_id, "right", 12.0)
    data = get_insights(conn, user_id)
    assert data["axes"]["Texture"] == round((1 - 0.2) * 100)


def test_adventure_axis_single_cuisine():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Sushi", cuisine="japanese")
    _insert_swipe(conn, user_id, item_id, "right", 12.0)
    data = get_insights(conn, user_id)
    assert data["axes"]["Adventure"] == 0  # 1 cuisine, entropy=0


def test_adventure_axis_equal_split():
    """Two cuisines with equal right-swipe counts → entropy normalized to 1.0 → 100."""
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_jp = _insert_food_item(conn, "Sushi", cuisine="japanese")
    item_it = _insert_food_item(conn, "Pizza", cuisine="italian")
    _insert_swipe(conn, user_id, item_jp, "right", 12.0)
    _insert_swipe(conn, user_id, item_it, "right", 12.0)
    data = get_insights(conn, user_id)
    # Equal split → entropy = log(2), normalized = 1.0 → 100
    assert data["axes"]["Adventure"] == 100


def test_tempo_axis_night():
    """All right swipes at hour 20 → tempo = 100."""
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Night Snack")
    _insert_swipe(conn, user_id, item_id, "right", time_of_day=20.0)
    data = get_insights(conn, user_id)
    assert data["axes"]["Tempo"] == 100


def test_tempo_axis_daytime():
    """Right swipe at noon → tempo = 0."""
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Lunch")
    _insert_swipe(conn, user_id, item_id, "right", time_of_day=12.0)
    data = get_insights(conn, user_id)
    assert data["axes"]["Tempo"] == 0


def test_tempo_axis_early_morning():
    """Hour 3 (04:00 exclusive) counts as nocturnal."""
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "3am snack")
    _insert_swipe(conn, user_id, item_id, "right", time_of_day=3.0)
    data = get_insights(conn, user_id)
    assert data["axes"]["Tempo"] == 100


def test_left_swipes_ignored_in_axes():
    """Left swipes must not affect axis computation."""
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_high = _insert_food_item(conn, "Fiery", spice=1.0)
    item_mild = _insert_food_item(conn, "Mild", spice=0.0)
    _insert_swipe(conn, user_id, item_high, "right", 12.0)
    _insert_swipe(conn, user_id, item_mild, "left", 12.0)  # must be ignored
    data = get_insights(conn, user_id)
    assert data["axes"]["Heat"] == 100


# ---------------------------------------------------------------------------
# Recap
# ---------------------------------------------------------------------------

def test_recap_top_cuisine():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_jp1 = _insert_food_item(conn, "Ramen", cuisine="japanese")
    item_jp2 = _insert_food_item(conn, "Sushi", cuisine="japanese")
    item_it = _insert_food_item(conn, "Pizza", cuisine="italian")
    _insert_swipe(conn, user_id, item_jp1, "right", 12.0)
    _insert_swipe(conn, user_id, item_jp2, "right", 12.0)
    _insert_swipe(conn, user_id, item_it, "right", 12.0)
    data = get_insights(conn, user_id)
    assert data["recap"]["top_cuisine"] == "japanese"


def test_recap_say_yes_rate():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Food")
    _insert_swipe(conn, user_id, item_id, "right", 12.0)
    _insert_swipe(conn, user_id, item_id, "left", 12.0)
    _insert_swipe(conn, user_id, item_id, "left", 12.0)
    data = get_insights(conn, user_id)
    assert data["recap"]["say_yes_rate"] == 33  # 1/3 * 100 rounded


# ---------------------------------------------------------------------------
# Drift
# ---------------------------------------------------------------------------

def test_drift_requires_two_months():
    """Single month → no drift data."""
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Food")
    for i in range(3):
        _insert_swipe(conn, user_id, item_id, "right", 12.0, "2026-06-01T12:00:00")
    data = get_insights(conn, user_id)
    assert data["drift"] is None


def test_drift_two_months_present():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_id = _insert_food_item(conn, "Food")
    _insert_swipe(conn, user_id, item_id, "right", 12.0, "2026-05-15T12:00:00")
    _insert_swipe(conn, user_id, item_id, "right", 12.0, "2026-06-15T12:00:00")
    data = get_insights(conn, user_id)
    assert data["drift"] is not None
    assert len(data["drift"]["windows"]) == 2
    assert "May" in data["drift"]["windows"]
    assert "Jun" in data["drift"]["windows"]
    for k in ["Heat", "Indulgence", "Texture", "Adventure", "Tempo"]:
        assert k in data["drift"]["series"]
        assert len(data["drift"]["series"][k]) == 2


def test_drift_cumulative():
    """Window 2 (cumulative) must include swipes from window 1."""
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_hot = _insert_food_item(conn, "Hot", spice=1.0)
    item_mild = _insert_food_item(conn, "Mild", spice=0.0)
    # Month 1: right-swipe spicy item
    _insert_swipe(conn, user_id, item_hot, "right", 12.0, "2026-05-15T12:00:00")
    # Month 2: right-swipe mild item
    _insert_swipe(conn, user_id, item_mild, "right", 12.0, "2026-06-15T12:00:00")
    data = get_insights(conn, user_id)
    drift = data["drift"]
    assert drift is not None
    # Month 2 window cumulative includes both: AVG(1.0, 0.0)*100 = 50
    assert drift["series"]["Heat"][1] == 50


def test_drift_biggest_mover():
    conn = _make_conn()
    user_id = 1
    conn.execute(
        "INSERT INTO users (id, api_token, name) VALUES (?, 'tok1', 'u')", [user_id]
    )
    item_hot = _insert_food_item(conn, "Hot", spice=0.9)
    item_mild = _insert_food_item(conn, "Mild", spice=0.1)
    _insert_swipe(conn, user_id, item_mild, "right", 12.0, "2026-05-01T12:00:00")
    _insert_swipe(conn, user_id, item_hot, "right", 12.0, "2026-06-01T12:00:00")
    data = get_insights(conn, user_id)
    # Heat changes most (from mild only → cumulative with hot)
    assert data["recap"]["biggest_mover"] is not None
