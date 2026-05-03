import { useState, useEffect, useCallback, useRef } from 'react'
import { ensureUser, getRecommendation, recordSwipe, getNearby } from './api'
import { useLocation } from './hooks/useLocation'
import { SwipeCard } from './components/SwipeCard'
import { RestaurantPanel } from './components/RestaurantPanel'
import './App.css'

function randomId() {
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

function SessionBadge({ swipeCount }) {
  if (swipeCount === 0) return null
  return (
    <div className="session-badge-wrap">
      <span className="session-badge">
        {swipeCount} swipe{swipeCount !== 1 ? 's' : ''} today
      </span>
    </div>
  )
}

export default function App() {
  const sessionId = useRef(randomId())
  const swipeCardRef = useRef(null)

  const [food, setFood] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [restaurants, setRestaurants] = useState([])
  const [screen, setScreen] = useState('swipe') // 'swipe' | 'restaurants'
  const [selectedFood, setSelectedFood] = useState(null)
  const [swiping, setSwiping] = useState(false)
  const [swipeCount, setSwipeCount] = useState(0)
  const [cardKey, setCardKey] = useState(0)

  const { requestLocation } = useLocation()

  useEffect(() => {
    async function init() {
      try {
        await ensureUser()
        await loadNextCard()
      } catch (e) {
        setError(e.message)
        setLoading(false)
      }
    }
    init()
  }, [])

  async function loadNextCard() {
    setLoading(true)
    setError(null)
    try {
      const recs = await getRecommendation(sessionId.current)
      if (!recs || recs.length === 0) {
        setFood(null)
        setError('No more items available.')
      } else {
        setFood(recs[0])
        setCardKey(k => k + 1)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSwipe = useCallback(async (direction) => {
    if (!food || swiping) return
    setSwiping(true)
    setSwipeCount(c => c + 1)
    const swipedFood = food

    try {
      await recordSwipe(swipedFood.id, direction, sessionId.current, swipedFood.snapshot_token)

      if (direction === 'right') {
        setSelectedFood(swipedFood)
        setRestaurants(null) // null = loading state in panel
        setScreen('restaurants')

        try {
          const loc = await requestLocation()
          const nearby = await getNearby(swipedFood.id, loc.lat, loc.lng)
          setRestaurants(Array.isArray(nearby) ? nearby : [])
        } catch {
          setRestaurants([])
        }
      } else {
        await loadNextCard()
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSwiping(false)
    }
  }, [food, swiping, requestLocation])

  useEffect(() => {
    function onKey(e) {
      if (screen === 'restaurants') {
        if (e.key === 'Enter' || e.key === 'ArrowRight') handleDismissPanel()
        return
      }
      if (e.key === 'ArrowLeft') swipeCardRef.current?.swipe('left')
      if (e.key === 'ArrowRight') swipeCardRef.current?.swipe('right')
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

  if (loading && !food && screen === 'swipe') {
    return (
      <div className="center-screen">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="app">
      <AppHeader />
      <SessionBadge swipeCount={swipeCount} />

      {error && <p className="error-msg">{error}</p>}

      <div className="card-wrap">
        {screen === 'swipe' ? (
          <div key={cardKey} className="card-enter">
            {food ? (
              <SwipeCard
                ref={swipeCardRef}
                food={food}
                onSwipe={handleSwipe}
                disabled={swiping || loading}
              />
            ) : (
              <div className="empty-state">
                <div className="empty-emoji">🍽️</div>
                <h2>You've seen it all!</h2>
                <p>Come back later for fresh picks,<br />or start over to refine your taste.</p>
                <button onClick={loadNextCard}>Start over</button>
              </div>
            )}
          </div>
        ) : (
          <div className="card-enter">
            <RestaurantPanel
              food={selectedFood}
              restaurants={restaurants}
              onDismiss={handleDismissPanel}
            />
          </div>
        )}
      </div>
    </div>
  )
}
