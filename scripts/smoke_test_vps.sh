#!/usr/bin/env bash
# Smoke test against live VPS. Usage: ./scripts/smoke_test_vps.sh [base_url]
# Default base_url: https://themshin.com/cravings

BASE="${1:-https://themshin.com/cravings}"
API="$BASE/api"
PASS=0
FAIL=0

ok()   { echo "  ✓ $1"; PASS=$((PASS+1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }
section() { echo; echo "── $1 ──"; }

# ── 1. Health ────────────────────────────────────────────────────────────────
section "Health"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/health")
[ "$STATUS" = "200" ] && ok "GET /api/health → 200" || fail "GET /api/health → $STATUS"

# ── 2. Create guest user ─────────────────────────────────────────────────────
section "Auth"
USER=$(curl -s -X POST "$API/users" \
  -H "Content-Type: application/json" \
  -d '{"name":"smoke-test"}')
TOKEN=$(echo "$USER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('api_token',''))")
USER_ID=$(echo "$USER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
[ -n "$TOKEN" ] && ok "POST /api/users → got token (user_id=$USER_ID)" || { fail "POST /api/users failed: $USER"; exit 1; }

AUTH="Authorization: Bearer $TOKEN"

# ── 3. Recommend ─────────────────────────────────────────────────────────────
section "Recommend"
SESSION="smoke-$$"
REC=$(curl -s "$API/recommend?session_id=$SESSION&mood=no_preference&dietary_mode=standard" \
  -H "$AUTH")
ITEM_ID=$(echo "$REC" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if isinstance(d,list) and d else d.get('id',''))" 2>/dev/null)
SNAP=$(echo "$REC" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d[0] if isinstance(d,list) else d; print(r.get('snapshot_token',''))" 2>/dev/null)
[ -n "$ITEM_ID" ] && ok "GET /api/recommend → item_id=$ITEM_ID" || fail "GET /api/recommend failed: $REC"

# ── 4. Swipe (right) — triggers push_recent_like ─────────────────────────────
section "Swipe"
if [ -n "$ITEM_ID" ] && [ -n "$SNAP" ]; then
  SWIPE=$(curl -s -X POST "$API/swipe" \
    -H "Content-Type: application/json" \
    -H "$AUTH" \
    -d "{\"food_item_id\":$ITEM_ID,\"direction\":\"right\",\"session_id\":\"$SESSION\",\"snapshot_token\":\"$SNAP\"}")
  TOTAL=$(echo "$SWIPE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_swipes','?'))")
  [ "$TOTAL" = "1" ] && ok "POST /api/swipe (right) → total_swipes=$TOTAL" || fail "POST /api/swipe failed: $SWIPE"
else
  fail "Skipped swipe — no item_id or snapshot_token"
fi

# ── 5. Do 4 more swipes to reach 5 and trigger cuisine prior seed ─────────────
section "Cuisine prior seed (swipe 5 trigger)"
for i in 2 3 4 5; do
  REC=$(curl -s "$API/recommend?session_id=$SESSION&mood=no_preference&dietary_mode=standard" \
    -H "$AUTH")
  IID=$(echo "$REC" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if isinstance(d,list) and d else '')" 2>/dev/null)
  SN=$(echo "$REC" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d[0] if isinstance(d,list) else d; print(r.get('snapshot_token',''))" 2>/dev/null)
  if [ -n "$IID" ] && [ -n "$SN" ]; then
    DIR="left"
    [ "$i" = "4" ] && DIR="right"
    SWIPE=$(curl -s -X POST "$API/swipe" \
      -H "Content-Type: application/json" \
      -H "$AUTH" \
      -d "{\"food_item_id\":$IID,\"direction\":\"$DIR\",\"session_id\":\"$SESSION\",\"snapshot_token\":\"$SN\"}")
    TOTAL=$(echo "$SWIPE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_swipes','?'))")
    ok "  swipe $i ($DIR) → total_swipes=$TOTAL"
  else
    fail "  swipe $i: no item"
  fi
done

# ── 6. Model status ───────────────────────────────────────────────────────────
section "Model status"
STATUS_JSON=$(curl -s "$API/model/status" -H "$AUTH")
TS=$(echo "$STATUS_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_swipes','?'))")
[ "$TS" = "5" ] && ok "GET /api/model/status → total_swipes=$TS" || fail "GET /api/model/status unexpected: $STATUS_JSON"

# ── 7. Check recent_likes persisted ──────────────────────────────────────────
section "Embedding / recent_likes (DB check on VPS)"
echo "  Run on VPS to verify recent_likes_json and embedding column:"
echo "  docker compose exec cravings uv run python /app/scripts/embed_items.py --validate"

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "══════════════════════════════"
echo "  PASSED: $PASS  FAILED: $FAIL"
echo "══════════════════════════════"
[ "$FAIL" = "0" ] && exit 0 || exit 1
