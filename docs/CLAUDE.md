# CLAUDE.md — Cravings Project

## Project Overview

**Cravings** is a swipe-based food recommendation app that learns each user's evolving food preferences using contextual Thompson Sampling. The model updates with every swipe and should feel noticeably smarter within 10–20 interactions.

Multi-user support is live: each user has their own model state (μ, B matrices) stored as BLOBs in the `users` table, isolated by bearer token auth.

## Architecture

```
┌─────────────────┐     ┌────────────────────────────────────────┐
│  React + Vite    │────▶│  FastAPI (single Python process)       │
│  (Web App)       │◀────│  REST API + Thompson Sampling in-proc  │
└─────────────────┘     └────────────────────────────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  SQLite / Postgres│
                              └──────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ LLM Tagging Svc  │
                              │ (Ollama, async)  │
                              └──────────────────┘
```

### Components

- **React + Vite Web App**: Swipe UI (✗/✓ buttons + ←/→ keyboard), guests swipe with no DB row (state in localStorage), registered users get personalized Thompson recommendations via Bearer token. Right-swipe triggers Google Places restaurant suggestions. Located in `frontend/`.
- **FastAPI App (`main.py`)**: REST API + Thompson Sampling in-process. Bearer-token auth, food item CRUD, Google Places proxy, swipe lifecycle. Blocking ML/SQLite calls wrapped in `asyncio.to_thread`. See ADR-0001 for the Go+gRPC reversal rationale.
- **Recommender seam (`recommender.py`)**: One interface, one adapter per **User Identity** class — `RegisteredRecommender` (DB-backed Local Model via `ModelServer`) and `GuestRecommender` (session-scoped Local Model in `SessionStore`, Global-Popularity fallback). Each owns its full request flow (intake → score → `shape_results` for `recommend()`; verify → model update → session-complete for `record()`). The recommend/swipe routes resolve identity once via `make_recommender()` and never branch on Guest vs Registered again. Reward comes from the shared `swipe.reward_for_direction()`.
- **Swipe module (`swipe/`)**: Owns Right-Swipe / Left-Swipe contract — context capture, HMAC-signed snapshot tokens, denormalized DB write, session seen-set. `SessionStore` also holds per-session guest Thompson models with TTL eviction. `reward_for_direction()` is the single source of the reward policy used by both identities.
- **Model service (`model_server/`)**: In-process Python module (NOT a server). `ModelServer` owns recommend/swipe/status/onboarding business logic; `recommend()` is a pure read of the posterior (impression write aside) and `apply_decay()` is the explicit write-bearing decay step the recommend flow calls first. `UserModelStore` handles thread-safe per-user μ/B BLOB persistence.
- **LLM Tagging Service**: Decomposes food items into 18-dimension attribute vectors via Ollama (gemma4:e2b, local inference). Runs async at ingestion time, not at recommendation time. **Ollama runs local-only** — never on the VPS.
- **Embedding pipeline** (`scripts/embed_items.py`): Computes 768-dim `nomic-embed-text` embeddings for every tagged item, stored as BLOB in `food_items.embedding`. Run locally; ship populated `cravings.db` to VPS. VPS reads BLOBs at startup — no Ollama at request time.
- **SQLite** (local dev) / **PostgreSQL** (production): users, food_items, restaurants, swipe_events, user_item_impressions tables. Schema kept SQL-standard for portability.

## Tech Stack

| Component | Language/Framework | Key Libraries |
|-----------|-------------------|---------------|
| Web app | React + Vite 5 + TypeScript | Strict mode, typescript-eslint with type-aware rules |
| Android app | Capacitor 7 (wraps the web bundle) | @capacitor/{core,android,cli,geolocation,preferences} |
| API + ML | Python 3.12 / FastAPI | uvicorn, httpx, NumPy, SciPy |
| LLM tagging | Python | Ollama (gemma4:e2b, local inference) |
| Database | SQLite (local dev) → PostgreSQL (production) | Individual columns for attribute vectors (not JSON blobs) |
| Containerization | Docker | Single app container |

> **Node version note**: Vite 5 used (not v9) — requires Node ≥ 18, compatible with Node 20.18.x on WSL2. Vite 9 requires Node 20.19+.
>
> **Android toolchain note**: Capacitor pinned to **v7** (CLI v8 requires Node ≥ 22; this env is Node 20). The Android Gradle build needs a **Java-21 toolchain** (Capacitor 7 plugins fail on JDK 17) and a **Linux** Android SDK (`~/Android/Sdk`, SDK 35) — the Windows SDK in `~/.bashrc` is not used. See `ANDROID_HANDOFF.md`.

## ML Model: Contextual Thompson Sampling

### Core Approach

- **Type**: Contextual bandit with Bayesian logistic regression
- **Feature vector**: 62 dimensions baseline (50 food + 12 context). Optional +8 curated interaction terms via `CRAVINGS_USE_INTERACTIONS=1` (70 dims). Food dims grew 40 → 50 when `cuisine_type` expanded 11 → 21 cuisines (ADR-0007).
- **Food attributes**: spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, temperature, texture_softness, sauce_heaviness, richness, protein_type (one-hot), cuisine_type (one-hot), carb_base (one-hot), veggie_density, dairy_content, smell_intensity, safety_risk (filter only), nausea_trigger
- **Context features**: dietary_mode (one-hot, 4: standard/vegetarian/vegan/restricted), time_of_day (sin/cos, 2), mood (one-hot, 4), recent_rejection_rate (scalar), days_since_last_session (scalar)
- **Update**: Online, after every swipe. Sherman–Morrison rank-1 update for O(d²) posterior updates
- **Reward signal**: right-swipe = 1.0, left-swipe = `CRAVINGS_LEFT_SWIPE_REWARD` (default 0.3). Left-swipe is a soft negative, not a hard veto.
- **Exploration**: Thompson Sampling with adaptive α (U-shaped 0.3 → 0.5 → 0.3, with drift detection reset). Swipe-0 α is low (0.3) so a freshly-seeded onboarding prior steers card 1; α opens up at swipe 20 once the onboarding signal is spent.
- **Non-stationarity**: Exponential decay on historical swipes, ~14-day half-life (tunable per user)
- **Cold start**: Informative prior from onboarding preferences (`μ[attr] = signal × 2.0`, `λ₀ = 1.0`) — retuned Jun 2026 so first-session variance doesn't swamp the sliders. See Per-User Model Lifecycle below.
- **Session length**: `CRAVINGS_SESSION_MAX_SWIPES` swipes per session (default 10). Backend returns `session_complete: true` on final swipe; frontend shows end-of-session screen.

### Performance Targets

- Inference: <50ms per recommendation
- Model update: <100ms per swipe
- Model state size: ~50KB (μ vector + B precision matrix)

---

## Per-User Model Lifecycle

This section explains how the model works end-to-end for a single user — from creation through each swipe cycle, and how preferences evolve over time.

> **See also:** [`MODEL_LIFECYCLE_SCENARIOS.md`](./MODEL_LIFECYCLE_SCENARIOS.md) — a visual,
> scenario-by-scenario walkthrough (guest cold start / revisit / reset, registered login /
> onboarding / multi-session / decay) with sequence diagrams and a master "what survives
> what" table.

### State Representation

Each user owns an isolated model stored in the `users` table as two numpy arrays:

