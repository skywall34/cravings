"""Emit the image-curation worklist as JSON for the Claude curator agent.

Reads the failed ids from images/judge_failures.csv, joins live DB state, and
prints one JSON array of items needing a correct image. Run AFTER the gemma
re-fetch pre-pass so items it already fixed (status flipped back to 'auto') are
surfaced for verification with their current on-disk file.

Usage:
    uv run python scripts/curator_worklist.py [--db PATH]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import db_connection
from scripts.fetch_food_images import _slugify, IMAGES_ROOT

DB_PATH = Path(os.environ.get("CRAVINGS_DB", "cravings.db"))
FAILURES_CSV = IMAGES_ROOT / "judge_failures.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--csv", type=Path, default=FAILURES_CSV)
    args = parser.parse_args()

    ids = [int(r["id"]) for r in csv.DictReader(open(args.csv)) if r.get("verdict") == "fail"]

    out = []
    with db_connection(args.db) as conn:
        ph = ",".join("?" * len(ids))
        rows = conn.execute(
            f"SELECT id, name, cuisine_type, image_slug, image_hash, image_review_status "
            f"FROM food_items WHERE id IN ({ph})",
            ids,
        ).fetchall()
        for r in rows:
            d = dict(r)
            slug = _slugify(d["name"])
            cur = None
            if d["image_slug"] and d["image_hash"]:
                cur = f"images/food/{d['image_slug']}-{d['image_hash']}-800.webp"
            out.append({
                "item_id": d["id"],
                "name": d["name"],
                "cuisine_type": d["cuisine_type"],
                "slug": slug,
                "current_status": d["image_review_status"],
                "current_image_path": cur,
            })

    out.sort(key=lambda x: x["item_id"])
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
