"""Tests for baseline HTTP security headers on every response."""

import os
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ.setdefault("CRAVINGS_DB", _tmp.name)

import main  # noqa: E402


@pytest_asyncio.fixture
async def client():
    async with main.lifespan(main.app):
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
            yield c


def _assert_security_headers(h):
    csp = h["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    # Google Fonts allowlisted; inline styles permitted (React inline style props).
    assert "https://fonts.googleapis.com" in csp
    assert "'unsafe-inline'" in csp
    assert h["strict-transport-security"] == "max-age=31536000; includeSubDomains"
    assert h["x-frame-options"] == "DENY"
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"] == "strict-origin-when-cross-origin"
    # geolocation must stay enabled — the app uses navigator.geolocation.
    assert "geolocation=(self)" in h["permissions-policy"]


@pytest.mark.asyncio
async def test_security_headers_on_api(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    _assert_security_headers(resp.headers)


@pytest.mark.asyncio
async def test_security_headers_on_unmatched_path(client):
    # Middleware wraps all responses, including 404s.
    resp = await client.get("/no/such/route/xyz")
    _assert_security_headers(resp.headers)
