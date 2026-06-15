# CRAVINGS — Food Preference Engine

**Technical Research Document**

Version 2.0 | April 2026 | Internal Working Document

---

## Executive Summary

Cravings is a swipe-based food recommendation app that learns any user's evolving food preferences using contextual Thompson Sampling. The model updates its belief about food preferences with every swipe, delivering noticeably smarter recommendations within 10–20 interactions.

This document covers three foundational research workstreams: (1) the food attribute schema that enables the model to generalize from sparse swipe data, (2) the data ingestion pipeline that transforms raw restaurant menu items into structured, model-ready feature vectors, and (3) the Thompson Sampling implementation specification.

The key technical insight: this is not a standard collaborative filtering problem. With a single user whose preferences shift over time, the model must learn over food attributes (flavor, texture, temperature, cuisine) rather than food IDs. Each swipe teaches the model about entire categories of food, not just one dish. Thompson Sampling with contextual features (time of day, recency) provides principled exploration-exploitation tradeoff and natural handling of preference drift via exponential decay weighting.

---

## Workstream 1: Food Attribute Schema Design

### 1.1 Why the Schema Is Foundational

The food attribute schema is the single most important design decision in Cravings. Every downstream component depends on it: the LLM tagging pipeline produces these attributes, the Thompson Sampling model learns weights over them, and the recommendation quality is bounded by how well the schema captures what makes foods feel "similar" or "different" to the user.

The schema must satisfy three competing constraints simultaneously. First, it must be rich enough to distinguish meaningfully different foods — pad thai and spaghetti carbonara are both noodle dishes with protein, but they should feel very different to the model. Second, it must be compact enough that 10–20 swipes can teach the model something useful — every dimension added requires more data to learn. Third, it must be reliably producible by an LLM from a restaurant menu item description, which is often vague ("chef's special") or minimal ("chicken tikka masala" with no further detail).

### 1.2 Proposed Schema: 18 Dimensions

The schema is organized into four categories: flavor profile, physical properties, composition, and sensory signals. Each attribute is designed to be independently meaningful to the model and reliably extractable by an LLM.

#### Flavor Profile (6 dimensions)

| Attribute | Range | Description & Rationale |
|-----------|-------|------------------------|
| spice_level | 0.0–1.0 | Heat intensity from none (0) to extremely spicy (1). Spice preference is one of the most dynamic and high-signal dimensions. |
| sweetness | 0.0–1.0 | Sweet taste intensity. Sweet preferences cluster strongly and are highly learnable. |
| sourness | 0.0–1.0 | Sour/acidic taste. Sour preference (citrus, vinegar, pickles) is a strong differentiator between users. |
| savory_umami | 0.0–1.0 | Depth of savory flavor — meaty, brothy, fermented. Distinguishes comfort food from light fare. |
| saltiness | 0.0–1.0 | Salt intensity. A core taste dimension that varies significantly across individuals. |
| bitterness | 0.0–1.0 | Bitter taste component. Bitter sensitivity varies widely between people and is a strong preference signal. |

#### Physical Properties (4 dimensions)

| Attribute | Range | Description & Rationale |
|-----------|-------|------------------------|
| temperature | 0.0–1.0 | Serving temperature from cold/frozen (0) through room temp (0.5) to very hot (1). Temperature preference varies by time of day. |
| texture_softness | 0.0–1.0 | Spectrum from crunchy/crispy (0) to soft/creamy (1). Texture is a major driver of food preferences. |
| sauce_heaviness | 0.0–1.0 | How saucy/wet the dish is, from dry (0) to heavily sauced (1). Distinguishes a grilled chicken breast from chicken tikka masala. |
| richness | 0.0–1.0 | Caloric density and fat content perception. From light/clean (0) to heavy/indulgent (1). |

#### Composition (5 dimensions)

