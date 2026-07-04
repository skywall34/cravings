"""Admin routes: content ingestion batch + cross-user metrics aggregates.

Metrics endpoints are is_admin-gated, JSON only (no UI). Registered users
only; "active" = swiped (see db.metrics for caveats).
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, Query

import db.database as db
import db.metrics as metrics
import main
from routers import deps

logger = logging.getLogger(__name__)

router = APIRouter()


async def _tag_items_background(item_ids: list[int]) -> None:
    conn = db.get_connection(main._db_path)
    try:
        for item_id in item_ids:
            row = conn.execute(
                "SELECT name, description FROM food_items WHERE id = ?", [item_id]
            ).fetchone()
            if row is None:
                continue
            try:
                tags = await asyncio.to_thread(main.tag_food_item, row["name"], row["description"])
                db.update_food_item_tags(conn, item_id, tags)
            except Exception as e:
                logger.warning("tagging failed for item %d: %s", item_id, e)
                db.mark_food_item_tagging_failed(conn, item_id)
    finally:
        conn.close()


@router.post("/api/admin/batch", status_code=202, dependencies=[Depends(deps.require_admin)])
async def admin_batch(body: dict):
    """Insert restaurants + food items and queue async LLM tagging.

    Body: {"restaurants": [{name, location, cuisine_type, source_type}, ...],
           "food_items":   [{name, description, restaurant_id?}, ...]}
    """
    restaurants = body.get("restaurants") or []
    food_items = body.get("food_items") or []

    conn = db.get_connection(main._db_path)
    try:
        restaurant_ids: dict[str, int] = {}
        for r in restaurants:
            rid = db.insert_restaurant(conn, r)
            if r.get("name"):
                restaurant_ids[r["name"]] = rid

        item_ids: list[int] = []
        for item in food_items:
            if "restaurant_name" in item and item["restaurant_name"] in restaurant_ids:
                item = {**item, "restaurant_id": restaurant_ids[item["restaurant_name"]]}
            fid = db.insert_food_item(conn, item)
            item_ids.append(fid)
    finally:
        conn.close()

    asyncio.create_task(_tag_items_background(item_ids))

    return {
        "restaurants_inserted": len(restaurants),
        "food_items_inserted": len(item_ids),
        "tagging": "queued",
    }


@router.get("/api/admin/metrics/foods", dependencies=[Depends(deps.require_admin_user)])
async def admin_metrics_foods(
    min_swipes: int = Query(5, ge=1),
    limit: int = Query(20, ge=1, le=200),
    cuisine: str | None = Query(None),
    conn=Depends(deps.get_conn),
):
    return metrics.food_performance(conn, min_swipes=min_swipes, limit=limit, cuisine=cuisine)


@router.get("/api/admin/metrics/catalog", dependencies=[Depends(deps.require_admin_user)])
async def admin_metrics_catalog(conn=Depends(deps.get_conn)):
    return metrics.catalog_trends(conn)


@router.get("/api/admin/metrics/retention", dependencies=[Depends(deps.require_admin_user)])
async def admin_metrics_retention(
    days: int = Query(30, ge=1, le=365),
    conn=Depends(deps.get_conn),
):
    return metrics.retention(conn, days=days)


@router.get("/api/admin/metrics/engagement", dependencies=[Depends(deps.require_admin_user)])
async def admin_metrics_engagement(
    days: int = Query(30, ge=1, le=365),
    conn=Depends(deps.get_conn),
):
    return metrics.engagement(conn, days=days)
