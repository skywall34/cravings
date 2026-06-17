// Archetype.tsx — The 5-axis Taste Archetype framework (paid-tier foundation).
/* eslint-disable react-refresh/only-export-components */

// ── Types ─────────────────────────────────────────────────────────────
export type AxisKey = 'Heat' | 'Indulgence' | 'Texture' | 'Adventure' | 'Tempo'
export type AxesMap = Record<AxisKey, number>

export interface AxisMeta {
  label: string
  low: string
  high: string
  emoji: string
  color: string
}

export interface ArchetypeInfo {
  id: string
  name: string
  emoji: string
  oneLiner: string
  axisKey: AxisKey
  dominant: AxisKey[]
  axes: AxesMap
}

// ── The 5 taste axes ─────────────────────────────────────────────────
export const AXIS_META: Record<AxisKey, AxisMeta> = {
  Heat:       { label: 'Heat',       low: 'Mild',     high: 'Fiery',     emoji: '🌶️', color: '#D4440E' },
  Indulgence: { label: 'Indulgence', low: 'Clean',    high: 'Decadent',  emoji: '🧈', color: '#C08B30' },
  Texture:    { label: 'Texture',    low: 'Smooth',   high: 'Crunchy',   emoji: '🥨', color: '#4E9060' },
  Adventure:  { label: 'Adventure',  low: 'Familiar', high: 'Explorer',  emoji: '🧭', color: '#3D7FA0' },
  Tempo:      { label: 'Tempo',      low: 'Daytime',  high: 'Nocturnal', emoji: '🌙', color: '#6B5CB8' },
}
export const AXIS_KEYS = Object.keys(AXIS_META) as AxisKey[]

// ── Archetype catalogue ───────────────────────────────────────────────
const ARCHETYPES: Array<{
  id: string; name: string; emoji: string; oneLiner: string
  axisKey: AxisKey; test: (a: AxesMap) => boolean
}> = [
  { id: 'heat-seeker',         name: 'The Heat Seeker',        emoji: '🔥', oneLiner: "If it doesn't fight back, you're not interested.",                    axisKey: 'Heat',       test: a => a.Heat >= 75 },
  { id: 'globe-trotter',       name: 'The Globe-Trotter',      emoji: '🧭', oneLiner: 'Eleven cuisines and counting — you never swipe the same world twice.', axisKey: 'Adventure',  test: a => a.Adventure >= 72 },
  { id: 'night-indulger',      name: 'The Night Indulger',     emoji: '🌙', oneLiner: 'Angelic at noon, decadent after dark.',                               axisKey: 'Tempo',      test: a => a.Tempo >= 65 && a.Indulgence >= 60 },
  { id: 'comfort-texturalist', name: 'The Comfort Texturalist',emoji: '🥨', oneLiner: 'You eat for the crunch and the cozy, not the novelty.',               axisKey: 'Texture',    test: a => a.Texture >= 60 && a.Indulgence >= 55 },
  { id: 'clean-minimalist',    name: 'The Clean Minimalist',   emoji: '🥬', oneLiner: 'Light, fresh, precise. You leave the table feeling good.',            axisKey: 'Indulgence', test: a => a.Indulgence <= 35 },
  { id: 'creature-of-habit',   name: 'The Creature of Habit',  emoji: '🛋️', oneLiner: 'You know what you like, and what you like is excellent.',             axisKey: 'Adventure',  test: a => a.Adventure <= 30 },
  { id: 'sweet-tooth',         name: 'The Sweet Tooth',        emoji: '🍯', oneLiner: "Dessert isn't a course, it's a worldview.",                           axisKey: 'Indulgence', test: a => a.Indulgence >= 80 },
]
const BALANCED = {
  id: 'balanced', name: 'The Balanced Eater', emoji: '⚖️',
  oneLiner: "You're the rare one the model can't pin down — and that's the point.",
  axisKey: 'Texture' as AxisKey, test: () => true,
}

