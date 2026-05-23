"""End-to-end tests for the image fetch pipeline."""

import csv
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from tests.mocks.wikimedia_responses import (
    COMMONS_EXTMETA_CC_BY_SA,
    COMMONS_EXTMETA_REJECTED,
    COMMONS_IMAGE_URL,
    COMMONS_SEARCH_MISS,
    SPARQL_TIER1_HIT,
    SPARQL_TIER1_MISS,
    WIKIPEDIA_PAGEIMAGE_HIT,
    WIKIPEDIA_PAGEIMAGE_MISS,
)
import db.database as db


MINIMAL_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1eB"
    b"\xed\xb2\xff\xd9"
)


def _make_image_bytes() -> bytes:
    """Return a valid tiny RGB JPEG/PNG-like bytes via Pillow."""
    from io import BytesIO
    from PIL import Image
    buf = BytesIO()
    img = Image.new("RGB", (100, 75), color=(200, 100, 50))
    img.save(buf, "JPEG")
    return buf.getvalue()


def _mock_client_seq(*responses):
    client = MagicMock(spec=httpx.Client)
    mock_resps = []
    for r in responses:
        m = MagicMock()
        if isinstance(r, bytes):
            m.content = r
            m.status_code = 200
            m.raise_for_status = MagicMock()
        elif r is None:
            m.status_code = 404
            m.json.return_value = {}
            m.raise_for_status = MagicMock()
        else:
            m.status_code = 200
            m.json.return_value = r
            m.raise_for_status = MagicMock()
        mock_resps.append(m)
    client.get.side_effect = mock_resps
    return client


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = db.init_db(db_path)
    # Insert a tagged item
    cursor = conn.execute(
        "INSERT INTO food_items (name, cuisine_type, tagging_status, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "veggie_density, dairy_content, smell_intensity, nausea_trigger, "
        "safety_risk_bitmask, dietary_flags_bitmask) "
        "VALUES ('Carbonara', 'italian', 'tagged', "
        "0.1, 0.2, 0.1, 0.8, 0.5, 0.1, "
        "0.7, 0.6, 0.7, 0.9, 0.1, 0.5, 0.4, 0.0, 0, 0)"
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return db_path, item_id


class TestPipelineEndToEnd:
    def test_tier1_hit_writes_files_and_updates_db(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        images_root = tmp_path / "images"
        img_bytes = _make_image_bytes()

        import scripts.fetch_food_images as pipeline
        orig_db = pipeline.DB_PATH
        orig_images = pipeline.IMAGES_ROOT

        try:
            pipeline.DB_PATH = db_path
            pipeline.IMAGES_ROOT = images_root
            pipeline.MISSING_CSV = images_root / "missing.csv"

            client = _mock_client_seq(
                SPARQL_TIER1_HIT,          # tier-1 SPARQL
                COMMONS_EXTMETA_CC_BY_SA,  # fetch_metadata
                COMMONS_IMAGE_URL,         # download_and_hash: get image URL
                img_bytes,                 # download_and_hash: fetch actual image
            )

            with patch("tagging.wikimedia.time.sleep"), patch("scripts.fetch_food_images.time.sleep"):
                item = {"id": item_id, "name": "Carbonara", "cuisine_type": "italian"}
                ok = pipeline.process_one(item, client, images_root / "food", dry_run=False, force=False)

            assert ok is True
            food_dir = images_root / "food"
            webp_files = list(food_dir.glob("carbonara-*-400.webp"))
            assert len(webp_files) == 1
            webp_800 = list(food_dir.glob("carbonara-*-800.webp"))
            assert len(webp_800) == 1

            with db.db_connection(db_path) as conn:
                row = conn.execute(
                    "SELECT image_slug, image_hash, image_review_status FROM food_items WHERE id = ?",
                    [item_id]
                ).fetchone()
            assert row["image_slug"] == "carbonara"
            assert row["image_hash"] is not None
            assert row["image_review_status"] == "auto"

        finally:
            pipeline.DB_PATH = orig_db
            pipeline.IMAGES_ROOT = orig_images
            pipeline.MISSING_CSV = orig_images / "missing.csv"

    def test_dry_run_does_not_write_files(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        images_root = tmp_path / "images"

        import scripts.fetch_food_images as pipeline
        orig_db, orig_images = pipeline.DB_PATH, pipeline.IMAGES_ROOT
        try:
            pipeline.DB_PATH = db_path
            pipeline.IMAGES_ROOT = images_root
            pipeline.MISSING_CSV = images_root / "missing.csv"

            client = _mock_client_seq(
                SPARQL_TIER1_HIT,
                COMMONS_EXTMETA_CC_BY_SA,
            )

            with patch("tagging.wikimedia.time.sleep"), patch("scripts.fetch_food_images.time.sleep"):
                item = {"id": item_id, "name": "Carbonara", "cuisine_type": "italian"}
                pipeline.process_one(item, client, images_root / "food", dry_run=True, force=False)

            assert not (images_root / "food").exists() or not any((images_root / "food").iterdir())
        finally:
            pipeline.DB_PATH = orig_db
            pipeline.IMAGES_ROOT = orig_images
            pipeline.MISSING_CSV = orig_images / "missing.csv"

    def test_tier3_hit_sets_needs_review_and_appends_csv(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        images_root = tmp_path / "images"
        img_bytes = _make_image_bytes()

        import scripts.fetch_food_images as pipeline
        orig_db, orig_images = pipeline.DB_PATH, pipeline.IMAGES_ROOT
        try:
            pipeline.DB_PATH = db_path
            pipeline.IMAGES_ROOT = images_root
            pipeline.MISSING_CSV = images_root / "missing.csv"

            client = _mock_client_seq(
                SPARQL_TIER1_MISS,
                WIKIPEDIA_PAGEIMAGE_MISS, WIKIPEDIA_PAGEIMAGE_MISS,  # tier-2 misses (2 attempts)
                COMMONS_SEARCH_MISS,                                  # tier-2.5 miss
                WIKIPEDIA_PAGEIMAGE_HIT,   # tier-3 hit
                COMMONS_EXTMETA_CC_BY_SA,  # metadata
                COMMONS_IMAGE_URL,         # image URL lookup
                img_bytes,                 # actual image
            )

            with patch("tagging.wikimedia.time.sleep"), patch("scripts.fetch_food_images.time.sleep"):
                item = {"id": item_id, "name": "Carbonara", "cuisine_type": "italian"}
                ok = pipeline.process_one(item, client, images_root / "food", dry_run=False, force=False)

            assert ok is True

            with db.db_connection(db_path) as conn:
                row = conn.execute(
                    "SELECT image_review_status FROM food_items WHERE id = ?", [item_id]
                ).fetchone()
            assert row["image_review_status"] == "needs_review"

            assert pipeline.MISSING_CSV.exists()
            with open(pipeline.MISSING_CSV) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert any(r["name"] == "Carbonara" for r in rows)

        finally:
            pipeline.DB_PATH = orig_db
            pipeline.IMAGES_ROOT = orig_images
            pipeline.MISSING_CSV = orig_images / "missing.csv"

    def test_rejected_license_appends_csv(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        images_root = tmp_path / "images"

        import scripts.fetch_food_images as pipeline
        orig_db, orig_images = pipeline.DB_PATH, pipeline.IMAGES_ROOT
        try:
            pipeline.DB_PATH = db_path
            pipeline.IMAGES_ROOT = images_root
            pipeline.MISSING_CSV = images_root / "missing.csv"

            client = _mock_client_seq(SPARQL_TIER1_HIT, COMMONS_EXTMETA_REJECTED)

            with patch("tagging.wikimedia.time.sleep"), patch("scripts.fetch_food_images.time.sleep"):
                item = {"id": item_id, "name": "Carbonara", "cuisine_type": "italian"}
                ok = pipeline.process_one(item, client, images_root / "food", dry_run=False, force=False)

            assert ok is False
            assert pipeline.MISSING_CSV.exists()
        finally:
            pipeline.DB_PATH = orig_db
            pipeline.IMAGES_ROOT = orig_images
            pipeline.MISSING_CSV = orig_images / "missing.csv"


class TestManualCuration:
    def test_valid_sidecar_writes_approved_image(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        images_root = tmp_path / "images"
        manual_dir = images_root / "manual"
        manual_dir.mkdir(parents=True)

        img_bytes = _make_image_bytes()
        (manual_dir / "carbonara.jpg").write_bytes(img_bytes)
        (manual_dir / "carbonara.attribution.json").write_text(json.dumps({
            "item_id": item_id,
            "author": "Manual Author",
            "license": "CC-BY-SA-4.0",
            "source_url": "https://commons.wikimedia.org/wiki/File:Carbonara_manual.jpg",
        }))

        import scripts.fetch_food_images as pipeline
        orig_db, orig_images = pipeline.DB_PATH, pipeline.IMAGES_ROOT
        try:
            pipeline.DB_PATH = db_path
            pipeline.IMAGES_ROOT = images_root
            pipeline.MISSING_CSV = images_root / "missing.csv"

            import argparse
            args = argparse.Namespace(manual=True)
            pipeline.cmd_manual(args)

            food_dir = images_root / "food"
            assert list(food_dir.glob("carbonara-*-400.webp"))

            with db.db_connection(db_path) as conn:
                row = conn.execute(
                    "SELECT image_review_status, image_author FROM food_items WHERE id = ?",
                    [item_id]
                ).fetchone()
            assert row["image_review_status"] == "approved"
            assert row["image_author"] == "Manual Author"

            # Source file moved to _processed
            assert (manual_dir / "_processed" / "carbonara.jpg").exists()
        finally:
            pipeline.DB_PATH = orig_db
            pipeline.IMAGES_ROOT = orig_images
            pipeline.MISSING_CSV = orig_images / "missing.csv"

    def test_missing_sidecar_refused(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        images_root = tmp_path / "images"
        manual_dir = images_root / "manual"
        manual_dir.mkdir(parents=True)

        (manual_dir / "carbonara.jpg").write_bytes(_make_image_bytes())
        # No sidecar

        import scripts.fetch_food_images as pipeline
        orig_db, orig_images = pipeline.DB_PATH, pipeline.IMAGES_ROOT
        try:
            pipeline.DB_PATH = db_path
            pipeline.IMAGES_ROOT = images_root
            pipeline.MISSING_CSV = images_root / "missing.csv"

            import argparse
            args = argparse.Namespace(manual=True)
            pipeline.cmd_manual(args)

            food_dir = images_root / "food"
            assert not food_dir.exists() or not list(food_dir.glob("*.webp"))

            with db.db_connection(db_path) as conn:
                row = conn.execute(
                    "SELECT image_slug FROM food_items WHERE id = ?", [item_id]
                ).fetchone()
            assert row["image_slug"] is None
        finally:
            pipeline.DB_PATH = orig_db
            pipeline.IMAGES_ROOT = orig_images
            pipeline.MISSING_CSV = orig_images / "missing.csv"

    def test_bad_license_refused(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        images_root = tmp_path / "images"
        manual_dir = images_root / "manual"
        manual_dir.mkdir(parents=True)

        (manual_dir / "foo.jpg").write_bytes(_make_image_bytes())
        (manual_dir / "foo.attribution.json").write_text(json.dumps({
            "item_id": item_id,
            "author": "Bad Corp",
            "license": "All rights reserved",
            "source_url": "https://example.com/foo.jpg",
        }))

        import scripts.fetch_food_images as pipeline
        orig_db, orig_images = pipeline.DB_PATH, pipeline.IMAGES_ROOT
        try:
            pipeline.DB_PATH = db_path
            pipeline.IMAGES_ROOT = images_root
            pipeline.MISSING_CSV = images_root / "missing.csv"

            import argparse
            args = argparse.Namespace(manual=True)
            pipeline.cmd_manual(args)

            food_dir = images_root / "food"
            assert not food_dir.exists() or not list(food_dir.glob("*.webp"))
        finally:
            pipeline.DB_PATH = orig_db
            pipeline.IMAGES_ROOT = orig_images
            pipeline.MISSING_CSV = orig_images / "missing.csv"
