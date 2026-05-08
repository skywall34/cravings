import { useState, useEffect, useCallback, useRef } from 'react'
import { ensureUser, getMe, getRecommendation, recordSwipe, getNearby } from './api'
import type { FoodItem, Restaurant, SwipeDirection } from './api'
import { useLocation } from './hooks/useLocation'
import { SwipeCard } from './components/SwipeCard'
import type { SwipeCardHandle } from './components/SwipeCard'
import { RestaurantPanel } from './components/RestaurantPanel'
import { OnboardingScreen } from './components/OnboardingScreen'
import { SessionSummary } from './components/SessionSummary'
import type { SwipeEntry } from './components/SessionSummary'
import { MoodSelector } from './components/MoodSelector'
import type { MoodOption, DietOption } from './components/MoodSelector'
import { moodToApi, dietToApi } from './components/MoodSelector'
import './App.css'

const SESSION_MAX = 10

function randomId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

function AppHeader() {
  return (
    <header className="app-header">
      <span className="app-header-emoji">🍽️</span>
      <h1 className="app-title">Cravings</h1>
    </header>
  )
}

interface SessionProgressProps {
  count: number
  total: number
}

function SessionProgress({ count, total }: SessionProgressProps) {
  if (count === 0) return null
  const pct = Math.min((count / total) * 100, 100)
  return (
    <div style={{ width: '100%', marginBottom: 14, display: 'flex', flexDirection: 'column', gap: 5 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontWeight: 700, color: '#B0A89E', letterSpacing: '0.04em' }}>
        <span>SESSION</span>
        <span>{count} / {total}</span>
      </div>
      <div style={{ height: 4, background: '#E8E0D8', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 2,
          background: 'linear-gradient(90deg, rgba(232,93,4,0.6), #E85D04)',
          width: `${pct}%`,
          transition: 'width 0.4s cubic-bezier(0.22,1,0.36,1)',
        }} />
      </div>
    </div>
  )
}

type Screen = 'onboarding' | 'swipe' | 'restaurants' | 'summary'

export default function App() {
  const sessionId = useRef(randomId())
  const swipeCardRef = useRef<SwipeCardHandle | null>(null)

  const [screen, setScreen] = useState<Screen>('swipe')
  const [food, setFood] = useState<FoodItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [restaurants, setRestaurants] = useState<Restaurant[] | null>([])
  const [selectedFood, setSelectedFood] = useState<FoodItem | null>(null)
  const [swiping, setSwiping] = useState(false)
  const [swipeHistory, setSwipeHistory] = useState<SwipeEntry[]>([])
  const [cardKey, setCardKey] = useState(0)
  const [mood, setMood] = useState<MoodOption>('Any')
  const [dietary, setDietary] = useState<DietOption>('Standard')

  const { requestLocation } = useLocation()

  const swipeCount = swipeHistory.length

  useEffect(() => {
    async function init() {
      try {
        await ensureUser()
        const me = await getMe()
        const hasToken = !!localStorage.getItem('cravings_token')
        if (!me.onboarding_complete && hasToken) {
          // token exists but onboarding not done — show onboarding before swipe
          setScreen('onboarding')
          setLoading(false)
          return
        }
        if (!hasToken) {
          setScreen('onboarding')
          setLoading(false)
          return
        }
        await loadNextCard()
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
        setLoading(false)
      }
    }
    void init()
  }, [])

  async function loadNextCard() {
    setLoading(true)
    setError(null)
    try {
      const recs = await getRecommendation(sessionId.current, moodToApi(mood), dietToApi(dietary))
      if (!recs || recs.length === 0) {
        setFood(null)
        setError('No more items available.')
      } else {
        setFood(recs[0])
        setCardKey(k => k + 1)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  const handleOnboardingComplete = useCallback(async () => {
    setScreen('swipe')
    await loadNextCard()
  }, [mood, dietary])

  const handleOnboardingSkip = useCallback(async () => {
    setScreen('swipe')
    await loadNextCard()
  }, [mood, dietary])

  async function handleNewSession() {
    sessionId.current = randomId()
    setSwipeHistory([])
    setScreen('swipe')
    await loadNextCard()
  }

  const handleSwipe = useCallback(async (direction: SwipeDirection) => {
    if (!food || swiping) return
    setSwiping(true)
    const swipedFood = food

    try {
      const result = await recordSwipe(swipedFood.id, direction, sessionId.current, swipedFood.snapshot_token)

      const newHistory = [...swipeHistory, { food: swipedFood, direction }]
      setSwipeHistory(newHistory)

      if (result.session_complete || newHistory.length >= SESSION_MAX) {
        setScreen('summary')
        return
      }

      if (direction === 'right') {
        setSelectedFood(swipedFood)
        setRestaurants(null)
        setScreen('restaurants')

        try {
          const loc = await requestLocation()
          const nearby = await getNearby(swipedFood.id, loc.lat, loc.lng)
          setRestaurants(nearby)
        } catch {
          setRestaurants([])
        }
      } else {
        await loadNextCard()
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSwiping(false)
    }
  }, [food, swiping, swipeHistory, requestLocation, mood, dietary])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (screen === 'restaurants') {
        if (e.key === 'Enter' || e.key === 'ArrowRight') void handleDismissPanel()
        return
      }
      if (screen === 'swipe') {
        if (e.key === 'ArrowLeft') swipeCardRef.current?.swipe('left')
        if (e.key === 'ArrowRight') swipeCardRef.current?.swipe('right')
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [screen, handleSwipe])

  async function handleDismissPanel() {
    setScreen('swipe')
    setSelectedFood(null)
    setRestaurants([])
    await loadNextCard()
  }

  if (loading && screen === 'swipe' && !food) {
    return (
      <div className="center-screen">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="app">
      {screen !== 'onboarding' && <AppHeader />}

      {screen === 'onboarding' && (
        <div className="card-enter" style={{ width: '100%' }}>
          <OnboardingScreen
            onComplete={() => void handleOnboardingComplete()}
            onSkip={() => void handleOnboardingSkip()}
          />
        </div>
      )}

      {screen === 'swipe' && (
        <>
          <SessionProgress count={swipeCount} total={SESSION_MAX} />
          <MoodSelector
            mood={mood} dietary={dietary}
            onMoodChange={setMood} onDietaryChange={setDietary}
          />
          {error && <p className="error-msg">{error}</p>}
          <div className="card-wrap">
            <div key={cardKey} className="card-enter">
              {food ? (
                <SwipeCard
                  ref={swipeCardRef}
                  food={food}
                  onSwipe={handleSwipe}
                  disabled={swiping || loading}
                  swipeCount={swipeCount}
                  totalSwipes={SESSION_MAX}
                />
              ) : (
                <div className="empty-state">
                  <div className="empty-emoji">🍽️</div>
                  <h2>You've seen it all!</h2>
                  <p>Come back later for fresh picks,<br />or start over to refine your taste.</p>
                  <button onClick={() => void loadNextCard()}>Start over</button>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {screen === 'restaurants' && (
        <div className="card-wrap">
          <div className="card-enter">
            <RestaurantPanel
              food={selectedFood}
              restaurants={restaurants}
              onDismiss={() => void handleDismissPanel()}
            />
          </div>
        </div>
      )}

      {screen === 'summary' && (
        <div className="card-wrap">
          <div className="card-enter">
            <SessionSummary
              swipeHistory={swipeHistory}
              onNewSession={() => void handleNewSession()}
            />
          </div>
        </div>
      )}
    </div>
  )
}
