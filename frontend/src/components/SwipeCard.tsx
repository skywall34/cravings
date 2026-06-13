import { useState, useEffect, useCallback, useRef, forwardRef, useImperativeHandle } from 'react'
import type { FoodItem, SwipeDirection } from '../api'
import { assetUrl } from '../api'
import { AllergenNote } from './AllergenNote'

const CUISINE_EMOJI: Record<string, string> = {
  japanese: '🍣', mexican: '🌮', italian: '🍕', indian: '🥘',
  american: '🍔', thai: '🦐', korean: '🥩', mediterranean: '🥗',
  chinese: '🥡', french: '🥐', vietnamese: '🍜', greek: '🫒',
  middle_eastern: '🧆', spanish: '🥘', german: '🥨', eastern_european: '🥟',
  filipino: '🍚', indonesian: '🍛', brazilian: '🥩', caribbean: '🌶️', ethiopian: '🫓',
}

const CUISINE_BG: Record<string, string> = {
  japanese: '#FFF1EC', mexican: '#FFF9EC', italian: '#FFF8EC',
  indian: '#FFF3EC', american: '#FFF8EC', thai: '#FFFAEC',
  korean: '#FFF2EC', mediterranean: '#F0FFF4', chinese: '#FFF6EC',
  french: '#FFF5EC', vietnamese: '#FFF4EC', greek: '#F5FFF0',
  middle_eastern: '#FFFBEC', spanish: '#FFF7EC', german: '#FFFFF0',
  eastern_european: '#F5F5FF', filipino: '#FFF8F0', indonesian: '#FFF6EC',
  brazilian: '#F0FFF0', caribbean: '#FFF8EC', ethiopian: '#FFF4E8',
}

