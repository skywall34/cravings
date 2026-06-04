# Cravings

**A swipe-based food recommendation app that learns what you want to eat.**

Live at **[themshin.com/cravings](https://themshin.com/cravings)**

---

## What it is

Cravings answers a small but constant question: *what do I feel like eating right now?*

You swipe through dishes — ✓ for "yes, that" and ✗ for "not now" — and the app
builds a picture of your taste. Swipe right on something and it surfaces nearby
restaurants that serve it. The recommendations should feel noticeably sharper
within 10–20 swipes, and they keep adapting as your cravings shift day to day.

It is single-user-personal, not social. There is no feed, no ratings from
strangers, no collaborative "people like you also liked." The only signal is
your own swipes.

## The model hypothesis

Most recommenders learn over **item IDs** — "you liked dish #412, here's dish
#598." That needs lots of data per item and breaks on anything new.

Cravings bets the opposite: **learn over food attributes, not food IDs.**

Every dish is broken down into 18 attributes: spice, sweetness, richness,
texture, temperature, cuisine, protein, and so on. The model learns weights over
*those attributes*. So a single swipe doesn't just teach the app about one dish
— it teaches it about every dish that shares those traits. Swipe right on three
spicy noodle bowls and the app understands "spicy" and "noodles," even for a dish
it has never shown you.

This is what makes learning from sparse, single-user data possible. Three
consequences fall out of it:

- **No cold-start per dish.** A brand-new menu item is scoreable immediately
  from its attributes — no swipe history on it required.
- **Context matters.** The same model also reads time of day, mood, and dietary
  mode, so "comfort food on a cold night" and "something light at noon" pull
  different recommendations.
- **Taste drifts.** Recent swipes are weighted more heavily than old ones
  (~14-day half-life), so the model follows you instead of locking onto what you
  liked a month ago.

The engine underneath is **contextual Thompson Sampling** — a Bayesian bandit
that balances showing you safe bets against exploring new things to learn from.
Validation against a random-pick baseline shows a consistent positive lift in
hit-rate.

## How a session works

```
  Onboarding ──▶  Swipe loop  ──▶  Session complete
  (optional)      (10 swipes)      (start a new one)
```

1. **First visit** — a guest account is created automatically. No signup wall.
2. **Onboarding (optional)** — a few sliders (spicy? sweet? hot or cold?) give
   the model a warm start. Skippable; 5–10 swipes override it anyway.
3. **Swipe loop** — the app shows one dish at a time.
   - **Swipe right (✓)** → the model learns a strong positive, *and* you get a
     list of nearby restaurants serving that dish.
   - **Swipe left (✗)** → a soft "not now" signal. The dish can come back later
     as your taste shifts. No restaurant lookup.
4. **Session complete** — after 10 swipes the session ends with a summary.
   Start a fresh one any time.
5. **Register (optional)** — add an email + password to keep your history and
   model across devices. Your guest swipes carry over — nothing is lost.

Two filters run *before* the model ever sees a dish:

- **Hard safety** — raw fish/egg/meat, unpasteurized dairy, high-mercury fish.
  Always filtered unless you explicitly opt in.
- **Dietary restrictions** — vegetarian, vegan, gluten-free, halal, kosher,
  allergens, etc. Set during onboarding, editable later.

These are deterministic rules — never a model judgment call.

## Tech at a glance

| Part        | Stack                                             |
|-------------|---------------------------------------------------|
| Web app     | React + Vite + TypeScript                         |
| Android app | Capacitor wrap of the same web bundle (no rewrite)|
| API + ML    | Python 3.12 / FastAPI (Thompson Sampling in-proc) |
| Database    | SQLite (local dev) → PostgreSQL (production)      |
| Food tagging| Ollama `gemma4:e2b`, run locally at ingest time   |
| Restaurants | Google Places API                                |
| Deploy      | Docker on a VPS behind Traefik                    |

The same React bundle powers three surfaces: the web app (desktop + iOS via the
browser) and a native **Android** build wrapped with [Capacitor](https://capacitorjs.com/) —
one UI codebase, no native rewrite. See `ANDROID_HANDOFF.md`.

The food catalog ships pre-tagged inside `cravings.db` — 510 dishes across 11
cuisines. The LLM only runs locally when adding new dishes; the live server
never calls it.

## Running it locally

**Prerequisites:** Python 3.12+, Node 20, [uv](https://docs.astral.sh/uv/).
Ollama with `gemma4:e2b` is only needed if you want to tag new dishes.

```bash
# 1. Install
uv sync
cd frontend && npm install && cd ..

# 2. Seed the food catalog (no Ollama needed)
uv run python scripts/run_pipeline.py --seed-only

# 3. Start the backend  → http://localhost:8080
uv run python main.py --db cravings.db

# 4. Start the frontend (second terminal)  → http://localhost:5173
cd frontend && npm run dev
```

Open <http://localhost:5173> — a guest user is created on first visit and
recommendations start immediately.

**Optional env vars** (in `.env`, all optional for local dev):

| Variable                 | Purpose                                          |
|--------------------------|--------------------------------------------------|
| `GOOGLE_PLACES_API_KEY`  | Real nearby-restaurant results (omit → stub mode)|
| `CRAVINGS_SWIPE_SECRET`  | Stable HMAC key so tokens survive restarts       |
| `CRAVINGS_ADMIN_TOKEN`   | Bearer token for the admin batch-load endpoint   |

Run the tests with `uv run pytest tests/ -v`.

## Learn more

- **`docs/QUICKSTART.md`** — fuller setup, including food images and Docker.
- **`docs/PROJECT.md`** — the research write-up: attribute schema, ingestion
  pipeline, and the full Thompson Sampling spec.
- **`docs/CLAUDE.md`** — architecture, per-user model lifecycle, API reference.
- **`docs/CONTEXT.md`** — domain glossary.
- **`docs/adr/`** — architecture decision records.
- **`ANDROID_HANDOFF.md`** — Android (Capacitor) build, env, and sideload guide.
