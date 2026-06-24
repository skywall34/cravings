"""Tests for /api/admin/metrics/* — cross-user aggregates + is_admin gate."""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
TEST_DB = _tmp.name
ADMIN_TOKEN = "test-admin-token-metrics"
os.environ["CRAVINGS_DB"] = TEST_DB
os.environ["CRAVINGS_ADMIN_TOKEN"] = ADMIN_TOKEN
os.environ["CRAVINGS_ADMIN_EMAILS"] = "admin@x.com"
os.environ.setdefault("CRAVINGS_BILLING_WEBHOOK_SECRET", "test-secret-metrics")
os.environ.pop("CRAVINGS_BILLING_PROVIDER", None)

import main  # noqa: E402
import db.database as _db  # noqa: E402
from db import metrics  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures / helpers
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


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _user(conn, user_id: int, *, email: str | None = "u@x.com",
          created_at: str = "2026-01-01T00:00:00", premium: int = 0) -> int:
    conn.execute(
        "INSERT INTO users (id, api_token, name, email, created_at, is_premium) "
        "VALUES (?, ?, 'u', ?, ?, ?)",
        [user_id, f"tok{user_id}", email, created_at, premium],
    )
    conn.commit()
    return user_id


def _food(conn, name: str, *, cuisine="japanese", protein="chicken", carb="rice",
          spice=0.5) -> int:
    cur = conn.execute(
        "INSERT INTO food_items (name, description, tagging_status, spice_level, "
        "richness, dairy_content, sauce_heaviness, texture_softness, savory_umami, "
        "veggie_density, sweetness, protein_type, cuisine_type, carb_base) "
        "VALUES (?, 't', 'tagged', ?, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, ?, ?, ?)",
        [name, spice, protein, cuisine, carb],
    )
    conn.commit()
    return cur.lastrowid


