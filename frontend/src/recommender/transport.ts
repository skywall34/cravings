import { getRecommendation, recordSwipe } from '../api'
import type { FoodItem, SwipeDirection, SwipeResult, GuestPrefs } from '../api'

// The seam to the network. Adapters depend on this interface, not on api.ts
// directly, so tests inject a fake and the swipe flow is exercisable without a
// real fetch. The prod adapter is a thin binding over the existing api.ts fns.
export interface RecommenderTransport {
  recommend(
    sessionId: string,
    mood: string,
    dietary: string,
    topN: number,
    guestPrefs?: GuestPrefs,
  ): Promise<FoodItem[]>
  swipe(
    foodItemId: string,
    direction: SwipeDirection,
    sessionId: string,
    snapshotToken: string,
    guestPrefs?: GuestPrefs,
  ): Promise<SwipeResult>
}

export const prodTransport: RecommenderTransport = {
  recommend: getRecommendation,
  swipe: recordSwipe,
}
