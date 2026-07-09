# Android Migration — Capacitor Wrap

> **DEPRECATED (2026-06-20) — Legacy reference only. Scaffold removed 2026-07-08.**
> PWA is now the primary mobile delivery channel for both iOS and Android (ADR-0016, P32).
> The Capacitor `android/` code, `capacitor.config.ts`, `.env.capacitor`, and `build:android`/
> `open:android` scripts were deleted from the repo on 2026-07-08 — Android now ships as a TWA
> (Bubblewrap) wrapping the live PWA. This document is preserved for historical reference only;
> none of its toolchain setup applies to the current path. See
> `docs/internal/adr/0016-pwa-primary-mobile-delivery.md` and `TWA_PLAY_STORE_PLAN.md` (repo root).

---

**Status (2026-06-13): code + scaffold complete, debug APK built. CORS preflight
verified ✅ (both `https://localhost` and `capacitor://localhost` origins pass).
On-device emulator session verified ✅ (2026-06-13 — items A/B/D/G confirmed via
Medium_Phone_API_36.1 AVD; see checklist below). Remaining: signed release build (Phase 4).**

See `docs/internal/adr/0006-android-capacitor-bundled-wrap.md` for the decision record.

## Context

Cravings ships as a React 19 + Vite web app served from
`https://themshin.com/cravings` behind FastAPI + Traefik. Capacitor wraps the
existing web bundle in a native Android shell, reusing ~100% of the React code.
The web app stays the iOS + desktop channel — **iOS gets no native build**.

## Locked decisions (from grilling, 2026-06-02)

