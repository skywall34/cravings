# DESIGN.md — Cravings Frontend Design Guide

## What Is Cravings?

Cravings is a swipe-based food discovery app. Users swipe right on foods they want, left on foods they don't. Every swipe teaches the model — within 10–20 swipes, recommendations feel personal. Right-swipes surface nearby restaurants serving that food.

**Guest mode**: guests have no server-side account. State (session id, dietary prefs, taste prefs, in-session seen items) lives in localStorage. When taste prefs are provided via onboarding sliders, a session-scoped Thompson model is seeded and updated on each swipe — same recommendation quality as registered users within a session, just without cross-session memory. Falls back to global popularity ranking when no prefs provided. Registration creates a fresh server-side account with persistent Thompson Sampling. See [ADR-0005](./adr/0005-stateless-guest-no-db-row.md).

---

## Core User Flow

```
App loads (first visit)
  → no token, no DB row created
  → Onboarding Screen (dietary restrictions + taste sliders for all users)
  → dietary prefs + taste prefs stored in localStorage
  → fetch first recommendation (guest path: session-scoped Thompson model seeded from taste prefs,
                                or global popularity fallback if no prefs provided)

App loads (returning visit, guest)
  → no token; dietary + taste prefs read from localStorage
  → fetch first recommendation (guest path: Thompson model seeded from stored taste prefs)

App loads (returning visit, registered)
  → token found in localStorage
  → fetch first recommendation from model
  (or: token lost → re-login via AuthMenu → token restored → model + history intact)

[ Swipe Screen ]
  Mood selector (top of screen, persistent)
    → comfort | adventurous | light | no preference
  Dietary mode selector (top of screen, persistent)
    → standard | vegetarian | vegan | restricted

[ Swipe Card ]
  ← Drag left / ✗ button    → Left-Swipe ("not today")
                               → model updates (reward=0.3) → next card
  ← Long-press ✗ / "Never" button  → Hard Left-Swipe ("never")
                               → model updates (reward=0.0) → next card
  → Drag right / ✓ button   → Right-Swipe (want this)
                               → request location
                               → fetch nearby restaurants
                               → show Restaurant Panel

[ Restaurant Panel ]
  → shows up to 5 nearby places (name, address, rating, Maps link)
  → dismiss (Enter / button) → next card

[ Session End (after 10 swipes) ]
  → summary: X right-swipes, top cuisine this session
  → "New Session" button → same prefs, continue swiping
  → "Adjust Tastes →" button → back to sliders, full model reset on submit

[ Repeat ]
```

Touch-first design: drag the card left or right to swipe. Buttons (✗/✓/Never) provide an explicit tap alternative.

---

## Architecture (Frontend Only)

| File | Role |
|------|------|
| `App.tsx` | Root — auth init, session state, swipe loop + view-state routing |
| `App.css` | All styles (single stylesheet, no CSS framework) |
| `api.ts` | Fetch wrappers + `FoodItem`, `Restaurant`, `UserInfo`, `SwipeStats` interfaces; auth + stats methods |
| `components/SwipeCard.tsx` | Food card with ✗/✓ buttons; exports `SwipeCardHandle` ref type |
| `components/RestaurantPanel.tsx` | Nearby restaurant list after right-swipe |
| `components/AuthMenu.tsx` | Header dropdown — guest: Log in/Register; registered: Profile/Logout |
| `components/LoginForm.tsx` | Email + password login form |
| `components/RegisterForm.tsx` | Registration form; creates a fresh users row (no guest claim — ADR-0005) |
| `components/ProfilePage.tsx` | Visual taste-profile page: gate card (< 15 swipes) or full insights (persona hero, flavor radar, say-yes gauge, cuisine affinity, mood donut, peak-times chart); inline password change; data export/delete |
| `components/StatsCharts.tsx` | Chart primitives used by ProfilePage: `deriveTasteProfile`, `TastePersonaCard`, `InsightCard`, `FlavorRadar`, `YesRateGauge`, `CuisineAffinity`, `MoodDonut`, `PeakTimesChart` |
| `hooks/useLocation.ts` | Deferred browser geolocation (requested only on right-swipe) |

