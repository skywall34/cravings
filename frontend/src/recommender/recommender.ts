import type { FoodItem, SwipeDirection, SwipeResult, GuestPrefs, UserInfo } from '../api'
import type { RecommenderTransport } from './transport'

// Client-side mirror of the backend Recommender seam (recommender.py): one
// adapter per User Identity, identity resolved once via makeRecommender(). Owns
// the Swipe Session client state (sessionId, seenIds, history, session-complete
// reconciliation) so App.tsx never branches on Guest vs Registered.

export const SESSION_MAX = 10

export interface SwipeEntry {
  food: FoodItem
  direction: SwipeDirection
}

export interface SwipeOutcome {
  result: SwipeResult
  // server flag OR local count >= SESSION_MAX (see ADR: local count is a fallback)
  sessionComplete: boolean
}

// Immutable snapshot consumed by useSyncExternalStore. getState() must return a
// cached reference between mutations or React loops, hence the snapshot field.
export interface RecommenderState {
  history: SwipeEntry[]
  count: number
  sessionId: string
}

export interface Recommender {
  next(): Promise<FoodItem | null>
  swipe(food: FoodItem, direction: SwipeDirection): Promise<SwipeOutcome>
  reset(): void
  // Arrow-typed (not methods) so they carry a stable, pre-bound reference for
  // useSyncExternalStore — see the bound arrow fields in BaseRecommender.
  getState: () => RecommenderState
  subscribe: (listener: () => void) => () => void
  /** Guest-only: update dietary prefs without rebuilding (avoids session ID rotation). */
  setDietary?(prefs: GuestPrefs): void
}

function randomId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

abstract class BaseRecommender implements Recommender {
  protected sessionId = randomId()
  protected history: SwipeEntry[] = []
  private listeners = new Set<() => void>()
  private snapshot: RecommenderState = this.computeSnapshot()

  private computeSnapshot(): RecommenderState {
    return { history: this.history, count: this.history.length, sessionId: this.sessionId }
  }

  // Recompute the cached snapshot and notify subscribers. Called after every
  // mutation so getState() stays referentially stable in between.
  protected commit(): void {
    this.snapshot = this.computeSnapshot()
    this.listeners.forEach(l => l())
  }

  // Bound as arrow fields so the references stay stable for useSyncExternalStore.
  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  getState = (): RecommenderState => this.snapshot

  reset(): void {
    this.sessionId = randomId()
    this.history = []
    this.onReset()
    this.commit()
  }

  // Record a swipe into session history and reconcile session-complete. Subclass
  // swipe() calls this after the transport write so ordering (e.g. guest seen-set
  // before the network call) stays the subclass's responsibility.
  protected record(food: FoodItem, direction: SwipeDirection, result: SwipeResult): SwipeOutcome {
    this.history = [...this.history, { food, direction }]
    this.commit()
    return {
      result,
      sessionComplete: result.session_complete || this.history.length >= SESSION_MAX,
    }
  }

  protected onReset(): void {}

  abstract next(): Promise<FoodItem | null>
  abstract swipe(food: FoodItem, direction: SwipeDirection): Promise<SwipeOutcome>
}

// Guest: tracks the seen-set client-side (→ excludedIds), and sends dietary +
// taste prefs on every call. guestDietary is captured at construction; the hook
// rebuilds the adapter when it changes (a rebuild yields a fresh session).
class GuestRecommender extends BaseRecommender {
  private seenIds: number[] = []

  constructor(
    private guestDietary: GuestPrefs,
    private transport: RecommenderTransport,
  ) {
    super()
  }

  setDietary(prefs: GuestPrefs): void {
    this.guestDietary = prefs
  }

  protected onReset(): void {
    this.seenIds = []
  }

  async next(): Promise<FoodItem | null> {
    const prefs: GuestPrefs = { ...this.guestDietary, excludedIds: this.seenIds }
    const recs = await this.transport.recommend(this.sessionId, 1, prefs)
    return recs[0] ?? null
  }

  async swipe(food: FoodItem, direction: SwipeDirection): Promise<SwipeOutcome> {
    // seen-set updated before the write, matching the prior App.tsx ordering so
    // the next() that may run during the restaurant panel excludes this item.
    this.seenIds = [...this.seenIds, Number(food.id)]
    const result = await this.transport.swipe(
      food.id, direction, this.sessionId, food.snapshot_token, this.guestDietary,
    )
    return this.record(food, direction, result)
  }
}

// Registered: server owns the seen-set and loads dietary from the user row, so
// no guest params are sent (the backend ignores pref_* under a bearer anyway).
class RegisteredRecommender extends BaseRecommender {
  constructor(private transport: RecommenderTransport) {
    super()
  }

  async next(): Promise<FoodItem | null> {
    const recs = await this.transport.recommend(this.sessionId, 1, undefined)
    return recs[0] ?? null
  }

  async swipe(food: FoodItem, direction: SwipeDirection): Promise<SwipeOutcome> {
    const result = await this.transport.swipe(
      food.id, direction, this.sessionId, food.snapshot_token, undefined,
    )
    return this.record(food, direction, result)
  }
}

// Resolve identity once — the client twin of make_recommender(). A null user is
// a Guest (no DB row, ADR-0005); anything else is Registered.
export function makeRecommender(
  user: UserInfo | null,
  guestDietary: GuestPrefs,
  transport: RecommenderTransport,
): Recommender {
  return user === null
    ? new GuestRecommender(guestDietary, transport)
    : new RegisteredRecommender(transport)
}
