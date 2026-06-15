"""FastAPI entry point — single-process replacement for the Go + gRPC split."""

import asyncio
import logging
import mimetypes
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

# python:3.12-slim ships without /etc/mime.types — register webp explicitly
# so StaticFiles serves food images as image/webp, not text/plain.
mimetypes.add_type("image/webp", ".webp")

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.http import HTTPBearer as _OptionalBearer
from fastapi.staticfiles import StaticFiles

load_dotenv()

import db.database as db
import swipe
from model_server.model_service import UserModelStore
from model_server.recommendation_service import ModelServer
from places import PlacesAdapter, PlacesError
from rate_limit import RateLimiter
from recommender import make_recommender
from schemas import (
    AuthResultOut,
    LoginBody,
    OnboardingBody,
    PasswordBody,
    PatchMeBody,
    RegisterBody,
    SessionResetBody,
    SwipeBody,
    UserInfoOut,
)
from tagging import safety
from tagging.client import tag_food_item

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

_db_path: Path = Path("cravings.db")  # resolved in lifespan from env
_model_service: ModelServer | None = None
_places: PlacesAdapter = PlacesAdapter()
_sessions: swipe.SessionStore = swipe.SessionStore()
_session_max_swipes: int = int(os.environ.get("CRAVINGS_SESSION_MAX_SWIPES", "10"))
_images_root: Path = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
_nearby_limiter: RateLimiter = RateLimiter(capacity=10, refill_seconds=30.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_path, _model_service, _places, _sessions, _images_root, _nearby_limiter
    _db_path = Path(os.environ.get("CRAVINGS_DB", "cravings.db"))
    _images_root = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
    db.init_db(_db_path)
    from db.seed_sync import sync_content_from_seed
    with db.db_connection(_db_path) as _seed_conn:
        sync_content_from_seed(_seed_conn)
    _model_service = ModelServer(UserModelStore(_db_path))
    _places = PlacesAdapter(api_key=os.environ.get("GOOGLE_PLACES_API_KEY", ""))
    _sessions = swipe.SessionStore()
    _nearby_limiter = RateLimiter(
        capacity=int(os.environ.get("CRAVINGS_NEARBY_BURST", "10")),
        refill_seconds=float(os.environ.get("CRAVINGS_NEARBY_REFILL_SECONDS", "30")),
    )

    yield


_base_path = os.environ.get("BASE_PATH", "")

app = FastAPI(lifespan=lifespan, root_path=_base_path)


@app.exception_handler(RequestValidationError)
async def _flatten_validation_error(request: Request, exc: RequestValidationError):
    """Reshape FastAPI's structured 422 (a list) into {"detail": "<string>"}.

    Shipped clients (incl. Android APKs) parse `detail` as a string, so request
    validation must keep that shape rather than emitting the default error list.
    """
    errors = exc.errors()
    msg = errors[0].get("msg", "invalid request") if errors else "invalid request"
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]
    return JSONResponse(status_code=422, content={"detail": msg})

# The Capacitor Android WebView serves bundled assets from https://localhost
# (androidScheme: https) and calls this API cross-origin. The production web app
# is same-origin and unaffected. Auth is a Bearer token, not cookies, so
# credentials stay disabled.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost", "capacitor://localhost", "http://localhost"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

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


@app.middleware("http")
async def _log_errors(request: Request, call_next):
    import traceback
    try:
        return await call_next(request)
    except Exception:
        logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url, traceback.format_exc())
        raise


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



@app.get("/api/users/me", response_model=UserInfoOut)
async def get_me(user=Depends(_get_user)):
    return UserInfoOut.of(user)


@app.patch("/api/users/me", response_model=UserInfoOut)
async def patch_me(body: PatchMeBody, user=Depends(_get_user), conn=Depends(_get_conn)):
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


@app.delete("/api/users/me", status_code=204)
async def delete_me(user=Depends(_get_user), conn=Depends(_get_conn)):
    """GDPR Art. 17 — right to erasure. Deletes all user data immediately."""
    user_id = user["id"]
    db.delete_swipes_for_user(conn, user_id)
    db.delete_impressions_for_user(conn, user_id)
    db.delete_user(conn, user_id)
    conn.commit()


@app.get("/api/users/me/export")
async def export_me(user=Depends(_get_user), conn=Depends(_get_conn)):
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


@app.post("/api/onboarding")
async def onboarding(body: OnboardingBody, user=Depends(_get_user), conn=Depends(_get_conn)):
    await asyncio.to_thread(_model_service.set_onboarding, user["id"], body.preferences, body.reset)
    db.mark_onboarding_complete(conn, user["id"])
    return {"success": True}


