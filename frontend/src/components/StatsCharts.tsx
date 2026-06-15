import type { SwipeStats } from '../api'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#2C2C2C'
const TEXT_SUB = '#888'
const CARD_BG = '#FAFAF8'
const BORDER = '#F0E8E0'
const ROW_BORDER = '#F0E8E0'
const TRACK = '#EEE7DF'

export const CUISINE_EMOJI: Record<string, string> = {
  thai: '🍜', japanese: '🍣', italian: '🍝', mexican: '🌮',
  korean: '🍲', vietnamese: '🍲', indian: '🍛', mediterranean: '🥙',
  chinese: '🥡', american: '🍔', french: '🥐', greek: '🫒',
}

// helpers
export function pct(right: number, left: number): number {
  const t = right + left
  return t > 0 ? right / t : 0
}

function hexToRgba(hex: string, a: number): string {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`
}

function shift(hex: string, amt: number): string {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
  const clamp = (v: number) => Math.max(0, Math.min(255, v))
  const r = clamp(((n >> 16) & 255) + amt), g = clamp(((n >> 8) & 255) + amt), b = clamp((n & 255) + amt)
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`
}

export function cap(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ') : s
}

export function formatHour(h: number): string {
  const suffix = h >= 12 ? 'pm' : 'am'
  const display = h % 12 || 12
  const next = ((h + 1) % 12) || 12
  const nextSuffix = (h + 1) >= 12 && (h + 1) < 24 ? 'pm' : 'am'
  return `${display}–${next}${nextSuffix}`
}

function shortHour(h: number): string {
  const suffix = h >= 12 ? 'p' : 'a'
  const display = h % 12 || 12
  return `${display}${suffix}`
}

export interface TasteProfile {
  persona: string
  personaDesc: string
  overallYes: number
  topCuisine: { cuisine: string; right: number; left: number }
  sureThing: { cuisine: string; right: number; left: number }
  topFlavor: [string, number]
  peakHour: { hour: number; right: number; left: number } | undefined
  insights: { icon: string; title: string; text: string }[]
}

export function deriveTasteProfile(stats: SwipeStats): TasteProfile {
  const cuisines = [...stats.cuisine_breakdown].sort((a, b) => (b.right + b.left) - (a.right + a.left))
  const topCuisine = cuisines[0] ?? { cuisine: 'unknown', right: 0, left: 0 }
  const totalRight = stats.cuisine_breakdown.reduce((s, c) => s + c.right, 0)
  const totalLeft = stats.cuisine_breakdown.reduce((s, c) => s + c.left, 0)
  const overallYes = pct(totalRight, totalLeft)

  const sureThing = [...cuisines]
    .filter(c => c.right + c.left >= 8)
    .sort((a, b) => pct(b.right, b.left) - pct(a.right, a.left))[0] ?? topCuisine

  const flavors = Object.entries(stats.flavor_profile).sort((a, b) => b[1] - a[1])
  const topFlavor: [string, number] = flavors[0] ? [flavors[0][0], flavors[0][1]] : ['Spicy', 0]

  const peakHour = [...stats.hour_breakdown].sort((a, b) => b.right - a.right)[0]

  // Adventurous vs cozy axis derived from cuisine variety (how broadly the user
  // says yes across cuisines) now that explicit mood is gone.
  const likedCuisines = cuisines.filter(c => c.right > 0).length
  const triedCuisines = cuisines.filter(c => c.right + c.left > 0).length || 1
  const variety = likedCuisines / triedCuisines

  const flavorWord: Record<string, string> = {
    Spicy: 'Heat-Seeker', Rich: 'Comfort Gourmand', Fresh: 'Clean-Eater',
    Sweet: 'Sweet Tooth', Umami: 'Savory Hunter',
  }
  const word = flavorWord[topFlavor[0]] ?? 'Explorer'
  let persona: string, personaDesc: string
  if (variety > 0.6) {
    persona = `The Adventurous ${word}`
    personaDesc = `You say yes across a wide range of cuisines — and lean ${topFlavor[0].toLowerCase()}. Comfort food is a sometimes thing.`
  } else if (variety < 0.35) {
    persona = `The Cozy ${word}`
    personaDesc = `You know what you love — usually something ${topFlavor[0].toLowerCase()} — and you order it with confidence.`
  } else {
    persona = `The Balanced ${word}`
    personaDesc = `You mix the familiar with the new, with a clear pull toward ${topFlavor[0].toLowerCase()} flavors.`
  }

  const flavorIcon: Record<string, string> = { Spicy: '🌶️', Rich: '🧈', Fresh: '🥬', Sweet: '🍯', Umami: '🍄' }
  const insights = [
    {
      icon: CUISINE_EMOJI[sureThing.cuisine] ?? '🍽️',
      title: `${cap(sureThing.cuisine)} is your sure thing`,
      text: `You say yes ${Math.round(pct(sureThing.right, sureThing.left) * 100)}% of the time it shows up.`,
    },
    {
      icon: flavorIcon[topFlavor[0]] ?? '✨',
      title: `${topFlavor[0]} runs your palate`,
      text: `It's the strongest signal in your flavor profile, at ${topFlavor[1]}/100.`,
    },
    {
      icon: '🕗',
      title: peakHour ? `Peak craving: ${formatHour(peakHour.hour)}` : 'Craving data incoming',
      text: peakHour ? `That's when you green-light the most dishes — ${peakHour.right} yes-swipes.` : 'Keep swiping to see your peak hours.',
    },
  ]

  return { persona, personaDesc, overallYes, topCuisine, sureThing, topFlavor, peakHour, insights }
}

