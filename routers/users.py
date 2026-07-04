"""Account routes: profile, GDPR export/erasure, stats, insights."""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

import db.database as db
import main
from routers import deps
from schemas import PatchMeBody, UserInfoOut
from tagging import safety

router = APIRouter()


@router.get("/api/users/me", response_model=UserInfoOut)
async def get_me(user=Depends(deps.get_user)):
    return UserInfoOut.of(user)


@router.patch("/api/users/me", response_model=UserInfoOut)
async def patch_me(body: PatchMeBody, user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    # None = field omitted → keep existing; validators already rejected bad flags.
    diet_mask = (
        safety.compute_dietary_bitmask(body.dietary_restrictions)
        if body.dietary_restrictions is not None
        else user["dietary_flags_bitmask"]
    )
    safety_mask = (
        safety.compute_safety_bitmask(body.safety_overrides)
        if body.safety_overrides is not None
        else user["safety_overrides_bitmask"]
    )
    db.update_user_dietary(conn, user["id"], diet_mask, safety_mask)
    return UserInfoOut.of(user, dietary_mask=diet_mask, safety_mask=safety_mask)


@router.delete("/api/users/me", status_code=204)
async def delete_me(user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    """GDPR Art. 17 — right to erasure. Deletes all user data immediately."""
    user_id = user["id"]
    db.delete_swipes_for_user(conn, user_id)
    db.delete_impressions_for_user(conn, user_id)
    db.delete_user(conn, user_id)
    conn.commit()


@router.get("/api/users/me/export")
async def export_me(user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    """GDPR Art. 20 — data portability. Returns all stored user data as JSON."""
    swipes = db.get_all_swipes_for_user(conn, user["id"])
    payload = {
        "account": {
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"],
        },
        "preferences": {
            "dietary_restrictions": safety.dietary_list_from_bitmask(user["dietary_flags_bitmask"]),
            "safety_overrides": safety.safety_list_from_bitmask(user["safety_overrides_bitmask"]),
            "onboarding_complete": bool(user["onboarding_complete"]),
        },
        "swipe_history": swipes,
        "stats": {
            "total_swipes": user["total_swipes"],
            "drift_active": bool(user["drift_active"]),
        },
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": 'attachment; filename="cravings-data.json"'},
    )


@router.get("/api/profile/stats")
async def profile_stats(user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    return db.get_swipe_stats(conn, user["id"])


@router.get("/api/insights")
async def insights(user=Depends(deps.require_premium)):
    # Several joined scans over full swipe history; run off the event loop.
    # Opens its own connection rather than reusing the request-scoped one
    # (Depends(deps.get_conn)), since sqlite3 connections aren't safe to hand
    # across threads.
    def _load() -> dict:
        with db.db_connection(main._db_path) as conn:
            return db.get_insights(conn, user["id"])

    return await asyncio.to_thread(_load)
