"""Shared FastAPI dependencies for the routers/ package.

State (db path, rate limiters, etc.) lives on the `main` module and is mutated
by `main.lifespan` at startup / by tests directly. Every function here reads
`main.<attr>` at call time (never imports the value directly) so it always
sees the current object — tests that do `main._db_path = ...` or
`patch.object(main._places, ...)` keep working unchanged.
"""

import hmac
import logging
import os

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import db.database as db
import main
from rate_limit import rate_limited
from schemas import is_admin_email

logger = logging.getLogger(__name__)

bearer = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)


async def get_conn():
    conn = db.get_connection(main._db_path)
    try:
        yield conn
    finally:
        conn.close()


async def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    conn=Depends(get_conn),
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


async def require_premium(user=Depends(get_user)):
    """Entitlement gate: premium or admin. Single source so a new premium-only
    route can't drift from the rule by hand-inlining it (mirrors `effectivePremium`
    on the frontend, which independently gates the same UI)."""
    if not (user.get("is_premium") or is_admin_email(user.get("email"))):
        raise HTTPException(status_code=403, detail="premium required")
    return user


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    admin_token = os.environ.get("CRAVINGS_ADMIN_TOKEN", "")
    if not admin_token or not hmac.compare_digest(credentials.credentials, admin_token):
        raise HTTPException(status_code=403, detail="forbidden")


def require_admin_user(user=Depends(get_user)):
    if not is_admin_email(user["email"]):
        raise HTTPException(status_code=403, detail="forbidden")
    return user


def client_ip(request: Request) -> str:
    """Caller IP for rate-limit keying.

    Behind one trusted proxy (Traefik), the genuine peer IP is the RIGHTMOST
    X-Forwarded-For entry — the one Traefik appends. The leftmost entries are
    client-supplied and spoofable, so trusting them would let an attacker rotate
    the value to bypass the limit.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


async def auth_throttle(key: str) -> None:
    """Raise 429 if the auth bucket for `key` is empty. Mirrors the nearby handler."""
    allowed, retry_after = await main._auth_limiter.consume(key)
    if not allowed:
        logger.warning("auth rate limited key=%s retry_after=%s", key, retry_after)
        raise rate_limited("too many attempts, try again later", retry_after)