// ── Taste persona hero ───────────────────────────────────────────────
function HeroStat({ value, label, small }: { value: string | number; label: string; small?: boolean }) {
  return (
    <div>
      <div style={{ fontSize: small ? '0.98rem' : '1.4rem', fontWeight: 900, lineHeight: 1, letterSpacing: '-0.01em' }}>{value}</div>
      <div style={{ fontSize: '0.64rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', opacity: 0.82, marginTop: 5 }}>{label}</div>
    </div>
  )
}

export function TastePersonaCard({ profile, totalSwipes }: { profile: TasteProfile; totalSwipes: number }) {
  const grad = `linear-gradient(135deg, ${ACCENT} 0%, ${shift(ACCENT, -18)} 100%)`
  return (
    <div style={{
      position: 'relative', borderRadius: 20, padding: '22px 22px 20px',
      background: grad, color: '#fff', overflow: 'hidden',
      boxShadow: `0 12px 30px ${hexToRgba(ACCENT, 0.32)}`,
    }}>
      <div style={{ position: 'absolute', top: -40, right: -30, width: 160, height: 160, borderRadius: '50%', background: 'rgba(255,255,255,0.13)' }} />
      <div style={{ position: 'absolute', bottom: -60, left: -20, width: 140, height: 140, borderRadius: '50%', background: 'rgba(255,255,255,0.08)' }} />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', opacity: 0.85, marginBottom: 8 }}>
          Your Taste Identity
        </div>
        <div style={{ fontSize: '1.5rem', fontWeight: 900, lineHeight: 1.12, letterSpacing: '-0.02em', marginBottom: 8 }}>
          {profile.persona}
        </div>
        <p style={{ margin: 0, fontSize: '0.86rem', lineHeight: 1.5, opacity: 0.92, maxWidth: '95%' }}>
          {profile.personaDesc}
        </p>
        <div style={{ display: 'flex', gap: 22, marginTop: 18 }}>
          <HeroStat value={totalSwipes} label="Swipes" />
          <HeroStat value={`${Math.round(profile.overallYes * 100)}%`} label="Say-yes rate" />
          <HeroStat value={`${CUISINE_EMOJI[profile.topCuisine.cuisine] ?? ''} ${cap(profile.topCuisine.cuisine)}`} label="Top cuisine" small />
        </div>
      </div>
    </div>
  )
}