@app.get("/api/recommend")
async def recommend(
    request: Request,
    top_n: int = Query(default=1, ge=1),
    session_id: str = Query(default=""),
    hour: float | None = Query(default=None),
    dietary_restrictions: list[str] = Query(default=[]),
    safety_overrides: list[str] = Query(default=[]),
    excluded_ids: list[int] = Query(default=[]),
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    conn=Depends(_get_conn),
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
        conn=conn, user=user, sessions=_sessions, model_service=_model_service,
        base_path=_base_path, session_max_swipes=_session_max_swipes, session_id=session_id,
        dietary_restrictions=dietary_restrictions, safety_overrides=safety_overrides,
        taste_prefs=taste_prefs,
    )
    results = await rec.recommend(
        hour=hour, top_n=top_n, excluded_ids=excluded_ids,
    )
    if not results:
        raise HTTPException(status_code=404, detail="no eligible food items")
    return results


@app.post("/api/swipe")
async def swipe_endpoint(
    body: SwipeBody,
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    conn=Depends(_get_conn),
):
    item = db.get_food_item(conn, body.food_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="food item not found")

    user = None
    if credentials:
        user = db.get_user_by_token(conn, credentials.credentials)

    rec = make_recommender(
        conn=conn, user=user, sessions=_sessions, model_service=_model_service,
        base_path=_base_path, session_max_swipes=_session_max_swipes, session_id=body.session_id,
        taste_prefs=body.taste_prefs,
    )
    try:
        outcome = await rec.record(item=item, direction=body.direction, token=body.snapshot_token)
    except swipe.SnapshotError as e:
        raise HTTPException(status_code=400, detail=f"invalid snapshot: {e}") from e
    except swipe.SwipeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"success": True, **outcome}


@app.post("/api/session/reset")
async def session_reset(body: SessionResetBody):
    await _sessions.reset(body.session_id)
    return {"success": True}


@app.get("/api/food-items")
async def list_food_items(conn=Depends(_get_conn), user=Depends(_get_user)):
    return db.list_food_items(conn)


@app.get("/api/food-items/{item_id}")
async def get_food_item(item_id: int, conn=Depends(_get_conn), user=Depends(_get_user)):
    item = db.get_food_item(conn, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="not found")
    return swipe.add_image_urls(item, _base_path)


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
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    conn=Depends(_get_conn),
):
    item = db.get_food_item(conn, food_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="food item not found")

    user = db.get_user_by_token(conn, credentials.credentials) if credentials else None
    rate_key = f"user:{user['id']}" if user else f"ip:{lat:.2f},{lng:.2f}"

    if _places.api_key:
        allowed, retry_after = await _nearby_limiter.consume(rate_key)
        if not allowed:
            retry_int = max(1, int(retry_after))
            logger.warning("nearby rate limited key=%s retry_after=%s", rate_key, retry_int)
            raise HTTPException(
                status_code=429,
                detail={"detail": "rate limited", "retry_after": retry_int},
                headers={"Retry-After": str(retry_int)},
            )

    fallback = f"{item['cuisine_type'] or ''} restaurant".strip()
    try:
        # lat/lng not stored — used only for this Places API call (privacy policy commitment)
        return await _places.search(item["name"], fallback, lat, lng)
    except PlacesError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/api/auth/register", status_code=201, response_model=AuthResultOut)
async def auth_register(body: RegisterBody, conn=Depends(_get_conn)):
    # email/password/name already normalized + validated by RegisterBody.
    existing = db.get_user_by_email(conn, body.email)
    if existing:
        raise HTTPException(status_code=409, detail="email already registered, please log in")

    password_hash = db.hash_password(body.password)
    user_id, token = db.create_registered_user(conn, body.email, password_hash, body.name)
    return AuthResultOut(
        id=user_id, name=body.name, email=body.email, api_token=token,
        is_registered=True, onboarding_complete=False,
    )


@app.post("/api/auth/login", response_model=AuthResultOut)
async def auth_login(body: LoginBody, conn=Depends(_get_conn)):
    user = db.get_user_by_email(conn, body.email)
    if not user or not user["password_hash"] or not db.verify_password(body.password.strip(), user["password_hash"]):
        await asyncio.sleep(0.25)
        raise HTTPException(status_code=401, detail="invalid email or password")

    return AuthResultOut(
        id=user["id"], name=user["name"], email=user["email"], api_token=user["api_token"],
        is_registered=True, onboarding_complete=bool(user["onboarding_complete"]),
    )


@app.post("/api/auth/logout")
async def auth_logout(user=Depends(_get_user), conn=Depends(_get_conn)):
    db.rotate_api_token(conn, user["id"])
    return {"success": True}


@app.post("/api/auth/password")
async def auth_change_password(body: PasswordBody, user=Depends(_get_user), conn=Depends(_get_conn)):
    if not user["password_hash"]:
        raise HTTPException(status_code=400, detail="guest users cannot change password")
    old_password = body.old_password.strip()
    new_password = body.new_password.strip()
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