| Field | Type | What it stores |
|-------|------|----------------|
| `mu_blob` | `np.save` BLOB | Weight vector μ (62–70 floats) — the model's current best estimate of the user's preferences across all food attributes + context |
| `b_blob` | `np.save` BLOB | Precision matrix B (d×d) — encodes how confident the model is and how correlated different preference signals are |

The model state is loaded from DB into `UserModelStore` (thread-safe cache) on first request, then written back to DB after every swipe. No model state is shared between users.

### Phase 1: User Creation (Zero State)

When `POST /api/auth/register` is called (the only way to create a `users` row; guests have no row — see ADR-0005), the model starts at:
- `μ = 0` (no preference for or against any food attribute)
- `B = λ₀ · I` where `λ₀ = 1.0` (unit-Gaussian isotropic prior — all attributes equally uncertain). *Raised from 0.25 in the Jun 2026 first-card retune; 0.25 made first-session sampling variance (stddev ≈ 2.0/dim) too large to honor seeded onboarding prefs.*

The model explores at this stage but with bounded swipe-0 variance (α = 0.3).

### Phase 2: Onboarding Prior (Optional Warm Start) / Taste Reset

`POST /api/onboarding` accepts slider values for continuous attributes (spice, sweetness, sourness, etc.) in `[-1, 1]`, plus an optional `reset: bool` flag.

**First-time onboarding (`reset` omitted or `false`):** sets μ entries only:
```
μ[attr_idx] = signal × 2.0
```
Strength 2.0 (raised from 0.5 in the Jun 2026 retune) is tuned to steer the **first card** past first-session sampling noise on the real mild-skewed catalog. B is unchanged, so confidence stays low elsewhere and the model still explores. Strength is capped at 2.0 — **not higher** — because B-growth makes in-session μ updates shrink fast (μ plateaus after ~3 contradicting swipes), so a stronger prior would trap a mis-set slider for the whole session rather than letting swipes correct it.

**Taste reset (`reset: true`):** first calls `model.reset()` which wipes the learned posterior back to uninformed prior (`μ = 0`, `B = λ₀·I`, `total_swipes = 0`, `drift_active = False`), then re-seeds μ from the new slider values as above. Triggered from the "Adjust Tastes →" button on the session summary screen. Past `swipe_events` rows are preserved — profile stats (radar, cuisines, lifetime count) survive a taste reset.

### Phase 3: Recommend–Swipe–Update Cycle

Every swipe executes the following sequence:

**3a. Recommend (`GET /api/recommend`)**

The route resolves a `Recommender` via `make_recommender()`; for a registered user `RegisteredRecommender.recommend()` runs:

1. `swipe.build_intake()`: computes `UserFilter` (safety mask + dietary flags), queries eligible items, excludes session seen-set, captures context Snapshot.
2. `ModelServer.apply_decay()` (in thread): explicit temporal-decay step — persists the model only if decay ran. Then `db.get_swiped_cuisines()` fetches which cuisines the user has swiped on (used for stratified cold-start).
3. `ModelServer.recommend()` (in thread): pure read — stratified cold-start or Thompson path, embedding similarity boost.
4. For each candidate, `build_feature_vector(item, context)` assembles 62-dim vector z.
5. Sample w̃ ~ N(μ, α² B⁻¹) — adds randomness proportional to uncertainty.
6. Score each candidate: `score = σ(w̃ᵀ z)`. Return top N.
7. `swipe.shape_results()`: enriches results with metadata, HMAC-seals snapshot → opaque `snapshot_token` (30-min TTL) returned to client.

**3b. Swipe (`POST /api/swipe`)**

1. Client returns `snapshot_token` + `food_item_id` + `direction`.
2. Server verifies HMAC token — rejects if tampered or expired. This ensures the context used for training matches the context that was active when the user made their decision.
3. Reward computed: right-swipe = 1.0, left-swipe = `CRAVINGS_LEFT_SWIPE_REWARD` (default 0.3). Non-zero left reward means the model adjusts rather than strongly penalizes — left-swipe = "not this time", not "never".
4. Model update (Laplace approximation):
   ```
   p   = σ(μᵀ z)               # current prediction
   h   = p(1-p)                 # Hessian contribution (Fisher info)
   B   ← B + h · z zᵀ          # precision matrix update (add certainty)
   μ   ← μ + B⁻¹ z (r - p)     # gradient step toward observed reward
   ```
5. Updated μ and B serialized with `np.save(allow_pickle=False)` and written to `users` table.
6. Swipe event written to `swipe_events` with full denormalized context snapshot.
7. Session seen-set count checked: if `count >= CRAVINGS_SESSION_MAX_SWIPES` (default 10), response includes `session_complete: true`.

### Phase 4: Exploration Schedule

α controls how much the model samples from the tails of the posterior (i.e., how much it explores vs. exploits):

| Swipes | α | Behavior |
|--------|---|----------|
| 0–19 | 0.3 | Low variance — trusts the freshly-seeded onboarding prior so card 1 reflects the sliders |
| 20–99 | 0.5 | Onboarding signal spent — explores to refine learned preferences |
| 100+ | 0.3 | Mostly exploit — recommendations feel stable and personalized |

The schedule is U-shaped by design (retuned Jun 2026): early α was 1.0, but combined with the old `λ₀ = 0.25` that drowned the onboarding prior under sampling noise (spicy guest → mild/sweet first card ~50% of the time). α is computed per-request in `_get_alpha()`. It never persists to DB — it's derived from `total_swipes` and `drift_active`.

### Phase 5: Drift Detection and Recovery

Computed every request from the user's last 10 swipe events (`recent_rejection_rate`):

- If `recent_rejection_rate ≥ 0.6` → `drift_active = True`, α reset to 0.8
- Signals that the user's current preferences diverge from what the model learned (e.g. mood shift, different context)
- Once rejection rate drops below 0.5, `drift_active` clears and α returns to schedule

`drift_active` is persisted in the `users` table so it survives restarts.

### Phase 6: Temporal Decay (Preference Shift)

The recommend flow calls `ModelServer.apply_decay()` on every recommend, which runs `maybe_apply_decay()` (at most once per 6 hours) and persists the bumped `last_decay_ts` only when decay actually ran — that persist is what prevents double-decay after a process restart. It applies exponential decay to B:

```
B ← decay · B + (1 - decay) · λ₀ · I
where decay = 0.5^(elapsed_days / 14)
```

Effect: old swipes gradually contribute less. After ~14 days, their influence halves. This lets the model adapt as user preferences change over time — what the user wanted two weeks ago is down-weighted relative to recent swipes.

### How This Affects Each User Differently

| User Behavior | Model Response |
|---------------|----------------|
| User only swipes right on spicy food | μ[spice_level] increases; model surfaces spicy dishes in exploitation phase |
| User rejects everything for 3 sessions | `recent_rejection_rate` > 0.6 → drift detected → exploration resets → model re-learns |
| User switches to vegetarian mode | `dietary_mode` one-hot changes; context features shift; model updates toward vegetarian-compatible items |
| User is active for 2 months then returns after a gap | `days_since_last_session` increases as scalar context feature; decay has run during absence, reducing confidence in old preferences |
| User completes onboarding with strong spice aversion | μ[spice_level] initialized to −2.0; first card and early recs avoid spicy food. Swipes can still correct it, but the prior is sticky (B-growth shrinks each update) — expect several consistent contradicting swipes before it flips |
| Two users use the same food item | Each sees independent scores — different μ/B means same food can rank #1 for one user and last for another |

