import type { FoodItem, Restaurant } from '../api'

const CUISINE_EMOJI: Record<string, string> = {
  japanese: '🍣', mexican: '🌮', italian: '🍕', indian: '🥘',
  american: '🍔', thai: '🦐', korean: '🥩', mediterranean: '🥗',
  chinese: '🥡', french: '🥐', vietnamese: '🍜', greek: '🫒',
}

interface StarRatingProps {
  rating: number
}

function StarRating({ rating }: StarRatingProps) {
  if (!rating || rating <= 0) return null
  const full = Math.floor(rating)
  const half = rating % 1 >= 0.5
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {[...Array(5)].map((_, i) => (
        <span key={i} style={{
          color: i < full ? '#F48C06' : (i === full && half ? '#F48C06' : '#E8E0D8'),
          fontSize: '0.95rem',
          opacity: i === full && half ? 0.6 : 1,
        }}>★</span>
      ))}
      <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1A1A1A', marginLeft: 4 }}>
        {rating.toFixed(1)}
      </span>
    </span>
  )
}

interface RestaurantCardProps {
  restaurant: Restaurant
}

function RestaurantCard({ restaurant }: RestaurantCardProps) {
  const mapsHref = restaurant.maps_url ??
    `https://maps.google.com/?q=${encodeURIComponent((restaurant.name ?? '') + ' ' + (restaurant.address ?? ''))}`

  return (
    <div
      style={{
        background: '#FFF8F0', border: '1.5px solid #E8E0D8', borderRadius: 12,
        padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10,
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'rgba(232,93,4,0.35)'
        e.currentTarget.style.boxShadow = '0 4px 20px rgba(232,93,4,0.10)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = '#E8E0D8'
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3, flex: 1 }}>
          <div style={{ fontSize: '0.98rem', fontWeight: 700, color: '#1A1A1A', lineHeight: 1.2 }}>
            {restaurant.name}
          </div>
          {restaurant.address && (
            <div style={{ fontSize: '0.8rem', color: '#6B6B6B' }}>{restaurant.address}</div>
          )}
        </div>
        <a
          href={mapsHref}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px',
            borderRadius: 100, background: '#E85D04', color: '#FFFFFF',
            textDecoration: 'none', fontSize: '0.78rem', fontWeight: 700,
            whiteSpace: 'nowrap', flexShrink: 0, transition: 'opacity 0.15s ease',
            letterSpacing: '0.02em',
          }}
          onMouseEnter={e => { e.currentTarget.style.opacity = '0.85' }}
          onMouseLeave={e => { e.currentTarget.style.opacity = '1' }}
        >
          <span style={{ fontSize: '0.8rem' }}>↗</span> Maps
        </a>
      </div>

      {restaurant.rating > 0 && (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <StarRating rating={restaurant.rating} />
        </div>
      )}
    </div>
  )
}

interface RestaurantPanelProps {
  food: FoodItem | null
  restaurants: Restaurant[] | null
  rateLimitedSeconds?: number | null
  onDismiss: () => void
}

export function RestaurantPanel({ food, restaurants, rateLimitedSeconds, onDismiss }: RestaurantPanelProps) {
  const cuisine = food?.cuisine_type?.toLowerCase() ?? ''
  const emoji = CUISINE_EMOJI[cuisine] ?? '🍽️'

  return (
    <div style={{
      background: '#FFFFFF', borderRadius: 24,
      boxShadow: '0 8px 40px rgba(232, 93, 4, 0.12), 0 2px 8px rgba(0,0,0,0.06)',
      padding: '32px 28px 24px', display: 'flex', flexDirection: 'column', gap: 20,
    }}>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, paddingBottom: 4 }}>
        <div style={{ fontSize: 48, lineHeight: 1, flexShrink: 0 }}>{emoji}</div>
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#1A1A1A', lineHeight: 1.2 }}>
            Restaurants near you
          </div>
          {food?.name && (
            <div style={{ fontSize: '0.88rem', color: '#6B6B6B', marginTop: 2 }}>
              serving <strong style={{ color: '#E85D04' }}>{food.name}</strong>
            </div>
          )}
        </div>
      </div>

      {restaurants === null ? (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', gap: 14, padding: '32px 0',
        }}>
          <div style={{
            width: 36, height: 36, border: '3px solid #E8E0D8',
            borderTopColor: '#E85D04', borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }} />
          <span style={{ fontSize: '0.88rem', color: '#6B6B6B' }}>Finding nearby spots…</span>
        </div>
      ) : restaurants.length === 0 ? (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          padding: '24px 0', textAlign: 'center', gap: 8,
        }}>
          <div style={{ fontSize: 40 }}>{rateLimitedSeconds ? '⏳' : '📍'}</div>
          <p style={{ margin: 0, color: '#6B6B6B', fontSize: '0.92rem', lineHeight: 1.5 }}>
            {rateLimitedSeconds
              ? `Slow down — too many lookups. Try again in ${rateLimitedSeconds}s.`
              : 'No nearby restaurants found. Try enabling location for better results.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {restaurants.slice(0, 5).map((r, i) => (
            <RestaurantCard key={i} restaurant={r} />
          ))}
        </div>
      )}

      <button
        style={{
          width: '100%', padding: '16px', border: 'none', borderRadius: 100,
          background: '#E85D04', color: '#FFFFFF', fontSize: '1rem', fontWeight: 700,
          cursor: 'pointer', letterSpacing: '0.02em', fontFamily: 'inherit',
          transition: 'opacity 0.15s ease, transform 0.15s ease',
          boxShadow: '0 4px 20px rgba(232,93,4,0.25)',
        }}
        onClick={onDismiss}
        onMouseEnter={e => {
          e.currentTarget.style.opacity = '0.9'
          e.currentTarget.style.transform = 'translateY(-1px)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.opacity = '1'
          e.currentTarget.style.transform = 'translateY(0)'
        }}
      >
        Next food →
      </button>

      <p style={{
        textAlign: 'center', fontSize: '0.75rem', color: '#B0A89E',
        margin: '-8px 0 0', letterSpacing: '0.02em',
      }}>
        Press Enter or → to continue
      </p>
    </div>
  )
}
