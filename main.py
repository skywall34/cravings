"""FastAPI entry point — single-process replacement for the Go + gRPC split."""

import asyncio
import logging
import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path

# python:3.12-slim ships without /etc/mime.types — register webp explicitly
# so StaticFiles serves food images as image/webp, not text/plain.
mimetypes.add_type("image/webp", ".webp")

from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.http import HTTPBearer as _OptionalBearer
from fastapi.staticfiles import StaticFiles

load_dotenv()

import db.database as db
import swipe
from model_server.model_service import ModelService
from places import PlacesAdapter, PlacesError
from tagging import safety
from tagging.client import tag_food_item

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

_db_path: Path = Path("cravings.db")  # resolved in lifespan from env
_model_service: ModelService | None = None
_places: PlacesAdapter = PlacesAdapter()
_sessions: swipe.SessionStore = swipe.SessionStore()
_session_max_swipes: int = int(os.environ.get("CRAVINGS_SESSION_MAX_SWIPES", "10"))
_images_root: Path = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_path, _model_service, _places, _sessions, _images_root
    _db_path = Path(os.environ.get("CRAVINGS_DB", "cravings.db"))
    _images_root = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
    db.init_db(_db_path)
    _model_service = ModelService(_db_path)
    _places = PlacesAdapter(api_key=os.environ.get("GOOGLE_PLACES_API_KEY", ""))
    _sessions = swipe.SessionStore()

    yield


_base_path = os.environ.get("BASE_PATH", "")

app = FastAPI(lifespan=lifespan, root_path=_base_path)
_bearer = HTTPBearer()
_optional_bearer = HTTPBearer(auto_error=False)


@app.middleware("http")
async def _image_cache_headers(request: Request, call_next):
    response: Response = await call_next(request)
    # Match regardless of mount prefix — request.url.path includes root_path
    # (e.g. /cravings/images/...) since the proxy forwards the full path.
    if "/images/" in request.url.path:
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

async def _get_conn():
    conn = db.get_connection(_db_path)
    try:
        yield conn
    finally:
        conn.close()