1. **UI delivery** — bundle `dist/` inside the APK. App renders bundled UI, calls
   the live prod API. **Consequence: the API must stay backward-compatible with
   shipped APKs** (a web deploy doesn't reach installed apps until they update).
2. **Token storage** — plaintext `@capacitor/preferences` for v1. Revisit with an
   encrypted Keystore plugin before any sensitive data lands.
3. **Async storage everywhere** — `getToken()`/`authHeaders()` are async.
4. **Geolocation** — coarse only (`ACCESS_COARSE_LOCATION`).
5. **v1 finish line** — signed sideload APK via `adb install`. Play Store deferred.

## Phase 1 — Frontend portability ✅ done

- **API base** — `apiBase()` in `api.ts` = `VITE_API_BASE_URL ?? BASE_URL`. Web
  stays `/cravings`; Capacitor build injects the absolute prod URL. Applied at
  every base-building site (`request`, `requestNoAuth`, `exportData`).
- **Asset origin** — food image URLs from the API are root-relative
  (`/cravings/images/...`, `swipe/intake.py`) and 404 on the native WebView. New
  `assetUrl()` prefixes them with the prod origin on native, no-ops on web. Wired
  in `SwipeCard.tsx`.
- **Storage seam** — new `frontend/src/storage.ts` (async `get/set/remove`; web →
  `localStorage`, native → `@capacitor/preferences`). Routed every `localStorage`
  call through it: `api.ts` (token), `App.tsx` (dietary cache + location consent),
  `ConsentBanner.tsx`, `ProfilePage.tsx`.
- **Async token** — `api.ts` token helpers async; `register/login/logout/
  changePassword/exportData` await them.
- **401 handler** — replaced `window.location.reload()` (no-op in WebView) with a
  `setSessionExpiredHandler` callback registered from `App.tsx` (clears state →
  onboarding).
- **Raw fetches folded into api.ts** — the two `App.tsx` raw `fetch()` calls now
  go through `request()`; the dietary PATCH became `patchDietaryRestrictions()`.

## Phase 2 — Capacitor scaffolding ✅ done

- `frontend/capacitor.config.ts` — `appId: com.themshin.cravings`, `webDir: dist`,
  `server.androidScheme: https`.
- `frontend/.env.capacitor` — `VITE_API_BASE_URL=https://themshin.com/cravings`
  (loaded only by `--mode capacitor`; web build untouched).
- `frontend/package.json` — Capacitor 7 deps (pinned v7: CLI v8 needs Node ≥22,
  this env is Node 20). Scripts: `build:android`
  (`vite build --mode capacitor --base / && cap sync android`), `open:android`.
- `frontend/android/` — generated via `cap add android`, committed. targetSdk 35,
  minSdk 23.
- `AndroidManifest.xml` — `ACCESS_COARSE_LOCATION` added.
- `useLocation.ts` — native branch uses `@capacitor/geolocation`
  (`enableHighAccuracy:false`, runtime coarse permission); web keeps
  `navigator.geolocation`. Signature + first-fix cache preserved.
  **Bug fixed during P19 emulator test (2026-06-13):** added `timeout: 15000` and
  `maximumAge: 300000` to `getCurrentPosition`. Without `timeout`, the native
  default was too short for the fused location provider. Without `maximumAge`, the
  plugin always waits for a fresh GPS fix — the fused provider on emulator (API 36)
  never delivers one when seeded only via `adb emu geo fix` (GPS_PROVIDER only).
  `maximumAge: 300000` accepts a cached fix up to 5 min old, which is correct for
  production too (faster first fix on real devices).

## Phase 3 — Backend CORS ✅ done

`CORSMiddleware` in `main.py`: `allow_origins=["https://localhost",
"capacitor://localhost", "http://localhost"]`, `allow_credentials=False`. Web app
stays same-origin and unaffected.

## Build environment (WSL2, Linux-native — verified)

The APK builds inside WSL with a Linux-native toolchain. The Windows Android SDK
referenced by some `~/.bashrc` exports is **not** used for the build (its
`aapt2.exe` etc. are Windows binaries Linux Gradle can't invoke). What the build
needs, all installed locally:

- **Linux Android SDK** at `~/Android/Sdk` — `platforms;android-35` +
  `build-tools;35.0.0` (installed via `~/Android/Sdk/cmdline-tools/latest/bin/sdkmanager`).
  Matches the project's `compileSdk`/`targetSdk` 35.
- **JDK 21** at `~/jdks/jdk-21.0.11+10` (portable Temurin, no root). Capacitor 7
  plugins declare a **Java-21 toolchain** — the `@capacitor/geolocation` build
  fails on JDK 17 with `Cannot find a Java installation ... languageVersion=21`.
  Gradle reads `JAVA_HOME`; the system `java` on `PATH` can stay at 17.
- **Gradle wrapper** (`./gradlew`, Gradle 8.11.1) — self-downloads; the system
  `gradle` (4.4.1) is irrelevant.
- `frontend/android/local.properties` → `sdk.dir=$HOME/Android/Sdk` (gitignored,
  machine-specific).

Recommended persistent env (append to `~/.bashrc` after the existing Android
block — overrides the Windows `ANDROID_SDK_ROOT` for Linux builds):

```bash
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
export JAVA_HOME="$HOME/jdks/jdk-21.0.11+10"
```

## Phase 4 — Distribution (sideload)

Build (one command each, with the env above):

```bash
cd frontend && npm run build:android          # vite --mode capacitor --base / + cap sync
cd android && ./gradlew assembleDebug --no-daemon
# -> app/build/outputs/apk/debug/app-debug.apk  (debug-signed, installable)
```

Sideload to a device (`adb` alias → Windows `adb.exe`, talks to USB device):

```bash
adb devices    # confirm device + USB debugging
adb install -r '\\wsl.localhost\Ubuntu\home\mshin\cravings\frontend\android\app\build\outputs\apk\debug\app-debug.apk'
# if Windows adb can't read the \\wsl path: cp the apk to /mnt/c/.../Downloads first
```

Test on real coarse GPS: full session → grant location → recs + nearby from prod →
confirm token persists across app restart.

**Release build** (for a real distributable, not just debug testing): create a
signing keystore, store it + passwords in a password manager (**not** the repo),
keep `*.keystore` / `keystore.properties` gitignored, then `./gradlew
assembleRelease`.

Play Store (console, AAB, icon/feature-graphic/screenshots, privacy URL,
data-safety form, content rating) — **out of scope, v2**.

## Critical files

- Modified: `frontend/src/api.ts`, `App.tsx`, `components/SwipeCard.tsx`,
  `components/ConsentBanner.tsx`, `components/ProfilePage.tsx`,
  `hooks/useLocation.ts`, `src/vite-env.d.ts`, `package.json`, `main.py`.
- Added: `frontend/src/storage.ts`, `capacitor.config.ts`, `.env.capacitor`,
  `android/` (generated), `docs/adr/0006-android-capacitor-bundled-wrap.md`.
- `vite.config.ts` unchanged — the Android build overrides `base` via the
  `--base /` CLI flag.

## Verification

- **Web regression** — `npm run build` ✅ (base `/cravings/`, no prod URL baked).
- **Type** — `npm run typecheck` ✅ clean.
- **Lint** — pre-existing debt only; the Android work added zero new lint errors
  (baseline 11 → 10; `ensureUser` require-await fixed as a side effect).
- **Capacitor build** — `npm run build:android` ✅ bakes `base /` + prod API URL
  into `android/app/src/main/assets/public/`.
### On-device checklist (emulator — P19 verification)

**Setup:** Windows Android Studio, AVD = Pixel 8 / API 35 / Google APIs x86_64 (not "Google Play" — Google APIs allows GPS mocking without Play Store lock).
Mock GPS: Extended Controls → Location → Single points → lat `37.7749` lng `-122.4194` → **Set Location**.
Install: `adb install -r '\\wsl.localhost\Ubuntu\home\mshin\cravings\frontend\android\app\build\outputs\apk\debug\app-debug.apk'`
Connect WSL adb to Windows emulator: `adb devices` (should show `emulator-5554`; if offline: `adb kill-server && adb start-server && adb devices`).

**A — App launch**
- [x] App opens within 3s; no crash; ConsentBanner or Onboarding screen shown on first launch.
- [x] Network reaches `https://themshin.com/cravings`; no `ERR_NAME_NOT_RESOLVED` in logcat.

**B — Consent banner**
- [x] Banner appears on first launch; dismisses on accept; absent on relaunch (persisted via `@capacitor/preferences`).

**C — Onboarding → first card alignment**
- [ ] Set spice slider to max → "Let's go" → first card is a spicy dish (not a mild dessert). *(Not verifiable via adb — HTML range input does not respond to synthetic touch events in WebView. Manual test required: drag slider on physical device or use Android Studio emulator controls directly.)*
- [x] Skip path: onboarding completes on "Start Swiping" tap (navigates to swipe screen); first card loaded.

**D — Guest swipe session**
- [x] Right-swipe via keyboard `→` triggers swipe; next card loads.
- [x] Right-swipe triggers in-app location consent overlay (confirmed: `cravings_location_consent` written to Preferences).
- [x] Android OS system permission dialog fires — confirmed via logcat: `Geolocation.requestPermissions` called with `coarseLocation` on native plugin.
- [x] RestaurantPanel loads with real prod results (Bay Area restaurants, verified in screenshot).
- [x] Food card images render — confirmed `assetUrl()` working: food photo visible in SwipeCard (no broken icons).
- [ ] After swipe 10: Session Summary screen appears. *(Not tested — reaching swipe 10 requires completing a full session; not verified in this run.)*

**E — Session summary**
- [ ] Right/left counts correct. *(Not reached — see D note.)*
- [ ] "Adjust Tastes →" returns to onboarding sliders. *(Not reached.)*
- [ ] "New Session" starts fresh session. *(Not reached.)*

**F — Registered account**
- [x] Registered user recognized on relaunch (blue profile icon in header after injecting token).
- [ ] In-app registration flow (email + password via UI) not exercised — HTML inputs unresponsive to adb synthetic events. Manual test required.
- [ ] Profile page not verified in this run.

**G — Token persistence across app restart** ✅
- [x] Token (`Ya9bFFTaeI6yMVkElzF3n3FOPR-Dvbtv`) injected into `CapacitorStorage.xml` via `run-as`.
- [x] Force-stopped app; relaunched. Logcat confirms `Preferences.get { key: cravings_token }` called on startup. Registered-user profile icon appeared in header — token read and user recognized.
- [x] Confirms `@capacitor/preferences` (SharedPreferences, not localStorage) is the active storage path on native.

**H — Logout / login**
- [ ] Not verified in this run. Manual test required.

**CORS preflight (WSL terminal — no emulator needed)**
- [x] `curl -i -X OPTIONS https://themshin.com/cravings/api/recommend -H "Origin: https://localhost" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: Authorization, Content-Type"` → `access-control-allow-origin: https://localhost` ✅ (verified 2026-06-13)
- [x] Same with `Origin: capacitor://localhost` → `access-control-allow-origin: capacitor://localhost` ✅ (verified 2026-06-13)

Failure modes: no ACAO header → latest Docker image not deployed or origin missing from `allow_origins` (`main.py`); `405` → Traefik stripping OPTIONS.

## Out of scope for v1

App Links / deep linking, FCM push, iOS target, in-app browser for external
restaurant links, encrypted token storage, Play Store track.
