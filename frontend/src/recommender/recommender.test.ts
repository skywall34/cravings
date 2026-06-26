import { describe, it, expect, beforeEach } from 'vitest'
import { makeRecommender, SESSION_MAX } from './recommender'
import type { RecommenderTransport } from './transport'
import type { FoodItem, SwipeResult, GuestPrefs, UserInfo, SwipeDirection } from '../api'

// --- test doubles ----------------------------------------------------------

interface RecommendCall {
  sessionId: string; topN: number; guestPrefs?: GuestPrefs
}
interface SwipeCall {
  foodItemId: string; direction: SwipeDirection; sessionId: string
  snapshotToken: string; guestPrefs?: GuestPrefs
}

class FakeTransport implements RecommenderTransport {
  recommendCalls: RecommendCall[] = []
  swipeCalls: SwipeCall[] = []
  pool: FoodItem[] = []
  swipeResult: SwipeResult = { success: true, total_swipes: 0, session_complete: false }

  recommend(sessionId: string, topN: number, guestPrefs?: GuestPrefs) {
    this.recommendCalls.push({ sessionId, topN, guestPrefs })
    return Promise.resolve(this.pool)
  }
  swipe(foodItemId: string, direction: SwipeDirection, sessionId: string, snapshotToken: string, guestPrefs?: GuestPrefs) {
    this.swipeCalls.push({ foodItemId, direction, sessionId, snapshotToken, guestPrefs })
    return Promise.resolve(this.swipeResult)
  }
}

function food(id: number): FoodItem {
  return {
    id: String(id), name: `food-${id}`, snapshot_token: `tok-${id}`,
    spice_level: 0, sweetness: 0, richness: 0, sauce_heaviness: 0,
    veggie_density: 0, dairy_content: 0,
  }
}

const GUEST_DIETARY: GuestPrefs = {
  dietaryRestrictions: ['vegan'], safetyOverrides: [], tastePrefs: { spice_level: 0.8 },
}
const REGISTERED: UserInfo = {
  id: 7, name: 'reg', email: 'a@b.c', is_registered: true, onboarding_complete: true,
  is_premium: false, is_admin: false, email_verified: true,
}

// --- factory (twin of make_recommender) ------------------------------------

describe('makeRecommender — identity resolved once', () => {
  let t: FakeTransport
  beforeEach(() => { t = new FakeTransport() })

  it('null user → Guest: sends dietary + taste prefs', async () => {
    const rec = makeRecommender(null, GUEST_DIETARY, t)
    await rec.next()
    expect(t.recommendCalls[0].guestPrefs).toMatchObject({
      dietaryRestrictions: ['vegan'], tastePrefs: { spice_level: 0.8 },
    })
  })

  it('registered user → omits guest prefs (server owns them)', async () => {
    const rec = makeRecommender(REGISTERED, GUEST_DIETARY, t)
    await rec.next()
    expect(t.recommendCalls[0].guestPrefs).toBeUndefined()
  })
})

// --- guest seen-set threading ---------------------------------------------

describe('GuestRecommender — client-side seen-set', () => {
  let t: FakeTransport
  beforeEach(() => { t = new FakeTransport() })

  it('threads accumulated excludedIds across next() calls', async () => {
    const rec = makeRecommender(null, GUEST_DIETARY, t)
    await rec.next()
    expect(t.recommendCalls[0].guestPrefs?.excludedIds).toEqual([])

    await rec.swipe(food(1), 'left')
    await rec.next()
    expect(t.recommendCalls[1].guestPrefs?.excludedIds).toEqual([1])

    await rec.swipe(food(2), 'right')
    await rec.next()
    expect(t.recommendCalls[2].guestPrefs?.excludedIds).toEqual([1, 2])
  })

  it('marks the item seen before recording (regression: ordering)', async () => {
    const rec = makeRecommender(null, GUEST_DIETARY, t)
    // swipe item 5, then the immediate next() (e.g. after a left-swipe) must exclude it
    await rec.swipe(food(5), 'left')
    await rec.next()
    expect(t.recommendCalls[0].guestPrefs?.excludedIds).toContain(5)
  })

  it('swipe sends snapshot token + dietary', async () => {
    const rec = makeRecommender(null, GUEST_DIETARY, t)
    await rec.swipe(food(3), 'right')
    expect(t.swipeCalls[0]).toMatchObject({
      foodItemId: '3', direction: 'right', snapshotToken: 'tok-3',
    })
    expect(t.swipeCalls[0].guestPrefs).toMatchObject({ dietaryRestrictions: ['vegan'] })
  })
})

