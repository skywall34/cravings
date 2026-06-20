"""Mark items listed in images/judge_failures.csv as image-rejected in the DB.

The judge_failures.csv is a dry-run/rejudge artifact: judge_images.py appends a
failure row even under --dry-run, so the verdicts there were never written to the
DB. This backfills the DB state so those items (a) stop serving the wrong photo
(add_image_urls suppresses URLs for 'rejected'), and (b) become visible to
fetch_food_images.py --refetch-rejected.

Usage:
    uv run python scripts/mark_csv_rejected.py [--db PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import db_connection, update_food_item_judgement

IMAGES_ROOT = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
DB_PATH = Path(os.environ.get("CRAVINGS_DB", "cravings.db"))
FAILURES_CSV = IMAGES_ROOT / "judge_failures.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark judge_failures.csv items as rejected")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--csv", type=Path, default=FAILURES_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}")
        sys.exit(1)

    with open(args.csv, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("verdict") == "fail"]

    print(f"{len(rows)} failed items (dry_run={args.dry_run})")
    n = 0
    for r in rows:
        item_id = int(r["id"])
        reason = r.get("reason") or "judge_failures.csv backfill"
        print(f"  [{item_id}] {r['name']} -> rejected")
        if not args.dry_run:
            with db_connection(args.db) as conn:
                update_food_item_judgement(conn, item_id, "fail", reason, "rejected")
        n += 1

    print(f"\nDone: {n} marked rejected")


if __name__ == "__main__":
    main()