def _swipe(conn, user_id, food_id, direction="right", ts="2026-06-21T12:00:00"):
    conn.execute(
        "INSERT INTO swipe_events (user_id, food_item_id, direction, time_of_day, "
        "recent_rejection_rate, days_since_last_session, timestamp) "
        "VALUES (?, ?, ?, 12.0, 0.0, 0.0, ?)",
        [user_id, food_id, direction, ts],
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Auth gate
# ---------------------------------------------------------------------------

async def test_metrics_requires_token(client):
    for path in ("foods", "catalog", "retention", "engagement"):
        resp = await client.get(f"/api/admin/metrics/{path}")
        assert resp.status_code in (401, 403)


async def test_metrics_rejects_non_admin(client):
    conn = _conn()
    _user(conn, 1, email="u@x.com")
    conn.close()
    resp = await client.get(
        "/api/admin/metrics/foods", headers={"Authorization": "Bearer tok1"}
    )
    assert resp.status_code == 403


async def test_metrics_accepts_admin_user(client):
    conn = _conn()
    _user(conn, 2, email="admin@x.com")
    conn.close()
    resp = await client.get(
        "/api/admin/metrics/foods", headers={"Authorization": "Bearer tok2"}
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Food performance
# ---------------------------------------------------------------------------

def test_food_performance_rate_and_ranking():
    conn = _conn()
    _user(conn, 1)
    winner = _food(conn, "Winner")
    loser = _food(conn, "Loser")
    for _ in range(8):
        _swipe(conn, 1, winner, "right")
    for _ in range(2):
        _swipe(conn, 1, winner, "left")
    for _ in range(8):
        _swipe(conn, 1, loser, "left")
    for _ in range(2):
        _swipe(conn, 1, loser, "right")

    out = metrics.food_performance(conn, min_swipes=5)
    assert out["food_count"] == 2
    assert out["best"][0]["name"] == "Winner"
    assert out["best"][0]["right_rate"] == 80
    assert out["worst"][0]["name"] == "Loser"
    assert out["worst"][0]["right_rate"] == 20


def test_food_performance_min_swipes_suppresses_noise():
    conn = _conn()
    _user(conn, 1)
    big = _food(conn, "Big")
    tiny = _food(conn, "Tiny")
    for _ in range(6):
        _swipe(conn, 1, big, "right")
    _swipe(conn, 1, tiny, "right")  # only 1 swipe → below threshold

    out = metrics.food_performance(conn, min_swipes=5)
    names = {f["name"] for f in out["best"]}
    assert names == {"Big"}


def test_food_performance_cuisine_filter():
    conn = _conn()
    _user(conn, 1)
    jp = _food(conn, "Sushi", cuisine="japanese")
    it = _food(conn, "Pizza", cuisine="italian")
    for _ in range(5):
        _swipe(conn, 1, jp, "right")
        _swipe(conn, 1, it, "right")
    out = metrics.food_performance(conn, min_swipes=5, cuisine="italian")
    assert out["food_count"] == 1
    assert out["best"][0]["name"] == "Pizza"


# ---------------------------------------------------------------------------
# Catalog trends
# ---------------------------------------------------------------------------

def test_catalog_trends_by_cuisine():
    conn = _conn()
    _user(conn, 1)
    jp = _food(conn, "Sushi", cuisine="japanese")
    it = _food(conn, "Pizza", cuisine="italian")
    for _ in range(4):
        _swipe(conn, 1, jp, "right")
    _swipe(conn, 1, it, "left")

    out = metrics.catalog_trends(conn)
    by_c = {d["key"]: d for d in out["by_cuisine"]}
    assert by_c["japanese"]["right_rate"] == 100
    assert by_c["italian"]["right_rate"] == 0
    # sorted desc → japanese first
    assert out["by_cuisine"][0]["key"] == "japanese"
    assert "spice_level" in out["right_swipe_attributes"]


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

def test_retention_caveat_fields_and_activity():
    conn = _conn()
    _user(conn, 1, created_at="2026-01-01T00:00:00")
    f = _food(conn, "F")
    _swipe(conn, 1, f, "right", ts="now")  # recent swipe → counts as active

    out = metrics.retention(conn, days=30)
    assert out["active_definition"] == "swiped"
    assert out["population"] == "registered_only"
    assert out["dau"] == 1
    assert out["wau"] == 1
    assert out["mau"] == 1
    assert set(out["cohort_retention"]) == {"D1", "D7", "D30"}


def test_retention_d1_cohort():
    conn = _conn()
    # User signed up 10 days ago, active on day 1 → retained at D1.
    _user(conn, 1, created_at="datetime-placeholder")
    conn.execute(
        "UPDATE users SET created_at = datetime('now', '-10 days') WHERE id = 1"
    )
    conn.commit()
    f = _food(conn, "F")
    conn.execute(
        "INSERT INTO swipe_events (user_id, food_item_id, direction, time_of_day, "
        "recent_rejection_rate, days_since_last_session, timestamp) "
        "VALUES (1, ?, 'right', 12.0, 0.0, 0.0, datetime('now', '-9 days'))",
        [f],
    )
    conn.commit()

    out = metrics.retention(conn, days=30)
    assert out["cohort_eligible"]["D1"] == 1
    assert out["cohort_retention"]["D1"] == 100


# ---------------------------------------------------------------------------
# Engagement
# ---------------------------------------------------------------------------

def test_engagement_histogram_and_say_yes():
    conn = _conn()
    _user(conn, 1)
    _user(conn, 2, email="b@x.com")
    f = _food(conn, "F")
    for _ in range(12):  # user 1 → 10-49 bucket
        _swipe(conn, 1, f, "right")
    for _ in range(3):   # user 2 → 1-9 bucket
        _swipe(conn, 2, f, "left")

    out = metrics.engagement(conn, days=30)
    hist = {b["bucket"]: b["users"] for b in out["swipes_per_user_histogram"]}
    assert hist["10-49"] == 1
    assert hist["1-9"] == 1
    assert out["total_swipes"] == 15
    assert out["global_say_yes_rate"] == 80  # 12/15
    assert out["active_users_with_swipes"] == 2
    assert out["registered_users"] == 2


def test_engagement_premium_count():
    conn = _conn()
    _user(conn, 1, premium=1)
    _user(conn, 2, email="b@x.com", premium=0)
    out = metrics.engagement(conn, days=30)
    assert out["premium_users"] == 1
    assert out["registered_users"] == 2
