# Quickstart

Get Cravings running locally in under 5 minutes.

## Prerequisites

- Python 3.12+
- Node 18+ (Node 20 recommended)
- [uv](https://docs.astral.sh/uv/) for Python package management
- [Ollama](https://ollama.com/) with `gemma4:e2b` pulled (optional — only needed for LLM tagging)

## 1. Clone and install

```bash
git clone <repo-url>
cd cravings
uv sync
cd frontend && npm install && cd ..
```

## 2. Configure environment

Copy the example and fill in your values:

```bash
cp .env.example .env
```

```dotenv
# .env
GOOGLE_PLACES_API_KEY=...   # enables real /api/nearby results (omit for stub mode)
CRAVINGS_SWIPE_SECRET=...   # stable HMAC key — generate with: openssl rand -hex 32
CRAVINGS_ADMIN_TOKEN=...    # bearer token for POST /api/admin/batch
```

All three are optional for local development. Without them the app runs in stub mode (no real Places results, ephemeral snapshot tokens).

## 3. Seed the database

```bash
# Seed restaurants + food items (no Ollama required)
uv run python scripts/run_pipeline.py --seed-only

# Seed + tag all items via Ollama (requires gemma4:e2b running)
uv run python scripts/run_pipeline.py
```

## 3b. Fetch food images (optional, ~30 min)

Food images are gitignored and shipped via rsync — the `images/` directory is empty on a fresh clone. Run the backfill to populate it locally:

```bash
uv run python scripts/fetch_food_images.py
# → downloads images for ~40-50% of the ~1000-item catalog; remainder falls back to cuisine placeholder or emoji
```

Images land in `images/food/` and are served by the backend at `/images/food/...`. The Vite dev proxy forwards `/images` to the backend automatically.

> **Without running the backfill**: the app works fine — cards show cuisine placeholder images or emoji. Run the backfill when you want real dish photos locally.

## 4. Start the backend

```bash
uv run python main.py --db cravings.db
# → API running at http://localhost:8080
```

## 5. Start the frontend

In a second terminal:

```bash
cd frontend && npm run dev
# → App running at http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) — guests onboard locally (no DB row) and get global-popularity recommendations. Use the menu (top-right) to register or log in for personalized Thompson Sampling.

> **Dev vs production base path**: `npm run dev` passes `--base /` so all API calls go to `/api/...` (proxied to `:8080`). The production build uses `base: '/cravings/'` (set in `vite.config.ts`), so asset and API URLs are prefixed with `/cravings/` automatically via `import.meta.env.BASE_URL`.

## Production

Live at **https://themshin.com/cravings** — served via Docker on Hostinger VPS, Traefik reverse proxy, auto-updated by Watchtower on new image push.

To redeploy after code changes:
```bash
./docker_build.sh <GITHUB_PAT>
# Watchtower pulls new image within ~30 seconds
```

See `VPS_DEPLOY.md` for full VPS setup instructions.

---

## Verify it works

```bash
# Health check
curl http://localhost:8080/api/health

# Guest recommend (no auth — global popularity ranking)
curl -s 'http://localhost:8080/api/recommend?session_id=demo&dietary_restrictions=vegetarian' \
  | python3 -m json.tool
# → [{id, name, snapshot_token, ...}]

# Register a new account (always creates a fresh row — see ADR-0005)
curl -s -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword","name":"Alice"}' | python3 -m json.tool

# Log in
curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}' | python3 -m json.tool
# → {api_token, ...} — use this token for subsequent requests

# Profile stats (requires bearer)
curl -s http://localhost:8080/api/profile/stats \
  -H "Authorization: Bearer <token>" | python3 -m json.tool

# Run tests
uv run pytest tests/ -v
```

## Common issues

**No recommendations showing** — the food pool is empty. Run `--seed-only` first.

**LLM tagging stuck as `pending`** — Ollama not running or `gemma4:e2b` not pulled. Run `ollama pull gemma4:e2b` then `uv run python scripts/run_pipeline.py --tag-only`.

**Location not working** — browser geolocation requires HTTPS or `localhost`. The dev server at `localhost:5173` works; a remote IP won't.

**Port conflict** — backend defaults to `8080`. Change with `uv run python main.py --db cravings.db --port <port>` and update `frontend/vite.config.ts` proxy target accordingly.