### Summary: Key Design Invariants

1. **Filtering before model** — safety/dietary flags remove incompatible items before any ML scoring. Model never sees unsafe items.
2. **Content-based, not collaborative** — model learns over food attributes (spice, texture, cuisine), not food IDs. A new dish is immediately scoreable from its attributes without any swipe history on that dish.
3. **Context round-trip is tamper-proof** — HMAC snapshot ensures training data reflects real context at swipe time.
4. **Decay enables preference drift** — user taste can evolve; model doesn't lock into early signals.
5. **Per-user isolation** — μ/B stored per user in DB; no shared state, no cross-user leakage.

## Food Safety & Dietary Filtering

Filtering is **deterministic and rule-based**, separated from the LLM tagging. Items matching active user flags are never shown. Two layers:

**Hard safety flags** (always filtered, not user-configurable):
- `raw_fish`, `raw_egg`, `raw_meat` (unless user explicitly opts in — e.g., sushi preference)
- `unpasteurized_dairy`
- `high_mercury_fish` (shark, swordfish, king mackerel, tilefish, bigeye tuna)

**User-configurable dietary restrictions** (set during onboarding, editable in profile):
- `vegetarian`, `vegan`
- `gluten_free`, `dairy_free`
- `halal`, `kosher`
- Allergens: `contains_nuts`, `contains_shellfish`, `contains_soy`, `contains_eggs`

**The filter must never be bypassed. It runs after LLM tagging and before any item enters the recommendation pool.**

## Data Pipeline

```
Food item (name + description)
  → LLM tagging (Python, Ollama/gemma4:e2b, few-shot prompt → JSON attribute vector)
  → Safety filter (rule-based, deterministic)
  → DB storage (individual columns per attribute)
```

At recommendation time (registered user — `RegisteredRecommender.recommend()`; guests follow `GuestRecommender` with `build_guest_intake` + Global Popularity / session model):
```
make_recommender(user, ...) → RegisteredRecommender

swipe.build_intake(conn, sessions, user, dietary_mode, mood, hour, session_id)
  → UserFilter.from_user(user) collapses safety mask + dietary restrictions
  → db.get_eligible_food_items(): filters by safety mask, dietary flags, session seen-set
  → swipe.capture(): builds Snapshot (dietary_mode, hour, mood, recent_rejection_rate, days_since_last_session)

asyncio.to_thread(model_server.apply_decay, user_id)   # explicit decay+persist, no-op unless ≥6h
db.get_swiped_cuisines(conn, user_id)
  → passed to ModelServer.recommend() for stratified cold-start routing

asyncio.to_thread(model_server.recommend, user_id, candidates, context, top_n, swiped_cuisines)
  → embedding similarity boost: cosine sim to centroid of user's last 10 right-swiped items
      λ = 0.3 if total_swipes < 20, λ = 0.1 if ≥ 20, λ = 0.0 if no likes yet
  → long-tail injection: every 7th recommendation (after swipe 20) forces least-impressed item

swipe.shape_results(results, candidates, snapshot, base_path)
  → enriches model results with candidate metadata + image URLs
  → seals snapshot as HMAC-signed token (snapshot_token returned to client)
  → client round-trips token on /api/swipe → server verifies + updates model
```

## Database Schema (Key Tables)

### users
- `id`, `name`, `api_token` (UNIQUE, 32-char URL-safe random)
- `email`, `password_hash` (bcrypt), `password_changed_at`, `token_issued_at`. *(Historical: column still nullable for the legacy guest-row schema. Since ADR-0005 (May 2026), every new row has both — guests live in localStorage only.)*
- `dietary_flags_bitmask`, `safety_overrides_bitmask` (integer bitmasks)
- `mu_blob`, `b_blob` (numpy-serialized model state, `np.save` allow_pickle=False)
- `total_swipes`, `last_decay_ts`, `drift_active`, `onboarding_complete`
- `created_at`, `updated_at`

### food_items
- `id`, `name`, `description`, `restaurant_id` (nullable for manual items)
- All 18 schema attributes as individual columns
- `safety_risk_bitmask` (integer for fast hard-safety filtering)
- `dietary_flags_bitmask` (integer for user-configurable dietary restriction filtering)
- `embedding BLOB` — 768-dim `nomic-embed-text` unit vector (`float32.tobytes()`). Computed locally via `scripts/embed_items.py`, never on VPS.
- `created_at`, `updated_at`

### restaurants
- `id`, `name`, `location`, `cuisine_type`, `source_type` (manual/api)

### swipe_events
- `id`, `user_id` (FK), `food_item_id`, `direction` (right/left), `timestamp`
- Context snapshot: `dietary_mode`, `time_of_day`, `mood`, `recent_rejection_rate`, `days_since_last_session`
- Fully denormalized context — captures state at time of swipe, not current state. All five context fields written from the verified Snapshot, never recomputed at training time.

### users (additional columns)
- `recent_likes_json TEXT` — JSON array of last 10 right-swiped item IDs. Used to build embedding centroid for similarity boost.

### user_item_impressions
- `(user_id, food_item_id)` composite PK, `count`, `last_seen`
- Tracks how many times each item has been recommended to each user. Used for long-tail injection (force least-impressed item every 7th recommendation after swipe 20).

## Build Status