function buildTags(food: FoodItem): string[] {
  const tags: string[] = []
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

export interface SwipeCardHandle {
  swipe: (direction: SwipeDirection) => void
}

interface SwipeCardProps {
  food: FoodItem
  onSwipe: (direction: SwipeDirection) => void
  disabled: boolean
  swipeCount: number
  totalSwipes: number
}

const ACCENT = '#E85D04'
const SWIPE_THRESHOLD = 120

export const SwipeCard = forwardRef<SwipeCardHandle, SwipeCardProps>(function SwipeCard(
  { food, onSwipe, disabled, swipeCount, totalSwipes },
  ref,
) {
  const [animDir, setAnimDir] = useState<SwipeDirection | null>(null)
  const [neverHeld, setNeverHeld] = useState(false)
  const [cuisineImgFailed, setCuisineImgFailed] = useState(false)
  const [dragX, setDragX] = useState(0)
  const [dragY, setDragY] = useState(0)
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => { setCuisineImgFailed(false) }, [food.id])
  const neverTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const dragStart = useRef<{ x: number; y: number } | null>(null)
  const dragOriginatedOnButton = useRef(false)

  const handleSwipe = useCallback(
    (direction: SwipeDirection) => {
      if (animDir || disabled) return
      setNeverHeld(false)
      setAnimDir(direction)
      setTimeout(() => {
        setAnimDir(null)
        onSwipe(direction)
      }, 380)
    },
    [animDir, disabled, onSwipe],
  )

  useImperativeHandle(ref, () => ({ swipe: handleSwipe }), [handleSwipe])

  const startNeverHold = () => {
    neverTimer.current = setTimeout(() => setNeverHeld(true), 600)
  }
  const cancelNeverHold = () => {
    if (neverTimer.current) clearTimeout(neverTimer.current)
    setNeverHeld(false)
  }

  function handlePointerDown(clientX: number, clientY: number, target: EventTarget) {
    if ((target as HTMLElement).closest('button, a')) {
      dragOriginatedOnButton.current = true
      return
    }
    dragOriginatedOnButton.current = false
    if (animDir || disabled) return
    dragStart.current = { x: clientX, y: clientY }
    setIsDragging(true)
    setDragX(0)
    setDragY(0)
  }

  function handlePointerMove(clientX: number, clientY: number) {
    if (!isDragging || !dragStart.current) return
    setDragX(clientX - dragStart.current.x)
    setDragY(clientY - dragStart.current.y)
  }

  function handlePointerUp() {
    if (!isDragging) return
    setIsDragging(false)
    dragStart.current = null
    if (Math.abs(dragX) >= SWIPE_THRESHOLD) {
      handleSwipe(dragX > 0 ? 'right' : 'left')
    }
    setDragX(0)
    setDragY(0)
  }

  useEffect(() => {
    if (!isDragging) return
    function onMouseMove(e: MouseEvent) { handlePointerMove(e.clientX, e.clientY) }
    function onMouseUp() { handlePointerUp() }
    function onTouchMove(e: TouchEvent) {
      e.preventDefault()
      handlePointerMove(e.touches[0].clientX, e.touches[0].clientY)
    }
    function onTouchEnd() { handlePointerUp() }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    window.addEventListener('touchmove', onTouchMove, { passive: false })
    window.addEventListener('touchend', onTouchEnd)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
      window.removeEventListener('touchmove', onTouchMove)
      window.removeEventListener('touchend', onTouchEnd)
    }
  }, [isDragging, dragX])

  const cuisine = food.cuisine_type?.toLowerCase() ?? ''
  const emoji = CUISINE_EMOJI[cuisine] ?? '🍽️'
  const bgColor = CUISINE_BG[cuisine] ?? '#FFF4EC'
  const tags = buildTags(food)

  const dragRotation = isDragging ? Math.max(-20, Math.min(20, dragX / 10)) : 0
  const nopeOpacity  = isDragging ? Math.max(0, Math.min(1, -dragX / 80)) : 0
  const likeOpacity  = isDragging ? Math.max(0, Math.min(1,  dragX / 80)) : 0

  // Progress dots: filled up to swipeCount, current dot = swipeCount, rest empty
  const dots = Array.from({ length: totalSwipes }, (_, i) => {
    if (i < swipeCount) return 'past'
    if (i === swipeCount) return 'current'
    return 'future'
  })

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* Progress dots */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginBottom: 16, alignItems: 'center' }}>
        {dots.map((state, i) => (
          <div key={i} style={{
            width: 8, height: 8, borderRadius: 4,
            transition: 'all 0.3s ease',
            background: state === 'current' ? ACCENT : state === 'past' ? `${ACCENT}66` : '#E8E0D8',
            transform: state === 'current' ? 'scale(1.3)' : 'scale(1)',
          }} />
        ))}
      </div>

      {/* Card */}
      <div
        onMouseDown={(e) => handlePointerDown(e.clientX, e.clientY, e.target)}
        onTouchStart={(e) => handlePointerDown(e.touches[0].clientX, e.touches[0].clientY, e.target)}
        style={{
          background: bgColor,
          borderRadius: 24,
          boxShadow: '0 8px 40px rgba(232, 93, 4, 0.12), 0 2px 8px rgba(0,0,0,0.06)',
          overflow: 'hidden',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          cursor: isDragging ? 'grabbing' : disabled ? 'default' : 'grab',
          touchAction: 'none',
          userSelect: 'none',
          WebkitUserSelect: 'none',
          transform: animDir === 'left' || animDir === 'never'
            ? 'translateX(-120%) rotate(-15deg)'
            : animDir === 'right'
            ? 'translateX(120%) rotate(15deg)'
            : isDragging
            ? `translateX(${dragX}px) translateY(${dragY * 0.15}px) rotate(${dragRotation}deg)`
            : 'translateX(0) rotate(0deg)',
          opacity: animDir ? 0 : 1,
          transition: animDir
            ? 'transform 0.38s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease'
            : isDragging
            ? 'none'
            : 'transform 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
        }}>

        {/* Food visual */}
        {food.image_url_400 ? (
          <div style={{ position: 'relative', width: '100%', aspectRatio: '4/3', overflow: 'hidden' }}>
            <img
              srcSet={food.image_url_800 ? `${assetUrl(food.image_url_400)} 400w, ${assetUrl(food.image_url_800)} 800w` : assetUrl(food.image_url_400)}
              sizes="(max-width: 480px) 400px, 800px"
              src={assetUrl(food.image_url_400)}
              alt={food.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              loading="lazy"
            />
            {food.image_author && (
              <a
                href={food.image_source_url ?? undefined}
                target="_blank"
                rel="noreferrer"
                style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0,
                  background: 'rgba(0,0,0,0.45)', color: 'rgba(255,255,255,0.85)',
                  fontSize: '0.65rem', padding: '4px 8px', textDecoration: 'none',
                  display: 'block', lineHeight: 1.4,
                }}
              >
                Photo: {food.image_author} · {food.image_license}
              </a>
            )}
          </div>
        ) : (
          <div style={{ position: 'relative', width: '100%', aspectRatio: '4/3', overflow: 'hidden', background: bgColor }}>
            {food.cuisine_type && !cuisineImgFailed ? (
              <img
                src={assetUrl(`/cravings/images/cuisines/${food.cuisine_type.toLowerCase()}.webp`)}
                alt={food.cuisine_type}
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                loading="lazy"
                onError={() => setCuisineImgFailed(true)}
              />
            ) : (
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 96, lineHeight: 1, filter: 'drop-shadow(0 8px 16px rgba(0,0,0,0.12))' }}>
                  {emoji}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Food info */}
        <div style={{ padding: '0 28px 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {food.cuisine_type && (
            <p style={{ fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: ACCENT, margin: 0 }}>
              {food.cuisine_type}
            </p>
          )}
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#1A1A1A', lineHeight: 1.1, margin: 0 }}>
            {food.name}
          </h1>
          {tags.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {tags.map(tag => (
                <span key={tag} style={{
                  fontSize: '0.78rem', fontWeight: 600, padding: '4px 12px',
                  borderRadius: 20, border: `1.5px solid ${ACCENT}33`,
                  background: 'rgba(255,255,255,0.7)', color: ACCENT, letterSpacing: '0.02em',
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

        <div style={{ height: 1, background: '#E8E0D8', margin: '0 24px' }} />

        {/* Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 48, padding: '24px 28px 16px' }}>
          {/* Reject group */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
            <button
              style={{
                width: 72, height: 72, borderRadius: '50%',
                border: `2.5px solid ${neverHeld ? '#6B6B6B' : '#DC2626'}`,
                background: neverHeld ? 'rgba(107,107,107,0.08)' : 'rgba(220,38,38,0.06)',
                color: neverHeld ? '#6B6B6B' : '#DC2626',
                cursor: disabled ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, transition: 'transform 0.15s ease, border-color 0.15s ease, background 0.15s ease',
                boxShadow: '0 4px 16px rgba(220,38,38,0.12)',
                opacity: disabled ? 0.4 : 1,
                transform: neverHeld ? 'scale(1.18)' : 'scale(1)',
              }}
              onClick={() => { cancelNeverHold(); handleSwipe('left') }}
              disabled={disabled || !!animDir}
              onMouseEnter={e => { if (!disabled && !neverHeld) e.currentTarget.style.transform = 'scale(1.12)' }}
              onMouseLeave={e => { if (!neverHeld) e.currentTarget.style.transform = 'scale(1)' }}
              onMouseDown={startNeverHold}
              onMouseUp={cancelNeverHold}
              onTouchStart={startNeverHold}
              onTouchEnd={cancelNeverHold}
              aria-label="Not today"
            >✕</button>
            <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#DC2626', letterSpacing: '0.04em' }}>
              not today
            </span>
            {/* Never pill */}
            <button
              style={{
                padding: '3px 10px', borderRadius: 100, border: '1.5px solid #6B6B6B',
                background: 'transparent', color: '#6B6B6B', fontSize: '0.7rem',
                fontWeight: 700, cursor: disabled ? 'not-allowed' : 'pointer',
                letterSpacing: '0.04em', fontFamily: 'inherit',
                transition: 'opacity 0.2s ease, transform 0.2s ease',
                opacity: neverHeld ? 1 : 0.45,
                transform: neverHeld ? 'scale(1.05)' : 'scale(1)',
              }}
              onClick={() => { cancelNeverHold(); handleSwipe('never') }}
              disabled={disabled || !!animDir}
              onMouseEnter={e => { e.currentTarget.style.opacity = '1' }}
              onMouseLeave={e => { if (!neverHeld) e.currentTarget.style.opacity = '0.45' }}
              aria-label="Never"
            >
              Never
            </button>
          </div>

          {/* Accept group */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
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
            <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#16A34A', letterSpacing: '0.04em' }}>
              yes!
            </span>
          </div>
        </div>

        <AllergenNote style={{ margin: '0 0 16px' }} />
      </div>

      {/* Overlays */}
      <div style={{
        position: 'absolute', top: 60, left: 28, fontSize: '2.2rem',
        fontWeight: 900, letterSpacing: '0.08em', padding: '8px 20px',
        borderRadius: 12, border: '3.5px solid #DC2626', color: '#DC2626',
        background: 'rgba(220,38,38,0.05)', pointerEvents: 'none', zIndex: 10,
        transform: 'rotate(-10deg)',
        opacity: animDir === 'left' ? 1 : nopeOpacity,
        transition: isDragging ? 'none' : 'opacity 0.15s ease',
      }}>
        NOPE
      </div>
      {animDir === 'never' && (
        <div style={{
          position: 'absolute', top: 60, left: 28, fontSize: '2.2rem',
          fontWeight: 900, letterSpacing: '0.08em', padding: '8px 20px',
          borderRadius: 12, border: '3.5px solid #6B6B6B', color: '#6B6B6B',
          background: 'rgba(107,107,107,0.05)', pointerEvents: 'none', zIndex: 10,
          transform: 'rotate(-10deg)',
        }}>
          NEVER
        </div>
      )}
      <div style={{
        position: 'absolute', top: 60, right: 28, fontSize: '2.2rem',
        fontWeight: 900, letterSpacing: '0.08em', padding: '8px 20px',
        borderRadius: 12, border: '3.5px solid #16A34A', color: '#16A34A',
        background: 'rgba(22,163,74,0.05)', pointerEvents: 'none', zIndex: 10,
        transform: 'rotate(10deg)',
        opacity: animDir === 'right' ? 1 : likeOpacity,
        transition: isDragging ? 'none' : 'opacity 0.15s ease',
      }}>
        LIKE
      </div>
    </div>
  )
})