| Attribute | Range | Description & Rationale |
|-----------|-------|------------------------|
| protein_type | categorical | One-hot encoded: chicken, beef, pork, fish, shellfish, egg, tofu/plant, legume, none. Protein preference is a primary differentiator. |
| cuisine_type | categorical | One-hot encoded: American, Mexican, Italian, Chinese, Japanese, Thai, Indian, Korean, Mediterranean, Middle Eastern, other. Enables cuisine-level preference learning. |
| carb_base | categorical | One-hot encoded: rice, noodles/pasta, bread, potato, tortilla, none. Carb preferences are common and type-specific. |
| veggie_density | 0.0–1.0 | How vegetable-forward the dish is. From no vegetables (0) to primarily vegetables (1). |
| dairy_content | 0.0–1.0 | Cheese, cream, milk presence. From none (0) to dairy-heavy (1). Important for preference and dietary filtering. |

#### Sensory Signals (3 dimensions)

| Attribute | Range | Description & Rationale |
|-----------|-------|------------------------|
| smell_intensity | 0.0–1.0 | How aromatic/pungent the dish is. Smell sensitivity varies between individuals and is a strong aversion signal. |
| safety_risk | binary flags | Bitmask for: raw_fish, raw_egg, raw_meat, unpasteurized_dairy, high_mercury_fish. Items with active flags are filtered by safety rules, not used as preference features. |
| nausea_trigger | 0.0–1.0 | Composite score estimating likelihood of triggering nausea based on smell, richness, and common trigger patterns. Useful for users who report sensitivity. |

### 1.3 Total Feature Vector Size

The continuous attributes contribute 14 scalar values. The categorical attributes (protein_type, cuisine_type, carb_base) are one-hot encoded, adding 9 + 21 + 6 = 36 binary dimensions (cuisine_type expanded from 11 → 21 in ADR-0007). The safety_risk flags are binary dimensions used for filtering, not model input. The total food vector is 50 dimensions; context features (time of day, rejection rate, days-since) add another 4, bringing the working dimensionality to 54 (56 with interaction terms enabled). *Context shrank from 12 → 4 when mood + session dietary_mode were dropped in ADR-0013.*

This is within the range where Linear Thompson Sampling can learn effectively from small data.

### 1.4 Schema Validation: Walk-Through

| Attribute | Pad Thai | Carbonara | Caesar Salad | Tikka Masala | Miso Soup |
|-----------|----------|-----------|-------------|-------------|-----------|
| spice_level | 0.3 | 0.1 | 0.0 | 0.6 | 0.0 |
| sweetness | 0.4 | 0.1 | 0.1 | 0.2 | 0.1 |
| sourness | 0.5 | 0.1 | 0.3 | 0.2 | 0.2 |
| savory_umami | 0.6 | 0.8 | 0.3 | 0.7 | 0.9 |
| richness | 0.5 | 0.9 | 0.4 | 0.7 | 0.2 |
| temperature | 0.8 | 0.9 | 0.2 | 0.9 | 0.9 |
| texture | 0.3 | 0.6 | 0.2 | 0.8 | 1.0 |
| sauce | 0.5 | 0.7 | 0.3 | 0.9 | 0.8 |
| protein | shrimp | pork | chicken | chicken | tofu |
| cuisine | Thai | Italian | American | Indian | Japanese |

---

## Workstream 2: Data Ingestion Pipeline

### 2.1 Pipeline Overview

The ingestion pipeline transforms raw food item descriptions (from restaurant menus or manual entry) into structured attribute vectors. Three stages: input capture, LLM tagging, and storage.

### 2.2 Input Sources

#### Pre-loaded Restaurant Menus

For MVP, the primary input method is an admin interface for pasting restaurant menus. The LLM parses freeform text into individual items with names and descriptions. Initial target: 5–10 local restaurants with 15–30 items each (75–300 food items).

#### Manual User Entry

Users can add food items directly: type a dish name (and optionally a description), and the LLM tags it. Handles home-cooked meals, snacks, or items from restaurants not in the pre-loaded set.

### 2.3 LLM Tagging Service

#### Architecture

The tagging service is a Python microservice that accepts a food item name and optional description, calls Ollama (gemma4:e2b) locally, and returns a structured attribute vector. The service runs asynchronously at ingestion time (not recommendation time), so 2–5 seconds per item is acceptable.