async def _get_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    conn=Depends(_get_conn),
):
    user = db.get_user_by_token(conn, credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    if (
        user["password_changed_at"]
        and user["token_issued_at"]
        and user["token_issued_at"] < user["password_changed_at"]
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token invalidated")
    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/users", status_code=201)
async def create_user(body: dict, conn=Depends(_get_conn)):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    dietary = body.get("dietary_restrictions") or []
    overrides = body.get("safety_overrides") or []
    diet_mask = safety.compute_dietary_bitmask(dietary)
    safety_mask = safety.compute_safety_bitmask(overrides)
    user_id, token = db.insert_user(conn, name, diet_mask, safety_mask)
    return {
        "id": user_id,
        "name": name,
        "api_token": token,
        "dietary_restrictions": safety.dietary_list_from_bitmask(diet_mask),
        "safety_overrides": safety.safety_list_from_bitmask(safety_mask),
    }


@app.get("/api/users/me")
async def get_me(user=Depends(_get_user)):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "is_registered": user["email"] is not None,
        "dietary_restrictions": safety.dietary_list_from_bitmask(user["dietary_flags_bitmask"]),
        "safety_overrides": safety.safety_list_from_bitmask(user["safety_overrides_bitmask"]),
        "onboarding_complete": bool(user["onboarding_complete"]),
    }


@app.post("/api/onboarding")
async def onboarding(body: dict, user=Depends(_get_user), conn=Depends(_get_conn)):
    prefs = body.get("preferences") or {}
    if not prefs:
        raise HTTPException(status_code=400, detail="preferences required")
    await asyncio.to_thread(_model_service.set_onboarding, user["id"], prefs)
    db.mark_onboarding_complete(conn, user["id"])
    return {"success": True}


@app.get("/api/recommend")
async def recommend(
    mood: str = Query(default="no_preference"),
    dietary_mode: str = Query(default="standard"),
    top_n: int = Query(default=1, ge=1),
    session_id: str = Query(default=""),
    hour: float | None = Query(default=None),
    user=Depends(_get_user),
    conn=Depends(_get_conn),
):
    snapshot = swipe.capture(conn, user["id"], dietary_mode, mood, hour)

    safety_mask = safety.user_safety_mask(user["safety_overrides_bitmask"])
    restrictions = safety.dietary_list_from_bitmask(user["dietary_flags_bitmask"])
    excluded = await _sessions.seen(session_id)

    candidates = db.get_eligible_food_items(conn, safety_mask, restrictions, excluded)
    if not candidates:
        raise HTTPException(status_code=404, detail="no eligible food items")

    results = await asyncio.to_thread(
        _model_service.get_recommendation, user["id"], candidates, snapshot.to_context(), top_n
    )
    if not results:
        raise HTTPException(status_code=404, detail="no eligible food items")

    id_to_candidate = {c["id"]: c for c in candidates}
    token = swipe.seal(snapshot)
    for r in results:
        r["snapshot_token"] = token
        candidate = id_to_candidate.get(r["id"], {})
        r.update({
            "description": candidate.get("description"),
            "cuisine_type": candidate.get("cuisine_type"),
            "spice_level": candidate.get("spice_level"),
            "sweetness": candidate.get("sweetness"),
            "richness": candidate.get("richness"),
            "sauce_heaviness": candidate.get("sauce_heaviness"),
            "veggie_density": candidate.get("veggie_density"),
            "dairy_content": candidate.get("dairy_content"),
            "protein_type": candidate.get("protein_type"),
            "image_slug": candidate.get("image_slug"),
            "image_hash": candidate.get("image_hash"),
            "image_author": candidate.get("image_author"),
            "image_license": candidate.get("image_license"),
            "image_source_url": candidate.get("image_source_url"),
            "image_review_status": candidate.get("image_review_status", "auto"),
        })
        _build_image_urls(r)
    return results


@app.post("/api/swipe")
async def swipe_endpoint(body: dict, user=Depends(_get_user), conn=Depends(_get_conn)):
    food_item_id = body.get("food_item_id")
    direction = body.get("direction")
    session_id = body.get("session_id") or ""
    token = body.get("snapshot_token") or ""

    item = db.get_food_item(conn, food_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="food item not found")

    try:
        snapshot = swipe.verify(token, user["id"])
    except swipe.SnapshotError as e:
        raise HTTPException(status_code=400, detail=f"invalid snapshot: {e}") from e

    try:
        total_swipes = await swipe.record_swipe(
            conn, _model_service, _sessions, user, item, snapshot, direction, session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    seen_count = await _sessions.count(session_id)
    session_complete = seen_count >= _session_max_swipes
    return {"success": True, "total_swipes": total_swipes, "session_complete": session_complete}


@app.post("/api/session/reset")
async def session_reset(body: dict):
    session_id = body.get("session_id") or ""
    await _sessions.reset(session_id)
    return {"success": True}


@app.get("/api/food-items")
async def list_food_items(conn=Depends(_get_conn), user=Depends(_get_user)):
    return db.list_food_items(conn)


@app.get("/api/food-items/{item_id}")
async def get_food_item(item_id: int, conn=Depends(_get_conn), user=Depends(_get_user)):
    item = db.get_food_item(conn, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    return _build_image_urls(item)


@app.get("/api/restaurants")
async def list_restaurants(conn=Depends(_get_conn), user=Depends(_get_user)):
    return db.list_restaurants(conn)


@app.get("/api/model/status")
async def model_status(user=Depends(_get_user)):
    status_data = await asyncio.to_thread(_model_service.get_status, user["id"])
    return status_data


@app.get("/api/nearby")
async def nearby(
    food_item_id: int = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    user=Depends(_get_user),
    conn=Depends(_get_conn),
):
    item = db.get_food_item(conn, food_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="food item not found")
    fallback = f"{item['cuisine_type'] or ''} restaurant".strip()
    try:
        return await _places.search(item["name"], fallback, lat, lng)
    except PlacesError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

def _validate_email(raw: str) -> str:
    try:
        return validate_email(raw, check_deliverability=False).normalized
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=f"invalid email: {e}") from e


@app.post("/api/auth/register", status_code=201)
async def auth_register(
    body: dict,
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    conn=Depends(_get_conn),
):
    email = _validate_email((body.get("email") or "").strip())
    password = (body.get("password") or "").strip()
    name = (body.get("name") or "").strip()
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="password must be at least 8 characters")

    existing = db.get_user_by_email(conn, email)
    if existing:
        raise HTTPException(status_code=409, detail="email already registered, please log in")

    password_hash = db.hash_password(password)

    if credentials:
        guest = db.get_user_by_token(conn, credentials.credentials)
        if guest and guest["email"] is None:
            db.attach_credentials(conn, guest["id"], email, password_hash)
            return {
                "id": guest["id"],
                "name": guest["name"],
                "email": email,
                "api_token": credentials.credentials,
                "is_registered": True,
                "onboarding_complete": bool(guest["onboarding_complete"]),
            }

    if not name:
        raise HTTPException(status_code=400, detail="name required for new registration")
    user_id, token = db.create_registered_user(conn, email, password_hash, name)
    return {
        "id": user_id,
        "name": name,
        "email": email,
        "api_token": token,
        "is_registered": True,
        "onboarding_complete": False,
    }


@app.post("/api/auth/login")
async def auth_login(body: dict, conn=Depends(_get_conn)):
    email = _validate_email((body.get("email") or "").strip())
    password = (body.get("password") or "").strip()

    user = db.get_user_by_email(conn, email)
    if not user or not user["password_hash"] or not db.verify_password(password, user["password_hash"]):
        await asyncio.sleep(0.25)
        raise HTTPException(status_code=401, detail="invalid email or password")

    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "api_token": user["api_token"],
        "is_registered": True,
        "onboarding_complete": bool(user["onboarding_complete"]),
    }


