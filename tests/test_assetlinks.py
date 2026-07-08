"""Tests for the Digital Asset Links (/.well-known/assetlinks.json) middleware."""

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
        transport = ASGITransport(app=main.app, root_path="/cravings")
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.mark.asyncio
async def test_assetlinks_returns_fingerprints_when_configured(client, monkeypatch):
    monkeypatch.setenv("CRAVINGS_ASSETLINKS_FINGERPRINTS", "AA:BB,CC:DD")
    resp = await client.get("/.well-known/assetlinks.json")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    body = resp.json()
    assert body[0]["relation"] == ["delegate_permission/common.handle_all_urls"]
    assert body[0]["target"]["package_name"] == "com.themshin.cravings"
    assert body[0]["target"]["sha256_cert_fingerprints"] == ["AA:BB", "CC:DD"]


@pytest.mark.asyncio
async def test_assetlinks_404_when_unset(client, monkeypatch):
    monkeypatch.delenv("CRAVINGS_ASSETLINKS_FINGERPRINTS", raising=False)
    resp = await client.get("/.well-known/assetlinks.json")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assetlinks_middleware_does_not_shadow_app(client):
    resp = await client.get("/cravings/api/health")
    assert resp.status_code == 200