#### Model Choice: Ollama + gemma4:e2b

- **Model**: Google Gemma 4 E2B (2.3B effective parameters, 5.1B total)
- **Runtime**: Ollama (local inference, no API costs)
- **Why**: Tagging is a structured extraction task — a small model with few-shot prompting is sufficient. Zero API cost enables unlimited re-tagging during schema iteration. 128K context window supports batch tagging.

#### Prompt Design

Few-shot prompting with 3–5 examples of correctly tagged dishes (covering diverse cuisines). The prompt includes the full schema definition with value ranges and output format specification (JSON). Few-shot over fine-tuning allows rapid schema iteration.

#### Handling Edge Cases

- **Vague descriptions** ("chef's special"): Return partial vector with moderate/neutral values.
- **Fusion dishes** ("Korean-Mexican tacos"): Tag with dominant cuisine; flavor/texture attributes capture actual character.
- **Customizable items** ("build your own bowl"): Tag the default/most common configuration.
- **Beverages and desserts**: Include with appropriate attributes (milkshake = high sweetness, high dairy, cold temperature).

#### Safety Filter

The safety filter is a deterministic, rule-based post-processing step after LLM tagging. Two layers:

**Hard safety flags** (always filtered, not user-configurable):
- `raw_fish`, `raw_egg`, `raw_meat` (unless user explicitly opts in)
- `unpasteurized_dairy`
- `high_mercury_fish` (shark, swordfish, king mackerel, tilefish, bigeye tuna)

**User-configurable dietary restrictions** (set during onboarding, editable):
- `vegetarian`, `vegan`
- `gluten_free`, `dairy_free`
- `halal`, `kosher`
- Allergens: `contains_nuts`, `contains_shellfish`, `contains_soy`, `contains_eggs`

The filter is deterministic — it does not rely on LLM judgment for safety decisions. The LLM tags attributes; the filter makes binary safe/unsafe decisions.

### 2.4 Storage Schema (SQLite → PostgreSQL)

SQLite for local development, PostgreSQL for production. Schema kept SQL-standard for portability.

#### food_items Table

Individual columns per attribute (not JSON blobs). `safety_risk_bitmask` (integer) for fast hard-safety filtering. `dietary_flags_bitmask` (integer) for user-configurable dietary restriction filtering.

#### restaurants Table

Name, location, cuisine type, source type (manual/api).

#### swipe_events Table

food_item_id, direction (right/left), timestamp, context snapshot (time_of_day). Context denormalized — captures state at time of swipe. (`dietary_mode`/`mood` columns deprecated since ADR-0013 — nullable, no longer written.)

### 2.5 Pipeline Flow

```
Food item (name + description)
  → LLM tagging via Ollama/gemma4:e2b (Python)
  → Structured attribute vector (JSON)
  → Safety filter (rule-based, deterministic)
  → SQLite/PostgreSQL storage
```

At recommendation time:
```
Go backend queries eligible food items from DB
  → sends attribute vectors + user context to Python model via gRPC
  → model returns ranked candidates
  → Go serves top candidate to app
```

---

## Workstream 3: Thompson Sampling Implementation Spec

### 3.1 Problem Formulation

Contextual bandit. At each timestep t, observe context vector c_t (time of day, recency) and select food item a_t from candidate pool A_t. User provides feedback r_t (swipe right = 1.0, left = `CRAVINGS_LEFT_SWIPE_REWARD`, default 0.3). Goal: maximize cumulative positive swipes while exploring sufficiently.

Each food item a is represented by attribute vector x_a. Combined feature vector: z_{a,c} = [x_a; c; x_a ⊗ c_selected], where x_a ⊗ c_selected includes selected interaction terms.

### 3.2 Linear Thompson Sampling with Logistic Reward

Bayesian logistic regression model:

```
P(r_t = 1 | z_{a,c}) = σ(wᵀ z_{a,c})
```

#### Algorithm: Per-Swipe Update Cycle

