import * as storage from './storage'

const TOKEN_KEY = 'cravings_token'

export async function getToken(): Promise<string | null> {
  return storage.get(TOKEN_KEY)
}

async function setToken(token: string): Promise<void> {
  await storage.set(TOKEN_KEY, token)
}

async function removeToken(): Promise<void> {
  await storage.remove(TOKEN_KEY)
}

async function authHeaders(): Promise<Record<string, string>> {
  const token = await getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Web build: BASE_URL ('/cravings/'), same-origin. Native build: absolute prod URL
// injected via VITE_API_BASE_URL so the WebView (https://localhost) reaches prod.
function apiBase(): string {
  return (import.meta.env.VITE_API_BASE_URL ?? import.meta.env.BASE_URL).replace(/\/$/, '')
}

// Food/asset URLs from the API are root-relative ('/cravings/images/...'). On native
// they must be prefixed with the prod origin or they resolve against https://localhost
// and 404. On web (no VITE_API_BASE_URL) they stay relative and same-origin.
export function assetUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined
  const base = import.meta.env.VITE_API_BASE_URL
  if (base && !/^https?:\/\//.test(path)) {
    return new URL(base).origin + path
  }
  return path
}

export interface FoodItem {
  id: string
  name: string
  description?: string
  cuisine_type?: string
  spice_level: number
  sweetness: number
  richness: number
  sauce_heaviness: number
  veggie_density: number
  dairy_content: number
  protein_type?: string
  snapshot_token: string
  image_url_400?: string | null
  image_url_800?: string | null
  image_author?: string | null
  image_license?: string | null
  image_source_url?: string | null
}

export interface Restaurant {
  name: string
  address?: string
  maps_url?: string
  rating: number
}

export type SwipeDirection = 'left' | 'right' | 'never'

let recovering = false
let onSessionExpired: (() => void) | null = null

// App registers a reset callback (clear state + route to onboarding). Replaces
// window.location.reload(), which is a no-op inside the Capacitor WebView.
export function setSessionExpiredHandler(fn: () => void): void {
  onSessionExpired = fn
}

async function recoverFromInvalidToken(): Promise<void> {
  if (recovering) return
  recovering = true
  await removeToken()
  if (onSessionExpired) onSessionExpired()
  else window.location.reload()
}

export class RateLimitError extends Error {
  retry_after: number
  constructor(retry_after: number) {
    super(`rate limited, retry in ${retry_after}s`)
    this.name = 'RateLimitError'
    this.retry_after = retry_after
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(apiBase() + path, opts)
  if (res.status === 401 && (await getToken())) {
    await recoverFromInvalidToken()
    throw new Error('session expired, reloading')
  }
  if (res.status === 204) return undefined as T
  let data: unknown = null
  try {
    data = await res.json()
  } catch {
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return undefined as T
  }
  if (res.status === 429) {
    const headerRetry = Number(res.headers.get('Retry-After')) || 0
    let bodyRetry = 0
    if (data !== null && typeof data === 'object' && 'detail' in data) {
      const detail = data.detail
      if (detail !== null && typeof detail === 'object' && 'retry_after' in detail) {
        bodyRetry = Number(detail.retry_after) || 0
      }
    }
    throw new RateLimitError(bodyRetry || headerRetry || 1)
  }
  if (!res.ok) {
    const errMsg =
      data !== null && typeof data === 'object' && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : `HTTP ${res.status}`
    throw new Error(errMsg)
  }
  return data as T
}

export interface UserInfo {
  id: number
  name: string
  email: string | null
  is_registered: boolean
  onboarding_complete: boolean
  is_premium: boolean
  is_admin: boolean
}

export interface AuthResult extends UserInfo {
  api_token: string
}

export interface CheckoutResult {
  session_id: string
  amount_cents: number
  provider: string
  url: string | null
}

export function effectivePremium(u: UserInfo | null): boolean {
  return !!u && (u.is_admin || u.is_premium)
}

export async function createCheckout(): Promise<CheckoutResult> {
  return request<CheckoutResult>('POST', '/api/billing/checkout')
}

export interface SwipeStats {
  total_swipes: number
  drift_active: boolean
  cuisine_breakdown: { cuisine: string; right: number; left: number }[]
  avg_swipes_to_right: number | null
  hour_breakdown: { hour: number; right: number; left: number }[]
  flavor_profile: Record<string, number>
}

export async function ensureUser(): Promise<void> {
  // No-op for guests — DB row created only on registration
  if (await getToken()) return
}

export async function getMe(): Promise<UserInfo> {
  return request<UserInfo>('GET', '/api/users/me')
}

async function requestNoAuth<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(apiBase() + path, opts)
  const data: unknown = await res.json()
  if (!res.ok) {
    const errMsg =
      data !== null && typeof data === 'object' && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : `HTTP ${res.status}`
    throw new Error(errMsg)
  }
  return data as T
}

