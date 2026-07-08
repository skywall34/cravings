"""FastAPI entry point — single-process replacement for the Go + gRPC split."""

import json
import logging
import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path

# python:3.12-slim ships without /etc/mime.types — register webp explicitly
# so StaticFiles serves food images as image/webp, not text/plain.
mimetypes.add_type("image/webp", ".webp")

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

import db.database as db
import swipe
from model_server.model_service import UserModelStore
from model_server.recommendation_service import ModelServer
from places import PlacesAdapter
from rate_limit import RateLimiter
from billing import make_payment_provider
from email_service import get_email_sender, send_verification_email
from tagging.client import tag_food_item

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

_db_path: Path = Path("cravings.db")  # resolved in lifespan from env
_model_service: ModelServer | None = None
_places: PlacesAdapter = PlacesAdapter()
_payment_provider = None
_sessions: swipe.SessionStore = swipe.SessionStore()
_session_max_swipes: int = int(os.environ.get("CRAVINGS_SESSION_MAX_SWIPES", "10"))
_images_root: Path = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
_nearby_limiter: RateLimiter = RateLimiter(capacity=10, refill_seconds=30.0)
_auth_limiter: RateLimiter = RateLimiter(capacity=5, refill_seconds=60.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_path, _model_service, _places, _sessions, _images_root, _nearby_limiter, _auth_limiter, _payment_provider
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
    _auth_limiter = RateLimiter(
        capacity=int(os.environ.get("CRAVINGS_AUTH_BURST", "5")),
        refill_seconds=float(os.environ.get("CRAVINGS_AUTH_REFILL_SECONDS", "60")),
    )
    _payment_provider = make_payment_provider()
    # Resolve the email sender at boot so a misconfigured prod (no SMTP_*) fails
    # fast here instead of on the first user's registration.
    get_email_sender()

    yield


_base_path = os.environ.get("BASE_PATH", "")

app = FastAPI(lifespan=lifespan, root_path=_base_path)


@app.exception_handler(RequestValidationError)
async def _flatten_validation_error(request: Request, exc: RequestValidationError):
    """Reshape FastAPI's structured 422 (a list) into {"detail": "<string>"}.

    Clients parse `detail` as a string, so request validation must keep that
    shape rather than emitting the default error list.
    """
    errors = exc.errors()
    msg = errors[0].get("msg", "invalid request") if errors else "invalid request"
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]
    return JSONResponse(status_code=422, content={"detail": msg})

@app.middleware("http")
async def _image_cache_headers(request: Request, call_next):
    response: Response = await call_next(request)
    # Match regardless of mount prefix — request.url.path includes root_path
    # (e.g. /cravings/images/...) since the proxy forwards the full path.
    if "/images/" in request.url.path:
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


# Baseline HTTP security headers on every response. CSP is enforcing but pragmatic:
# 'unsafe-inline' style is required (heavy inline style={{}} in the React SPA) and
# Google Fonts is allowlisted. Stripe needs no exception — checkout is a full-page
# redirect, not an iframe. Permissions-Policy keeps geolocation (used by the app).
_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Content-Security-Policy"] = _CSP
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
    return response


@app.middleware("http")
async def _log_errors(request: Request, call_next):
    import traceback
    try:
        return await call_next(request)
    except Exception:
        logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url, traceback.format_exc())
        raise


_ASSETLINKS_PATH = "/.well-known/assetlinks.json"


class _AssetLinksMiddleware:
    """Pure ASGI: serves Digital Asset Links before root_path routing.

    Traefik forwards /.well-known/assetlinks.json WITHOUT the /cravings prefix,
    so it can't be a normal route while root_path=/cravings (VPS_DEPLOY.md).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] == _ASSETLINKS_PATH:
            # Read env at request time: VPS restart picks up new fingerprints,
            # and tests can monkeypatch os.environ per-case.
            fingerprints = [
                f.strip()
                for f in os.environ.get("CRAVINGS_ASSETLINKS_FINGERPRINTS", "").split(",")
                if f.strip()
            ]
            if not fingerprints:
                body = json.dumps({"detail": "not configured"}).encode()
                status = 404
            else:
                package_name = os.environ.get("CRAVINGS_ANDROID_PACKAGE", "com.themshin.cravings")
                body = json.dumps([
                    {
                        "relation": ["delegate_permission/common.handle_all_urls"],
                        "target": {
                            "namespace": "android_app",
                            "package_name": package_name,
                            "sha256_cert_fingerprints": fingerprints,
                        },
                    }
                ]).encode()
                status = 200
            await send({
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"cache-control", b"public, max-age=300"),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)


app.add_middleware(_AssetLinksMiddleware)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Route handlers live in routers/ (users, catalog, auth, billing, admin), split
# out of this module for size. They read shared state via `main.<attr>` at call
# time, so lifespan's `global` reassignments above are still visible to them.
from routers import admin as _admin_router  # noqa: E402
from routers import auth as _auth_router  # noqa: E402
from routers import billing as _billing_router  # noqa: E402
from routers import catalog as _catalog_router  # noqa: E402
from routers import users as _users_router  # noqa: E402

app.include_router(_users_router.router)
app.include_router(_catalog_router.router)
app.include_router(_auth_router.router)
app.include_router(_billing_router.router)
app.include_router(_admin_router.router)


# ---------------------------------------------------------------------------
# Static files (images + SPA) — must be mounted after all API routes
# ---------------------------------------------------------------------------

# Images: mount at module load time. CRAVINGS_IMAGES_ROOT must be set before import.
_images_dir = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
if _images_dir.is_dir():
    app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")

_dist = Path("frontend/dist")


def _spa_index_or_404() -> FileResponse:
    index = _dist / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="not built")
    return FileResponse(index, media_type="text/html")


@app.get("/privacy")
async def privacy_page():
    return _spa_index_or_404()


@app.get("/terms")
async def terms_page():
    return _spa_index_or_404()


@app.get("/account-deletion")
async def account_deletion_page():
    return _spa_index_or_404()


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