1. Observe context c_t (time_of_day, recency).
2. Construct candidate set A_t: all food items not yet seen in current session, passing safety filter.
3. For each candidate a in A_t, compute feature vector z_{a,c_t}.
4. Sample weight vector w̃ from posterior: w̃ ~ N(μ_t, α² B_t⁻¹).
5. Compute score for each candidate: s_a = σ(w̃ᵀ z_{a,c_t}).
6. Present highest-scoring candidate to user.
7. Observe reward r_t (1.0 = right-swipe, 0.3 = left-swipe by default).
8. Update posterior: B_{t+1} = B_t + z z^T · decay_t, μ_{t+1} = B_{t+1}⁻¹ (B_t μ_t + z r_t · decay_t).

### 3.3 Non-Stationarity: Exponential Decay

Exponential decay on historical swipe contributions. Half-life ~14 days (λ ≈ 0.952 per day). Implemented by periodically recomputing precision matrix B_t with decayed weights.

Half-life is tunable per user. If prediction accuracy drops (hit rate over last N swipes), half-life shortens to adapt faster.

### 3.4 Cold Start Strategy

#### Informative Prior from Onboarding

User selects broad preference categories: craving salty/sweet/sour/spicy, preferred temperature, texture preference, current aversions. These initialize prior mean μ_0 as `μ[attr] = signal × 2.0` (signal in `[-1, 1]`).

**First-card alignment retune (Jun 2026):** the original `prior_strength = 0.5` with `λ₀ = 0.25` and swipe-0 `α = 1.0` let first-session sampling variance (stddev ≈ 2.0 per dim) swamp the seeded prior — a guest who set "spicy" got a mild/sweet first card ~50% of the time. Fixed by raising prior precision `λ₀` 0.25 → **1.0**, lowering swipe-0 `α` 1.0 → **0.3**, and raising `prior_strength` 0.5 → **2.0**. On the real mild-skewed catalog (spice median ~0.10), spicy-guest "mild first card" rate dropped to ~3% with mean top-1 spice ~0.68 (catalog mean ~0.24); neutral sliders stay unbiased. `prior_strength` is capped at 2.0 (not higher) because B-growth makes in-session μ updates shrink fast — a stronger prior would trap a mis-set slider for the whole session.

#### New Item Cold Start

Not a problem for contextual bandits — model predicts based on attribute vectors, not per-item history. Thompson Sampling's exploration handles unfamiliar attribute combinations naturally.

### 3.5 Context Feature Engineering

| Feature | Encoding | Rationale |
|---------|----------|-----------|
| time_of_day | cyclical (2 dims) | Sin/cos encoding of hour (0–23) |
| recent_rejection_rate | scalar (1 dim) | Proportion of left-swipes in last 10 interactions |
| days_since_last_session | scalar (1 dim) | Time gap since last swiping session |

> **Removed (ADR-0013, Jun 2026):** `mood` (one-hot 4) and session `dietary_mode` (one-hot 4) were dropped from the context vector. Diet is now a mandatory hard filter from onboarding restrictions, not a soft signal; mood was an unused ephemeral context. Context shrank 12 → 4 dims.

### 3.6 Exploration Control

Adaptive α schedule (U-shaped — retuned Jun 2026 so a fresh onboarding prior survives card 1):
- **Initial (swipes 0–19):** α = 0.3 (trust the seeded onboarding prior; low variance so card 1 reflects the sliders even on a mild-skewed catalog)
- **Learning (swipes 20–99):** α = 0.5 (onboarding signal spent — explore to refine)
- **Exploitation (swipes 100+):** α = 0.3 (mostly exploit)
- **Drift detection:** If recent_rejection_rate > 0.6, reset α to 0.8

> The early phase was α = 1.0 originally; with `λ₀ = 0.25` that made first-session sampling variance drown the onboarding prior (spicy guest → mild card ~50%). See §3.4.

### 3.7 Performance Budget

- Inference: <50ms per recommendation
- Model update: <100ms per swipe (Sherman–Morrison rank-1 update, O(d²))
- Model state: ~50KB (μ vector + B precision matrix)

---

## Open Questions

