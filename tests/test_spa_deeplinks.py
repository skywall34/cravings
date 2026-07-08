"""Tests for the /privacy, /terms, /account-deletion SPA deep-link routes."""

import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ.setdefault("CRAVINGS_DB", _tmp.name)

import main  # noqa: E402

_SENTINEL = "<html>sentinel-index</html>"


@pytest.fixture
def built_dist(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text(_SENTINEL)
    monkeypatch.setattr(main, "_dist", tmp_path)
    return tmp_path


@pytest_asyncio.fixture
async def client():
    async with main.lifespan(main.app):
        async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture
async def prefixed_client():
    async with main.lifespan(main.app):
        transport = ASGITransport(app=main.app, root_path="/cravings")
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.mark.parametrize("path", ["/privacy", "/terms", "/account-deletion"])
@pytest.mark.asyncio
async def test_deeplink_route_serves_index(client, built_dist, path):
    resp = await client.get(path)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert resp.text == _SENTINEL


@pytest.mark.asyncio
async def test_deeplink_route_under_root_path_prefix(prefixed_client, built_dist):
    resp = await prefixed_client.get("/cravings/privacy")
    assert resp.status_code == 200
    assert resp.text == _SENTINEL


@pytest.mark.asyncio
async def test_deeplink_route_404_when_not_built(client, monkeypatch):
    monkeypatch.setattr(main, "_dist", Path("/no/such/dist/dir"))
    resp = await client.get("/privacy")
    assert resp.status_code == 404
