"""Tests for VLM image judge module."""

import io
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from tagging.judge import (
    JudgeError,
    Verdict,
    check_ollama_available,
    judge_image_bytes,
    judge_image_file,
    parse_verdict,
    prepare_image,
)


# --- Helpers ---

def _make_jpeg(width=200, height=150) -> bytes:
    img = Image.new("RGB", (width, height), color=(180, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _ollama_response(verdict: str, reason: str) -> dict:
    return {"message": {"content": json.dumps({"verdict": verdict, "reason": reason})}}


# --- parse_verdict ---

class TestParseVerdict:
    def test_pass(self):
        v = parse_verdict(json.dumps({"verdict": "pass", "reason": "looks like carbonara"}))
        assert v.verdict == "pass"
        assert v.reason == "looks like carbonara"

    def test_fail(self):
        v = parse_verdict(json.dumps({"verdict": "fail", "reason": "painting not photograph"}))
        assert v.verdict == "fail"

    def test_garbage_json_raises(self):
        with pytest.raises(JudgeError):
            parse_verdict("not json at all {{")

    def test_unknown_verdict_raises(self):
        with pytest.raises(JudgeError, match="Unknown verdict"):
            parse_verdict(json.dumps({"verdict": "maybe", "reason": "unsure"}))

    def test_empty_verdict_raises(self):
        with pytest.raises(JudgeError):
            parse_verdict(json.dumps({"verdict": "", "reason": "nothing"}))

    def test_missing_verdict_raises(self):
        with pytest.raises(JudgeError):
            parse_verdict(json.dumps({"reason": "no verdict key"}))


# --- prepare_image ---

class TestPrepareImage:
    def test_small_image_unchanged_dimensions(self):
        small = _make_jpeg(100, 75)
        b64 = prepare_image(small, max_side=896)
        import base64
        decoded = base64.b64decode(b64)
        img = Image.open(io.BytesIO(decoded))
        assert max(img.size) <= 896

    def test_large_image_downscaled(self):
        large = _make_jpeg(2000, 1500)
        b64 = prepare_image(large, max_side=896)
        import base64
        decoded = base64.b64decode(b64)
        img = Image.open(io.BytesIO(decoded))
        assert max(img.size) <= 896

    def test_returns_string(self):
        b64 = prepare_image(_make_jpeg())
        assert isinstance(b64, str)


# --- judge_image_bytes ---

class TestJudgeImageBytes:
    def test_happy_path_pass(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _ollama_response("pass", "plausible pasta dish")
        mock_resp.raise_for_status = MagicMock()

        with patch("tagging.judge.requests.post", return_value=mock_resp):
            verdict = judge_image_bytes(_make_jpeg(), "Carbonara")

        assert verdict.verdict == "pass"
        assert verdict.reason == "plausible pasta dish"

    def test_happy_path_fail(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _ollama_response("fail", "painting not food photo")
        mock_resp.raise_for_status = MagicMock()

        with patch("tagging.judge.requests.post", return_value=mock_resp):
            verdict = judge_image_bytes(_make_jpeg(), "Kritharoto")

        assert verdict.verdict == "fail"

    def test_connection_error_raises_judge_error(self):
        import requests as req_lib
        with patch("tagging.judge.requests.post", side_effect=req_lib.ConnectionError("down")):
            with pytest.raises(JudgeError, match="Ollama request failed"):
                judge_image_bytes(_make_jpeg(), "Spaghetti")

    def test_unparsable_response_raises_judge_error(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": {"content": "not json"}}
        mock_resp.raise_for_status = MagicMock()

        with patch("tagging.judge.requests.post", return_value=mock_resp):
            with pytest.raises(JudgeError):
                judge_image_bytes(_make_jpeg(), "Ramen")


# --- judge_image_file ---

class TestJudgeImageFile:
    def test_reads_file_and_judges(self, tmp_path):
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(_make_jpeg())

        mock_resp = MagicMock()
        mock_resp.json.return_value = _ollama_response("pass", "food photo")
        mock_resp.raise_for_status = MagicMock()

        with patch("tagging.judge.requests.post", return_value=mock_resp):
            verdict = judge_image_file(img_path, "Bibimbap")

        assert verdict.verdict == "pass"


# --- check_ollama_available ---

class TestCheckOllamaAvailable:
    def test_available(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("tagging.judge.requests.get", return_value=mock_resp):
            assert check_ollama_available() is True

    def test_unavailable_connection_error(self):
        import requests as req_lib
        with patch("tagging.judge.requests.get", side_effect=req_lib.ConnectionError):
            assert check_ollama_available() is False

    def test_unavailable_bad_status(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("tagging.judge.requests.get", return_value=mock_resp):
            assert check_ollama_available() is False


# --- Audit script behaviour via DB ---

@pytest.fixture
def tmp_db(tmp_path):
    from db.database import init_db, insert_restaurant, insert_food_item, update_food_item_image
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    rest_id = insert_restaurant(conn, {"name": "R", "cuisine_type": "italian"})
    item_id = insert_food_item(conn, {
        "name": "Carbonara", "restaurant_id": rest_id, "tagging_status": "tagged",
    })
    update_food_item_image(conn, item_id, "carbonara", "abc123", "Author", "CC-BY-SA-4.0",
                           "https://example.com", "needs_review")
    conn.close()
    return db_path, item_id


class TestAuditScriptBehaviour:
    """Tests for judge_images.py logic exercised through DB helpers."""

    def _run_audit(self, db_path, tmp_path, pass_verdict: bool, judge_error: bool = False):
        """Simulate the audit loop logic inline."""
        from db.database import db_connection, get_items_for_judging, update_food_item_judgement

        # Create a fake 800px webp
        food_dir = tmp_path / "images" / "food"
        food_dir.mkdir(parents=True)
        img = Image.new("RGB", (800, 600), color=(100, 200, 100))
        buf = io.BytesIO()
        img.save(buf, format="WEBP")

        with db_connection(db_path) as conn:
            items = get_items_for_judging(conn)

        for item in items:
            slug = item["image_slug"]
            hash_ = item["image_hash"]
            img_path = food_dir / f"{slug}-{hash_}-800.webp"
            img_path.write_bytes(buf.getvalue())

            if judge_error:
                # JudgeError — leave verdict NULL
                continue

            current_status = item["image_review_status"]
            if pass_verdict:
                new_status = "auto" if current_status == "needs_review" else current_status
                with db_connection(db_path) as conn:
                    update_food_item_judgement(conn, item["id"], "pass", "plausible", new_status)
            else:
                with db_connection(db_path) as conn:
                    update_food_item_judgement(conn, item["id"], "fail", "wrong food", "rejected")

    def test_fail_sets_rejected(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        self._run_audit(db_path, tmp_path, pass_verdict=False)
        from db.database import db_connection
        with db_connection(db_path) as conn:
            row = conn.execute("SELECT image_review_status, image_judge_verdict FROM food_items WHERE id=?", [item_id]).fetchone()
        assert row["image_judge_verdict"] == "fail"
        assert row["image_review_status"] == "rejected"

    def test_pass_promotes_needs_review_to_auto(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        self._run_audit(db_path, tmp_path, pass_verdict=True)
        from db.database import db_connection
        with db_connection(db_path) as conn:
            row = conn.execute("SELECT image_review_status, image_judge_verdict FROM food_items WHERE id=?", [item_id]).fetchone()
        assert row["image_judge_verdict"] == "pass"
        assert row["image_review_status"] == "auto"

    def test_judge_error_leaves_verdict_null(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        self._run_audit(db_path, tmp_path, pass_verdict=False, judge_error=True)
        from db.database import db_connection
        with db_connection(db_path) as conn:
            row = conn.execute("SELECT image_judge_verdict FROM food_items WHERE id=?", [item_id]).fetchone()
        assert row["image_judge_verdict"] is None

    def test_resumability_second_run_selects_zero(self, tmp_db, tmp_path):
        db_path, item_id = tmp_db
        self._run_audit(db_path, tmp_path, pass_verdict=True)
        from db.database import db_connection, get_items_for_judging
        with db_connection(db_path) as conn:
            remaining = get_items_for_judging(conn)
        assert len(remaining) == 0