- ~~How many food-context interaction terms~~ — **Resolved Apr 2026**: 8 curated terms (`model/features.py:INTERACTION_TERMS`), togglable via `CRAVINGS_USE_INTERACTIONS=1`, default OFF. Synthetic-user A/B (30 runs) shows neutral effect; revisit with real user data.
- ~~Session length (unlimited vs. fixed 10–15 swipes)~~ — **Resolved May 2026**: 10 swipes per session, `CRAVINGS_SESSION_MAX_SWIPES`. `/api/swipe` returns `session_complete: true`; frontend shows end-of-session screen with "New Session".
- ~~Left-swipe signal weighting (equal to right-swipe, or discounted)~~ — **Resolved May 2026**: left-swipe reward = 0.3 (default), `CRAVINGS_LEFT_SWIPE_REWARD`. Soft negative, not hard veto.
- "Not today" vs. "never" distinction in swipe UI (both currently map to reward=0.3)
- ~~Multi-user expansion~~ — **Resolved Apr 2026 (P2)**: per-user (μ, B) stored in users table as BLOBs, bearer token auth, onboarding flow implemented.
- ~~Account persistence / login~~ — **Resolved May 2026 (P9)**: email+password auth, profile stats. See ADR-0003. *(Guest→registered claim from P9 was later removed by ADR-0005 — guests now have no DB row.)*

## P9 User Accounts + Profile Stats (May 2026, completed)

*Note: the guest→registered claim listed below was removed by ADR-0005 (P17, May 2026). `POST /api/auth/register` now always creates a fresh row.*

- **Email + password registration/login** — bcrypt hashing, `POST /api/auth/register|login|logout|password`.
- **Guest → registered claim** *(removed by ADR-0005)* — register while holding a guest token attaches credentials to the existing row; swipe history, model state, dietary flags all preserved. Cold register (no bearer) creates a fresh row.
- **Token rotation** — logout and password change rotate `api_token`; `_get_user` rejects tokens older than `password_changed_at`.
- **Profile stats** — `GET /api/profile/stats` returns cuisine breakdown, avg swipes to right, time-of-day breakdown. Derived live from `swipe_events` join `food_items` — no materialized aggregate table. (mood breakdown removed in ADR-0013.)
- **Frontend** — `AuthMenu` in header (guest: Login/Register; registered: Profile/Logout), `LoginForm`, `RegisterForm`, `ProfilePage` with inline password change. View-state routing in `App.tsx`.
- **Schema** — `email`, `password_hash`, `password_changed_at`, `token_issued_at` added to `users` via idempotent `_migrate()`.
- **Tests** — 13 new auth tests; 161 total passing. See ADR-0003 for auth design decisions.

## P2 Multi-User Auth (Apr 2026, completed)

*Note: the guest-creation endpoint and public-paths list below were superseded by ADR-0005 (May 2026). `POST /api/users` is removed; public auth paths are `/api/auth/register|login`; `/api/recommend` and `/api/swipe` accept optional bearer.*

- **users table**: `api_token` (32-char URL-safe random), dietary/safety bitmasks, model state BLOBs (numpy, allow_pickle=False), onboarding flag.
- **Bearer token auth (FastAPI dep)**: `HTTPBearer` extracts `Authorization: Bearer <token>`, `_get_user` looks up user, injects via `Depends`. *(Historical: original public paths were `/api/health`, `/api/users`.)*
- **Endpoints** *(historical — `POST /api/users` removed)*: `POST /api/users` (create + return token), `POST /api/onboarding` (5-slider prefs), `GET /api/users/me`.
- **Per-user isolation**: separate model state per user; drift signals scoped to user's swipe history; dietary/safety filtering uses user profile bitmasks.
- **Bitmask helpers** (`tagging/safety.py`): dietary + safety bitmask encode/decode functions. `UserFilter.from_user(user)` collapses both into one object for intake use.

## P1 API Hardening (Apr 2026, completed)

