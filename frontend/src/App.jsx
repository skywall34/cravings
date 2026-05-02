import { useState, useEffect, useCallback, useRef } from 'react'
import { ensureUser, getRecommendation, recordSwipe, getNearby } from './api'
import { useLocation } from './hooks/useLocation'
import { SwipeCard } from './components/SwipeCard'
import { RestaurantPanel } from './components/RestaurantPanel'
import './App.css'

function randomId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export default function App() {
  const sessionId = useRef(randomId())

  const [food, setFood] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [restaurants, setRestaurants] = useState([])
  const [showPanel, setShowPanel] = useState(false)
  const [swiping, setSwiping] = useState(false)

  const { requestLocation, error: locationError } = useLocation()

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
    const swipedFood = food

    try {
      await recordSwipe(swipedFood.id, direction, sessionId.current, swipedFood.snapshot_token)

      if (direction === 'right') {
        try {
          const loc = await requestLocation()
          const nearby = await getNearby(swipedFood.id, loc.lat, loc.lng)
          setRestaurants(Array.isArray(nearby) ? nearby : [])
        } catch {
          setRestaurants([])
        }
        setShowPanel(true)
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
      if (showPanel) {
        if (e.key === 'Enter' || e.key === 'ArrowRight') handleDismissPanel()
        return
      }
      if (e.key === 'ArrowLeft') handleSwipe('left')
      if (e.key === 'ArrowRight') handleSwipe('right')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [handleSwipe, showPanel])

  async function handleDismissPanel() {
    setShowPanel(false)
    setRestaurants([])
    await loadNextCard()
  }

  if (loading && !food) {
    return <div className="center-screen"><div className="spinner" /></div>
  }

  if (showPanel) {
    return (
      <div className="app">
        <RestaurantPanel
          foodName={food?.name}
          restaurants={restaurants}
          onDismiss={handleDismissPanel}
        />
        {locationError && <p className="location-error">{locationError}</p>}
      </div>
    )
  }

  return (
    <div className="app">
      <h1 className="app-title">Cravings</h1>
      {error && <p className="error-msg">{error}</p>}
      {food ? (
        <SwipeCard food={food} onSwipe={handleSwipe} disabled={swiping || loading} />
      ) : (
        <div className="empty-state">
          <p>No more items. Reset to start over.</p>
          <button onClick={loadNextCard}>Try again</button>
        </div>
      )}
    </div>
  )
}
