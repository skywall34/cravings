"""Invariant: every tagged catalog item has an image and an embedding.

Guards against silent backlogs like the one this test was added for — 79 items
with no image_slug and 493 items (an entire un-embedded cohort) that went
unnoticed because nothing asserted the invariant.

Read-only: opens cravings.db with no writes. Skips cleanly if the DB is absent (CI).
"""

import sqlite3
from pathlib import Path

import pytest

REAL_DB = Path(__file__).resolve().parent.parent / "cravings.db"


def _real_db_available() -> bool:
    if not REAL_DB.exists():
        return False
    conn = sqlite3.connect(REAL_DB)
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM food_items WHERE tagging_status='tagged'"
        ).fetchone()[0]
        return n >= 100
    except sqlite3.Error:
        return False
    finally:
        conn.close()


pytestmark = pytest.mark.skipif(
    not _real_db_available(), reason="real cravings.db not present or too small"
)


def test_all_tagged_items_have_image_and_embedding():
    conn = sqlite3.connect(REAL_DB)
    try:
        rows = conn.execute(
            "SELECT id, name, image_slug, embedding FROM food_items "
            "WHERE tagging_status = 'tagged' "
            "AND (image_slug IS NULL OR image_slug = '' OR embedding IS NULL)"
        ).fetchall()
    finally:
        conn.close()

    assert rows == [], (
        f"{len(rows)} tagged items missing image_slug and/or embedding: "
        f"{[(r[0], r[1]) for r in rows[:10]]}"
    )
