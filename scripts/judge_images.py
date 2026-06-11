"""Audit existing food images with the VLM judge.

Usage:
    uv run python scripts/judge_images.py [--limit N] [--dry-run] [--rejudge] [--db PATH]
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import (
    db_connection,
    get_items_for_judging,
    update_food_item_judgement,
)
from tagging.judge import JudgeError, check_ollama_available, judge_image_file

IMAGES_ROOT = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
DB_PATH = Path(os.environ.get("CRAVINGS_DB", "cravings.db"))
FAILURES_CSV = IMAGES_ROOT / "judge_failures.csv"


def _append_failure(item_id: int, name: str, verdict: str, reason: str) -> None:
    FAILURES_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not FAILURES_CSV.exists()
    with open(FAILURES_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["id", "name", "verdict", "reason"])
        writer.writerow([item_id, name, verdict, reason])


def judge_all(args: argparse.Namespace) -> None:
    if not check_ollama_available():
        print("ERROR: Ollama not reachable at localhost:11434. Aborting.")
        sys.exit(1)

    with db_connection(DB_PATH) as conn:
        if args.rejudge:
            items = conn.execute(
                "SELECT id, name, image_slug, image_hash, image_review_status "
                "FROM food_items WHERE image_slug IS NOT NULL"
            ).fetchall()
            items = [dict(r) for r in items]
        else:
            items = get_items_for_judging(conn)

    if args.limit:
        items = items[: args.limit]

    print(f"Judging {len(items)} items (dry_run={args.dry_run}, rejudge={args.rejudge})")

    n_pass = n_fail = n_error = n_missing = 0

    for item in items:
        item_id = item["id"]
        name = item["name"]
        slug = item["image_slug"]
        hash_ = item["image_hash"]
        current_status = item["image_review_status"]

        image_path = IMAGES_ROOT / "food" / f"{slug}-{hash_}-800.webp"
        print(f"  [{item_id}] {name} ...", end=" ", flush=True)

        if not image_path.exists():
            reason = "local file missing"
            print(f"MISSING ({image_path.name})")
            if not args.dry_run:
                with db_connection(DB_PATH) as conn:
                    update_food_item_judgement(conn, item_id, "fail", reason, "rejected")
            _append_failure(item_id, name, "fail", reason)
            n_missing += 1
            continue

        try:
            verdict = judge_image_file(image_path, name)
        except JudgeError as e:
            # JudgeError must NEVER write rejected — leave verdict NULL for retry
            print(f"JUDGE_ERROR: {e}")
            n_error += 1
            time.sleep(1)
            continue

        if verdict.verdict == "pass":
            new_status = "auto" if current_status == "needs_review" else current_status
            print(f"PASS [{new_status}] — {verdict.reason}")
            if not args.dry_run:
                with db_connection(DB_PATH) as conn:
                    update_food_item_judgement(conn, item_id, "pass", verdict.reason, new_status)
            n_pass += 1
        else:
            print(f"FAIL — {verdict.reason}")
            if not args.dry_run:
                with db_connection(DB_PATH) as conn:
                    update_food_item_judgement(conn, item_id, "fail", verdict.reason, "rejected")
            _append_failure(item_id, name, "fail", verdict.reason)
            n_fail += 1

        time.sleep(0.5)

    print(
        f"\nDone: {n_pass} pass, {n_fail} fail, {n_missing} missing, "
        f"{n_error} judge_error (verdict left NULL)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit food images with VLM judge")
    parser.add_argument("--limit", type=int, default=0, help="Max items to judge")
    parser.add_argument("--dry-run", action="store_true", help="Print verdicts, write nothing")
    parser.add_argument("--rejudge", action="store_true", help="Re-judge already-judged items")
    parser.add_argument("--db", type=Path, default=None, help="Path to cravings.db")
    args = parser.parse_args()

    if args.db:
        global DB_PATH
        DB_PATH = args.db

    judge_all(args)


if __name__ == "__main__":
    main()
