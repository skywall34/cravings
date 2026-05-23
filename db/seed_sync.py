"""Idempotent upsert of content tables (restaurants, food_items) from a seed DB.

The seed DB ships baked into the Docker image at /app/seed/cravings.db.
The live DB is volume-mounted at /app/cravings.db (CRAVINGS_DB env var).
On every container start, this module copies content rows seed -> live by id,
leaving user data (users, swipe_events, user_item_impressions) untouched.

Replaces the legacy `rsync cravings.db` deploy step that was overwriting VPS
user rows and invalidating api_tokens.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

CONTENT_TABLES = ("restaurants", "food_items")

DEFAULT_SEED_PATH = Path(os.environ.get("CRAVINGS_SEED_DB", "/app/seed/cravings.db"))


def _upsert_table(live: sqlite3.Connection, seed: sqlite3.Connection, table: str) -> int:
    seed_cols = [r["name"] for r in seed.execute(f"PRAGMA table_info({table})")]
    live_cols = {r["name"] for r in live.execute(f"PRAGMA table_info({table})")}
    cols = [c for c in seed_cols if c in live_cols]
    if "id" not in cols:
        raise RuntimeError(f"seed table {table} missing id column")

    col_list = ",".join(cols)
    placeholders = ",".join("?" * len(cols))
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c != "id")
    sql = (
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}"
    )

    count = 0
    for row in seed.execute(f"SELECT {col_list} FROM {table}"):
        live.execute(sql, tuple(row))
        count += 1
    return count


def sync_content_from_seed(
    live: sqlite3.Connection,
    seed_path: Path = DEFAULT_SEED_PATH,
) -> dict[str, int | bool]:
    """Upsert content rows from seed DB into live DB. Idempotent.

    Returns counts per table, or {"skipped": True} if seed not present.
    """
    if not seed_path.exists():
        logger.info("seed DB not found at %s — skipping content sync", seed_path)
        return {"skipped": True}

    # Avoid syncing seed-into-itself if CRAVINGS_DB == seed path.
    live_db_path = None
    for row in live.execute("PRAGMA database_list"):
        if row["name"] == "main":
            live_db_path = row["file"]
            break
    if live_db_path and Path(live_db_path).resolve() == seed_path.resolve():
        logger.info("live DB and seed DB are the same file — skipping sync")
        return {"skipped": True}

    seed = sqlite3.connect(seed_path)
    seed.row_factory = sqlite3.Row
    try:
        results: dict[str, int | bool] = {}
        for table in CONTENT_TABLES:
            results[table] = _upsert_table(live, seed, table)
        live.commit()
        logger.info("seed content sync: %s", results)
        return results
    finally:
        seed.close()
