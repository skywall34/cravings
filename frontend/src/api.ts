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
}

export interface Restaurant {
  name: string
  address?: string
  maps_url?: string
  rating: number
}

export type SwipeDirection = 'left' | 'right' | 'never'

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const base = import.meta.env.BASE_URL.replace(/\/$/, '')
  const res = await fetch(base + path, opts)
  const data: unknown = await res.json()
  if (!res.ok) {
    const errMsg =
      data !== null && typeof data === 'object' && 'error' in data
        ? String((data as { error: unknown }).error)
        : `HTTP ${res.status}`
    throw new Error(errMsg)
  }
  return data as T
}

export async function ensureUser(): Promise<void> {
  if (getToken()) return
  const data = await request<{ api_token: string }>('POST', '/api/users', { name: 'guest' })
  setToken(data.api_token)
}

export async function getMe(): Promise<{ onboarding_complete: boolean }> {
  return request<{ onboarding_complete: boolean }>('GET', '/api/users/me')
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
