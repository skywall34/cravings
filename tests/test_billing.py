"""Billing unit + integration tests. MockProvider only — no Stripe keys required."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set env before importing main so lifespan picks up the test DB.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
TEST_DB = _tmp.name
os.environ["CRAVINGS_DB"] = TEST_DB
os.environ.setdefault("CRAVINGS_BILLING_WEBHOOK_SECRET", "test-secret-123")
os.environ.pop("CRAVINGS_BILLING_PROVIDER", None)  # force mock

import main  # noqa: E402
import db.database as _db  # noqa: E402
from billing import MockProvider, _hmac_sign
from schemas import is_admin_email


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    os.environ["CRAVINGS_DB"] = TEST_DB  # re-assert so lifespan uses billing test DB
    main._db_path = Path(TEST_DB)
    Path(TEST_DB).unlink(missing_ok=True)
    _db.init_db(Path(TEST_DB))
    main._sessions.clear_all()
    # Re-init provider with test secret
    os.environ["CRAVINGS_BILLING_WEBHOOK_SECRET"] = "test-secret-123"
    os.environ.pop("CRAVINGS_BILLING_PROVIDER", None)
    from billing import make_payment_provider
    main._payment_provider = make_payment_provider()
    yield


@pytest_asyncio.fixture
async def client(reset_db):
    async with main.lifespan(main.app):
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture
async def auth_client(client):
    resp = await client.post("/api/auth/register", json={
        "email": "billing_test@example.com",
        "password": "securepass1",
        "name": "Buyer",
    })
    assert resp.status_code == 201
    data = resp.json()
    client.headers["Authorization"] = f"Bearer {data['api_token']}"
    yield client, data["api_token"], data["id"]


# ---------------------------------------------------------------------------
# Unit: MockProvider
# ---------------------------------------------------------------------------

def test_mock_provider_session_shape():
    provider = MockProvider("secret")
    session = provider.create_checkout_session({"id": 1}, 499)
    assert session.session_id.startswith("mock_cs_")
    assert session.amount_cents == 499
    assert session.provider == "mock"
    assert session.url is None


def test_mock_provider_webhook_accept():
    provider = MockProvider("secret")
    payload = json.dumps({
        "type": "checkout.session.completed",
        "data": {"object": {"id": "mock_cs_abc", "metadata": {"user_id": "42"}}},
    }).encode()
    sig = _hmac_sign(payload, "secret")
    event = provider.verify_and_parse_webhook(payload, sig)
    assert event.event_type == "checkout.session.completed"
    assert event.session_id == "mock_cs_abc"
    assert event.user_id == 42


def test_mock_provider_webhook_reject_bad_sig():
    provider = MockProvider("secret")
    payload = b'{"type":"checkout.session.completed","data":{"object":{"id":"x","metadata":{"user_id":"1"}}}}'
    with pytest.raises(ValueError, match="invalid mock webhook signature"):
        provider.verify_and_parse_webhook(payload, "badsig")


def test_mock_provider_webhook_reject_empty_sig():
    provider = MockProvider("secret")
    payload = b'{"type":"checkout.session.completed","data":{"object":{"id":"x","metadata":{"user_id":"1"}}}}'
    with pytest.raises(ValueError):
        provider.verify_and_parse_webhook(payload, "")


# ---------------------------------------------------------------------------
# Unit: is_admin_email
# ---------------------------------------------------------------------------

def test_is_admin_email_match(monkeypatch):
    monkeypatch.setenv("CRAVINGS_ADMIN_EMAILS", "admin@example.com,boss@example.com")
    assert is_admin_email("admin@example.com") is True
    assert is_admin_email("ADMIN@EXAMPLE.COM") is True
    assert is_admin_email("boss@example.com") is True


def test_is_admin_email_no_match(monkeypatch):
    monkeypatch.setenv("CRAVINGS_ADMIN_EMAILS", "admin@example.com")
    assert is_admin_email("user@example.com") is False


def test_is_admin_email_none():
    assert is_admin_email(None) is False


def test_is_admin_email_empty_env(monkeypatch):
    monkeypatch.delenv("CRAVINGS_ADMIN_EMAILS", raising=False)
    assert is_admin_email("admin@example.com") is False


# ---------------------------------------------------------------------------
# Unit: DB premium helpers
# ---------------------------------------------------------------------------

def test_set_premium_persists():
    with _db.db_connection(Path(TEST_DB)) as conn:
        user_id, _ = _db.insert_user(conn, "TestUser")
        assert _db.get_user(conn, user_id)["is_premium"] == 0
        _db.set_premium(conn, user_id)
        u = _db.get_user(conn, user_id)
        assert u["is_premium"] == 1
        assert u["premium_since"] is not None


def test_set_premium_idempotent():
    with _db.db_connection(Path(TEST_DB)) as conn:
        user_id, _ = _db.insert_user(conn, "TestUser2")
        _db.set_premium(conn, user_id)
        _db.set_premium(conn, user_id)  # second call — no error
        assert _db.get_user(conn, user_id)["is_premium"] == 1


def test_billing_session_lifecycle():
    with _db.db_connection(Path(TEST_DB)) as conn:
        user_id, _ = _db.insert_user(conn, "TestUser3")
        _db.create_billing_session(conn, "cs_abc", user_id, 499)
        session = _db.get_billing_session(conn, "cs_abc")
        assert session["status"] == "pending"
        assert session["amount_cents"] == 499
        _db.complete_billing_session(conn, "cs_abc")
        session = _db.get_billing_session(conn, "cs_abc")
        assert session["status"] == "completed"
        assert session["completed_at"] is not None


# ---------------------------------------------------------------------------
# Integration: full billing flow
# ---------------------------------------------------------------------------

def _make_webhook(session_id: str, user_id: int, secret: str = "test-secret-123") -> tuple[bytes, str]:
    payload = json.dumps({
        "type": "checkout.session.completed",
        "data": {"object": {"id": session_id, "metadata": {"user_id": str(user_id)}}},
    }).encode()
    sig = _hmac_sign(payload, secret)
    return payload, sig


@pytest.mark.asyncio
async def test_register_shows_not_premium(auth_client):
    client, _, _ = auth_client
    resp = await client.get("/api/users/me")
    data = resp.json()
    assert data["is_premium"] is False
    assert data["is_admin"] is False


@pytest.mark.asyncio
async def test_checkout_guest_returns_403(client):
    resp = await client.post("/api/billing/checkout")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_checkout_registered_returns_session(auth_client):
    client, _, _ = auth_client
    resp = await client.post("/api/billing/checkout")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "mock"
    assert data["url"] is None
    assert data["session_id"].startswith("mock_cs_")
    assert data["amount_cents"] == 499


@pytest.mark.asyncio
async def test_webhook_flips_premium(auth_client):
    client, _, user_id = auth_client

    # Create a session first
    resp = await client.post("/api/billing/checkout")
    session_id = resp.json()["session_id"]

    # Fire signed webhook
    payload, sig = _make_webhook(session_id, user_id)
    wresp = await client.post(
        "/api/billing/webhook",
        content=payload,
        headers={"x-mock-signature": sig, "content-type": "application/json"},
    )
    assert wresp.status_code == 200

    # Premium now true
    me = (await client.get("/api/users/me")).json()
    assert me["is_premium"] is True


@pytest.mark.asyncio
async def test_webhook_idempotent(auth_client):
    client, _, user_id = auth_client
    resp = await client.post("/api/billing/checkout")
    session_id = resp.json()["session_id"]
    payload, sig = _make_webhook(session_id, user_id)

    # Fire twice
    for _ in range(2):
        wresp = await client.post(
            "/api/billing/webhook",
            content=payload,
            headers={"x-mock-signature": sig, "content-type": "application/json"},
        )
        assert wresp.status_code == 200

    me = (await client.get("/api/users/me")).json()
    assert me["is_premium"] is True


@pytest.mark.asyncio
async def test_webhook_bad_sig_rejected(auth_client):
    client, _, user_id = auth_client
    resp = await client.post("/api/billing/checkout")
    session_id = resp.json()["session_id"]
    payload, _ = _make_webhook(session_id, user_id)

    wresp = await client.post(
        "/api/billing/webhook",
        content=payload,
        headers={"x-mock-signature": "badsignature", "content-type": "application/json"},
    )
    assert wresp.status_code == 400

    me = (await client.get("/api/users/me")).json()
    assert me["is_premium"] is False


@pytest.mark.asyncio
async def test_admin_bypass(client, monkeypatch):
    monkeypatch.setenv("CRAVINGS_ADMIN_EMAILS", "admin@example.com")
    resp = await client.post("/api/auth/register", json={
        "email": "admin@example.com",
        "password": "securepass1",
        "name": "Admin",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_admin"] is True
    assert data["is_premium"] is False  # not paid — just admin

    client.headers["Authorization"] = f"Bearer {data['api_token']}"
    me = (await client.get("/api/users/me")).json()
    assert me["is_admin"] is True