export function deriveArchetype(axes: AxesMap): ArchetypeInfo {
  const match = ARCHETYPES.find(a => a.test(axes)) ?? BALANCED
  const dominant = [...AXIS_KEYS]
    .sort((x, y) => Math.abs(axes[y] - 50) - Math.abs(axes[x] - 50))
    .slice(0, 2)
  return { ...match, dominant, axes }
}

export function deriveArchetypeAt(windowIndex: number, series: Record<AxisKey, number[]>): ArchetypeInfo {
  const axes = {} as AxesMap
  AXIS_KEYS.forEach(k => { axes[k] = series[k][windowIndex] })
  return deriveArchetype(axes)
}

// ── Color helpers ─────────────────────────────────────────────────────
export function archHex(hex: string, a: number): string {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`
}

export function archShift(hex: string, amt: number): string {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
  const cl = (v: number) => Math.max(0, Math.min(255, v))
  const r = cl(((n >> 16) & 255) + amt), g = cl(((n >> 8) & 255) + amt), b = cl((n & 255) + amt)
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`
}

// ── Palette (light mode, hardcoded) ──────────────────────────────────
const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#8A7E72'
const TRACK = '#EFE7DD'

// ── ArchetypeHero ─────────────────────────────────────────────────────
export function ArchetypeHero({ archetype, compact = false, nameOnly = false }: {
  archetype: ArchetypeInfo
  compact?: boolean
  nameOnly?: boolean
}) {
  const grad = `linear-gradient(140deg, ${archShift(ACCENT, 4)} 0%, ${archShift(ACCENT, -26)} 100%)`
  return (
    <div style={{
      position: 'relative', borderRadius: 22, overflow: 'hidden', color: '#fff',
      padding: compact ? '20px 20px 18px' : '26px 24px 22px',
      background: grad,
      boxShadow: `0 16px 38px ${archHex(ACCENT, 0.30)}`,
    }}>
      <div style={{ position: 'absolute', top: -50, right: -36, width: 180, height: 180, borderRadius: '50%', background: 'rgba(255,255,255,0.13)' }} />
      <div style={{ position: 'absolute', bottom: -70, left: -28, width: 150, height: 150, borderRadius: '50%', background: 'rgba(255,255,255,0.08)' }} />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <span style={{
            width: 44, height: 44, borderRadius: 13, flexShrink: 0,
            background: 'rgba(255,255,255,0.18)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem',
          }}>{archetype.emoji}</span>
          <div style={{ fontSize: '0.64rem', fontWeight: 800, letterSpacing: '0.16em', textTransform: 'uppercase', opacity: 0.85 }}>
            Your Taste Archetype
          </div>
        </div>
        <div style={{ fontSize: compact ? '1.5rem' : '1.85rem', fontWeight: 900, lineHeight: 1.08, letterSpacing: '-0.02em' }}>
          {archetype.name}
        </div>
        {!nameOnly && (
          <p style={{ margin: '10px 0 0', fontSize: '0.95rem', lineHeight: 1.45, opacity: 0.94, fontWeight: 600, fontStyle: 'italic' }}>
            &ldquo;{archetype.oneLiner}&rdquo;
          </p>
        )}
        {!nameOnly && (
          <div style={{ display: 'flex', gap: 7, marginTop: 16, flexWrap: 'wrap' }}>
            {archetype.dominant.map(k => (
              <span key={k} style={{
                display: 'inline-flex', alignItems: 'center', gap: 5,
                padding: '5px 11px 5px 9px', borderRadius: 100,
                background: 'rgba(255,255,255,0.16)', fontSize: '0.74rem', fontWeight: 800,
              }}>
                <span style={{ fontSize: '0.85rem' }}>{AXIS_META[k].emoji}</span>
                {AXIS_META[k].label}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── AxisBars — breakdown behind the identity ──────────────────────────
export function AxisBars({ axes }: { axes: AxesMap }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 17 }}>
      {AXIS_KEYS.map(k => {
        const v = axes[k]
        const m = AXIS_META[k]
        return (
          <div key={k}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 7 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: '0.9rem', fontWeight: 800, color: TEXT_PRIMARY }}>
                <span style={{ fontSize: '1rem' }}>{m.emoji}</span>{m.label}
              </span>
              <span style={{ fontSize: '0.78rem', fontWeight: 800, color: m.color }}>
                {v}<span style={{ opacity: 0.5, fontWeight: 700 }}>/100</span>
              </span>
            </div>
            <div style={{ height: 9, background: TRACK, borderRadius: 5, position: 'relative', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute', inset: 0, width: `${v}%`, borderRadius: 5,
                background: `linear-gradient(90deg, ${m.color} 0%, ${archShift(m.color, 30)} 100%)`,
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: TEXT_SUB }}>{m.low}</span>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: TEXT_SUB }}>{m.high}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── LockGlyph ─────────────────────────────────────────────────────────
export function LockGlyph({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" style={{ display: 'block' }}>
      <rect x="4.5" y="10.5" width="15" height="10" rx="2.6" />
      <path d="M7.5 10.5V8a4.5 4.5 0 0 1 9 0v2.5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" fill="none" />
    </svg>
  )
}

// ── LockOverlay — frosted gate over blurred premium content ───────────
export function LockOverlay({ eyebrow, title, sub, cta, onUnlock }: {
  eyebrow?: string
  title: string
  sub?: string
  cta: React.ReactNode
  onUnlock: () => void
}) {
  return (
    <div style={{
      position: 'absolute', inset: 0, zIndex: 3,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      textAlign: 'center', padding: '22px 26px', gap: 4,
      background: 'rgba(255,248,240,0.60)',
      backdropFilter: 'blur(2px)',
    }}>
      <div style={{
        width: 46, height: 46, borderRadius: '50%', marginBottom: 8,
        background: ACCENT, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: `0 8px 22px ${archHex(ACCENT, 0.4)}`,
      }}>
        <LockGlyph />
      </div>
      {eyebrow && (
        <div style={{ fontSize: '0.64rem', fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', color: ACCENT }}>
          {eyebrow}
        </div>
      )}
      <div style={{ fontSize: '1.08rem', fontWeight: 900, color: TEXT_PRIMARY, letterSpacing: '-0.01em' }}>{title}</div>
      {sub && (
        <p style={{ margin: '2px 0 0', fontSize: '0.84rem', lineHeight: 1.45, color: '#6B6B6B', maxWidth: 260 }}>{sub}</p>
      )}
      <button
        onClick={onUnlock}
        style={{
          marginTop: 12, padding: '12px 22px', border: 'none', borderRadius: 100,
          background: ACCENT, color: '#fff', fontSize: '0.92rem', fontWeight: 800, cursor: 'pointer',
          fontFamily: 'inherit', boxShadow: `0 6px 18px ${archHex(ACCENT, 0.32)}`,
          display: 'inline-flex', alignItems: 'center', gap: 7,
        }}
      >
        {cta}
      </button>
    </div>
  )
}

// ── PremiumBadge ──────────────────────────────────────────────────────
export function PremiumBadge({ small = false }: { small?: boolean }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: small ? '3px 9px' : '4px 11px', borderRadius: 100,
      background: 'linear-gradient(120deg, #F0B429, #D97706)',
      color: '#4A3000', fontSize: small ? '0.62rem' : '0.68rem', fontWeight: 900,
      letterSpacing: '0.08em', textTransform: 'uppercase',
      boxShadow: '0 2px 8px rgba(180,120,0,0.25)',
    }}>
      <span style={{ fontSize: small ? '0.7rem' : '0.78rem' }}>✦</span>Premium
    </span>
  )
}