**Stack**: React + Vite 5 + TypeScript (strict mode), vanilla browser fetch, zero UI framework dependencies. All API calls proxy through Vite (`/api → localhost:8080`) to the FastAPI backend.

**Session**: Each browser tab gets a random `session_id` (ref, not state). The backend uses it to track seen items and avoid repeats within a session.

---

## Visual Design

### Philosophy

Food is visceral, sensory, joyful. The UI should feel warm and appetizing — not clinical or corporate. Think: a cozy restaurant menu meets a modern mobile app. Generous whitespace, rounded corners, rich warm colors.

The experience should be frictionless. One card. Two buttons. No clutter.

---

### Color Palette

Food-forward warm palette. Inspired by spices, citrus, and fresh produce.

| Role | Color | Hex |
|------|-------|-----|
| Primary accent | Burnt orange | `#E85D04` |
| Secondary accent | Saffron yellow | `#F48C06` |
| Positive (right-swipe) | Fresh green | `#16A34A` |
| Negative (left-swipe) | Soft red | `#DC2626` |
| Background | Warm off-white | `#FFF8F0` |
| Card surface | Pure white | `#FFFFFF` |
| Text primary | Near-black | `#1A1A1A` |
| Text secondary | Warm gray | `#6B6B6B` |
| Border / divider | Light warm gray | `#E8E0D8` |
| Shadow | Warm translucent | `rgba(232, 93, 4, 0.08)` |

Avoid cool grays and blues — they feel clinical. Keep the warm beige/orange family throughout.

---

### Typography

| Use | Font | Weight | Size |
|-----|------|--------|------|
| App title | System UI (or Nunito if loaded) | 800 | 2.2rem |
| Food name | System UI | 700 | 1.8–2rem |
| Food subtitle (cuisine, type) | System UI | 400 | 1rem |
| Body / labels | System UI | 400 | 0.9rem |
| Hint text | System UI | 400 | 0.8rem |

Use `system-ui` as the base — fast, native feel. If a web font is added later, prefer a rounded humanist sans-serif (Nunito, Poppins) — warm and approachable, not geometric or corporate.

---

### Layout

Single-column, centered, max-width `480px`. Designed mobile-first but works on desktop.

```
┌──────────────────────────────┐
│                              │
│         🍽 Cravings           │  ← app title, centered
│                              │
│  ┌────────────────────────┐  │
│  │                        │  │
│  │     [Food Image / Icon]│  │  ← food visual (emoji or image)
│  │                        │  │
│  │  Spicy Tuna Roll        │  │  ← food name, large bold
│  │  Japanese · Raw fish    │  │  ← tags: cuisine + attributes
│  │                        │  │
│  │  [Description excerpt] │  │  ← optional 1–2 line description
│  │                        │  │
│  │  ────────────────────  │  │
│  │                        │  │
│  │      ✗        ✓        │  │  ← swipe buttons, large + circular
│  │  [not for me]  [yes!]  │  │
│  │                        │  │
│  └────────────────────────┘  │
│                              │
└──────────────────────────────┘
```

The card should feel like a physical card — white, elevated, rounded corners (20px+), warm shadow.

---

### Swipe Card

- **Shape**: Rounded rectangle, `border-radius: 20px`, card shadow `0 8px 32px rgba(232,93,4,0.10)`
- **Food visual**: 4:3 food photo from Wikimedia when available; falls back to per-cuisine placeholder image; falls back further to a large emoji (🍣 🌮 🍜) centered. Photo fills the full card width with `object-fit: cover`. CC attribution link overlaid in the bottom-left corner.
- **Food name**: 1.8rem bold, dark. The star of the card.
- **Subtitle row**: Cuisine type + key attribute tags (e.g. "Japanese · Spicy · Raw") in soft pill badges
- **Description**: Optional 1–2 sentence excerpt in warm gray. Truncate if long.
- **Buttons**: Two circles, 72px diameter. ✗ on left (red tint), ✓ on right (green tint). Scale up 10% on hover. Disabled state = 40% opacity.