- Dietary filter wired into `store.GetEligibleFoodItems` (was previously ignored).
- Session-scoped seen-set on `/api/recommend?session_id=X` prevents repeat items within session; `/api/session/reset` clears it; `/api/swipe` auto-adds.
- Backend computes `recent_rejection_rate` (last 10) + `days_since_last_session` from `swipe_events` — no longer client-passed.
- Decay (`maybe_apply_decay`) wired into gRPC `GetRecommendation` — idempotent, runs at most every 6h.

## P0 Validation Results (Apr 2026)

Sim methodology: synthetic "picky" user (polarized prefs, ~30% base random hit) vs Thompson Sampling model. Compared against random-policy baseline (same seed) over 30 runs × 30 swipes, pool size 10, 50 tagged items.

| Configuration | Model hit rate | Random hit rate | Lift |
|---------------|----------------|-----------------|------|
| Interactions OFF | 62.1% | 57.0% | **+5.1%** |
| Interactions ON  | 62.4% | 57.0% | **+5.4%** |

Findings:
- Bandit clearly beats random — proceed to user-layer / frontend work.
- First-vs-last hit-rate metric (originally targeted) shows ceiling effect with this synthetic user; **model-vs-random is the correct validation metric**.
- Interaction terms neutral here (synthetic user has flat context prefs); re-evaluate with real swipe data before committing.
- Bug found + fixed: pre-fix simulation reused already-swiped items (no seen-set) which masked learning. Real `/api/recommend` has same gap → P1.

## P3 Web Frontend + Restaurant Suggestions (Apr 2026, completed)

- **Platform pivot**: React Native dropped (WSL2 dev environment, no iOS deploy). React + Vite 5 web app instead. Vite 5 required — Vite 9 incompatible with Node 20.18.x on WSL2. *(Update P19, June 2026: Android now ships as a Capacitor wrap of the same Vite bundle — no UI rewrite, web stays the iOS/desktop channel. See ADR-0006 and `ANDROID_HANDOFF.md`.)*
- **Frontend**: `frontend/` — Vite proxy `/api → http://localhost:8080`. *(Historical: originally auto-created a guest user on first visit. Since ADR-0005 (May 2026), guests have no DB row — state lives in localStorage; bearer token issued only on registration.)*
- **Auth flow** *(historical)*: `POST /api/users` returns bearer token → stored in localStorage → sent as `Authorization: Bearer <token>` on all subsequent requests. Single-guest-user pattern for now; multi-user path documented in `CONTEXT.md`. *(Current flow: see ADR-0005.)*
- **Restaurant suggestions**: On right-swipe, Go backend proxies `places:searchText` to Google Places API v1. Food name tried first; falls back to `cuisine_type + " restaurant"` if <3 results. Returns top 5 `{name, address, rating, maps_url}`. API key server-side (`--maps-api-key` flag or `GOOGLE_MAPS_API_KEY` env). Stub (3 fake restaurants) returned when key not set.
- **Location**: Browser `navigator.geolocation` requested on first right-swipe, cached for session. Never prompted on left-swipe.
- **New endpoint**: `GET /api/nearby?food_item_id=X&lat=Y&lng=Z` — authenticated, returns restaurant array.
- **ADR 0001**: Keep Go + Python two-service architecture — browser can't speak gRPC, API key must stay server-side, existing filtering logic retained.
- **Pending (P4)**: Wire real Google Maps API key. **Pending (P5)**: Admin UI + batch restaurant loading.

## MVP Build Order

| Phase | What | Tech | Milestone |
|-------|------|------|-----------|
| Week 1–2 | Schema + tagging pipeline | Python + Ollama/gemma4:e2b | 50 tagged food items with validated vectors |
| Week 2–3 | Thompson Sampling prototype | Python + NumPy | Notebook demo: model learns synthetic preferences in <20 steps |
| Week 3–4 | Go backend + gRPC bridge | Go + gRPC | API endpoints working end-to-end |
| Week 4–5 | React web app (swipe UI) | React + Vite 5 | Swipe UI connected to real model |
| Week 5–6 | Admin UI + restaurant loading | React | 5–10 local restaurants loaded, full flow working |

Critical path: Thompson Sampling prototype (Week 2–3) must validate learning from sparse data before building the app.