export async function register(email: string, password: string, name?: string): Promise<AuthResult> {
  const result = await request<AuthResult>('POST', '/api/auth/register', { email, password, name })
  await setToken(result.api_token)
  return result
}

export async function login(email: string, password: string): Promise<AuthResult> {
  const result = await requestNoAuth<AuthResult>('POST', '/api/auth/login', { email, password })
  await setToken(result.api_token)
  return result
}

export async function logout(): Promise<void> {
  try {
    await request('POST', '/api/auth/logout')
  } finally {
    await removeToken()
  }
}

// Persist dietary restrictions for registered users. Routed through request() so
// it shares the API base, auth header, and 401 handling — replaces a raw fetch().
export async function patchDietaryRestrictions(restrictions: string[]): Promise<void> {
  await request('PATCH', '/api/users/me', { dietary_restrictions: restrictions })
}

export interface GuestPrefs {
  dietaryRestrictions: string[]
  safetyOverrides: string[]
  excludedIds?: number[]
  tastePrefs?: Record<string, number>
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const result = await request<{ api_token: string }>('POST', '/api/auth/password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
  await setToken(result.api_token)
}

export async function fetchStats(): Promise<SwipeStats> {
  return request<SwipeStats>('GET', '/api/profile/stats')
}

export async function postOnboarding(prefs: Record<string, number>, reset = false): Promise<void> {
  await request('POST', '/api/onboarding', { preferences: prefs, reset })
}

export async function getRecommendation(
  sessionId: string,
  topN = 1,
  guestPrefs?: GuestPrefs,
): Promise<FoodItem[]> {
  const params = new URLSearchParams({
    session_id: sessionId,
    top_n: String(topN),
  })
  if (guestPrefs) {
    guestPrefs.dietaryRestrictions.forEach(r => params.append('dietary_restrictions', r))
    guestPrefs.safetyOverrides.forEach(o => params.append('safety_overrides', o))
    ;(guestPrefs.excludedIds ?? []).forEach(id => params.append('excluded_ids', String(id)))
    Object.entries(guestPrefs.tastePrefs ?? {}).forEach(([k, v]) => params.set('pref_' + k, String(v)))
  }
  return request<FoodItem[]>('GET', `/api/recommend?${params}`)
}

export interface SwipeResult {
  success: boolean
  total_swipes: number
  session_complete: boolean
}

export async function recordSwipe(
  foodItemId: string,
  direction: SwipeDirection,
  sessionId: string,
  snapshotToken: string,
  guestPrefs?: GuestPrefs,
): Promise<SwipeResult> {
  return request<SwipeResult>('POST', '/api/swipe', {
    food_item_id: foodItemId,
    direction,
    session_id: sessionId,
    snapshot_token: snapshotToken,
    ...(guestPrefs ? {
      dietary_restrictions: guestPrefs.dietaryRestrictions,
      safety_overrides: guestPrefs.safetyOverrides,
      taste_prefs: guestPrefs.tastePrefs ?? {},
    } : {}),
  })
}

export async function getNearby(foodItemId: string, lat: number, lng: number): Promise<Restaurant[]> {
  const params = new URLSearchParams({
    food_item_id: foodItemId,
    lat: String(lat),
    lng: String(lng),
  })
  return request<Restaurant[]>('GET', `/api/nearby?${params}`)
}

export async function resetSession(sessionId: string): Promise<void> {
  return request('POST', '/api/session/reset', { session_id: sessionId })
}

export async function deleteAccount(): Promise<void> {
  return request('DELETE', '/api/users/me')
}

export async function exportData(): Promise<Blob> {
  const res = await fetch(`${apiBase()}/api/users/me/export`, {
    headers: await authHeaders(),
  })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)
  return res.blob()
}

