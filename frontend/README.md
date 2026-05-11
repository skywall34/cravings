# Cravings Frontend

React + Vite + TypeScript SPA. Swipe UI for the food preference engine.

## Stack

- React 19 + TypeScript (strict mode)
- Vite 5 (required — Vite 9 incompatible with Node 20.18.x on WSL2)
- No routing library — screen state machine in `App.tsx` (`onboarding | swipe | restaurants | summary`)

## Dev

```bash
npm install
npm run dev       # http://localhost:5173 — proxies /api → localhost:8080
npm run typecheck
npm run lint
npm run build     # production build with base=/cravings/
```

The `dev` script passes `--base /` so API calls use `/api/...` and proxy to the local FastAPI backend. Production builds use `base: '/cravings/'` (vite.config.ts), which sets `import.meta.env.BASE_URL=/cravings/` — all fetch calls in `api.ts` prepend this automatically.

## Key files

| File | What |
|------|------|
| `src/api.ts` | All fetch wrappers. `request()` prepends `import.meta.env.BASE_URL` to paths. |
| `src/App.tsx` | Root component: auth init, session lifecycle, screen state |
| `src/components/SwipeCard.tsx` | Food card, ✗/✓ buttons, ←/→ keyboard shortcuts |
| `src/components/RestaurantPanel.tsx` | Nearby restaurant results after right-swipe |
| `src/hooks/useLocation.ts` | Deferred browser geolocation (only requested on first right-swipe) |
| `vite.config.ts` | `base: '/cravings/'` for prod, `/api` proxy for dev |

## Auth flow

`POST /api/users` on first visit → bearer token stored in `localStorage` → sent as `Authorization: Bearer <token>` on every request. Single guest-user pattern; no login UI.
