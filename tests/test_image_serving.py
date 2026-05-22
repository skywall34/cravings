"""Tests for StaticFiles image serving and Cache-Control headers."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import main
import db.database as _db

_PROJECT_ROOT = Path(__file__).parent.parent
_IMAGES_ROOT = _PROJECT_ROOT / "images"
_TEST_FILE = _IMAGES_ROOT / "food" / "_test-serving-abc12345-400.webp"


@pytest.fixture(autouse=True)
def _write_test_image():
    """Write a small sentinel file into images/food/ for serving tests; clean up after."""
    _IMAGES_ROOT.joinpath("food").mkdir(parents=True, exist_ok=True)
    _TEST_FILE.write_bytes(b"RIFF\x00\x00\x00\x00WEBP")
    yield
    _TEST_FILE.unlink(missing_ok=True)


@pytest_asyncio.fixture
async def client(tmp_path, monkeypatch):
    db_path = tmp_path / "img_serving_test.db"
    monkeypatch.setenv("CRAVINGS_DB", str(db_path))
    _db.init_db(db_path)
    main._db_path = db_path

    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as c:
        yield c


class TestImageServing:
    async def test_image_returns_200(self, client, _write_test_image):
        resp = await client.get("/images/food/_test-serving-abc12345-400.webp")
        assert resp.status_code == 200

    async def test_image_has_cache_control(self, client, _write_test_image):
        resp = await client.get("/images/food/_test-serving-abc12345-400.webp")
        cc = resp.headers.get("cache-control", "")
        assert "public" in cc
        assert "max-age=31536000" in cc
        assert "immutable" in cc

    async def test_missing_image_returns_404(self, client):
        resp = await client.get("/images/food/nonexistent-000-400.webp")
        assert resp.status_code == 404