| Phase | What | Status |
|-------|------|--------|
| P0 | Food attribute schema + LLM tagging pipeline | ✅ 50 items tagged |
| P0 | Thompson Sampling prototype + sim validation | ✅ +5% lift over random |
| P1 | FastAPI single-process API + hardening (Go+gRPC reversed, see ADR-0001) | ✅ Complete |
| P2 | Multi-user auth, per-user model state | ✅ Complete |
| P3 | React + Vite web app, swipe UI, restaurant suggestions | ✅ Complete |
| P3.1 | Frontend migrated to TypeScript (strict mode, typescript-eslint) | ✅ Complete |
| P4 | Google Places API key + dotenv loading | ✅ Complete |
| P5 | Admin batch restaurant loading | ✅ Complete |
| P6 | Session length (10 swipes, configurable) + left-swipe weighting (reward=0.3) | ✅ Complete |
| P7 | `/api/nearby` end-to-end: live Places key verified, full test coverage (stub + live + error paths) | ✅ Complete |
| P8 | Docker deployment: multi-stage image, GHCR push, Traefik subpath routing on themshin.com | ✅ Live at https://themshin.com/cravings |
| P9 | User accounts: email+password registration/login, guest→registered claim, profile stats page | ✅ Complete |
| P10 | Expand food catalog to 510 items (10× growth), LLM-tagged locally via Ollama | ✅ Complete |
| P11 | Item embeddings (nomic-embed-text, 768-dim), similarity boost, cuisine prior seed, long-tail injection | ✅ Complete |
| P12 | Food images per item: Wikimedia 3-tier pipeline, SwipeCard photo + attribution, cuisine placeholders | ✅ Complete |
| P13 | Sim validation: Thompson Sampling lift ≥ +10pp over random (picky profile, 30 runs × 50 swipes) | ✅ +12.6pp, 71.3% hit rate |
| P14 | `PATCH /api/users/me` — dietary restriction edits from profile page | ✅ Complete |
| P15 | Architecture deepening: `ModelServer`, `RecommendationIntake`, db sub-modules, `UserFilter`, image URL dedup | ✅ Complete |
| P16 | Rate limit `/api/nearby` — in-process token bucket, 429 + `Retry-After`, frontend `RateLimitError` | ✅ Complete |
| P17 | Legal compliance: GDPR Art.17 erasure (`DELETE /api/users/me`), Art.20 portability (`GET /api/users/me/export`), allergen disclaimers, consent banners, location consent gating, guest recommendation variety fixes | ✅ Complete |
| P18 | Guest taste preferences: session-scoped Thompson model seeded from onboarding sliders, per-session locks, TTL eviction, `pref_*` query params on recommend, `taste_prefs` on swipe | ✅ Complete |
| P19 | Android via Capacitor: bundled wrap of the Vite app, async storage seam, native coarse geolocation, backend CORS, debug APK built in WSL (Linux SDK 35 + JDK 21). See ADR-0006 + `ANDROID_HANDOFF.md` | ✅ Code + scaffold + debug APK; device test ✅ (2026-06-13, emulator A/B/D/G); release/Play pending |
| P20 | Profile page redesign: visual taste-profile experience. Backend adds `flavor_profile` (5-axis 0–100 vector) to `/api/profile/stats`. Frontend: new `StatsCharts.tsx` (all-SVG chart primitives), `ProfilePage` recomposed with gate card (< 15 swipes) + full insights above threshold (persona hero, insight callouts, flavor radar, say-yes gauge, cuisine affinity, mood donut, peak-times chart). Additive API change — backward-compatible with shipped APKs | ✅ Complete |
| P21 | Taste preference reset: "Adjust Tastes →" button on session summary screen. `POST /api/onboarding` gains `reset: true` flag — wipes learned posterior (mu, B, total_swipes) before re-seeding from new sliders. Profile lifetime count decoupled to `COUNT(*)` from `swipe_events` (never resets). Android bundle rebuilt via `npm run build:android`. | ✅ Complete |
| P22 | World cuisine expansion: `cuisine_type` enum 11 → 21 (added french, spanish, german, eastern_european, vietnamese, filipino, indonesian, brazilian, caribbean, ethiopian), ~500 new dishes → ~1000 total. Feature dim 52 → 62. One-time per-user model reset (swipe_events preserved); self-heal guard in `UserModelStore._load_or_create` resets stale-dim blobs to fresh prior instead of crashing. Tagger no longer overwrites a restaurant's specific cuisine. ADR-0007. | ✅ Complete |
| P23 | Architecture deepening (Recommender seam): collapsed the duplicated Guest/Registered branching across `/api/recommend` + `/api/swipe` into `recommender.py` (Guest/RegisteredRecommender adapters + `make_recommender()`); routes are thin transport. Fixed guest Left-Swipe reward drift via shared `swipe.reward_for_direction()`. Collapsed `verify`/`verify_guest` into one `_decode_authentic()` + thin binding checks. Extracted hidden decay-persist out of `ModelServer.recommend()` into explicit `apply_decay()`. New `tests/test_recommender.py`. 282 tests passing. | ✅ Complete |
| P24 | Cold-start first-card alignment: onboarding sliders weren't steering the guest's first recommendation (spicy guest → mild/sweet card ~50%). Retuned `model/thompson.py` — `prior_precision` 0.25→1.0, swipe-0 `α` 1.0→0.3 (U-shaped 0.3→0.5→0.3), onboarding `prior_strength` 0.5→2.0. `prior_strength` capped at 2.0 due to sticky-prior (B-growth shrinks in-session μ updates → a stronger prior traps a mis-set slider). New layered tests: `tests/test_recommend_alignment.py` (L2 Monte Carlo), real-catalog `tests/test_recommend_real_data.py` (L4), L3 HTTP cases in `test_api.py`. Real-catalog spicy mild-miss 50%→3%, mean top-1 spice 0.68 vs catalog 0.24. ADR-0008. 294 tests passing. | ✅ Complete |

## Next Steps (for next session)

**P0 deploy fix verified (2026-05-23)**: token-invalidation bug closed. Deploy contract now: rebuild Docker image to ship content (cravings.db baked as `/app/seed/cravings.db` → upserted into volume DB on startup); only `images/` rsyncs. **Never** rsync `cravings.db` again. See `db/seed_sync.py` and `docs/VPS_DEPLOY.md`.

**P12 image backfill complete (2026-05-23)**: 436/510 items (85.5%) have images. Pipeline upgraded to 4 tiers — Wikidata SPARQL → Wikipedia REST disambig → **Wikimedia Commons search (tier-2.5, new)** → plain title. Tier-2.5 is the main driver: full-text search in File namespace with license check, marked `auto`. All 11 cuisine placeholders now deployed. `scripts/smoke_test_vps.sh` extended with image checks (17 checks, all pass). 231 tests passing.

**P19 Android (Capacitor) — code + debug APK done (2026-06-03)**: bundled wrap of the Vite app; iOS/desktop stay on web. Decisions in ADR-0006; full guide in `ANDROID_HANDOFF.md`. Done: async storage seam (`frontend/src/storage.ts`), `apiBase()`/`assetUrl()` in `api.ts` (native hits prod, prefixes relative food-image URLs with prod origin), callback 401, native coarse geolocation, `CORSMiddleware` in `main.py` (localhost origins, `allow_credentials=False`), `frontend/android/` scaffold, debug APK built in WSL. **Build env is Linux-native** (not the Windows SDK in `~/.bashrc`): `~/Android/Sdk` platform/build-tools 35 + portable JDK 21 at `~/jdks` (Capacitor 7 plugins need a Java-21 toolchain). Build constraint: bundled UI means **the API must stay backward-compatible with shipped APKs**. Open next steps:
  1. `adb install` the debug APK to a device; run a full on-device session (grant coarse location, confirm recs + nearby load from prod, token persists across restart).
  2. After deploy, verify CORS preflight: `curl -i -X OPTIONS https://themshin.com/cravings/api/recommend -H "Origin: https://localhost" -H "Access-Control-Request-Method: POST"`.
  3. Signed **release** build (own keystore in a password manager, not the repo) → `./gradlew assembleRelease`.
  4. Play Store internal track (console $25, AAB, store assets, data-safety form, content rating) — deferred, v2.
  5. Deferred: encrypted token storage (currently plaintext Preferences), `cap add ios`, App Links/deep-linking, FCM push.

**Image status (2026-05-23)**:
- `auto`: 74 items with verified images
- `needs_review`: 248 items with tier-3 (plain title) images — usable but unaudited
- no image: 188 items (serve cuisine placeholder in frontend)

Open work:

0. **P0 token-invalidation bug — FIXED + VERIFIED (2026-05-23).** Root cause: VPS deploy used to `rsync cravings.db` over the volume, wiping VPS user rows so any VPS-issued `api_token` returned 401 after the next deploy; frontend `ensureUser()` then skipped guest-mint because localStorage still held the stale token. Fix (both layers shipped):
   - **Frontend** — `frontend/src/api.ts` `request()` detects 401 on any auth'd call, clears `cravings_token`, and reloads. Bootstrap mints a fresh guest. Registered users re-login once.
   - **Backend/deploy** — Dockerfile bakes `cravings.db` to `/app/seed/cravings.db`; `db/seed_sync.py` UPSERTs `food_items` + `restaurants` from seed into the volume DB at startup (`main.py` lifespan). User data on the volume is now never touched by a deploy. `VPS_DEPLOY.md` updated to drop the DB rsync step. Tests: `tests/test_seed_sync.py` (7 cases, 238 total pass).
   - **Post-deploy verification (VPS, 2026-05-23):** `users=16`, `swipes=163` preserved across the deploy; `food_items_with_image=436 / total=510` matches local seed. Smoke tests 17/17.

