"""Tests for auth endpoints and profile stats."""

import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
TEST_DB = _tmp.name
os.environ.setdefault("CRAVINGS_DB", TEST_DB)

import main  # noqa: E402
import db.database as _db  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
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
async def guest_client(client):
    """Client with auto-created guest user; yields (client, token, user_id)."""
    resp = await client.post("/api/users", json={"name": "guest"})
    assert resp.status_code == 201
    data = resp.json()
    client.headers["Authorization"] = f"Bearer {data['api_token']}"
    yield client, data["api_token"], data["id"]


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

async def test_register_cold(client):
    """Cold register (no bearer) creates a new registered user."""
    resp = await client.post("/api/auth/register", json={
        "email": "alice@example.com",
        "password": "securepass1",
        "name": "Alice",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["is_registered"] is True
    assert "api_token" in data


async def test_register_claims_guest(guest_client):
    """Registering while holding a guest token claims the guest row."""
    client, guest_token, guest_id = guest_client
    resp = await client.post("/api/auth/register", json={
        "email": "bob@example.com",
        "password": "securepass2",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == guest_id
    assert data["api_token"] == guest_token
    assert data["is_registered"] is True


async def test_register_email_conflict(client):
    """Second register with same email returns 409."""
    payload = {"email": "carol@example.com", "password": "securepass3", "name": "Carol"}
    r1 = await client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/auth/register", json=payload)
    assert r2.status_code == 409
    assert "log in" in r2.json()["detail"].lower()


async def test_register_short_password(client):
    """Passwords < 8 chars rejected."""
    resp = await client.post("/api/auth/register", json={
        "email": "dave@example.com",
        "password": "short",
        "name": "Dave",
    })
    assert resp.status_code == 400


async def test_register_invalid_email(client):
    """Invalid email rejected."""
    resp = await client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "securepass4",
        "name": "Eve",
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_success(client):
    """Login with correct credentials returns token."""
    await client.post("/api/auth/register", json={
        "email": "frank@example.com",
        "password": "correcthorse",
        "name": "Frank",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "frank@example.com",
        "password": "correcthorse",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "api_token" in data
    assert data["email"] == "frank@example.com"


async def test_login_bad_password(client):
    """Wrong password returns 401."""
    await client.post("/api/auth/register", json={
        "email": "grace@example.com",
        "password": "correcthorse",
        "name": "Grace",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "grace@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    """Unknown email returns 401."""
    resp = await client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

async def test_logout_rotates_token(client):
    """Logout invalidates the old token."""
    r = await client.post("/api/auth/register", json={
        "email": "henry@example.com",
        "password": "securepass5",
        "name": "Henry",
    })
    old_token = r.json()["api_token"]
    client.headers["Authorization"] = f"Bearer {old_token}"

    logout_resp = await client.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    # Old token no longer works
    me_resp = await client.get("/api/users/me")
    assert me_resp.status_code == 401


# ---------------------------------------------------------------------------
# Password change
# ---------------------------------------------------------------------------

async def test_password_change_invalidates_old_token(client):
    """After password change, old token rejected."""
    r = await client.post("/api/auth/register", json={
        "email": "iris@example.com",
        "password": "original123",
        "name": "Iris",
    })
    old_token = r.json()["api_token"]
    client.headers["Authorization"] = f"Bearer {old_token}"

    pw_resp = await client.post("/api/auth/password", json={
        "old_password": "original123",
        "new_password": "newpass456",
    })
    assert pw_resp.status_code == 200
    new_token = pw_resp.json()["api_token"]
    assert new_token != old_token

    # Old token rejected
    client.headers["Authorization"] = f"Bearer {old_token}"
    me_resp = await client.get("/api/users/me")
    assert me_resp.status_code == 401

    # New token works
    client.headers["Authorization"] = f"Bearer {new_token}"
    me_resp2 = await client.get("/api/users/me")
    assert me_resp2.status_code == 200


async def test_password_change_wrong_old_password(client):
    """Wrong old password returns 401."""
    r = await client.post("/api/auth/register", json={
        "email": "jack@example.com",
        "password": "original123",
        "name": "Jack",
    })
    client.headers["Authorization"] = f"Bearer {r.json()['api_token']}"

    resp = await client.post("/api/auth/password", json={
        "old_password": "wrongold",
        "new_password": "newpass789",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Profile stats
# ---------------------------------------------------------------------------

async def test_stats_empty(client):
    """Stats endpoint returns zero-state for user with no swipes."""
    r = await client.post("/api/auth/register", json={
        "email": "kate@example.com",
        "password": "securepass6",
        "name": "Kate",
    })
    client.headers["Authorization"] = f"Bearer {r.json()['api_token']}"

    resp = await client.get("/api/profile/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_swipes"] == 0
    assert data["cuisine_breakdown"] == []
    assert data["avg_swipes_to_right"] is None
    assert data["mood_breakdown"] == []


async def test_stats_requires_auth(client):
    """Stats endpoint requires bearer token."""
    resp = await client.get("/api/profile/stats")
    assert resp.status_code in (401, 403)
