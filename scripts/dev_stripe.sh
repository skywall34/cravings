#!/usr/bin/env bash
# Start stripe listen + backend together for local Stripe sandbox testing.
# Captures the webhook signing secret from stripe listen output and injects it
# into the backend process — no manual .env editing needed.
#
# Usage:
#   ./scripts/dev_stripe.sh [--db <path>]
#
# Prerequisites:
#   - stripe CLI installed and authenticated (stripe login)
#   - STRIPE_SECRET_KEY set in .env (sk_test_...)
#   - CRAVINGS_BILLING_PROVIDER=stripe set in .env (or pass via env)

set -euo pipefail

DB="${1:-cravings.db}"
if [[ "$1" == "--db" && -n "${2:-}" ]]; then
  DB="$2"
fi

BACKEND_PORT=8080
WEBHOOK_PATH="/api/billing/webhook"
FORWARD_TO="http://localhost:${BACKEND_PORT}${WEBHOOK_PATH}"

STRIPE_OUT=$(mktemp)
trap 'kill $(jobs -p) 2>/dev/null; rm -f "$STRIPE_OUT"' EXIT

echo "[stripe] Starting stripe listen → ${FORWARD_TO}"
stripe listen --forward-to "$FORWARD_TO" >"$STRIPE_OUT" 2>&1 &
STRIPE_PID=$!

# Wait for stripe listen to print the webhook signing secret (up to 10s)
WEBHOOK_SECRET=""
for i in $(seq 1 20); do
  WEBHOOK_SECRET=$(grep -oP 'whsec_\S+' "$STRIPE_OUT" | head -1 || true)
  if [[ -n "$WEBHOOK_SECRET" ]]; then
    break
  fi
  sleep 0.5
done

if [[ -z "$WEBHOOK_SECRET" ]]; then
  echo "[stripe] ERROR: timed out waiting for webhook secret. Is stripe CLI logged in?"
  cat "$STRIPE_OUT"
  exit 1
fi

echo "[stripe] Webhook secret: ${WEBHOOK_SECRET}"
echo "[stripe] Forwarding events — keep this running"
echo ""

# Tail stripe output in background so events print alongside backend logs
tail -f "$STRIPE_OUT" &

echo "[backend] Starting backend (db=${DB})"
STRIPE_WEBHOOK_SECRET="$WEBHOOK_SECRET" \
CRAVINGS_BILLING_PROVIDER=stripe \
  uv run python main.py --db "$DB"