1. ~~**Simulate P11 improvements**~~ — **DONE (2026-05-24)**. `last_10` hit rate 71.3% (+12.6pp lift over random, 30 runs × 50 swipes, picky profile). Both pass bars cleared.
2. **Re-evaluate interaction terms with real data** — `CRAVINGS_USE_INTERACTIONS=1` neutral on synthetic user; re-run A/B once 200+ real swipes exist.
3. **Open product questions**:
   - "Not today" vs. "never" distinction (both currently reward=0.3)
   - ~~Edit dietary restrictions from profile page (`PATCH /api/users/me`)~~ — **DONE (2026-05-24)**. Partial PATCH, validates unknown flags → 422, 244 tests passing.
   - Rate limiting on `/api/nearby` (no quota check today)
   - Google OAuth (ADR-0003, deferred to v2)

Architectural backlog (no current pain):
- `model_server/` still named "server" — no longer accurate since gRPC removal, but harmless.
- Callers of `db.database` can gradually migrate to direct imports from `db.connection`, `db.users`, `db.food`, `db.swipe_events` sub-modules. (`db/database.py` is a pure re-export hub — deletion test passes; pure churn to remove, so deferred.)
- `get_swipe_stats()` is a 96-line monolith computing all 6 Profile Stats dimensions in one call. Cohesive (one consumer) — split only if a caller ever needs a single dimension.
- Lifespan mutates 6 module globals instead of FastAPI `Depends`. Real coupling, but large blast radius for modest gain — deferred.
- ~~Guest vs Registered recommend/swipe branching duplicated across both routes~~ — **RESOLVED**: collapsed behind the `Recommender` seam (`recommender.py`); routes are now thin transport. This also fixed the guest Left-Swipe reward drift (was hardcoded `0.0`, now shares `reward_for_direction()` → honors `CRAVINGS_LEFT_SWIPE_REWARD` + `never`).

## Key Design Decisions

1. **Content-based learning over food attributes, not food IDs** — enables generalization from sparse single-user data
2. **LLM for food knowledge, model for preference learning** — the LLM tags attributes at ingestion; the bandit model only sees attribute vectors at recommendation time
3. **Filtering separated from LLM** — hard safety flags + user dietary restrictions are deterministic rule-based, never subject to model uncertainty
4. **Single Python process for API + ML** — Go+gRPC split reversed (ADR-0001); FastAPI + `asyncio.to_thread` removes serialization overhead and operational complexity for single-host deployment
5. **Swipe data denormalized with HMAC-signed context snapshot** — context captured at recommend-time, sealed as opaque token, round-tripped through client, verified on swipe. Tamper-proof and ensures training data reflects the context at the time of the swipe
6. **Exponential decay for non-stationarity** — recent swipes weighted more heavily, with adaptive half-life
7. **SQLite everywhere for now** — schema kept SQL-standard (no MySQL-specific types/syntax) so Postgres migration stays open as future option, but not pursued until SQLite hits a real limit.

## Project Structure

```
cravings/
├── frontend/               # React + Vite + TypeScript web app (+ Capacitor Android shell)
│   ├── src/
│   │   ├── App.tsx         # Root: auth init, session state, swipe loop
│   │   ├── App.css         # All styles
│   │   ├── api.ts          # fetch wrappers + interfaces; apiBase() (web=/cravings, native=prod), assetUrl() (native prefixes relative img URLs with prod origin), async token, callback 401
│   │   ├── storage.ts      # Storage seam: async get/set/remove — web→localStorage, native→@capacitor/preferences
│   │   ├── vite-env.d.ts   # Vite client types + VITE_API_BASE_URL (set only in the Capacitor build)
│   │   ├── components/
│   │   │   ├── SwipeCard.tsx       # Food card with ✗/✓/Never buttons; cuisine image with emoji fallback; AllergenNote
│   │   │   ├── RestaurantPanel.tsx # Nearby restaurants after right-swipe; AllergenNote
│   │   │   ├── AuthMenu.tsx        # Header dropdown: guest→Login/Register, registered→Profile/Logout
│   │   │   ├── LoginForm.tsx       # Email+password login
│   │   │   ├── RegisterForm.tsx    # Registration + legal consent line (Terms / Privacy links)
│   │   │   ├── ProfilePage.tsx     # Visual taste profile: gate card (<15 swipes) or full insights (persona, radar, gauge, affinity, donut, peak-times); password change; data export/delete (GDPR)
│   │   │   ├── StatsCharts.tsx     # Chart primitives (all SVG, no chart lib): deriveTasteProfile, TastePersonaCard, InsightCard, FlavorRadar, YesRateGauge, CuisineAffinity, MoodDonut, PeakTimesChart
│   │   │   ├── AllergenNote.tsx    # Inline amber allergen disclaimer (best-effort, not certified)
│   │   │   ├── ConsentBanner.tsx   # First-load cookie/session consent banner (storage-seam-persisted)
│   │   │   └── LegalPages.tsx      # Full Privacy Policy + Terms of Service screens
│   │   └── hooks/
│   │       └── useLocation.ts      # Geolocation: native→@capacitor/geolocation (coarse), web→navigator.geolocation
│   ├── capacitor.config.ts # appId com.themshin.cravings, webDir dist, androidScheme https
│   ├── .env.capacitor      # VITE_API_BASE_URL=https://themshin.com/cravings (Capacitor build only; web build untouched)
│   ├── android/            # Generated Capacitor Android project (committed); coarse-location manifest, targetSdk 35
│   ├── tsconfig.json       # strict mode, bundler resolution, react-jsx
│   └── vite.config.ts      # base /cravings/ (web); Android build overrides via --base /. Proxy /api → localhost:8080
├── db/
│   ├── schema.sql          # SQLite/PostgreSQL schema
│   ├── connection.py       # get_connection, db_connection, init_db, _migrate
│   ├── users.py            # user CRUD, auth, password, recent_likes; delete_user (GDPR Art.17)
│   ├── food.py             # food items, restaurants, embeddings, impressions
│   ├── swipe_events.py     # swipe recording, stats, swiped-cuisine history; delete_swipes_for_user,
│   │                       #   delete_impressions_for_user, get_all_swipes_for_user (GDPR)
│   └── database.py         # re-export hub — all callers unchanged; prefer direct sub-module imports
├── tagging/
│   ├── prompt.py           # Few-shot prompt template for Ollama/gemma4:e2b
│   ├── client.py           # Ollama API client, response parsing/validation
│   └── safety.py           # Safety & dietary bitmask computation; UserFilter dataclass
├── model/
│   ├── features.py         # Feature engineering: one-hot encoding, context vectors (62-dim total)
│   └── thompson.py         # Contextual Thompson Sampling with Bayesian logistic regression
├── scripts/
│   ├── seed_data.py        # ~73 restaurants, ~1000 food items across 21 cuisines
│   ├── run_pipeline.py     # Seed DB → tag via Ollama → store results
│   ├── simulate.py         # Synthetic user simulation for model validation
│   └── fetch_food_images.py  # Wikimedia image backfill + manual curation CLI
├── tagging/
│   └── wikimedia.py        # 3-tier image lookup: Wikidata SPARQL → Wikipedia REST → plain title
├── model_server/
│   ├── model_service.py        # UserModelStore — thread-safe per-user μ/B BLOB cache
│   └── recommendation_service.py  # ModelServer — apply_decay (explicit decay+persist), recommend (pure read), record_swipe, get_status, set_onboarding
├── swipe/
│   ├── snapshot.py             # Snapshot dataclass, capture(), seal(); _decode_authentic() + verify()/verify_guest() (HMAC-SHA256, 30-min TTL)
│   ├── session.py              # SessionStore: per-session locks, seen-set, guest ThompsonSamplingModel storage, TTL eviction
│   ├── recorder.py             # record_swipe(): full Right-Swipe / Left-Swipe contract; reward_for_direction() (shared reward policy)
│   └── intake.py               # build_intake()/build_guest_intake(): snapshot + filtering; shape_results() + add_image_urls()
├── recommender.py              # Recommender seam: Guest/RegisteredRecommender adapters + make_recommender() factory (identity resolved once; routes are thin transport)
├── main.py                     # FastAPI app: routes, lifespan, auth dep, Places proxy, StaticFiles SPA mount
├── rate_limit.py               # Generic per-key token-bucket limiter (asyncio.Lock, injectable clock, lazy sweep)
├── Dockerfile                  # Multi-stage: node builds frontend/dist, python runtime serves both
├── docker_build.sh             # Build + push to ghcr.io/skywall34/cravings:prod
├── .dockerignore
├── VPS_DEPLOY.md               # Step-by-step VPS setup (for manual execution on Hostinger)
├── docs/
│   └── adr/
│       └── 0001-keep-go-python-architecture.md  # Note: ADR title superseded — see ADR for the reversal
├── CONTEXT.md                  # Domain glossary (Swipe Session, Right-Swipe, Restaurant Suggestion, etc.)
├── images/
│   ├── food/                   # {slug}-{hash}-400.webp + {slug}-{hash}-800.webp  (gitignored)
│   └── cuisines/               # american.webp, italian.webp, … (gitignored; auto-fetched via --placeholders)
├── tests/
│   ├── mocks/
│   │   ├── ollama_responses.py
│   │   └── wikimedia_responses.py   # Canned Wikimedia API responses for image pipeline tests
│   ├── test_api.py             # FastAPI route tests (httpx ASGITransport); guest taste pref + L3 first-card alignment over HTTP
│   ├── test_recommender.py     # Recommender seam: Guest/Registered adapters direct (no ASGI); reward-policy regression, identity factory
│   ├── test_recommend_alignment.py  # L2: Monte-Carlo slider→first-card alignment (in-process, synthetic pools)
│   ├── test_recommend_real_data.py  # L4: slider→first-card alignment on the real cravings.db catalog (read-only; skips if DB absent)
│   ├── test_session_store.py   # SessionStore unit tests: model storage, TTL eviction, per-session lock isolation
│   ├── test_auth.py            # Auth + profile stats (incl. flavor_profile) + GDPR delete/export + location audit (27 tests)
│   ├── test_database.py
│   ├── test_safety.py
│   ├── test_tagging.py
│   ├── test_prompt.py
│   ├── test_features.py
│   ├── test_thompson.py
│   ├── test_model_service.py   # ModelServer + UserModelStore direct tests; stratified cold-start
│   ├── test_wikimedia.py       # Wikimedia lookup tiers + license filter tests
│   ├── test_image_pipeline.py  # End-to-end: tier hits, dry-run, manual curation
│   └── test_image_serving.py   # StaticFiles mount + Cache-Control header tests
└── pyproject.toml
```