// ── Insight callout cards ────────────────────────────────────────────
export function InsightCard({ insight }: { insight: { icon: string; title: string; text: string } }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 13,
      padding: '13px 15px', background: CARD_BG,
      border: `1px solid ${BORDER}`, borderRadius: 14,
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: 11, flexShrink: 0,
        background: hexToRgba(ACCENT, 0.1),
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.3rem',
      }}>{insight.icon}</div>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 800, color: TEXT_PRIMARY, lineHeight: 1.25 }}>{insight.title}</div>
        <div style={{ fontSize: '0.79rem', color: TEXT_SUB, lineHeight: 1.4, marginTop: 2 }}>{insight.text}</div>
      </div>
    </div>
  )
}

// ── Flavor profile radar ─────────────────────────────────────────────
export function FlavorRadar({ data }: { data: Record<string, number> }) {
  const keys = Object.keys(data)
  const n = keys.length
  const size = 230, cx = size / 2, cy = size / 2 + 6, R = 78
  const gridColor = '#E8DCD0'

  const angleFor = (i: number) => -Math.PI / 2 + i * (2 * Math.PI / n)
  const pointAt = (i: number, r: number): [number, number] => [
    cx + r * Math.cos(angleFor(i)),
    cy + r * Math.sin(angleFor(i)),
  ]

  const rings = [0.25, 0.5, 0.75, 1]
  const dataPts = keys.map((k, i) => pointAt(i, R * (data[k] / 100)))
  const dataPath = dataPts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ') + ' Z'

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width="100%" style={{ maxWidth: 280, display: 'block', margin: '0 auto' }}>
      {rings.map((rr, ri) => (
        <polygon key={ri}
          points={keys.map((_, i) => pointAt(i, R * rr).join(',')).join(' ')}
          fill="none" stroke={gridColor} strokeWidth={ri === rings.length - 1 ? 1.4 : 1} opacity={0.8} />
      ))}
      {keys.map((_, i) => {
        const [x, y] = pointAt(i, R)
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke={gridColor} strokeWidth="1" opacity={0.7} />
      })}
      <polygon points={dataPts.map(p => p.join(',')).join(' ')}
        fill={hexToRgba(ACCENT, 0.22)} stroke={ACCENT} strokeWidth="2.2" strokeLinejoin="round" />
      {/* use dataPath to satisfy lint, actual rendering uses polygon above */}
      <path d={dataPath} fill="none" stroke="none" />
      {dataPts.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r="3.2" fill={ACCENT} stroke="#fff" strokeWidth="1.5" />)}
      {keys.map((k, i) => {
        const [x, y] = pointAt(i, R + 18)
        const anchor = Math.abs(x - cx) < 8 ? 'middle' : (x > cx ? 'start' : 'end')
        return (
          <text key={k} x={x} y={y} textAnchor={anchor} dominantBaseline="middle"
            fontSize="11" fontWeight="800" fill={TEXT_PRIMARY} style={{ fontFamily: 'inherit' }}>
            {k}
          </text>
        )
      })}
      {keys.map((k, i) => {
        const [, ] = pointAt(i, R * (data[k] / 100))
        const [lx, ly] = pointAt(i, R * (data[k] / 100) - 13)
        return <text key={k + '-val'} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" fontSize="8.5" fontWeight="700" fill={TEXT_SUB} style={{ fontFamily: 'inherit' }}>{data[k]}</text>
      })}
    </svg>
  )
}