**Drag-to-swipe animation**: The card follows the drag gesture with tilt proportional to horizontal offset (±20° max). NOPE (red, top-left) and LIKE (green, top-right) overlays fade in as the card is dragged, reaching full opacity at ~80px of drag. Past a 120px CSS threshold the card flies off screen; below that threshold it springs back to center with cubic-bezier easing. `touchAction: none` prevents native scroll stealing on mobile.

---

### Restaurant Panel

Appears full-width (replaces card) after a right-swipe.

```
┌──────────────────────────────┐
│  Restaurants near you        │  ← header
│  serving: Spicy Tuna Roll    │
│                              │
│  ┌──────────────────────┐    │
│  │ Sakura Sushi          │    │  ← name
│  │ 123 Main St           │    │  ← address
│  │ ★ 4.5  →  Open Maps  │    │  ← rating + link
│  └──────────────────────┘    │
│  [ repeat per restaurant ]   │
│                              │
│  [ Next food →  ]            │  ← dismiss / continue button
└──────────────────────────────┘
```

- Restaurant cards: light background (`#FFF8F0`), subtle border, 12px radius
- Rating: gold star icon + numeric
- Maps link: opens Google Maps in new tab
- "Next food" button: full-width, burnt orange fill, white text

---

### Loading State

Center-screen spinner. Warm orange color. No skeleton screens needed at this scale.

```css
/* spinner: rotating border, burnt orange */
border-top-color: #E85D04;
```

---

### Empty / Error States

- **No more items**: Card replaced with friendly message — "You've seen everything! Come back later." + "Start over" button.
- **API error**: Inline red message below title. Non-blocking — user can retry.
- **Location denied**: Graceful — restaurant panel shows "Enable location to see nearby spots" instead of crashing.

---

## Interaction Summary

| Action | Trigger | Result |
|--------|---------|--------|
| App opens (first visit) | No token in localStorage | Onboarding screen shown (dietary checkboxes + taste sliders); no DB row created |
| App opens (returning guest) | Dietary + taste prefs in localStorage | First card loaded immediately; session Thompson model seeded from stored taste prefs |
| App opens (registered, token lost) | No token | App falls back to guest mode; re-login via AuthMenu restores registered account |
| Register | AuthMenu → Register, submit form | Fresh `users` row created, new bearer token issued, `onboarding_complete: false` → onboarding screen re-shown pre-filled |
| Register (email exists) | Submit form with taken email | 409 — "log in instead" CTA shown |
| Log in | AuthMenu → Log in, submit form | Registered user's token written to localStorage; subsequent calls use Thompson path |
| Log out | AuthMenu → Log out | Token rotated server-side, localStorage token cleared, app returns to guest onboarding |
| View profile | AuthMenu → Profile & Stats | ProfilePage shown: if < 15 swipes → "keep swiping" gate card; if ≥ 15 → taste persona hero, 3 insight callouts, flavor radar, say-yes gauge, cuisine affinity, mood donut, peak-times chart |
| Change password | ProfilePage → Change password | Old token invalidated, new token written to localStorage |
| Onboarding complete | Submit sliders | `POST /api/onboarding`, model warm-started, first card loaded |
| Mood changed | Selector tap/click | Updates `mood` param on next `GET /api/recommend` |
| Dietary mode changed | Selector tap/click | Updates `dietary_mode` param on next `GET /api/recommend` |
| Left-swipe ("not today") | ✗ button or drag left past threshold | Model updated (reward=0.3), next card |
| Hard left-swipe ("never") | Long-press ✗ or "Never" button | Model updated (reward=0.0), next card |
| Right-swipe | ✓ button or drag right past threshold | Model updated (reward=1.0), location requested, restaurant panel shown |
| Dismiss panel | Button or Enter/→ key | Restaurant panel closed, next card |
| Session end | After 10 swipes | Summary screen: right-swipe count + top cuisine; "New Session" (same prefs) + "Adjust Tastes →" (resets model, back to sliders) |

---

## Planned Features (not yet implemented)