## Development Commands

```bash
# ── Python (run from project root) ──────────────────────────────────────────

# Run Python tests
uv run pytest tests/ -v

# Seed database only (no tagging)
uv run python scripts/run_pipeline.py --seed-only

# Seed + tag all items (requires Ollama running with gemma4:e2b)
uv run python scripts/run_pipeline.py

# Tag only (existing untagged items)
uv run python scripts/run_pipeline.py --tag-only

# Embed tagged items missing embeddings (requires nomic-embed-text pulled in Ollama)
uv run python scripts/run_pipeline.py --embed-only

# ── Food images (P12) ────────────────────────────────────────────────────────

# Full backfill: fetch images for all items without one (~30 min, ~85% hit rate via 4-tier pipeline)
uv run python scripts/fetch_food_images.py

# Dry-run first (no writes, shows what would happen)
uv run python scripts/fetch_food_images.py --dry-run

# Force re-fetch for items that already have images
uv run python scripts/fetch_food_images.py --force

# Fetch per-cuisine placeholder images for the cuisines/ directory
uv run python scripts/fetch_food_images.py --placeholders

# Manually curate images with a sidecar attribution JSON
# (put {slug}.jpg + {slug}.attribution.json in images/manual/)
uv run python scripts/fetch_food_images.py --manual

# Audit results after backfill
python3 -c "
import sqlite3; conn = sqlite3.connect('cravings.db')
rows = conn.execute('SELECT image_review_status, COUNT(*) c FROM food_items GROUP BY 1').fetchall()
total = conn.execute('SELECT COUNT(*) FROM food_items WHERE image_slug IS NOT NULL').fetchone()[0]
print(f'Items with images: {total}'); [print(f'  {r[0]}: {r[1]}') for r in rows]
"
# or directly:
uv run python scripts/embed_items.py
uv run python scripts/embed_items.py --validate   # spot-check nearest neighbors

# Run Thompson Sampling simulation (requires seeded+tagged DB)
uv run python scripts/simulate.py --swipes 50 --pool 10

# A/B model vs random policy (recommended validation metric)
uv run python scripts/simulate.py --swipes 30 --runs 30 --compare --profile picky

# ── FastAPI app ──────────────────────────────────────────────────────────────

# Run app (port 8080)
uv run python main.py --db cravings.db

# With Google Places API key (enables real Places results; omit for stub mode)
uv run python main.py --db cravings.db --maps-api-key YOUR_KEY
# or set GOOGLE_PLACES_API_KEY in .env (auto-loaded via python-dotenv)

# Required env vars in .env (all three needed for production):
#   GOOGLE_PLACES_API_KEY=...         — enables real /api/nearby results
#   CRAVINGS_SWIPE_SECRET=...         — stable HMAC key; tokens survive restarts
#   CRAVINGS_ADMIN_TOKEN=...          — bearer token for POST /api/admin/batch
#
# Optional tuning:
#   CRAVINGS_SESSION_MAX_SWIPES=10    — swipes per session before session_complete (default 10)
#   CRAVINGS_LEFT_SWIPE_REWARD=0.3    — reward signal for left-swipes; 0=hard veto, 1=same as right (default 0.3)
#   CRAVINGS_IMAGES_ROOT=./images     — filesystem root for food+cuisine WebP images (default ./images)
#   CRAVINGS_NEARBY_BURST=10          — /api/nearby token bucket capacity per user (default 10)
#   CRAVINGS_NEARBY_REFILL_SECONDS=30 — seconds to refill 1 token (default 30 → 120/hr sustained per user)

# ── Frontend ─────────────────────────────────────────────────────────────────

# Dev server with HMR (proxies /api → localhost:8080)
# Note: dev script passes --base / so BASE_URL=/ and API calls go to /api/...
# Production build uses base: '/cravings/' (vite.config.ts) → BASE_URL=/cravings/
cd frontend && npm run dev   # → http://localhost:5173

# Type-check (no emit)
cd frontend && npm run typecheck

# Production build
cd frontend && npm run build

# Lint (typescript-eslint, type-aware rules)
cd frontend && npm run lint

# ── Android (Capacitor) ──────────────────────────────────────────────────────
# Requires (see ANDROID_HANDOFF.md): Linux Android SDK 35 at ~/Android/Sdk,
# JDK 21 at ~/jdks (Capacitor 7 plugins need a Java-21 toolchain), and
# frontend/android/local.properties → sdk.dir. ~/.bashrc exports JAVA_HOME +
# ANDROID_SDK_ROOT so the commands below need no inline env.

# Build the Android web bundle (vite --mode capacitor --base /) and sync to native
cd frontend && npm run build:android

# Build the installable debug APK  → app/build/outputs/apk/debug/app-debug.apk
cd frontend/android && ./gradlew assembleDebug --no-daemon

# Sideload to a device (adb alias → Windows adb.exe talking to a USB device)
adb devices
adb install -r '\\wsl.localhost\Ubuntu\home\mshin\cravings\frontend\android\app\build\outputs\apk\debug\app-debug.apk'

# Open the project in Android Studio
cd frontend && npm run open:android

# ── Full stack (2 terminals) ──────────────────────────────────────────────────
# Terminal 1: uv run python main.py --db cravings.db
# Terminal 2: cd frontend && npm run dev

# ── Docker (production image) ─────────────────────────────────────────────────

# Build image
docker build -t cravings:prod .

# Run locally (mirrors production)
docker run -p 8080:8080 \
  -e BASE_PATH=/cravings \
  -e CRAVINGS_DB=/app/cravings.db \
  -e CRAVINGS_IMAGES_ROOT=/app/images \
  -v $(pwd)/cravings.db:/app/cravings.db \
  -v $(pwd)/images:/app/images:ro \
  -v $(pwd)/.env:/app/.env \
  cravings:prod
# → http://localhost:8080/cravings/

# Push to GHCR (triggers Watchtower redeploy within ~30s)
./docker_build.sh <GITHUB_PAT>

# ── API reference ─────────────────────────────────────────────────────────────
#
# Public (no auth):
#   GET  /api/health
#   POST /api/auth/login  {"email":"...","password":"..."}
#                    → {id, name, email, api_token, is_registered, onboarding_complete}
#   POST /api/auth/register  {"email":"...","password":"...","name":"..."}
#                    → 201 {id, name, email, api_token, is_registered:true, onboarding_complete:false}
#                      Always creates a fresh row (no guest claim — ADR-0005). Email conflict: 409.
#
# Guest-or-auth (optional bearer — guests pass dietary + taste prefs as query/body params):
#   GET  /api/recommend?session_id=X&dietary_restrictions=vegan&safety_overrides=raw_fish
#                       &excluded_ids=1&excluded_ids=2&mood=...&dietary_mode=...&top_n=1&hour=...
#                       &pref_spice_level=0.8&pref_sweetness=-0.5&pref_sourness=0.0&...
#     No bearer → guest path: if pref_* params present, seeds/retrieves session-scoped
#                 ThompsonSamplingModel (stored in SessionStore, evicted after 1h idle);
#                 scores via asyncio.to_thread(model.score_items). Falls back to global
#                 popularity (score=0.0) when no prefs. Snapshot binds to session_id, no DB writes.
#     With bearer → registered path: Thompson sampling, snapshot binds to user_id,
#                   dietary loaded from users row (pref_* query params ignored).
#   POST /api/swipe  {"food_item_id":1,"direction":"right","session_id":"X","snapshot_token":"...",
#                      "dietary_restrictions":[...],"safety_overrides":[...],
#                      "taste_prefs":{"spice_level":0.8,...}}
#                    → {success, total_swipes, session_complete}
#                      Guest path: snapshot verified by session_id, marks seen, updates session
#                      Thompson model via asyncio.to_thread(model.record_swipe), NO swipe_events
#                      write, total_swipes=0. Seeds model from taste_prefs if not yet initialized.
#                      Registered path: full model update + swipe_events insert (existing flow).
#
# Authenticated (Authorization: Bearer <token>):
#   GET  /api/users/me  → {id, name, email, is_registered, onboarding_complete,
#                          dietary_restrictions, safety_overrides}
#   PATCH /api/users/me  {"dietary_restrictions":["vegetarian","gluten_free"],
#                         "safety_overrides":["raw_fish"]}
#                    → updated profile (same shape as GET). Partial update — omit field to keep unchanged.
#                      Unknown flag name → 422.
#   DELETE /api/users/me → 204 No Content. Hard-deletes user row + all swipe_events + impressions.
#                          Token immediately invalid (stateful DB lookup returns nothing). GDPR Art.17.
#   GET  /api/users/me/export → JSON download (Content-Disposition: attachment).
#                          Fields: account {name,email,created_at}, preferences, swipe_history [], stats.
#                          GDPR Art.20 portability.
#   POST /api/auth/logout           → rotates token server-side (old token invalid)
#   POST /api/auth/password  {"old_password":"...","new_password":"..."}
#                    → {success, api_token}  (new token — update localStorage)
#   GET  /api/profile/stats → {total_swipes, cuisine_breakdown, avg_swipes_to_right,
#                              mood_breakdown, hour_breakdown, drift_active,
#                              flavor_profile: {Spicy,Rich,Umami,Fresh,Sweet} (0–100 int each;
#                                all-zero when user has no right-swipes)}
#   POST /api/onboarding  {"preferences":{"spice_level":0.8,"sweetness":-0.5,...}, "reset": false}
#                    (registered-only — persists Thompson prior to DB; guests onboard client-side,
#                     prefs stored in localStorage + sent as pref_* params on /api/recommend)
#                    reset=true: wipe posterior (mu=0, B=prior·I, total_swipes=0) then re-seed.
#                    Client always sends reset=true; skip path (onSkip) does NOT call this endpoint.
#   POST /api/session/reset  {"session_id":"X"}
#
# Guest-or-auth (optional bearer):
#   GET  /api/nearby?food_item_id=1&lat=37.77&lng=-122.41
#        → [{name, address, rating, maps_url}]  (stub when no API key)
#        → 429 {detail:{detail:"rate limited", retry_after:N}} + Retry-After header
#          when per-user/per-IP token bucket empty (CRAVINGS_NEARBY_BURST / _REFILL_SECONDS).
#          Guests rate-limited by approximate location bucket (lat/lng truncated to 2dp).
#          Skipped in stub mode (no API cost).
#          lat/lng are NOT stored — used only for this Places API call (privacy policy commitment).
#   GET  /api/food-items
#   GET  /api/food-items/{id}
#   GET  /api/restaurants
#   GET  /api/model/status
#
# Admin (Authorization: Bearer <CRAVINGS_ADMIN_TOKEN>):
#   POST /api/admin/batch  {"restaurants":[{name,location,cuisine_type,source_type},...],
#                           "food_items":[{name,description,restaurant_name?},...]}
#                          → 202 {restaurants_inserted, food_items_inserted, tagging:"queued"}
#                          Inserts items as 'pending', fires async LLM tagging in background.
```

