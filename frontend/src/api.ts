const TOKEN_KEY = 'cravings_token'

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
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

function recoverFromInvalidToken(): void {
  if (recovering) return
  recovering = true
  localStorage.removeItem(TOKEN_KEY)
  window.location.reload()
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
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const base = import.meta.env.BASE_URL.replace(/\/$/, '')
  const res = await fetch(base + path, opts)
  if (res.status === 401 && getToken()) {
    recoverFromInvalidToken()
    throw new Error('session expired, reloading')
  }
  const data: unknown = await res.json()
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
}

export interface AuthResult extends UserInfo {
  api_token: string
}

export interface SwipeStats {
  total_swipes: number
  drift_active: boolean
  cuisine_breakdown: { cuisine: string; right: number; left: number }[]
  avg_swipes_to_right: number | null
  mood_breakdown: { mood: string; right: number; left: number }[]
  hour_breakdown: { hour: number; right: number; left: number }[]
}

export async function ensureUser(): Promise<void> {
  if (getToken()) return
  const data = await request<{ api_token: string }>('POST', '/api/users', { name: 'guest' })
  setToken(data.api_token)
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
  const base = import.meta.env.BASE_URL.replace(/\/$/, '')
  const res = await fetch(base + path, opts)
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
  setToken(result.api_token)
  return result
}

export async function login(email: string, password: string): Promise<AuthResult> {
  const result = await requestNoAuth<AuthResult>('POST', '/api/auth/login', { email, password })
  setToken(result.api_token)
  return result
}

export async function logout(): Promise<void> {
  try {
    await request('POST', '/api/auth/logout')
  } finally {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const result = await request<{ api_token: string }>('POST', '/api/auth/password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
  setToken(result.api_token)
}

export async function fetchStats(): Promise<SwipeStats> {
  return request<SwipeStats>('GET', '/api/profile/stats')
}

export async function postOnboarding(prefs: Record<string, number>): Promise<void> {
  await request('POST', '/api/onboarding', { preferences: prefs })
}

export async function getRecommendation(
  sessionId: string,
  mood = 'no_preference',
  dietaryMode = 'standard',
  topN = 1,
): Promise<FoodItem[]> {
  const params = new URLSearchParams({
    session_id: sessionId,
    mood,
    dietary_mode: dietaryMode,
    top_n: String(topN),
  })
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
): Promise<SwipeResult> {
  return request<SwipeResult>('POST', '/api/swipe', {
    food_item_id: foodItemId,
    direction,
    session_id: sessionId,
    snapshot_token: snapshotToken,
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
