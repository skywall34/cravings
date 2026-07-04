"""Auth routes: register, login, email verification, logout, password change."""

import asyncio
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request

import db.database as db
import main
from rate_limit import rate_limited
from routers import deps
from schemas import (
    AuthResultOut,
    LoginBody,
    PasswordBody,
    RegisterBody,
    ResendVerificationBody,
    VerifyEmailBody,
)

router = APIRouter()


@router.post("/api/auth/register", status_code=201, response_model=AuthResultOut)
async def auth_register(body: RegisterBody, request: Request, conn=Depends(deps.get_conn)):
    await deps.auth_throttle(f"register|ip:{deps.client_ip(request)}")
    # email/password/name already normalized + validated by RegisterBody.
    existing = db.get_user_by_email(conn, body.email)

    # bcrypt is CPU-heavy (~200-300ms at the configured work factor); run it off
    # the event loop so concurrent auth calls don't stall in-flight requests.
    # Hash unconditionally (even when the email is taken) so the existing-email
    # branch costs roughly the same as the create branch — no timing tell.
    password_hash = await asyncio.to_thread(db.hash_password, body.password)

    if existing:
        # Don't disclose that the email is taken via a different status code
        # or shape (M1: register was a user-enumeration oracle). Return a
        # look-alike response that is never persisted and can't authenticate
        # anyone — same treatment as resend/verify, which stay silent too.
        return AuthResultOut.of(
            id=0, name=body.name, email=body.email, api_token=secrets.token_hex(32),
        )

    # The account starts unverified (email_verified defaults to 0). Login is
    # blocked until the user confirms the 6-digit code we email next. The token
    # is returned only so the client can drive the verify screen — the frontend
    # does not persist it as a session until verification succeeds.
    user_id, token = db.create_registered_user(conn, body.email, password_hash, body.name)
    code = db.generate_verification_code()
    db.upsert_verification(conn, body.email, code)
    await main.send_verification_email(main.get_email_sender(), body.email, code)
    return AuthResultOut.of(id=user_id, name=body.name, email=body.email, api_token=token)


@router.post("/api/auth/login", response_model=AuthResultOut)
async def auth_login(body: LoginBody, request: Request, conn=Depends(deps.get_conn)):
    # Throttle before the password check so guesses are rate-limited. Fold in the
    # email so per-account spray is bounded and one IP can't lock out all accounts.
    await deps.auth_throttle(f"login|ip:{deps.client_ip(request)}|email:{body.email.lower()}")
    user = db.get_user_by_email(conn, body.email)
    # bcrypt verify off the event loop (see register). Only run it when a hash
    # exists; short-circuits keep the guest/no-account path cheap.
    password_ok = bool(
        user
        and user["password_hash"]
        and await asyncio.to_thread(db.verify_password, body.password.strip(), user["password_hash"])
    )
    if not password_ok:
        await asyncio.sleep(0.25)
        raise HTTPException(status_code=401, detail="invalid email or password")

    # Gate login on verification — only after a correct password so we never
    # disclose verification state to someone guessing credentials.
    if not user["email_verified"]:
        raise HTTPException(status_code=403, detail="please verify your email")

    return AuthResultOut.of_user_row(user, email_verified=True)


@router.post("/api/auth/verify-email", response_model=AuthResultOut)
async def auth_verify_email(body: VerifyEmailBody, request: Request, conn=Depends(deps.get_conn)):
    await deps.auth_throttle(f"verify|ip:{deps.client_ip(request)}|email:{body.email.lower()}")
    user = db.get_user_by_email(conn, body.email)
    rec = db.get_verification(conn, body.email)
    # Generic failure for missing user/code keeps the two cases indistinguishable.
    if not user or not rec:
        raise HTTPException(status_code=400, detail="invalid or expired code")
    if db.verification_is_expired(rec):
        db.delete_verification(conn, body.email)
        raise HTTPException(status_code=400, detail="verification code expired, request a new one")
    if rec["attempts"] >= db.VERIFICATION_MAX_ATTEMPTS:
        db.delete_verification(conn, body.email)
        raise HTTPException(status_code=400, detail="too many attempts, request a new code")
    if not db.verification_code_matches(rec, body.code):
        attempts = db.bump_verification_attempts(conn, body.email)
        if attempts >= db.VERIFICATION_MAX_ATTEMPTS:
            db.delete_verification(conn, body.email)
        raise HTTPException(status_code=400, detail="invalid or expired code")

    db.set_email_verified(conn, user["id"])
    db.delete_verification(conn, body.email)
    return AuthResultOut.of_user_row(user, email_verified=True)


@router.post("/api/auth/resend-verification")
async def auth_resend_verification(body: ResendVerificationBody, request: Request, conn=Depends(deps.get_conn)):
    await deps.auth_throttle(f"resend|ip:{deps.client_ip(request)}|email:{body.email.lower()}")
    user = db.get_user_by_email(conn, body.email)
    # Only act for an existing, still-unverified account; otherwise return ok
    # without sending so we don't disclose which addresses are registered.
    if user and not user["email_verified"]:
        rec = db.get_verification(conn, body.email)
        if rec:
            wait = db.verification_resend_too_soon(rec)
            if wait > 0:
                raise rate_limited("please wait before requesting another code", wait)
        code = db.generate_verification_code()
        db.upsert_verification(conn, body.email, code)
        await main.send_verification_email(main.get_email_sender(), body.email, code)
    return {"ok": True}


@router.post("/api/auth/logout")
async def auth_logout(user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    db.rotate_api_token(conn, user["id"])
    return {"success": True}


@router.post("/api/auth/password")
async def auth_change_password(body: PasswordBody, user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    if not user["password_hash"]:
        raise HTTPException(status_code=400, detail="guest users cannot change password")
    old_password = body.old_password.strip()
    new_password = body.new_password.strip()
    if not await asyncio.to_thread(db.verify_password, old_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="incorrect current password")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="new password must be at least 8 characters")
    new_hash = await asyncio.to_thread(db.hash_password, new_password)
    new_token = db.update_password(conn, user["id"], new_hash)
    return {"success": True, "api_token": new_token}