## Open Questions (To Resolve During Development)

- ~~How many food-context interaction terms to include~~ — **Resolved (Apr 2026)**: 8 curated terms implemented in `model/features.py:INTERACTION_TERMS` (spice×mood, temp×time, dairy×vegan, etc.). Toggle via `CRAVINGS_USE_INTERACTIONS=1`. **Default OFF** — synthetic-user A/B (30 runs) showed neutral effect (+5.1% off vs +5.4% on, within noise) since synthetic user has flat context preferences. Re-evaluate with real user swipe data.
- ~~Session length (unlimited vs. fixed 10–15 swipes)~~ — **Resolved (May 2026)**: 10 swipes per session, configurable via `CRAVINGS_SESSION_MAX_SWIPES`. `/api/swipe` returns `session_complete: true` on final swipe; frontend shows end-of-session screen.
- ~~Left-swipe signal weighting (equal to right-swipe, or discounted)~~ — **Resolved (May 2026)**: left-swipe reward = 0.3 (default), configurable via `CRAVINGS_LEFT_SWIPE_REWARD`. Treats left-swipe as "not now" rather than hard veto.
- LLM tagging quality with gemma4:e2b (monitor and evaluate, upgrade to larger model if needed)
- ~~Edit dietary restrictions from profile page~~ — **Resolved (May 2026)**: `PATCH /api/users/me` implemented. Partial update semantics, validates unknown flags (422), leaves `onboarding_complete` untouched.
- "Not today" vs. "never" distinction in swipe UI (both currently map to reward=0.3; would need separate reward values or a UI affordance to distinguish)

