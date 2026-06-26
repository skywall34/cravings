"""Pluggable transactional email sender.

No email infrastructure ships by default: when ``SMTP_HOST`` is unset (local
dev, tests) the :class:`ConsoleSender` logs the message — including the
verification code — so a developer can read it from stderr. In production, set
the ``SMTP_*`` env vars and :class:`SmtpSender` delivers over stdlib smtplib.

The blocking smtplib call is run in a worker thread via ``anyio.to_thread`` so
it never stalls the event loop. No third-party dependency is required.
"""

from __future__ import annotations

import logging
import os
import smtplib
import sys
from email.message import EmailMessage
from typing import Protocol

import anyio

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleSender:
    """Dev/test sender — prints the message instead of delivering it.

    Writes straight to stderr (not the logger) so the verification code is always
    visible in the dev console — uvicorn doesn't attach a handler to this module's
    logger, so logger.info would be swallowed.
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        print(
            f"\n=== EMAIL (console sender, not delivered) ===\n"
            f"  to: {to}\n  subject: {subject}\n  body:\n{body}\n"
            f"============================================\n",
            file=sys.stderr,
            flush=True,
        )


class SmtpSender:
    """Production sender backed by stdlib smtplib."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        sender: str,
        use_starttls: bool,
        use_ssl: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender
        self._use_starttls = use_starttls
        self._use_ssl = use_ssl

    def _send_sync(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self._sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        # Port 465 = implicit TLS (handshake on connect, no plaintext banner) →
        # SMTP_SSL. Port 587/2525 = plaintext connect then STARTTLS upgrade.
        if self._use_ssl:
            smtp_cm = smtplib.SMTP_SSL(self._host, self._port, timeout=10)
        else:
            smtp_cm = smtplib.SMTP(self._host, self._port, timeout=10)
        with smtp_cm as smtp:
            if self._use_starttls and not self._use_ssl:
                smtp.starttls()
            if self._username:
                smtp.login(self._username, self._password or "")
            smtp.send_message(msg)

    async def send(self, to: str, subject: str, body: str) -> None:
        await anyio.to_thread.run_sync(self._send_sync, to, subject, body)


def _is_production() -> bool:
    """Prod is signalled by CRAVINGS_ENV, or by BASE_PATH (set on the VPS deploy)."""
    if os.environ.get("CRAVINGS_ENV", "").lower() in {"prod", "production"}:
        return True
    return bool(os.environ.get("BASE_PATH"))


def _build_sender() -> EmailSender:
    host = os.environ.get("SMTP_HOST")
    if not host:
        # Fail fast rather than silently falling back to ConsoleSender in prod —
        # otherwise no user gets an email and codes leak into container logs.
        if _is_production():
            raise RuntimeError(
                "SMTP_HOST is not set but this looks like production "
                "(CRAVINGS_ENV/BASE_PATH). Configure SMTP_* env vars, or set "
                "CRAVINGS_ENV=dev to allow the console email fallback."
            )
        return ConsoleSender()
    port = int(os.environ.get("SMTP_PORT", "587"))
    # Implicit TLS when explicitly asked, or on the conventional SSL port 465.
    use_ssl = os.environ.get("SMTP_SSL", "").lower() in {"1", "true", "yes"} or port == 465
    return SmtpSender(
        host=host,
        port=port,
        username=os.environ.get("SMTP_USER"),
        password=os.environ.get("SMTP_PASS"),
        sender=os.environ.get("SMTP_FROM", "Cravings <no-reply@cravings.app>"),
        use_starttls=os.environ.get("SMTP_STARTTLS", "1") != "0",
        use_ssl=use_ssl,
    )


_sender: EmailSender | None = None


def get_email_sender() -> EmailSender:
    """Process-wide singleton, chosen from the environment on first use."""
    global _sender
    if _sender is None:
        _sender = _build_sender()
    return _sender


async def send_verification_email(sender: EmailSender, email: str, code: str) -> None:
    subject = "Your Cravings verification code"
    body = (
        f"Welcome to Cravings!\n\n"
        f"Your verification code is: {code}\n\n"
        f"Enter it in the app to finish creating your account. "
        f"This code expires in 10 minutes.\n\n"
        f"If you didn't sign up, you can ignore this email."
    )
    await sender.send(email, subject, body)
