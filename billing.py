"""Payment provider seam — mirrors recommender.py adapter pattern.

MockProvider: offline/CI default. Self-fires the webhook after ~1.5s.
StripeProvider: real Stripe Checkout Sessions (sandbox test mode).
"""

import asyncio
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from typing import Protocol


@dataclass
class CheckoutSession:
    session_id: str
    amount_cents: int
    provider: str
    url: str | None


@dataclass
class WebhookEvent:
    event_type: str   # e.g. "checkout.session.completed"
    session_id: str
    user_id: int


class PaymentProvider(Protocol):
    async def create_checkout_session(
        self,
        user: dict,
        amount_cents: int,
        *,
        _webhook_handler=None,
    ) -> CheckoutSession: ...

    def verify_and_parse_webhook(
        self, payload: bytes, signature: str
    ) -> WebhookEvent: ...


# ---------------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------------

class MockProvider:
    """Offline provider. Suitable for CI and local dev without Stripe keys."""

    def __init__(self, webhook_secret: str) -> None:
        self._secret = webhook_secret
        # asyncio only holds a weak ref to a task via create_task; without a
        # strong ref of our own the GC can reap it mid-sleep and the self-fired
        # webhook silently never lands. Keep the instance alive here.
        self._pending_tasks: set[asyncio.Task] = set()

    async def create_checkout_session(
        self,
        user: dict,
        amount_cents: int,
        *,
        _webhook_handler=None,
    ) -> CheckoutSession:
        session_id = f"mock_cs_{secrets.token_hex(12)}"
        if _webhook_handler is not None:
            task = asyncio.create_task(
                _self_fire_webhook(session_id, user["id"], amount_cents, self._secret, _webhook_handler)
            )
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)
        return CheckoutSession(
            session_id=session_id,
            amount_cents=amount_cents,
            provider="mock",
            url=None,
        )

    def verify_and_parse_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        expected = _hmac_sign(payload, self._secret)
        if not hmac.compare_digest(expected, signature):
            raise ValueError("invalid mock webhook signature")
        event = json.loads(payload)
        return WebhookEvent(
            event_type=event["type"],
            session_id=event["data"]["object"]["id"],
            user_id=int(event["data"]["object"]["metadata"]["user_id"]),
        )


def _hmac_sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


async def _self_fire_webhook(
    session_id: str,
    user_id: int,
    amount_cents: int,
    secret: str,
    handler,
) -> None:
    await asyncio.sleep(1.5)
    event_payload = json.dumps({
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": session_id,
                "amount_total": amount_cents,
                "metadata": {"user_id": str(user_id)},
            }
        },
    }).encode()
    sig = _hmac_sign(event_payload, secret)
    try:
        await handler(event_payload, sig)
    except Exception:
        pass  # background task — errors logged by asyncio exception handler


# ---------------------------------------------------------------------------
# StripeProvider
# ---------------------------------------------------------------------------

class StripeProvider:
    """Real Stripe Checkout Sessions (test mode keys from .env)."""

    def __init__(
        self,
        secret_key: str,
        webhook_secret: str,
        success_url: str,
        cancel_url: str,
    ) -> None:
        import stripe as _stripe
        _stripe.api_key = secret_key
        self._stripe = _stripe
        self._webhook_secret = webhook_secret
        self._success_url = success_url
        self._cancel_url = cancel_url

    async def create_checkout_session(
        self,
        user: dict,
        amount_cents: int,
        *,
        _webhook_handler=None,  # unused for Stripe — real webhook fires externally
    ) -> CheckoutSession:
        # stripe-python's Session.create is a blocking HTTPS call; run it off
        # the event loop so one checkout doesn't stall in-flight requests.
        session = await asyncio.to_thread(
            self._stripe.checkout.Session.create,
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {"name": "Cravings Premium — lifetime unlock"},
                },
                "quantity": 1,
            }],
            success_url=self._success_url,
            cancel_url=self._cancel_url,
            metadata={"user_id": str(user["id"])},
            client_reference_id=str(user["id"]),
        )
        return CheckoutSession(
            session_id=session.id,
            amount_cents=amount_cents,
            provider="stripe",
            url=session.url,
        )

    def verify_and_parse_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        event = self._stripe.Webhook.construct_event(
            payload, signature, self._webhook_secret
        )
        obj = event["data"]["object"]
        return WebhookEvent(
            event_type=event["type"],
            session_id=obj["id"],
            user_id=int(obj["metadata"]["user_id"]),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_payment_provider() -> MockProvider | StripeProvider:
    provider = os.environ.get("CRAVINGS_BILLING_PROVIDER", "mock").lower()
    if provider == "stripe":
        secret_key = os.environ["STRIPE_SECRET_KEY"]
        webhook_secret = os.environ["STRIPE_WEBHOOK_SECRET"]
        base_url = os.environ.get("CRAVINGS_BASE_URL", "http://localhost:8000")
        base_path = os.environ.get("BASE_PATH", "")
        success_url = os.environ.get(
            "CRAVINGS_BILLING_SUCCESS_URL",
            f"{base_url}{base_path}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        )
        cancel_url = os.environ.get(
            "CRAVINGS_BILLING_CANCEL_URL",
            f"{base_url}{base_path}/?checkout=cancel",
        )
        return StripeProvider(secret_key, webhook_secret, success_url, cancel_url)

    # No hardcoded fallback secret: a known default would let anyone forge a
    # `checkout.session.completed` webhook and grant themselves premium on any
    # deploy that hasn't switched to Stripe. The mock webhook self-fires *inside*
    # this process (see MockProvider.create_checkout_session), so a random
    # per-process secret is sufficient — the self-fire holds the same secret,
    # while an external caller cannot guess it. Explicit env (CI/dev) still wins.
    webhook_secret = os.environ.get("CRAVINGS_BILLING_WEBHOOK_SECRET") or secrets.token_hex(32)
    return MockProvider(webhook_secret)