## Validation Status

- **P0 sim validation (Apr 2026)**: Thompson Sampling beats random policy by **+5% mean hit-rate** over 30 runs × 30 swipes (picky synthetic user, 50 items, pool=10). Not the +20% improvement first→last targeted in PROJECT.md — that metric showed ceiling effect. Random-policy baseline lift is the load-bearing measure.
- **P13 sim validation (May 2026, 510-item catalog + embeddings)**: `last_10` hit rate **71.3%** (target ≥ 60% ✅), lift over random **+12.6pp** (target ≥ +10pp ✅). 30 runs × 50 swipes, picky profile. Model won 27/30 runs.
- Sim flags: `--compare` runs both policies same seed, `--profile picky|easy`, `--policy model|random`.
- **P24 first-card alignment (Jun 2026, ADR-0008)**: onboarding-slider → first-recommendation alignment. Synthetic uniform pools: spicy-slider top-1 alignment **49% → 94%** across all 5 sliders (neutral stays ~50%, unbiased). Real `cravings.db` catalog (spice median 0.10): spicy-guest "mild first card" rate **50% → 3%**, mean top-1 spice 0.68 vs catalog mean 0.24. Layered tests L2 (`test_recommend_alignment.py`) / L3 (`test_api.py`) / L4 (`test_recommend_real_data.py`).
- **P25 model accuracy SLAs (Jun 2026, ADR-0009)**: two gated SLAs driven through the Recommender seam on the real catalog. **Gate 1 (cold start, fast, default suite)** — dietary filter never leaks an ineligible item into recommendations, and a spicy slider still steers the first card spicier than the vegetarian-pool mean under a `vegetarian` filter (sliders ∘ filters compose). **Gate 2 (learning, `@pytest.mark.slow`, opt-in via `pytest -m slow`)** — swiping converges and beats random; bars `last_10 ≥ 60%` and `lift ≥ +10pp` (mean over runs, margin below baseline). Observed (deep sweep, 30 runs × 50 swipes, picky, both adapters, model won 30/30): guest **84.0% / +32.5pp**, registered **87.7% / +33.8pp**. Deep sweep `scripts/sla_eval.py`; gate `tests/test_model_sla.py`. Skips if `cravings.db` absent.

## P1 API Hardening (Apr 2026, completed)

- `store.GetEligibleFoodItems` now applies `dietary_restrictions` (positive flags = item must have bit; `contains_*` = item must NOT have bit).
- `GetEligibleFoodItemsExcluding(safetyMask, restrictions, excludeIDs)` — used by recommend handler with session seen-set.
- `SessionStore` (in-memory, `sync.Mutex`-guarded): `/api/recommend?session_id=X` excludes items already swiped in session; `/api/swipe` adds to set; `/api/session/reset` clears.
- Backend auto-computes `recent_rejection_rate` (last 10 swipes) and `days_since_last_session` from `swipe_events` table; clients no longer pass these in query params.
- `model.maybe_apply_decay()` called on each `GetRecommendation` (idempotent — no-op unless ≥6h elapsed since `last_decay_ts`).

## P2 Multi-User Auth (Apr 2026, completed)

*Note: the guest-row contract described below was superseded by ADR-0005 (May 2026) — guests now have no DB row. `POST /api/users` is removed; `/api/recommend` and `/api/swipe` use optional-bearer auth.*


- **users table**: `api_token` (32-char URL-safe random), `dietary_flags_bitmask`, `safety_overrides_bitmask`, `mu_blob`/`b_blob` (model state), `total_swipes`, `last_decay_ts`, `drift_active`, `onboarding_complete`.
- **swipe_events.user_id**: All swipes now scoped to a user.
- **Bearer token auth (FastAPI dep)**: `HTTPBearer` extracts `Authorization: Bearer <token>`, `_get_user` looks up user, injects via `Depends`. Public paths: `/api/health`, `/api/users`.
- **Per-user model state**: `UserModelStore` (thread-safe) loads/persists `ThompsonSamplingModel` from DB BLOBs using `np.save`/`np.load` (allow_pickle=False).
- **Endpoints**: `POST /api/users`, `GET /api/users/me`, `POST /api/onboarding`, `GET /api/recommend`, `POST /api/swipe`, `POST /api/session/reset`.
- **Bitmask helpers** (`tagging/safety.py`): `dietary_list_from_bitmask`, `safety_list_from_bitmask`, `user_safety_mask`, `compute_dietary_bitmask`, `compute_safety_bitmask`. `UserFilter.from_user(user)` collapses safety mask + dietary restrictions into one object — used by `swipe.build_intake`.

## P4 + P5 (May 2026, completed)

- **dotenv**: `python-dotenv` added; `load_dotenv()` called at startup in `main.py`. All secrets loaded from `.env` automatically.
- **Google Places API (P4)**: env var renamed `GOOGLE_MAPS_API_KEY` → `GOOGLE_PLACES_API_KEY` throughout. `PlacesAdapter` now live when key present.
- **CRAVINGS_SWIPE_SECRET**: stable secret in `.env` — snapshot tokens survive backend restarts.
- **Admin batch route (P5)**: `POST /api/admin/batch` authenticated via `CRAVINGS_ADMIN_TOKEN`. Accepts JSON with `restaurants` + `food_items` arrays (supports `restaurant_name` lookup for cross-linking). Inserts to DB and fires async LLM tagging (`asyncio.create_task`). Items stay `pending` on Ollama failure for later retry via `--tag-only` script.

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/` in this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.

### Rerun Claude

Read the attached cravings.zip and the README inside.
Implement: the designs in this project

claude --resume c78e9cc6-83e1-4a7c-b691-6a0071b917cf
