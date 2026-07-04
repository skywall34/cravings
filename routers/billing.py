"""Billing routes: checkout session creation + provider webhook."""

import os

from fastapi import APIRouter, Depends, HTTPException, Request

import db.database as db
import main
from routers import deps

router = APIRouter()


async def _process_webhook(payload: bytes, signature: str) -> None:
    """Parse + apply a signed webhook event. Raises ValueError on bad sig."""
    event = main._payment_provider.verify_and_parse_webhook(payload, signature)
    if event.event_type == "checkout.session.completed":
        with db.db_connection(main._db_path) as conn:
            session = db.get_billing_session(conn, event.session_id)
            if session and session["status"] != "completed":
                # Upgrade the account that OWNS this session, never the user_id
                # carried in the (attacker-controllable) webhook payload. The
                # payload's event.user_id is not trusted for the grant.
                db.complete_billing_session(conn, event.session_id)
                db.set_premium(conn, session["user_id"])


@router.post("/api/billing/checkout")
async def billing_checkout(user=Depends(deps.get_user), conn=Depends(deps.get_conn)):
    if not user.get("email"):
        raise HTTPException(status_code=403, detail="registered account required to purchase")
    amount_cents = int(os.environ.get("CRAVINGS_PREMIUM_PRICE_CENTS", "499"))
    session = await main._payment_provider.create_checkout_session(
        user, amount_cents, _webhook_handler=_process_webhook
    )
    db.create_billing_session(conn, session.session_id, user["id"], amount_cents)
    return {
        "session_id": session.session_id,
        "amount_cents": session.amount_cents,
        "provider": session.provider,
        "url": session.url,
    }


@router.post("/api/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("stripe-signature") or request.headers.get("x-mock-signature", "")
    try:
        await _process_webhook(payload, signature)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid webhook") from exc
    return {"received": True}
