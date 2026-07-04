import { useState, useEffect, useCallback, useRef } from 'react'
import { getMe, getNearby, logout, getToken, patchDietaryRestrictions, setSessionExpiredHandler, RateLimitError, effectivePremium } from './api'
import type { FoodItem, Restaurant, SwipeDirection, UserInfo, GuestPrefs } from './api'
import * as storage from './storage'
import { useLocation } from './hooks/useLocation'
import { useLocationConsent } from './hooks/useLocationConsent'
import { useRecommender } from './hooks/useRecommender'
import { SESSION_MAX } from './recommender/recommender'
import { SwipeCard } from './components/SwipeCard'
import type { SwipeCardHandle } from './components/SwipeCard'
import { RestaurantPanel } from './components/RestaurantPanel'
import { OnboardingScreen } from './components/OnboardingScreen'
import { SessionSummary } from './components/SessionSummary'
import { AuthMenu } from './components/AuthMenu'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import { EmailVerification } from './components/EmailVerification'
import { ProfilePage } from './components/ProfilePage'
import { InsightsScreen } from './components/Insights'
import { PaywallSheet } from './components/PaywallSheet'
import { ConsentBanner } from './components/ConsentBanner'
import { LegalPage } from './components/LegalPages'
import { LocationConsentModal } from './components/LocationConsentModal'
import { InstallPrompt } from './InstallPrompt'
import { useInstall } from './useInstall'
import './App.css'

const DIETARY_KEY = 'cravings_dietary'

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

