// Canonical cuisine → emoji map. Previously drifted across 5 copy-pasted
// definitions (StatsCharts, AdminCharts, RestaurantPanel, SwipeCard,
// SessionSummary) that disagreed on several cuisines (e.g. thai was 🍜 in
// some screens and 🦐 in others) — one source so a cuisine reads the same
// emoji everywhere in the app.
export const CUISINE_EMOJI: Record<string, string> = {
  japanese: '🍣', mexican: '🌮', italian: '🍕', indian: '🥘',
  american: '🍔', thai: '🦐', korean: '🥩', mediterranean: '🥗',
  chinese: '🥡', french: '🥐', vietnamese: '🍜', greek: '🫒',
  middle_eastern: '🧆', spanish: '🥘', german: '🥨', eastern_european: '🥟',
  filipino: '🍚', indonesian: '🍛', brazilian: '🥩', caribbean: '🌶️', ethiopian: '🫓',
}
