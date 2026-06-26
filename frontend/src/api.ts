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
  email_verified: boolean
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

// Registration no longer starts a session: the account is created unverified
// and login is blocked until the emailed code is confirmed. The returned token
// is held by the verify screen and only persisted by verifyEmail() on success.
export async function register(email: string, password: string, name?: string): Promise<AuthResult> {
  return request<AuthResult>('POST', '/api/auth/register', { email, password, name })
}

// Confirm the 6-digit code. On success this is where the real session begins.
export async function verifyEmail(email: string, code: string): Promise<AuthResult> {
  const result = await requestNoAuth<AuthResult>('POST', '/api/auth/verify-email', { email, code })
  await setToken(result.api_token)
  return result
}

export async function resendVerification(email: string): Promise<void> {
  await requestNoAuth('POST', '/api/auth/resend-verification', { email })
}

// Thrown by login() when the account exists but hasn't verified its email yet,
// so the UI can route the user into the verification step.
export class EmailNotVerifiedError extends Error {
  email: string
  constructor(email: string) {
    super('please verify your email')
    this.name = 'EmailNotVerifiedError'
    this.email = email
  }
}

export async function login(email: string, password: string): Promise<AuthResult> {
  let result: AuthResult
  try {
    result = await requestNoAuth<AuthResult>('POST', '/api/auth/login', { email, password })
  } catch (err) {
    // The server returns 403 "please verify your email" for an unverified
    // account — surface it as a typed error so the UI can open the verify step.
    if (err instanceof Error && err.message.toLowerCase().includes('verify your email')) {
      throw new EmailNotVerifiedError(email)
    }
    throw err
  }
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

export interface InsightsDrift {
  windows: string[]
  series: Record<string, number[]>
}

export interface InsightsData {
  axes: Record<string, number>
  drift?: InsightsDrift | null
  recap: { top_cuisine: string | null; top_cuisines: string[]; say_yes_rate: number; biggest_mover: string | null }
  ready: boolean
  total_right_swipes: number
}

export async function fetchInsights(): Promise<InsightsData> {
  return request<InsightsData>('GET', '/api/insights')
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

// ---------------------------------------------------------------------------
// Admin metrics types + API calls
// ---------------------------------------------------------------------------

export interface AdminFoodMetric {
  food_id: number; name: string; cuisine_type: string; restaurant: string | null
  right: number; left: number; never: number; total: number; right_rate: number; impressions: number
}
export interface AdminFoodsMetrics { min_swipes: number; food_count: number; best: AdminFoodMetric[]; worst: AdminFoodMetric[] }
export interface AdminDim { key: string; right: number; total: number; right_rate: number }
export interface AdminCatalogMetrics {
  by_cuisine: AdminDim[]; by_protein: AdminDim[]; by_carb: AdminDim[]
  right_swipe_attributes: Record<string, number>
}
export interface AdminRetentionMetrics {
  active_definition: string; population: string; dau: number; wau: number; mau: number
  signups: { day: string; n: number }[]
  cohort_retention: { D1: number; D7: number; D30: number }
  cohort_eligible: { D1: number; D7: number; D30: number }
}
export interface AdminEngagementMetrics {
  total_swipes: number; global_say_yes_rate: number
  swipes_per_day: { day: string; n: number; right: number; say_yes_rate: number }[]
  swipes_per_user_histogram: { bucket: string; users: number }[]
  active_users_with_swipes: number; registered_users: number; premium_users: number; premium_conversions_recent: number
}

function qs(p?: Record<string, string | number | undefined>): string {
  if (!p) return ''
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(p)) {
    if (v !== undefined) params.set(k, String(v))
  }
  const s = params.toString()
  return s ? `?${s}` : ''
}

export async function getAdminFoods(p?: { min_swipes?: number; limit?: number; cuisine?: string }): Promise<AdminFoodsMetrics> {
  return request<AdminFoodsMetrics>('GET', `/api/admin/metrics/foods${qs(p)}`)
}

export async function getAdminCatalog(): Promise<AdminCatalogMetrics> {
  return request<AdminCatalogMetrics>('GET', '/api/admin/metrics/catalog')
}

export async function getAdminRetention(days = 30): Promise<AdminRetentionMetrics> {
  return request<AdminRetentionMetrics>('GET', `/api/admin/metrics/retention?days=${days}`)
}

export async function getAdminEngagement(days = 30): Promise<AdminEngagementMetrics> {
  return request<AdminEngagementMetrics>('GET', `/api/admin/metrics/engagement?days=${days}`)
}

export async function exportData(): Promise<Blob> {
  const res = await fetch(`${apiBase()}/api/users/me/export`, {
    headers: await authHeaders(),
  })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)
  return res.blob()
}

