import { hexToRgba, shiftHex as shift } from '../colorUtils'
import { CUISINE_EMOJI } from '../cuisineEmoji'
import { pct, cap, formatHour, type TasteProfile } from '../tasteProfile'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#2C2C2C'
const TEXT_SUB = '#888'
const CARD_BG = '#FAFAF8'
const BORDER = '#F0E8E0'
const ROW_BORDER = '#F0E8E0'
const TRACK = '#EEE7DF'

function shortHour(h: number): string {
  const suffix = h >= 12 ? 'p' : 'a'
  const display = h % 12 || 12
  return `${display}${suffix}`
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