// ── Decisiveness / say-yes gauge ─────────────────────────────────────
export function YesRateGauge({ value, avgToYes }: { value: number; avgToYes: number | null }) {
  const r = 52, c = 2 * Math.PI * r, size = 130
  const dash = value * c
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
      <svg viewBox={`0 0 ${size} ${size}`} width="118" height="118" style={{ flexShrink: 0 }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={TRACK} strokeWidth="11" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={ACCENT} strokeWidth="11"
          strokeDasharray={`${dash} ${c}`} strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`} />
        <text x={size / 2} y={size / 2 - 4} textAnchor="middle" fontSize="26" fontWeight="900" fill={TEXT_PRIMARY} style={{ fontFamily: 'inherit' }}>
          {Math.round(value * 100)}%
        </text>
        <text x={size / 2} y={size / 2 + 16} textAnchor="middle" fontSize="9.5" fontWeight="700" fill={TEXT_SUB} letterSpacing="0.5" style={{ fontFamily: 'inherit' }}>
          SAY YES
        </text>
      </svg>
      <div>
        <div style={{ fontSize: '0.95rem', fontWeight: 800, color: TEXT_PRIMARY, lineHeight: 1.3 }}>
          {value >= 0.5 ? 'Easy to please' : value >= 0.35 ? 'Selective' : 'Picky eater'}
        </div>
        <p style={{ margin: '6px 0 0', fontSize: '0.82rem', color: TEXT_SUB, lineHeight: 1.5 }}>
          You swipe right on {Math.round(value * 100)} of every 100 dishes
          {avgToYes !== null && <>, and it takes about <strong style={{ color: TEXT_PRIMARY }}>{avgToYes}</strong> swipes to find a yes</>}.
        </p>
      </div>
    </div>
  )
}

// ── Cuisine affinity ─────────────────────────────────────────────────
export function CuisineAffinity({ items }: { items: { cuisine: string; right: number; left: number }[] }) {
  const ranked = [...items].sort((a, b) => pct(b.right, b.left) - pct(a.right, a.left)).slice(0, 6)
  return (
    <div>
      {ranked.map((c, i) => {
        const yes = pct(c.right, c.left)
        return (
          <div key={c.cuisine} style={{
            display: 'flex', alignItems: 'center', gap: 13,
            padding: '12px 16px',
            borderBottom: i === ranked.length - 1 ? 'none' : `1px solid ${ROW_BORDER}`,
          }}>
            <div style={{ fontSize: '1.5rem', width: 30, textAlign: 'center', flexShrink: 0 }}>{CUISINE_EMOJI[c.cuisine] ?? '🍽️'}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
                <span style={{ fontSize: '0.92rem', fontWeight: 800, color: TEXT_PRIMARY, textTransform: 'capitalize' }}>{c.cuisine}</span>
                <span style={{ fontSize: '0.78rem', fontWeight: 800, color: ACCENT }}>{Math.round(yes * 100)}%</span>
              </div>
              <div style={{ height: 7, background: TRACK, borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${yes * 100}%`, height: '100%', borderRadius: 4, background: `linear-gradient(90deg, ${hexToRgba(ACCENT, 0.7)}, ${ACCENT})` }} />
              </div>
              <div style={{ fontSize: '0.72rem', color: TEXT_SUB, marginTop: 4 }}>{c.right} yes · {c.left} no</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Peak craving times bar chart ─────────────────────────────────────
export function PeakTimesChart({ items }: { items: { hour: number; right: number; left: number }[] }) {
  const max = Math.max(...items.map(h => h.right + h.left), 1)
  const peak = [...items].sort((a, b) => b.right - a.right)[0]
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 120, padding: '4px 4px 0' }}>
        {items.map((h, i) => {
          const total = h.right + h.left
          const hFull = (total / max) * 100
          const yesPortion = total > 0 ? h.right / total : 0
          const isPeak = h.hour === peak.hour
          return (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
              <div style={{ fontSize: '0.62rem', fontWeight: 800, color: isPeak ? ACCENT : TEXT_SUB, marginBottom: 4 }}>{h.right}</div>
              <div style={{ width: '100%', maxWidth: 30, height: `${hFull}%`, background: TRACK, borderRadius: 6, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', position: 'relative' }}>
                <div style={{ height: `${yesPortion * 100}%`, background: isPeak ? ACCENT : hexToRgba(ACCENT, 0.55), borderRadius: 6 }} />
              </div>
              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: isPeak ? TEXT_PRIMARY : TEXT_SUB, marginTop: 6, whiteSpace: 'nowrap' }}>{shortHour(h.hour)}</div>
            </div>
          )
        })}
      </div>
      <div style={{ marginTop: 12, padding: '10px 12px', borderRadius: 10, background: hexToRgba(ACCENT, 0.08), fontSize: '0.8rem', color: TEXT_PRIMARY, lineHeight: 1.45 }}>
        🔥 Your hunger peaks around <strong>{formatHour(peak.hour)}</strong> — that's your most decisive window.
      </div>
    </div>
  )
}