function AppHeader({ user, isPremium, onLogin, onRegister, onProfile, onInsights, onLogout, isStandalone, onInstall }: {
  user: UserInfo | null
  isPremium: boolean
  onLogin: () => void
  onRegister: () => void
  onProfile: () => void
  onInsights: () => void
  onLogout: () => void
  isStandalone: boolean
  onInstall: () => void
}) {
  return (
    <header className="app-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="app-header-emoji">🍽️</span>
        <h1 className="app-title">Cravings</h1>
      </div>
      <AuthMenu user={user} isPremium={isPremium} onLogin={onLogin} onRegister={onRegister} onProfile={onProfile} onInsights={onInsights} onLogout={onLogout} isStandalone={isStandalone} onInstall={onInstall} />
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

type Screen = 'onboarding' | 'swipe' | 'restaurants' | 'summary' | 'login' | 'register' | 'verify' | 'profile' | 'insights' | 'privacy' | 'terms'

export default function App() {
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
  const [cardKey, setCardKey] = useState(0)
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(null)
  const [pendingVerifyEmail, setPendingVerifyEmail] = useState('')
  const [guestDietary, setGuestDietary] = useState<GuestPrefs>(EMPTY_DIETARY)
  const [paywall, setPaywall] = useState<{ open: boolean; context: string }>({ open: false, context: '' })
  const isPremium = effectivePremium(currentUser)

  // Recommender seam: owns Swipe Session state (sessionId, seenIds, history) and
  // the Guest/Registered split. App never branches on identity for recommend/swipe.
  const { rec, history: swipeHistory, count: swipeCount } = useRecommender(currentUser, guestDietary)

  const install = useInstall()
  const [consentDismissed, setConsentDismissed] = useState(false)

  const { requestLocation } = useLocation()
  const { needsConsent, gate, allow, deny } = useLocationConsent()

  function navigateTo(next: Screen) {
    setPrevScreen(screen)
    setScreen(next)
  }

  function navigateBack() {
    setScreen(prevScreen === screen ? 'swipe' : prevScreen)
  }

  useEffect(() => {
    // Route a server 401 (expired/invalid token) back to onboarding instead of
    // window.location.reload(), which is a no-op inside the Capacitor WebView.
    // Clearing currentUser flips identity → the seam rebuilds a fresh session.
    setSessionExpiredHandler(() => {
      setCurrentUser(null)
      setScreen('onboarding')
    })
  }, [])

  useEffect(() => {
    // If consent was already given in a prior session, gate the install prompt immediately.
    void storage.get('cravings_consent').then(v => { if (v) setConsentDismissed(true) })
  }, [])

  const refetchingUserRef = useRef(false)

  useEffect(() => {
    // Refetch user on resume from background so webhook-granted premium reflects.
    // Desktop tab-switch fires both 'visibilitychange' and 'focus' together;
    // the in-flight guard collapses that pair into a single getMe() call.
    async function onVisible() {
      if (refetchingUserRef.current) return
      const token = await getToken()
      if (!token) return
      refetchingUserRef.current = true
      try {
        const me = await getMe()
        setCurrentUser(me)
      } finally {
        refetchingUserRef.current = false
      }
    }
    const onVisibilityChange = () => { if (document.visibilityState === 'visible') void onVisible() }
    const onFocus = () => void onVisible()
    document.addEventListener('visibilitychange', onVisibilityChange)
    window.addEventListener('focus', onFocus)
    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange)
      window.removeEventListener('focus', onFocus)
    }
  }, [])

  useEffect(() => {
    async function init() {
      try {
        const storedDietary = await loadDietaryFromStorage()
        setGuestDietary(storedDietary)
        const token = await getToken()
        if (token) {
          const me = await getMe()
          setCurrentUser(me)
          const params = new URLSearchParams(window.location.search)
          const checkout = params.get('checkout')
          if (checkout === 'success') {
            // Stripe redirect back — premium granted by webhook; refetch me
            window.history.replaceState({}, '', window.location.pathname)
            setScreen('insights')
          } else if (checkout === 'cancel') {
            window.history.replaceState({}, '', window.location.pathname)
            setScreen('swipe')
            setPaywall({ open: true, context: '' })
            await loadNextCard()
          } else if (!me.onboarding_complete) {
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
      const next = await rec.next()
      if (!next) {
        setFood(null)
        setError('No more items available.')
      } else {
        setFood(next)
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
    rec.setDietary?.(dietary)
    rec.reset()
    setScreen('swipe')
    await loadNextCard()
  }, [currentUser, rec])

  const handleOnboardingSkip = useCallback(async (dietary: GuestPrefs) => {
    await saveDietaryToStorage(dietary)
    setGuestDietary(dietary)
    rec.setDietary?.(dietary)
    rec.reset()
    setScreen('swipe')
    await loadNextCard()
  }, [rec])

  async function handleNewSession() {
    rec.reset()
    setScreen('swipe')
    await loadNextCard()
  }

  const handleSwipe = useCallback(async (direction: SwipeDirection) => {
    if (!food || swiping) return
    setSwiping(true)
    const swipedFood = food

    try {
      const outcome = await rec.swipe(swipedFood, direction)

      if (outcome.sessionComplete) {
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

        await gate(doNearby, () => setRestaurants([]))
      } else {
        await loadNextCard()
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSwiping(false)
    }
  }, [food, swiping, rec, requestLocation, gate])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (screen === 'restaurants') {
        if (e.key === 'Enter' || e.key === 'ArrowRight') void handleDismissPanel()
        return
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
    setGuestDietary(await loadDietaryFromStorage())
    setScreen('onboarding')
  }

  function handleUpgrade(context: string) {
    if (!currentUser?.is_registered) {
      navigateTo('register')
      return
    }
    setPaywall({ open: true, context })
  }

  async function handlePurchaseSuccess() {
    const me = await getMe()
    setCurrentUser(me)
    setPaywall({ open: false, context: '' })
    setScreen('insights')
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
    isPremium,
    onLogin: () => navigateTo('login'),
    onRegister: () => navigateTo('register'),
    onProfile: () => navigateTo('profile'),
    onInsights: () => navigateTo('insights'),
    onLogout: () => void handleLogout(),
    isStandalone: install.isStandalone,
    onInstall: () => {
      if (install.bucket === 'event') install.promptInstall()
      else install.forceShow()
    },
  }

  function openLegal(doc: 'privacy' | 'terms') {
    setPrevScreen(screen)
    setScreen(doc)
  }

  return (
    <div className="app">
      <AppHeader {...authMenuProps} />
      <ConsentBanner onOpenPrivacy={() => openLegal('privacy')} onDismiss={() => setConsentDismissed(true)} />
      <InstallPrompt {...install} gated={consentDismissed && screen !== 'onboarding'} />

      {screen === 'login' && (
        <LoginForm
          onSuccess={user => { setCurrentUser(user); navigateBack(); void loadNextCard() }}
          onSwitchToRegister={() => setScreen('register')}
          onBack={navigateBack}
          onNeedsVerification={email => { setPendingVerifyEmail(email); setScreen('verify') }}
        />
      )}

      {screen === 'register' && (
        <RegisterForm
          onNeedsVerification={email => { setPendingVerifyEmail(email); setScreen('verify') }}
          onSwitchToLogin={() => setScreen('login')}
          onBack={navigateBack}
          isGuest={currentUser !== null && !currentUser.is_registered}
          onOpenTerms={() => openLegal('terms')}
          onOpenPrivacy={() => openLegal('privacy')}
        />
      )}

      {screen === 'verify' && (
        <EmailVerification
          email={pendingVerifyEmail}
          onVerified={user => { setCurrentUser(user); setPendingVerifyEmail(''); setScreen('swipe'); void loadNextCard() }}
          onBack={() => setScreen('login')}
        />
      )}

      {screen === 'profile' && currentUser && (
        <ProfilePage
          user={currentUser}
          isPremium={isPremium}
          onBack={navigateBack}
          onViewInsights={() => navigateTo('insights')}
          onDeleteAccount={() => {
            setCurrentUser(null)
            setGuestDietary(EMPTY_DIETARY)
            setScreen('onboarding')
          }}
        />
      )}

      {screen === 'insights' && (
        <InsightsScreen
          isPremium={isPremium}
          onBack={navigateBack}
          onUpgrade={handleUpgrade}
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

      {screen === 'swipe' && (
        <>
          <SessionProgress count={swipeCount} total={SESSION_MAX} />
          {error && <p className="error-msg">{error}</p>}
          <div className="card-wrap">
            <div key={cardKey} className="card-enter">
              {food ? (
                <SwipeCard
                  ref={swipeCardRef}
                  food={food}
                  onSwipe={d => void handleSwipe(d)}
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

      <PaywallSheet
        open={paywall.open}
        context={paywall.context}
        onClose={() => setPaywall(p => ({ ...p, open: false }))}
        onSuccess={() => void handlePurchaseSuccess()}
      />

      {/* Location consent overlay — shown before first nearby lookup */}
      <LocationConsentModal
        open={needsConsent}
        onAllow={() => void allow()}
        onDeny={() => void deny()}
        onOpenPrivacy={() => openLegal('privacy')}
      />

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
