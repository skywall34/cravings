import type { FoodItem, SwipeDirection } from '../api'

const CUISINE_EMOJI: Record<string, string> = {
  japanese: '🍣', mexican: '🌮', italian: '🍕', indian: '🥘',
  american: '🍔', thai: '🦐', korean: '🥩', mediterranean: '🥗',
  chinese: '🥡', french: '🥐', vietnamese: '🍜', greek: '🫒',
}

export interface SwipeEntry {
  food: FoodItem
  direction: SwipeDirection
}

interface SessionSummaryProps {
  swipeHistory: SwipeEntry[]
  onNewSession: () => void
  onAdjustTastes: () => void
}

export function SessionSummary({ swipeHistory, onNewSession, onAdjustTastes }: SessionSummaryProps) {
  const rightSwipes = swipeHistory.filter(s => s.direction === 'right')
  const neverSwipes = swipeHistory.filter(s => s.direction === 'never')
  const notTodayCount = swipeHistory.filter(s => s.direction === 'left').length
  const total = swipeHistory.length
  const likeRate = total > 0 ? Math.round((rightSwipes.length / total) * 100) : 0

  const cuisineCounts: Record<string, number> = {}
  rightSwipes.forEach(s => {
    const c = s.food.cuisine_type
    if (c) cuisineCounts[c] = (cuisineCounts[c] ?? 0) + 1
  })
  const topCuisineEntry = Object.entries(cuisineCounts).sort((a, b) => b[1] - a[1])[0]

  const likedFoods = rightSwipes.slice(0, 3).map(s => s.food)
  const headerEmoji = likeRate >= 60 ? '🎉' : likeRate >= 30 ? '😋' : '🤔'

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {/* Hero */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, padding: '28px 0 20px', textAlign: 'center' }}>
        <div style={{ fontSize: 52, lineHeight: 1, marginBottom: 4 }}>{headerEmoji}</div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 900, margin: 0, letterSpacing: '-0.01em', color: '#E85D04' }}>
          Session wrap-up
        </h2>
        <p style={{ fontSize: '0.88rem', color: '#6B6B6B', margin: 0 }}>
          Your taste model just got smarter.
        </p>
      </div>

      {/* Card */}
      <div style={{
        width: '100%', background: '#FFFFFF', borderRadius: 24,
        boxShadow: '0 8px 40px rgba(232, 93, 4, 0.12), 0 2px 8px rgba(0,0,0,0.06)',
        padding: '28px', display: 'flex', flexDirection: 'column', gap: 20,
      }}>

        {/* Stats row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, padding: '8px 0' }}>
            <div style={{ fontSize: '2.2rem', fontWeight: 900, lineHeight: 1, color: '#16A34A' }}>{rightSwipes.length}</div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#B0A89E', letterSpacing: '0.05em', textTransform: 'uppercase' }}>liked</div>
          </div>
          <div style={{ width: 1, height: 40, background: '#E8E0D8' }} />
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, padding: '8px 0' }}>
            <div style={{ fontSize: '2.2rem', fontWeight: 900, lineHeight: 1, color: '#DC2626' }}>{notTodayCount}</div>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#B0A89E', letterSpacing: '0.05em', textTransform: 'uppercase' }}>not today</div>
          </div>
          {neverSwipes.length > 0 && (
            <>
              <div style={{ width: 1, height: 40, background: '#E8E0D8' }} />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, padding: '8px 0' }}>
                <div style={{ fontSize: '2.2rem', fontWeight: 900, lineHeight: 1, color: '#6B6B6B' }}>{neverSwipes.length}</div>
                <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#B0A89E', letterSpacing: '0.05em', textTransform: 'uppercase' }}>never</div>
              </div>
            </>
          )}
        </div>

        {/* Top cuisine */}
        {topCuisineEntry && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px',
            borderRadius: 12, border: '1.5px solid rgba(232,93,4,0.13)',
            background: 'rgba(232,93,4,0.05)',
          }}>
            <span style={{ fontSize: '1.4rem', flexShrink: 0 }}>🏆</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#E85D04' }}>
                Top cuisine
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1A1A1A', marginTop: 1 }}>
                {topCuisineEntry[0]}
              </div>
            </div>
            <div style={{
              marginLeft: 'auto', padding: '4px 10px', borderRadius: 100,
              background: 'rgba(232,93,4,0.15)', color: '#E85D04',
              fontSize: '0.82rem', fontWeight: 800,
            }}>
              {topCuisineEntry[1]}×
            </div>
          </div>
        )}

        {/* Liked foods */}
        {likedFoods.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#B0A89E', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              You loved
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {likedFoods.map((food, i) => {
                const emoji = CUISINE_EMOJI[food.cuisine_type?.toLowerCase() ?? ''] ?? '🍽️'
                return (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '6px 12px', background: '#FFF8F0',
                    border: '1.5px solid #E8E0D8', borderRadius: 100,
                  }}>
                    <span style={{ fontSize: '1.1rem' }}>{emoji}</span>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1A1A1A' }}>{food.name}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Like rate */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#6B6B6B' }}>Like rate</span>
            <span style={{ fontSize: '0.88rem', fontWeight: 800, color: '#E85D04' }}>{likeRate}%</span>
          </div>
          <div style={{ height: 8, background: '#E8E0D8', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 4,
              width: `${likeRate}%`,
              background: 'linear-gradient(90deg, rgba(232,93,4,0.6), #E85D04)',
              transition: 'width 0.6s cubic-bezier(0.22, 1, 0.36, 1)',
            }} />
          </div>
        </div>

        {/* CTAs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <button
            style={{
              width: '100%', padding: '16px', border: 'none', borderRadius: 100,
              background: '#E85D04', color: '#FFFFFF', fontSize: '1rem', fontWeight: 700,
              cursor: 'pointer', letterSpacing: '0.02em', fontFamily: 'inherit',
              transition: 'opacity 0.15s ease, transform 0.15s ease',
              boxShadow: '0 4px 20px rgba(232,93,4,0.25)',
            }}
            onClick={onNewSession}
            onMouseEnter={e => { e.currentTarget.style.opacity = '0.9'; e.currentTarget.style.transform = 'translateY(-1px)' }}
            onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = 'translateY(0)' }}
          >
            New Session →
          </button>
          <button
            style={{
              width: '100%', padding: '14px', border: '1.5px solid #E85D04', borderRadius: 100,
              background: 'transparent', color: '#E85D04', fontSize: '0.95rem', fontWeight: 700,
              cursor: 'pointer', letterSpacing: '0.02em', fontFamily: 'inherit',
              transition: 'opacity 0.15s ease, transform 0.15s ease',
            }}
            onClick={onAdjustTastes}
            onMouseEnter={e => { e.currentTarget.style.opacity = '0.8'; e.currentTarget.style.transform = 'translateY(-1px)' }}
            onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = 'translateY(0)' }}
          >
            Adjust Tastes →
          </button>
        </div>
        <p style={{ textAlign: 'center', fontSize: '0.75rem', color: '#B0A89E', margin: '-4px 0 0', letterSpacing: '0.02em' }}>
          New Session keeps current preferences · Adjust Tastes resets them
        </p>
      </div>
    </div>
  )
}