@app.post("/api/auth/logout")
async def auth_logout(user=Depends(_get_user), conn=Depends(_get_conn)):
    db.rotate_api_token(conn, user["id"])
    return {"success": True}


@app.post("/api/auth/password")
async def auth_change_password(body: dict, user=Depends(_get_user), conn=Depends(_get_conn)):
    if not user["password_hash"]:
        raise HTTPException(status_code=400, detail="guest users cannot change password")
    old_password = (body.get("old_password") or "").strip()
    new_password = (body.get("new_password") or "").strip()
    if not db.verify_password(old_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="incorrect current password")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="new password must be at least 8 characters")
    new_token = db.update_password(conn, user["id"], db.hash_password(new_password))
    return {"success": True, "api_token": new_token}


@app.get("/api/profile/stats")
async def profile_stats(user=Depends(_get_user), conn=Depends(_get_conn)):
    return db.get_swipe_stats(conn, user["id"])


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

async def _tag_items_background(item_ids: list[int]) -> None:
    conn = db.get_connection(_db_path)
    try:
        for item_id in item_ids:
            row = conn.execute(
                "SELECT name, description FROM food_items WHERE id = ?", [item_id]
            ).fetchone()
            if row is None:
                continue
            try:
                tags = await asyncio.to_thread(tag_food_item, row["name"], row["description"])
                db.update_food_item_tags(conn, item_id, tags)
            except Exception as e:
                logger.warning("tagging failed for item %d: %s", item_id, e)
                conn.execute(
                    "UPDATE food_items SET tagging_status = 'failed' WHERE id = ?", [item_id]
                )
                conn.commit()
    finally:
        conn.close()


def _require_admin(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    admin_token = os.environ.get("CRAVINGS_ADMIN_TOKEN", "")
    if not admin_token or credentials.credentials != admin_token:
        raise HTTPException(status_code=403, detail="forbidden")


@app.post("/api/admin/batch", status_code=202, dependencies=[Depends(_require_admin)])
async def admin_batch(body: dict):
    """Insert restaurants + food items and queue async LLM tagging.

    Body: {"restaurants": [{name, location, cuisine_type, source_type}, ...],
           "food_items":   [{name, description, restaurant_id?}, ...]}
    """
    restaurants = body.get("restaurants") or []
    food_items = body.get("food_items") or []

    conn = db.get_connection(_db_path)
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


# ---------------------------------------------------------------------------
# Image URL helper
# ---------------------------------------------------------------------------

def _build_image_urls(item: dict) -> dict:
    """Add image_url_400, image_url_800 fields to a food item dict."""
    slug = item.get("image_slug")
    hash_ = item.get("image_hash")
    status = item.get("image_review_status", "auto")
    if slug and hash_ and status in ("auto", "approved", "needs_review"):
        base = f"{_base_path}/images/food/{slug}-{hash_}"
        item["image_url_400"] = f"{base}-400.webp"
        item["image_url_800"] = f"{base}-800.webp"
    else:
        item["image_url_400"] = None
        item["image_url_800"] = None
    return item


# ---------------------------------------------------------------------------
# Static files (images + SPA) — must be mounted after all API routes
# ---------------------------------------------------------------------------

# Images: mount at module load time. CRAVINGS_IMAGES_ROOT must be set before import.
_images_dir = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
if _images_dir.is_dir():
    app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")

_dist = Path("frontend/dist")
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", type=str, default="cravings.db")
    parser.add_argument("--maps-api-key", type=str, default="")
    args = parser.parse_args()

    os.environ["CRAVINGS_DB"] = args.db
    if args.maps_api_key:
        os.environ["GOOGLE_PLACES_API_KEY"] = args.maps_api_key

    uvicorn.run("main:app", host="0.0.0.0", port=args.port, reload=False)
