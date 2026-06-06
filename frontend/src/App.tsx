import { useState, useEffect, useCallback, useRef } from 'react'
import { ensureUser, getMe, getRecommendation, recordSwipe, getNearby, logout, getToken, patchDietaryRestrictions, setSessionExpiredHandler, RateLimitError } from './api'
import type { FoodItem, Restaurant, SwipeDirection, UserInfo, GuestPrefs } from './api'
import * as storage from './storage'
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
import { AuthMenu } from './components/AuthMenu'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import { ProfilePage } from './components/ProfilePage'
import { ConsentBanner } from './components/ConsentBanner'
import { LegalPage } from './components/LegalPages'
import './App.css'

const LOCATION_CONSENT_KEY = 'cravings_location_consent'

const SESSION_MAX = 10
const DIETARY_KEY = 'cravings_dietary'

function randomId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

const EMPTY_DIETARY: GuestPrefs = { dietaryRestrictions: [], safetyOverrides: [], tastePrefs: {} }

async function loadDietaryFromStorage(): Promise<GuestPrefs> {
  try {
    const raw = await storage.get(DIETARY_KEY)
    if (raw) return JSON.parse(raw) as GuestPrefs
  } catch { /* ignore */ }
  return EMPTY_DIETARY
}

async function saveDietaryToStorage(prefs: GuestPrefs): Promise<void> {
  await storage.set(DIETARY_KEY, JSON.stringify(prefs))
}

