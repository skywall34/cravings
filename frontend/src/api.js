const TOKEN_KEY = 'cravings_token'

function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(path, opts)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
  return data
}

// Creates a user and stores the token. Called on first visit.
export async function ensureUser() {
  if (getToken()) return
  const data = await request('POST', '/api/users', { name: 'guest' })
  setToken(data.api_token)
}

// Returns top recommendation(s) for the session.
export async function getRecommendation(sessionId, mood = 'no_preference', dietaryMode = 'standard', topN = 1) {
  const params = new URLSearchParams({ session_id: sessionId, mood, dietary_mode: dietaryMode, top_n: topN })
  return request('GET', `/api/recommend?${params}`)
}

// Records a swipe. direction: 'left' | 'right'.
// snapshotToken is the opaque server-issued token from the recommendation that produced this card.
export async function recordSwipe(foodItemId, direction, sessionId, snapshotToken) {
  return request('POST', '/api/swipe', {
    food_item_id: foodItemId,
    direction,
    session_id: sessionId,
    snapshot_token: snapshotToken,
  })
}

// Returns nearby restaurants for a food item.
export async function getNearby(foodItemId, lat, lng) {
  const params = new URLSearchParams({ food_item_id: foodItemId, lat, lng })
  return request('GET', `/api/nearby?${params}`)
}

// Resets the seen-set for a session.
export async function resetSession(sessionId) {
  return request('POST', '/api/session/reset', { session_id: sessionId })
}
