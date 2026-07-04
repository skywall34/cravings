"""Recommendation loop: onboarding, recommend, swipe, catalog reads, nearby search."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials

import db.database as db
import main
import swipe
from places import PlacesError
from rate_limit import rate_limited
from recommender import make_recommender
from routers import deps
from schemas import OnboardingBody, SessionResetBody, SwipeBody

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/onboarding")
async def onboarding(body: OnboardingBody, user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    await asyncio.to_thread(main._model_service.set_onboarding, user["id"], body.preferences, body.reset)
    db.mark_onboarding_complete(conn, user["id"])
    return {"success": True}


@router.get("/api/recommend")
async def recommend(
    request: Request,
    top_n: int = Query(default=1, ge=1),
    session_id: str = Query(default=""),
    hour: float | None = Query(default=None),
    dietary_restrictions: list[str] = Query(default=[]),
    safety_overrides: list[str] = Query(default=[]),
    excluded_ids: list[int] = Query(default=[]),
    credentials: HTTPAuthorizationCredentials | None = Depends(deps.optional_bearer),
    conn=Depends(deps.get_conn),
):
    user = None
    if credentials:
        user = db.get_user_by_token(conn, credentials.credentials)

    taste_prefs = {
        k[5:]: float(v)
        for k, v in request.query_params.items()
        if k.startswith("pref_")
    }
    rec = make_recommender(
        conn=conn, user=user, sessions=main._sessions, model_service=main._model_service,
        base_path=main._base_path, session_max_swipes=main._session_max_swipes, session_id=session_id,
        dietary_restrictions=dietary_restrictions, safety_overrides=safety_overrides,
        taste_prefs=taste_prefs,
    )
    results = await rec.recommend(
        hour=hour, top_n=top_n, excluded_ids=excluded_ids,
    )
    if not results:
        raise HTTPException(status_code=404, detail="no eligible food items")
    return results


@router.post("/api/swipe")
async def swipe_endpoint(
    body: SwipeBody,
    credentials: HTTPAuthorizationCredentials | None = Depends(deps.optional_bearer),
    conn=Depends(deps.get_conn),
):
    item = db.get_food_item(conn, body.food_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="food item not found")

    user = None
    if credentials:
        user = db.get_user_by_token(conn, credentials.credentials)

    rec = make_recommender(
        conn=conn, user=user, sessions=main._sessions, model_service=main._model_service,
        base_path=main._base_path, session_max_swipes=main._session_max_swipes, session_id=body.session_id,
        taste_prefs=body.taste_prefs,
    )
    try:
        outcome = await rec.record(item=item, direction=body.direction, token=body.snapshot_token)
    except swipe.SnapshotError as e:
        raise HTTPException(status_code=400, detail=f"invalid snapshot: {e}") from e
    except swipe.SwipeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"success": True, **outcome}


@router.post("/api/session/reset")
async def session_reset(body: SessionResetBody):
    await main._sessions.reset(body.session_id)
    return {"success": True}


@router.get("/api/food-items")
async def list_food_items(conn=Depends(deps.get_conn), user=Depends(deps.get_user)):
    return db.list_food_items(conn)


@router.get("/api/food-items/{item_id}")
async def get_food_item(item_id: int, conn=Depends(deps.get_conn), user=Depends(deps.get_user)):
    item = db.get_food_item(conn, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    return swipe.add_image_urls(item, main._base_path)


@router.get("/api/restaurants")
async def list_restaurants(conn=Depends(deps.get_conn), user=Depends(deps.get_user)):
    return db.list_restaurants(conn)


@router.get("/api/model/status")
async def model_status(user=Depends(deps.get_user)):
    status_data = await asyncio.to_thread(main._model_service.get_status, user["id"])
    return status_data


@router.get("/api/nearby")
async def nearby(
    food_item_id: int = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(deps.optional_bearer),
    conn=Depends(deps.get_conn),
):
    item = db.get_food_item(conn, food_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="food item not found")

    user = db.get_user_by_token(conn, credentials.credentials) if credentials else None
    rate_key = f"user:{user['id']}" if user else f"ip:{lat:.2f},{lng:.2f}"

    if main._places.api_key:
        allowed, retry_after = await main._nearby_limiter.consume(rate_key)
        if not allowed:
            logger.warning("nearby rate limited key=%s retry_after=%s", rate_key, retry_after)
            raise rate_limited("rate limited", retry_after)

    fallback = f"{item['cuisine_type'] or ''} restaurant".strip()
    try:
        # lat/lng not stored — used only for this Places API call (privacy policy commitment)
        return await main._places.search(item["name"], fallback, lat, lng)
    except PlacesError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
