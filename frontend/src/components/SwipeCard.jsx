import { useState, useCallback, forwardRef, useImperativeHandle } from 'react'

const CUISINE_EMOJI = {
  japanese: '🍣', mexican: '🌮', italian: '🍕', indian: '🥘',
  american: '🍔', thai: '🦐', korean: '🥩', mediterranean: '🥗',
  chinese: '🥡', french: '🥐', vietnamese: '🍜', greek: '🫒',
}

const CUISINE_BG = {
  japanese: '#FFF1EC', mexican: '#FFF9EC', italian: '#FFF8EC',
  indian: '#FFF3EC', american: '#FFF8EC', thai: '#FFFAEC',
  korean: '#FFF2EC', mediterranean: '#F0FFF4', chinese: '#FFF6EC',
  french: '#FFF5EC', vietnamese: '#FFF4EC', greek: '#F5FFF0',
}

function buildTags(food) {
  const tags = []
  if (food.spice_level > 0.6) tags.push('Spicy')
  if (food.sweetness > 0.6) tags.push('Sweet')
  if (food.richness > 0.7) tags.push('Rich')
  if (food.sauce_heaviness > 0.7) tags.push('Saucy')
  if (food.veggie_density > 0.7) tags.push('Veggie')
  if (food.dairy_content > 0.5) tags.push('Dairy')
  if (food.protein_type && food.protein_type !== 'none' && food.protein_type !== 'other') {
    tags.push(food.protein_type.charAt(0).toUpperCase() + food.protein_type.slice(1))
  }
  return tags.slice(0, 3)
}

export const SwipeCard = forwardRef(function SwipeCard({ food, onSwipe, disabled }, ref) {
  const [animDir, setAnimDir] = useState(null) // 'left' | 'right' | null

  const handleSwipe = useCallback((direction) => {
    if (animDir || disabled) return
    setAnimDir(direction)
    setTimeout(() => {
      setAnimDir(null)
      onSwipe(direction)
    }, 380)
  }, [animDir, disabled, onSwipe])

  useImperativeHandle(ref, () => ({ swipe: handleSwipe }), [handleSwipe])

  const cuisine = food.cuisine_type?.toLowerCase() || ''
  const emoji = CUISINE_EMOJI[cuisine] || '🍽️'
  const bgColor = CUISINE_BG[cuisine] || '#FFF4EC'
  const tags = buildTags(food)

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <div style={{
        background: bgColor,
        borderRadius: 24,
        boxShadow: '0 8px 40px rgba(232, 93, 4, 0.12), 0 2px 8px rgba(0,0,0,0.06)',
        overflow: 'hidden',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        transform: animDir === 'left'
          ? 'translateX(-120%) rotate(-15deg)'
          : animDir === 'right'
          ? 'translateX(120%) rotate(15deg)'
          : 'translateX(0) rotate(0deg)',
        opacity: animDir ? 0 : 1,
        transition: animDir
          ? 'transform 0.38s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease'
          : 'none',
      }}>

        {/* Emoji */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '36px 24px 24px',
        }}>
          <span style={{
            fontSize: 96,
            lineHeight: 1,
            filter: 'drop-shadow(0 8px 16px rgba(0,0,0,0.12))',
          }}>
            {emoji}
          </span>
        </div>

        {/* Food info */}
        <div style={{ padding: '0 28px 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {food.cuisine_type && (
            <p style={{
              fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.1em',
              textTransform: 'uppercase', color: '#E85D04', margin: 0,
            }}>
              {food.cuisine_type}
            </p>
          )}

          <h1 style={{
            fontSize: '2rem', fontWeight: 800, color: '#1A1A1A', lineHeight: 1.1, margin: 0,
          }}>
            {food.name}
          </h1>

          {tags.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {tags.map(tag => (
                <span key={tag} style={{
                  fontSize: '0.78rem', fontWeight: 600, padding: '4px 12px',
                  borderRadius: 20, border: '1.5px solid rgba(232,93,4,0.3)',
                  background: 'rgba(255,255,255,0.7)', color: '#E85D04', letterSpacing: '0.02em',
                }}>
                  {tag}
                </span>
              ))}
            </div>
          )}

          {food.description && (
            <p style={{ fontSize: '0.92rem', color: '#6B6B6B', lineHeight: 1.6, margin: 0 }}>
              {food.description}
            </p>
          )}
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: '#E8E0D8', margin: '0 24px' }} />

        {/* Buttons */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: 32, padding: '24px 28px 8px', position: 'relative',
        }}>
          <button
            style={{
              width: 72, height: 72, borderRadius: '50%',
              border: '2.5px solid #DC2626', background: 'rgba(220,38,38,0.06)',
              color: '#DC2626', cursor: disabled ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 28, transition: 'transform 0.15s ease',
              boxShadow: '0 4px 16px rgba(220,38,38,0.12)', opacity: disabled ? 0.4 : 1,
            }}
            onClick={() => handleSwipe('left')}
            disabled={disabled || !!animDir}
            onMouseEnter={e => { if (!disabled) e.currentTarget.style.transform = 'scale(1.12)' }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)' }}
            aria-label="Not for me"
          >✕</button>

          <div style={{
            display: 'flex', gap: 48, position: 'absolute',
            bottom: -4, left: '50%', transform: 'translateX(-50%)',
          }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#DC2626', letterSpacing: '0.04em' }}>
              not for me
            </span>
            <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#16A34A', letterSpacing: '0.04em' }}>
              yes!
            </span>
          </div>

          <button
            style={{
              width: 72, height: 72, borderRadius: '50%',
              border: 'none', background: '#16A34A', color: '#FFFFFF',
              cursor: disabled ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 28, transition: 'transform 0.15s ease',
              boxShadow: '0 4px 16px rgba(22,163,74,0.30)', opacity: disabled ? 0.4 : 1,
            }}
            onClick={() => handleSwipe('right')}
            disabled={disabled || !!animDir}
            onMouseEnter={e => { if (!disabled) e.currentTarget.style.transform = 'scale(1.12)' }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)' }}
            aria-label="Yes"
          >✓</button>
        </div>

        <p style={{
          textAlign: 'center', fontSize: '0.75rem', color: '#B0A89E',
          margin: '12px 0 20px', letterSpacing: '0.02em',
        }}>
          ← / → arrow keys to swipe
        </p>
      </div>

      {/* NOPE overlay */}
      {animDir === 'left' && (
        <div style={{
          position: 'absolute', top: 60, left: 28, fontSize: '2.2rem',
          fontWeight: 900, letterSpacing: '0.08em', padding: '8px 20px',
          borderRadius: 12, border: '3.5px solid #DC2626', color: '#DC2626',
          background: 'rgba(220,38,38,0.05)', pointerEvents: 'none', zIndex: 10,
          transform: 'rotate(-10deg)',
        }}>
          NOPE
        </div>
      )}

      {/* LIKE overlay */}
      {animDir === 'right' && (
        <div style={{
          position: 'absolute', top: 60, right: 28, fontSize: '2.2rem',
          fontWeight: 900, letterSpacing: '0.08em', padding: '8px 20px',
          borderRadius: 12, border: '3.5px solid #16A34A', color: '#16A34A',
          background: 'rgba(22,163,74,0.05)', pointerEvents: 'none', zIndex: 10,
          transform: 'rotate(10deg)',
        }}>
          LIKE
        </div>
      )}
    </div>
  )
})
