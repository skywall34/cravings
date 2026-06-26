"""Tests for auth endpoints and profile stats."""

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
os.environ.setdefault("CRAVINGS_DB", TEST_DB)

import main  # noqa: E402
import db.database as _db  # noqa: E402

# Codes the app "emails" during a test, keyed by lowercased address. Populated by
# the capture_codes fixture which stands in for the real email sender.
_sent_codes: dict[str, str] = {}


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    # lifespan reads CRAVINGS_DB from env, which may differ from this file's TEST_DB
    active_db = Path(os.environ.get("CRAVINGS_DB", TEST_DB))
    main._db_path = active_db
    active_db.unlink(missing_ok=True)
    _db.init_db(active_db)
    main._sessions.clear_all()
    yield


@pytest.fixture(autouse=True)
def capture_codes(monkeypatch):
    """Intercept verification emails so tests can read the generated code."""
    _sent_codes.clear()

    async def _fake_send(_sender, email, code):
        _sent_codes[email.lower()] = code

    monkeypatch.setattr(main, "send_verification_email", _fake_send)
    yield


async def _verify(client, email):
    """Submit the captured code for `email` and return the response."""
    return await client.post(
        "/api/auth/verify-email", json={"email": email, "code": _sent_codes[email.lower()]}
    )


@pytest_asyncio.fixture
async def client(reset_db):
    async with main.lifespan(main.app):
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture
async def registered_client(client):
    """Client with a registered user; yields (client, token, user_id)."""
    resp = await client.post("/api/auth/register", json={
        "email": "auth_test_user@example.com",
        "password": "securepass9",
        "name": "Tester",
    })
    assert resp.status_code == 201
    data = resp.json()
    # Finish verification so the fixture yields a fully active registered user.
    vresp = await _verify(client, "auth_test_user@example.com")
    assert vresp.status_code == 200
    token = vresp.json()["api_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client, token, data["id"]


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

async def test_register_cold(client):
    """Register creates a new user row with onboarding_complete=False."""
    resp = await client.post("/api/auth/register", json={
        "email": "alice@example.com",
        "password": "securepass1",
        "name": "Alice",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["is_registered"] is True
    assert data["onboarding_complete"] is False
    assert data["email_verified"] is False
    assert "api_token" in data


async def test_register_always_fresh_row(client):
    """Register always creates a clean row (no guest migration)."""
    resp = await client.post("/api/auth/register", json={
        "email": "bob@example.com",
        "password": "securepass2",
        "name": "Bob",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_registered"] is True
    assert data["onboarding_complete"] is False


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
    assert resp.status_code == 422


async def test_register_invalid_email(client):
    """Invalid email rejected."""
    resp = await client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "securepass4",
        "name": "Eve",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_success(client):
    """Login with correct credentials returns token once the email is verified."""
    await client.post("/api/auth/register", json={
        "email": "frank@example.com",
        "password": "correcthorse",
        "name": "Frank",
    })
    assert (await _verify(client, "frank@example.com")).status_code == 200
    resp = await client.post("/api/auth/login", json={
        "email": "frank@example.com",
        "password": "correcthorse",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "api_token" in data
    assert data["email"] == "frank@example.com"
    assert data["email_verified"] is True


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
# Email verification
# ---------------------------------------------------------------------------

async def test_login_blocked_until_verified(client):
    """A correct password on an unverified account is rejected with 403."""
    await client.post("/api/auth/register", json={
        "email": "unv@example.com", "password": "correcthorse", "name": "Unv",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "unv@example.com", "password": "correcthorse",
    })
    assert resp.status_code == 403
    assert "verify" in resp.json()["detail"].lower()


async def test_verify_email_then_login(client):
    """Verifying with the emailed code flips the flag and unblocks login."""
    await client.post("/api/auth/register", json={
        "email": "verme@example.com", "password": "correcthorse", "name": "Ver",
    })
    vresp = await _verify(client, "verme@example.com")
    assert vresp.status_code == 200
    assert vresp.json()["email_verified"] is True
    assert "api_token" in vresp.json()

    login = await client.post("/api/auth/login", json={
        "email": "verme@example.com", "password": "correcthorse",
    })
    assert login.status_code == 200


async def test_verify_wrong_code(client):
    """A wrong code returns 400 and does not verify the account."""
    await client.post("/api/auth/register", json={
        "email": "wrong@example.com", "password": "correcthorse", "name": "W",
    })
    resp = await client.post("/api/auth/verify-email", json={
        "email": "wrong@example.com", "code": "000000",
    })
    assert resp.status_code == 400
    # still blocked
    login = await client.post("/api/auth/login", json={
        "email": "wrong@example.com", "password": "correcthorse",
    })
    assert login.status_code == 403


async def test_verify_max_attempts_invalidates_code(client):
    """After 5 wrong attempts the code is invalidated; the real code stops working."""
    main._auth_limiter.reset()
    await client.post("/api/auth/register", json={
        "email": "brute@example.com", "password": "correcthorse", "name": "B",
    })
    real_code = _sent_codes["brute@example.com"]
    for _ in range(5):
        r = await client.post("/api/auth/verify-email", json={
            "email": "brute@example.com", "code": "111111",
        })
        assert r.status_code == 400
    # Reset the throttle so the final check exercises code-invalidation, not the
    # rate limiter (5 wrong attempts already spent the burst).
    main._auth_limiter.reset()
    # even the correct code now fails — it was wiped after too many attempts
    after = await client.post("/api/auth/verify-email", json={
        "email": "brute@example.com", "code": real_code,
    })
    assert after.status_code == 400


async def test_verify_expired_code(client):
    """An expired code is rejected and cleared."""
    await client.post("/api/auth/register", json={
        "email": "stale@example.com", "password": "correcthorse", "name": "S",
    })
    # Force the stored code to be in the past.
    conn = sqlite3.connect(str(main._db_path))
    conn.execute(
        "UPDATE email_verifications SET expires_at = '2000-01-01T00:00:00+00:00' WHERE email = ?",
        ["stale@example.com"],
    )
    conn.commit()
    conn.close()
    resp = await _verify(client, "stale@example.com")
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


async def test_resend_respects_cooldown(client):
    """A resend within the 30s cooldown is throttled with 429."""
    main._auth_limiter.reset()
    await client.post("/api/auth/register", json={
        "email": "resend@example.com", "password": "correcthorse", "name": "R",
    })
    resp = await client.post("/api/auth/resend-verification", json={
        "email": "resend@example.com",
    })
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


async def test_resend_unknown_email_is_ok(client):
    """Resend for an unknown address returns ok without disclosing existence."""
    main._auth_limiter.reset()
    resp = await client.post("/api/auth/resend-verification", json={
        "email": "ghost@example.com",
    })
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


async def test_migration_backfills_existing_registered_users(client):
    """Pre-migration registered users are grandfathered as verified."""
    conn = sqlite3.connect(str(main._db_path))
    conn.row_factory = sqlite3.Row
    # Simulate a legacy DB: drop the column and add a registered user without it.
    conn.execute("ALTER TABLE users DROP COLUMN email_verified")
    conn.execute(
        "INSERT INTO users (name, api_token, email, password_hash) "
        "VALUES ('Legacy', 'legacy-token', 'legacy@example.com', 'x')"
    )
    conn.commit()
    _db._migrate(conn)
    row = conn.execute(
        "SELECT email_verified FROM users WHERE email = 'legacy@example.com'"
    ).fetchone()
    conn.close()
    assert row["email_verified"] == 1


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
    fp = data["flavor_profile"]
    assert set(fp.keys()) == {"Spicy", "Rich", "Umami", "Fresh", "Sweet"}
    assert all(v == 0 for v in fp.values())


def _insert_food_item_auth(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "INSERT INTO food_items (name, description, tagging_status, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "protein_type, cuisine_type, carb_base, veggie_density, dairy_content, "
        "smell_intensity, nausea_trigger, safety_risk_bitmask, dietary_flags_bitmask) "
        "VALUES ('Test Dish', 'A test item', 'tagged', "
        "0.8, 0.6, 0.3, 0.7, 0.5, 0.1, "
        "0.7, 0.4, 0.6, 0.9, "
        "'chicken', 'japanese', 'noodles_pasta', 0.4, 0.1, "
        "0.5, 0.0, 0, 0)",
    )
    item_id = cur.lastrowid
    conn.commit()
    conn.close()
    return item_id


async def test_stats_flavor_profile_with_swipes(client):
    """flavor_profile axes are 0–100 ints derived from right-swiped dishes."""
    r = await client.post("/api/auth/register", json={
        "email": "flavor@example.com",
        "password": "securepass7",
        "name": "Flavor",
    })
    token = r.json()["api_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    active_db = str(main._db_path)
    item_id = _insert_food_item_auth(active_db)

    snap_resp = await client.get("/api/recommend?session_id=s1")
    assert snap_resp.status_code == 200
    snap_token = snap_resp.json()[0]["snapshot_token"]

    await client.post("/api/swipe", json={
        "food_item_id": item_id,
        "direction": "right",
        "session_id": "s1",
        "snapshot_token": snap_token,
    })

    resp = await client.get("/api/profile/stats")
    assert resp.status_code == 200
    fp = resp.json()["flavor_profile"]
    assert set(fp.keys()) == {"Spicy", "Rich", "Umami", "Fresh", "Sweet"}
    assert all(isinstance(v, int) and 0 <= v <= 100 for v in fp.values())
    assert fp["Spicy"] == 80
    assert fp["Rich"] == 90


async def test_stats_requires_auth(client):
    """Stats endpoint requires bearer token."""
    resp = await client.get("/api/profile/stats")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# PATCH /api/users/me
# ---------------------------------------------------------------------------

async def test_patch_me_dietary(registered_client):
    """PATCH dietary_restrictions updates and returns new value."""
    client, _, _ = registered_client
    resp = await client.patch("/api/users/me", json={"dietary_restrictions": ["vegetarian", "gluten_free"]})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["dietary_restrictions"]) == {"vegetarian", "gluten_free"}
    assert data["safety_overrides"] == []

    # Persisted: GET reflects change
    me = await client.get("/api/users/me")
    assert set(me.json()["dietary_restrictions"]) == {"vegetarian", "gluten_free"}


async def test_patch_me_safety_overrides(registered_client):
    """PATCH safety_overrides updates independently."""
    client, _, _ = registered_client
    resp = await client.patch("/api/users/me", json={"safety_overrides": ["raw_fish"]})
    assert resp.status_code == 200
    assert resp.json()["safety_overrides"] == ["raw_fish"]


async def test_patch_me_partial_update(registered_client):
    """PATCH only the field sent; other field unchanged."""
    client, _, _ = registered_client
    await client.patch("/api/users/me", json={"dietary_restrictions": ["vegan"]})
    # Now patch only safety_overrides — dietary should stay
    resp = await client.patch("/api/users/me", json={"safety_overrides": ["raw_egg"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["dietary_restrictions"] == ["vegan"]
    assert data["safety_overrides"] == ["raw_egg"]


async def test_patch_me_clear_restrictions(registered_client):
    """PATCH with empty list clears restrictions."""
    client, _, _ = registered_client
    await client.patch("/api/users/me", json={"dietary_restrictions": ["vegan"]})
    resp = await client.patch("/api/users/me", json={"dietary_restrictions": []})
    assert resp.status_code == 200
    assert resp.json()["dietary_restrictions"] == []


async def test_patch_me_unknown_flag(registered_client):
    """Unknown dietary flag returns 422."""
    client, _, _ = registered_client
    resp = await client.patch("/api/users/me", json={"dietary_restrictions": ["not_a_flag"]})
    assert resp.status_code == 422


async def test_patch_me_requires_auth(client):
    """PATCH without token returns 401/403."""
    resp = await client.patch("/api/users/me", json={"dietary_restrictions": []})
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# DELETE /api/users/me — GDPR Art. 17 erasure
# ---------------------------------------------------------------------------

async def test_delete_account(registered_client):
    """Delete returns 204 and invalidates the token."""
    client, token, _ = registered_client
    resp = await client.delete("/api/users/me")
    assert resp.status_code == 204

    # Token is dead — user row gone
    me = await client.get("/api/users/me")
    assert me.status_code in (401, 403)


async def test_delete_allows_email_reuse(registered_client):
    """After deletion the same email can be re-registered."""
    client, _, _ = registered_client
    await client.delete("/api/users/me")
    client.headers.pop("Authorization", None)

    resp = await client.post("/api/auth/register", json={
        "email": "auth_test_user@example.com",
        "password": "newpassword1",
        "name": "Reborn",
    })
    assert resp.status_code == 201
    assert resp.json()["email"] == "auth_test_user@example.com"


async def test_delete_requires_auth(client):
    """DELETE without token returns 401/403."""
    resp = await client.delete("/api/users/me")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /api/users/me/export — GDPR Art. 20 portability
# ---------------------------------------------------------------------------

async def test_export_returns_account_fields(registered_client):
    """Export JSON contains account, preferences, swipe_history, stats."""
    client, _, _ = registered_client
    resp = await client.get("/api/users/me/export")
    assert resp.status_code == 200
    data = resp.json()
    assert "account" in data
    assert data["account"]["email"] == "auth_test_user@example.com"
    assert "preferences" in data
    assert "swipe_history" in data
    assert isinstance(data["swipe_history"], list)
    assert "stats" in data
    assert "exported_at" in data


async def test_export_empty_swipe_history(registered_client):
    """Fresh account exports with empty swipe_history."""
    client, _, _ = registered_client
    resp = await client.get("/api/users/me/export")
    assert resp.status_code == 200
    assert resp.json()["swipe_history"] == []


async def test_export_requires_auth(client):
    """Export without token returns 401/403."""
    resp = await client.get("/api/users/me/export")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Location data audit
# ---------------------------------------------------------------------------

async def test_no_location_columns_in_schema(client):
    """Schema must not store lat/lng — privacy policy commitment."""
    import sqlite3
    conn = sqlite3.connect(str(main._db_path))
    conn.row_factory = sqlite3.Row
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for table in tables:
        cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        assert "lat" not in cols, f"table {table!r} has lat column"
        assert "lng" not in cols, f"table {table!r} has lng column"
        assert "latitude" not in cols, f"table {table!r} has latitude column"
        assert "longitude" not in cols, f"table {table!r} has longitude column"
    conn.close()


# ---------------------------------------------------------------------------
# Auth rate limiting (brute-force protection)
# ---------------------------------------------------------------------------

async def test_login_rate_limited(client):
    """Repeated login attempts on one email get 429 once the burst is spent."""
    main._auth_limiter.reset()
    await client.post("/api/auth/register", json={
        "email": "rl@example.com", "password": "password123", "name": "RL",
    })
    body = {"email": "rl@example.com", "password": "wrongpassword"}
    # capacity default 5 → first 5 attempts reach the password check (401), 6th throttled.
    for _ in range(5):
        r = await client.post("/api/auth/login", json=body)
        assert r.status_code == 401
    blocked = await client.post("/api/auth/login", json=body)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert blocked.json()["detail"]["retry_after"] >= 1


async def test_register_rate_limited(client):
    """Bursting registrations from one IP gets 429 past the burst."""
    main._auth_limiter.reset()
    for i in range(5):
        r = await client.post("/api/auth/register", json={
            "email": f"burst{i}@example.com", "password": "password123", "name": "B",
        })
        assert r.status_code == 201
    blocked = await client.post("/api/auth/register", json={
        "email": "burst-over@example.com", "password": "password123", "name": "B",
    })
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


async def test_rate_limit_ignores_spoofed_xff(client):
    """Rotating the client-supplied (leftmost) XFF entry must not bypass the limit.

    Traefik appends the real peer IP on the right; we key on that. A spoofed
    leftmost value changes each request but the trusted rightmost stays fixed.
    """
    main._auth_limiter.reset()
    body = {"email": "spoof@example.com", "password": "wrongpassword"}
    statuses = []
    for i in range(6):
        r = await client.post(
            "/api/auth/login",
            json=body,
            headers={"X-Forwarded-For": f"10.0.0.{i}, 203.0.113.7"},
        )
        statuses.append(r.status_code)
    # Despite a fresh leftmost IP each call, the fixed rightmost IP shares one
    # bucket → still throttled after the burst.
    assert 429 in statuses
