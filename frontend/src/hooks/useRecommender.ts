import { useState, useSyncExternalStore } from 'react'
import type { UserInfo, GuestPrefs } from '../api'
import { makeRecommender } from '../recommender/recommender'
import type { Recommender, RecommenderState } from '../recommender/recommender'
import { prodTransport } from '../recommender/transport'

// Thin React binding over the Recommender seam. The adapter is rebuilt when User
// Identity flips (guest <-> registered, or a different registered user) or when
// guestDietary changes — each rebuild yields a fresh Swipe Session, matching the
// prior reset-on-identity behavior. Uses React's "adjust state during render"
// pattern (no refs) so the instance stays stable across unrelated re-renders.
export function useRecommender(user: UserInfo | null, guestDietary: GuestPrefs): {
  rec: Recommender
  history: RecommenderState['history']
  count: number
  sessionId: string
} {
  const identity = user === null ? 'guest' : `u:${user.id}`

  const [store, setStore] = useState(() => ({
    identity,
    dietary: guestDietary,
    rec: makeRecommender(user, guestDietary, prodTransport),
  }))

  if (store.identity !== identity || store.dietary !== guestDietary) {
    setStore({ identity, dietary: guestDietary, rec: makeRecommender(user, guestDietary, prodTransport) })
  }

  const rec = store.rec
  const state = useSyncExternalStore(rec.subscribe, rec.getState)
  return { rec, history: state.history, count: state.count, sessionId: state.sessionId }
}