// --- registered adapter ----------------------------------------------------

describe('RegisteredRecommender', () => {
  it('swipe sends token + direction, no guest prefs', async () => {
    const t = new FakeTransport()
    const rec = makeRecommender(REGISTERED, GUEST_DIETARY, t)
    await rec.swipe(food(9), 'left')
    expect(t.swipeCalls[0]).toMatchObject({
      foodItemId: '9', direction: 'left', snapshotToken: 'tok-9',
    })
    expect(t.swipeCalls[0].guestPrefs).toBeUndefined()
  })
})

// --- session-complete reconciliation (both adapters) -----------------------

describe('session-complete = server flag OR local SESSION_MAX', () => {
  it('honors the server flag immediately', async () => {
    const t = new FakeTransport()
    t.swipeResult = { success: true, total_swipes: 1, session_complete: true }
    const rec = makeRecommender(REGISTERED, GUEST_DIETARY, t)
    const outcome = await rec.swipe(food(1), 'right')
    expect(outcome.sessionComplete).toBe(true)
  })

  it('falls back to local count when server flag never fires', async () => {
    const t = new FakeTransport() // server flag stays false
    const rec = makeRecommender(null, GUEST_DIETARY, t)
    const outcomes = []
    for (let i = 0; i < SESSION_MAX; i++) {
      outcomes.push(await rec.swipe(food(i), 'left'))
    }
    expect(outcomes.slice(0, SESSION_MAX - 1).every(o => !o.sessionComplete)).toBe(true)
    expect(outcomes[SESSION_MAX - 1].sessionComplete).toBe(true)
  })
})

// --- reset + state ---------------------------------------------------------

describe('reset() + getState()', () => {
  it('getState reflects accumulating history', async () => {
    const rec = makeRecommender(null, GUEST_DIETARY, new FakeTransport())
    expect(rec.getState().count).toBe(0)
    await rec.swipe(food(1), 'right')
    await rec.swipe(food(2), 'left')
    const s = rec.getState()
    expect(s.count).toBe(2)
    expect(s.history.map(h => h.direction)).toEqual(['right', 'left'])
  })

  it('clears history + seen-set and rotates sessionId', async () => {
    const t = new FakeTransport()
    const rec = makeRecommender(null, GUEST_DIETARY, t)
    await rec.swipe(food(1), 'left')
    const before = rec.getState().sessionId

    rec.reset()
    const after = rec.getState()
    expect(after.count).toBe(0)
    expect(after.sessionId).not.toBe(before)

    // seen-set wiped: next() excludes nothing
    await rec.next()
    const lastCall = t.recommendCalls[t.recommendCalls.length - 1]
    expect(lastCall.guestPrefs?.excludedIds).toEqual([])
  })

  it('notifies subscribers on mutation', async () => {
    const rec = makeRecommender(null, GUEST_DIETARY, new FakeTransport())
    let hits = 0
    const unsub = rec.subscribe(() => { hits++ })
    await rec.swipe(food(1), 'right')
    rec.reset()
    expect(hits).toBe(2)
    unsub()
    await rec.swipe(food(2), 'right')
    expect(hits).toBe(2) // no more after unsubscribe
  })
})