function AppHeader({ user, onLogin, onRegister, onProfile, onLogout }: {
  user: UserInfo | null
  onLogin: () => void
  onRegister: () => void
  onProfile: () => void
  onLogout: () => void
}) {
  return (
    <header className="app-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="app-header-emoji">🍽️</span>
        <h1 className="app-title">Cravings</h1>
      </div>
      <AuthMenu user={user} onLogin={onLogin} onRegister={onRegister} onProfile={onProfile} onLogout={onLogout} />
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

type Screen = 'onboarding' | 'swipe' | 'restaurants' | 'summary' | 'login' | 'register' | 'profile' | 'privacy' | 'terms'

export default function App() {
  const sessionId = useRef(randomId())
  const swipeCardRef = useRef<SwipeCardHandle | null>(null)

  const [screen, setScreen] = useState<Screen>('swipe')
  const [prevScreen, setPrevScreen] = useState<Screen>('swipe')
  const [food, setFood] = useState<FoodItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [restaurants, setRestaurants] = useState<Restaurant[] | null>([])
  const [rateLimitedSeconds, setRateLimitedSeconds] = useState<number | null>(null)
  const [selectedFood, setSelectedFood] = useState<FoodItem | null>(null)
  const [swiping, setSwiping] = useState(false)
  const [swipeHistory, setSwipeHistory] = useState<SwipeEntry[]>([])
  const [cardKey, setCardKey] = useState(0)
  const [mood, setMood] = useState<MoodOption>('Any')
  const [dietary, setDietary] = useState<DietOption>('Standard')
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(null)
  const [guestDietary, setGuestDietary] = useState<GuestPrefs>(EMPTY_DIETARY)
  const seenIds = useRef<number[]>([])
  const [locationConsentPending, setLocationConsentPending] = useState<(() => void) | null>(null)

  const { requestLocation } = useLocation()

  function navigateTo(next: Screen) {
    setPrevScreen(screen)
    setScreen(next)
  }

  function navigateBack() {
    setScreen(prevScreen === screen ? 'swipe' : prevScreen)
  }

  const swipeCount = swipeHistory.length

  useEffect(() => {
    // Route a server 401 (expired/invalid token) back to onboarding instead of
    // window.location.reload(), which is a no-op inside the Capacitor WebView.
    setSessionExpiredHandler(() => {
      setCurrentUser(null)
      seenIds.current = []
      setSwipeHistory([])
      sessionId.current = randomId()
      setScreen('onboarding')
    })
  }, [])

  useEffect(() => {
    async function init() {
      try {
        const storedDietary = await loadDietaryFromStorage()
        setGuestDietary(storedDietary)
        await ensureUser()
        const token = await getToken()
        if (token) {
          const me = await getMe()
          setCurrentUser(me)
          if (!me.onboarding_complete) {
            setScreen('onboarding')
          } else {
            setScreen('swipe')
            await loadNextCard()
          }
        } else {
          // Guest: go straight to onboarding, no DB row
          setCurrentUser(null)
          setScreen('onboarding')
        }
        setLoading(false)
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
      const guestPrefs = currentUser === null
        ? { ...guestDietary, excludedIds: seenIds.current }
        : undefined
      const recs = await getRecommendation(sessionId.current, moodToApi(mood), dietToApi(dietary), 1, guestPrefs)
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

  const handleOnboardingComplete = useCallback(async (dietary: GuestPrefs) => {
    await saveDietaryToStorage(dietary)
    setGuestDietary(dietary)
    if (currentUser?.is_registered) {
      try {
        await patchDietaryRestrictions(dietary.dietaryRestrictions)
      } catch { /* non-fatal */ }
    }
    // Reset session so post-adjust session starts clean (also harmless on first-run onboarding)
    sessionId.current = randomId()
    seenIds.current = []
    setSwipeHistory([])
    setScreen('swipe')
    await loadNextCard()
  }, [mood, dietary, currentUser])

  const handleOnboardingSkip = useCallback(async (dietary: GuestPrefs) => {
    await saveDietaryToStorage(dietary)
    setGuestDietary(dietary)
    setScreen('swipe')
    await loadNextCard()
  }, [mood, dietary])

  async function handleNewSession() {
    sessionId.current = randomId()
    seenIds.current = []
    setSwipeHistory([])
    setScreen('swipe')
    await loadNextCard()
  }

  const handleSwipe = useCallback(async (direction: SwipeDirection) => {
    if (!food || swiping) return
    setSwiping(true)
    const swipedFood = food

    try {
      const guestPrefs = currentUser === null ? guestDietary : undefined
      if (currentUser === null) {
        seenIds.current = [...seenIds.current, Number(swipedFood.id)]
      }
      const result = await recordSwipe(swipedFood.id, direction, sessionId.current, swipedFood.snapshot_token, guestPrefs)

      const newHistory = [...swipeHistory, { food: swipedFood, direction }]
      setSwipeHistory(newHistory)

      if (result.session_complete || newHistory.length >= SESSION_MAX) {
        setScreen('summary')
        return
      }

      if (direction === 'right') {
        setSelectedFood(swipedFood)
        setRestaurants(null)
        setRateLimitedSeconds(null)
        setScreen('restaurants')

        const doNearby = async () => {
          try {
            const loc = await requestLocation()
            const nearby = await getNearby(swipedFood.id, loc.lat, loc.lng)
            setRestaurants(nearby)
          } catch (err) {
            if (err instanceof RateLimitError) {
              setRateLimitedSeconds(err.retry_after)
              setRestaurants([])
            } else {
              setRestaurants([])
            }
          }
        }

        const hasConsent = await storage.get(LOCATION_CONSENT_KEY)
        if (hasConsent) {
          await doNearby()
        } else {
          setLocationConsentPending(() => doNearby)
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

  async function handleLogout() {
    await logout()
    setCurrentUser(null)
    seenIds.current = []
    setSwipeHistory([])
    sessionId.current = randomId()
    setGuestDietary(await loadDietaryFromStorage())
    setScreen('onboarding')
  }

  if (loading && screen === 'swipe' && !food) {
    return (
      <div className="center-screen">
        <div className="spinner" />
      </div>
    )
  }

  const authMenuProps = {
    user: currentUser,
    onLogin: () => navigateTo('login'),
    onRegister: () => navigateTo('register'),
    onProfile: () => navigateTo('profile'),
    onLogout: () => void handleLogout(),
  }

  function openLegal(doc: 'privacy' | 'terms') {
    setPrevScreen(screen)
    setScreen(doc)
  }

  return (
    <div className="app">
      <AppHeader {...authMenuProps} />
      <ConsentBanner onOpenPrivacy={() => openLegal('privacy')} />

      {screen === 'login' && (
        <LoginForm
          onSuccess={user => { setCurrentUser(user); navigateBack(); void loadNextCard() }}
          onSwitchToRegister={() => setScreen('register')}
          onBack={navigateBack}
        />
      )}

      {screen === 'register' && (
        <RegisterForm
          onSuccess={user => { setCurrentUser(user); navigateBack(); void loadNextCard() }}
          onSwitchToLogin={() => setScreen('login')}
          onBack={navigateBack}
          isGuest={currentUser !== null && !currentUser.is_registered}
          onOpenTerms={() => openLegal('terms')}
          onOpenPrivacy={() => openLegal('privacy')}
        />
      )}

      {screen === 'profile' && currentUser && (
        <ProfilePage
          user={currentUser}
          onBack={navigateBack}
          onDeleteAccount={() => {
            setCurrentUser(null)
            seenIds.current = []
            setSwipeHistory([])
            sessionId.current = randomId()
            setGuestDietary(EMPTY_DIETARY)
            setScreen('onboarding')
          }}
        />
      )}

      {screen === 'onboarding' && (
        <div className="card-enter" style={{ width: '100%' }}>
          <OnboardingScreen
            onComplete={dietary => void handleOnboardingComplete(dietary)}
            onSkip={dietary => void handleOnboardingSkip(dietary)}
            hasExistingProfile={currentUser?.onboarding_complete ?? false}
            isRegistered={currentUser?.is_registered ?? false}
            initialDietary={guestDietary}
          />
        </div>
      )}

      {screen !== 'login' && screen !== 'register' && screen !== 'profile' && screen === 'swipe' && (
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
              rateLimitedSeconds={rateLimitedSeconds}
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
              onAdjustTastes={() => setScreen('onboarding')}
            />
          </div>
        </div>
      )}

      {(screen === 'privacy' || screen === 'terms') && (
        <LegalPage doc={screen} onBack={navigateBack} />
      )}

      {/* Location consent overlay — shown before first nearby lookup */}
      {locationConsentPending && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
          display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
          zIndex: 8000, padding: '0 12px 24px',
        }}>
          <div style={{
            width: '100%', maxWidth: 480, background: '#fff',
            borderRadius: 20, padding: '24px 20px 20px',
            boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
          }}>
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <div style={{
                width: 56, height: 56, borderRadius: '50%',
                background: 'rgba(232,93,4,0.10)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, margin: '0 auto 12px',
              }}>📍</div>
              <h3 style={{ margin: '0 0 6px', fontSize: '1.1rem', fontWeight: 800, color: '#1A1A1A' }}>
                Use your location?
              </h3>
              <p style={{ margin: '0 auto', maxWidth: 320, fontSize: '0.86rem', lineHeight: 1.55, color: '#6B6B6B' }}>
                Cravings uses your approximate location to find nearby restaurants. We don't store
                precise coordinates.{' '}
                <button
                  onClick={() => openLegal('privacy')}
                  style={{ background: 'none', border: 'none', padding: 0, color: '#E85D04', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', fontSize: '0.86rem', textDecoration: 'underline', textUnderlineOffset: 2 }}
                >
                  Privacy Policy
                </button>.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                onClick={() => {
                  void storage.set(LOCATION_CONSENT_KEY, 'granted')
                  const fn = locationConsentPending
                  setLocationConsentPending(null)
                  void fn()
                }}
                style={{
                  width: '100%', padding: '13px', background: '#E85D04', color: '#fff',
                  border: 'none', borderRadius: 100, fontSize: '0.95rem', fontWeight: 700,
                  cursor: 'pointer', fontFamily: 'inherit',
                  boxShadow: '0 4px 16px rgba(232,93,4,0.33)',
                }}
              >
                Allow location
              </button>
              <button
                onClick={() => {
                  void storage.set(LOCATION_CONSENT_KEY, 'denied')
                  setLocationConsentPending(null)
                  setRestaurants([])
                }}
                style={{
                  width: '100%', padding: '11px', background: 'transparent',
                  color: '#6B6B6B', border: 'none', borderRadius: 100,
                  fontSize: '0.88rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                Not now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={{
        width: '100%', textAlign: 'center',
        padding: '16px 20px 24px',
        fontSize: '0.75rem', color: '#B0A89E',
        display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap',
      }}>
        <button onClick={() => openLegal('privacy')} style={footerLinkStyle}>Privacy Policy</button>
        <button onClick={() => openLegal('terms')} style={footerLinkStyle}>Terms of Service</button>
        <span>© {new Date().getFullYear()} Cravings</span>
      </footer>
    </div>
  )
}

const footerLinkStyle: React.CSSProperties = {
  background: 'none', border: 'none', padding: 0,
  color: '#B0A89E', cursor: 'pointer', fontFamily: 'inherit',
  fontSize: '0.75rem', textDecoration: 'underline', textUnderlineOffset: 2,
}