### ~~Onboarding Screen~~ — **Implemented (Jun 2026)**
Shown on first visit (and on registration before first swipe). Dietary restriction checkboxes + taste sliders for all users (guests and registered).

- Sliders for: spice level, sweetness, sourness, texture preference (soft ↔ crunchy), richness
- Range: −1 (dislike) to +1 (love), default 0 (no preference)
- "Start Swiping" CTA — for registered users: calls `POST /api/onboarding`; for guests: stores prefs in `localStorage` and seeds session-scoped Thompson model via `pref_<attr>` query params
- Skip option — proceeds without calling onboarding (falls back to global popularity for guests)
- Backend field: `onboarding_complete` in `GET /api/users/me` — used to decide whether to show on return visits

```
┌──────────────────────────────┐
│        🍽 Cravings            │
│   Let's learn your taste     │
│                              │
│  Spice     ○──────●──────○   │
│  Sweet     ○──●──────────○   │
│  Sour      ○──────────●──○   │
│  Texture   Soft ●──────── Crunchy │
│  Richness  ○──────●──────○   │
│                              │
│       [ Start Swiping ]      │
│         or skip →            │
└──────────────────────────────┘
```

### Mood + Dietary Mode Selectors
Persistent controls above the swipe card. Compact, tap-friendly on mobile.

- **Mood**: pill buttons — "Comfort" | "Adventurous" | "Light" | "Any" (default)
- **Dietary mode**: pill buttons — "Standard" | "Vegetarian" | "Vegan" | "Restricted"
- Active selection: burnt orange fill. Inactive: outline only.
- Changing either selector takes effect on the very next `GET /api/recommend` call (no reload needed).
- State lives in `App.tsx` as React state, passed as query params to `getRecommendation()`.

```
┌──────────────────────────────┐
│  Mood:  [Comfort] Adventurous  Light  Any  │
│  Diet:  [Standard] Vegetarian  Vegan  ...  │
│                              │
│  ┌────────────────────────┐  │
│  │     [Swipe Card]       │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

### "Not Today" vs "Never" Left-Swipe
Two distinct negative signals.

- **"Not today" (existing ✗ / ← key)**: reward=0.3 — "not feeling it right now"
- **"Never" (new)**: reward=0.0 — hard dislike. UI options:
  - Long-press on ✗ button (mobile-friendly)
  - Secondary small button below ✗, labeled "Never"
- Backend: `CRAVINGS_LEFT_SWIPE_REWARD` applies only to "not today". "Never" always sends reward=0.0. API already supports arbitrary reward values — this is a frontend change only; backend `/api/swipe` will need a `reward` field or a `hard_reject: true` flag.

### ~~Session End Summary~~ — **Implemented (Jun 2026)**

- Right-swipe count, not-today count, never count (if any)
- Most common cuisine type this session (derived client-side)
- Like-rate progress bar
- "New Session" button — same prefs, new `session_id`
- "Adjust Tastes →" button — navigates to onboarding sliders (neutral/centered); on submit `POST /api/onboarding` with `reset: true`, which wipes the learned posterior (`mu`, `B`, model `total_swipes`) and re-seeds from new slider values. New `session_id` starts clean.
- Subtitle clarifies: "New Session keeps current preferences · Adjust Tastes resets them"

---

## Future Design Considerations

- ~~**Swipe gesture on mobile**: Touch drag left/right on the card — natural mobile UX~~ — **Implemented (Jun 2026)**. Tinder-style drag with tilt, NOPE/LIKE overlays, 120px fly-off threshold, spring snap-back. Keyboard arrow-key swipe removed (mobile-first).
- **Food imagery**: Replace emoji placeholders with curated food photos
- ~~**Edit dietary restrictions from profile**: `PATCH /api/users/me`~~ — **Implemented (May 2026)**. Partial update, unknown flags → 422.
- **Google OAuth**: Add alongside email/password (ADR-0003 deferred to v2)
- **Dark mode**: Warm dark palette — deep brown/charcoal background, same orange accent
- **Micro-animations**: Card entrance (slide up), swipe exit (slide + fade), button pulse on action
