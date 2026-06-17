// Insights.tsx — Paid hub: full archetype, 5-axis breakdown, drift tracking, monthly recap.
// Free users see the archetype name only; premium sections are blurred behind LockOverlay.
// MOCK DATA: all axes/drift are placeholders until a backend projection endpoint exists.

import { useRef, useState } from 'react'
import {
  MOCK_DRIFT, MOCK_AXES, AXIS_META, AXIS_KEYS,
  deriveArchetype, deriveArchetypeAt,
  ArchetypeHero, AxisBars, LockOverlay, LockGlyph, PremiumBadge,
  archHex, archShift,
  type ArchetypeInfo,
} from './Archetype'
import { FlavorRadar } from './StatsCharts'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#8A7E72'
const CARD_BG = '#FFFFFF'
const BORDER = '#F0E8E0'

// ── Drift line chart ───────────────────────────────────────────────────
function DriftChart() {
  const { windows, series } = MOCK_DRIFT
  const W = 320, H = 168, padL = 8, padR = 8, padT = 14, padB = 24
  const innerW = W - padL - padR, innerH = H - padT - padB
  const n = windows.length
  const x = (i: number) => padL + (innerW * i) / (n - 1)
  const y = (v: number) => padT + innerH * (1 - v / 100)
  const grid = '#EEE4D8'

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: 'block' }}>
        {[0, 25, 50, 75, 100].map(g => (
          <line key={g} x1={padL} y1={y(g)} x2={W - padR} y2={y(g)} stroke={grid} strokeWidth="1" />
        ))}
        {windows.map((w, i) => (
          <text key={w} x={x(i)} y={H - 7} textAnchor="middle" fontSize="10" fontWeight="700" fill={TEXT_SUB} style={{ fontFamily: 'inherit' }}>{w}</text>
        ))}
        {AXIS_KEYS.map(k => {
          const pts = series[k].map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`)
          const d = 'M' + pts.join(' L')
          const last = series[k][n - 1]
          return (
            <g key={k}>
              <path d={d} fill="none" stroke={AXIS_META[k].color} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx={x(n - 1)} cy={y(last)} r="3.4" fill={AXIS_META[k].color} stroke="#fff" strokeWidth="1.5" />
            </g>
          )
        })}
      </svg>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 14px', marginTop: 8, justifyContent: 'center' }}>
        {AXIS_KEYS.map(k => (
          <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: '0.72rem', fontWeight: 700, color: TEXT_PRIMARY }}>
            <span style={{ width: 9, height: 9, borderRadius: '50%', background: AXIS_META[k].color }} />
            {AXIS_META[k].label}
          </span>
        ))}
      </div>
    </div>
  )
}

// ── Delta callout chips (biggest movers) ───────────────────────────────
function DriftDeltas() {
  const { series } = MOCK_DRIFT
  const deltas = AXIS_KEYS.map(k => {
    const s = series[k]
    return { k, delta: s[s.length - 1] - s[0] }
  }).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
  const cardBg = '#FFFFFF'
  const border = '#F0E8E0'
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(92px, 1fr))', gap: 8 }}>
      {deltas.slice(0, 3).map(({ k, delta }) => {
        const up = delta >= 0
        const m = AXIS_META[k]
        return (
          <div key={k} style={{ background: cardBg, border: `1px solid ${border}`, borderRadius: 13, padding: '11px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.74rem', fontWeight: 800, color: TEXT_SUB, marginBottom: 4 }}>
              <span style={{ fontSize: '0.85rem' }}>{m.emoji}</span>{m.label}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span style={{ fontSize: '1.35rem', fontWeight: 900, color: m.color, letterSpacing: '-0.02em' }}>
                {up ? '+' : '−'}{Math.abs(delta)}
              </span>
              <span style={{ fontSize: '0.9rem', color: m.color, fontWeight: 800 }}>{up ? '↑' : '↓'}</span>
            </div>
            <div style={{ fontSize: '0.64rem', color: TEXT_SUB, fontWeight: 600, marginTop: 1 }}>since {MOCK_DRIFT.windows[0]}</div>
          </div>
        )
      })}
    </div>
  )
}

// ── "Your archetype evolved" banner ────────────────────────────────────
function ArchetypeShiftBanner() {
  const past = deriveArchetypeAt(0)
  const now = deriveArchetypeAt(MOCK_DRIFT.windows.length - 1)
  if (past.id === now.id) return null
  return (
    <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 16, padding: '15px 16px' }}>
      <div style={{ fontSize: '0.66rem', fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: ACCENT, marginBottom: 11 }}>
        You&rsquo;ve evolved
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <ShiftChip archetype={past} faded />
        <span style={{ color: ACCENT, fontSize: '1.2rem', fontWeight: 900, flexShrink: 0 }}>→</span>
        <ShiftChip archetype={now} />
      </div>
    </div>
  )
}

function ShiftChip({ archetype, faded }: { archetype: ArchetypeInfo; faded?: boolean }) {
  return (
    <div style={{ flex: 1, minWidth: 0, opacity: faded ? 0.62 : 1 }}>
      <div style={{ fontSize: '1.4rem', lineHeight: 1 }}>{archetype.emoji}</div>
      <div style={{ fontSize: '0.86rem', fontWeight: 800, color: faded ? TEXT_SUB : ACCENT, marginTop: 4, lineHeight: 1.2 }}>{archetype.name}</div>
    </div>
  )
}

// ── Monthly recap — portrait, screenshot-shaped ─────────────────────
function MonthlyRecap({ month = 'June' }: { month?: string }) {
  const now = deriveArchetypeAt(MOCK_DRIFT.windows.length - 1)
  const top = deriveArchetypeAt(0)
  const grad = `linear-gradient(165deg, ${archShift(ACCENT, 8)} 0%, ${archShift(ACCENT, -34)} 62%, ${archShift(ACCENT, -54)} 100%)`
  const mover = AXIS_KEYS.map(k => { const s = MOCK_DRIFT.series[k]; return { k, d: s[s.length - 1] - s[0] } })
    .sort((a, b) => Math.abs(b.d) - Math.abs(a.d))[0]
  return (
    <div style={{
      position: 'relative', width: '100%', maxWidth: 320, margin: '0 auto',
      aspectRatio: '9 / 16', borderRadius: 24, overflow: 'hidden',
      color: '#fff', background: grad,
      boxShadow: `0 20px 50px ${archHex(ACCENT, 0.34)}`,
      padding: '26px 24px', display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ position: 'absolute', top: -60, right: -50, width: 200, height: 200, borderRadius: '50%', background: 'rgba(255,255,255,0.10)' }} />
      <div style={{ position: 'absolute', bottom: -40, left: -50, width: 170, height: 170, borderRadius: '50%', background: 'rgba(255,255,255,0.07)' }} />
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.66rem', fontWeight: 800, letterSpacing: '0.16em', textTransform: 'uppercase', opacity: 0.85 }}>
            {month} · in your taste
          </span>
          <span style={{ fontSize: '0.8rem', fontWeight: 900, letterSpacing: '-0.01em' }}>Cravings</span>
        </div>
        <div style={{ marginTop: 'auto', marginBottom: 'auto', textAlign: 'center', padding: '10px 0' }}>
          <div style={{ fontSize: '3.4rem', lineHeight: 1, marginBottom: 10 }}>{now.emoji}</div>
          <div style={{ fontSize: '0.66rem', fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', opacity: 0.8, marginBottom: 6 }}>
            You&rsquo;re now
          </div>
          <div style={{ fontSize: '1.7rem', fontWeight: 900, lineHeight: 1.1, letterSpacing: '-0.02em' }}>{now.name}</div>
          {top.id !== now.id && (
            <div style={{ fontSize: '0.8rem', opacity: 0.82, marginTop: 8, fontWeight: 600 }}>
              up from {top.name}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <RecapStat big={`${mover.d >= 0 ? '+' : ''}${mover.d}`} label={`${AXIS_META[mover.k].label} this month`} />
          <RecapStat big="🌶️ Thai" label="Top cuisine" />
          <RecapStat big="84%" label="Say-yes rate" />
        </div>
      </div>
    </div>
  )
}

function RecapStat({ big, label }: { big: string; label: string }) {
  return (
    <div style={{
      flex: 1, background: 'rgba(255,255,255,0.14)', borderRadius: 13,
      padding: '11px 9px', textAlign: 'center', backdropFilter: 'blur(3px)',
    }}>
      <div style={{ fontSize: '1.05rem', fontWeight: 900, lineHeight: 1.1, letterSpacing: '-0.01em' }}>{big}</div>
      <div style={{ fontSize: '0.58rem', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', opacity: 0.82, marginTop: 4, lineHeight: 1.2 }}>{label}</div>
    </div>
  )
}

// ── Section wrapper ────────────────────────────────────────────────────
interface InsightSectionProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  locked: boolean
  lockEyebrow?: string
  lockTitle: string
  lockSub?: string
  onUnlock: () => void
}

function InsightSection({ title, subtitle, children, locked, lockEyebrow, lockTitle, lockSub, onUnlock }: InsightSectionProps) {
  return (
    <div style={{ marginTop: 26 }}>
      <h3 style={{ margin: '0 0 2px', fontSize: '0.74rem', fontWeight: 800, color: TEXT_SUB, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{title}</h3>
      {subtitle && <p style={{ margin: '0 0 12px', fontSize: '0.82rem', color: TEXT_SUB, lineHeight: 1.4 }}>{subtitle}</p>}
      {!subtitle && <div style={{ height: 12 }} />}
      <div style={{ position: 'relative', borderRadius: 18, overflow: 'hidden' }}>
        <div style={{ filter: locked ? 'blur(9px)' : 'none', pointerEvents: locked ? 'none' : 'auto', userSelect: locked ? 'none' : 'auto' }}>
          {children}
        </div>
        {locked && (
          <LockOverlay
            eyebrow={lockEyebrow ?? 'Premium'}
            title={lockTitle}
            sub={lockSub}
            cta={<><LockGlyph size={14} /> Unlock for $4.99</>}
            onUnlock={onUnlock}
          />
        )}
      </div>
    </div>
  )
}

// ── ShareGlyph ─────────────────────────────────────────────────────────
function ShareGlyph({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
      <path d="M8.6 10.5l6.8-4M8.6 13.5l6.8 4" />
    </svg>
  )
}

// ── InsightsScreen — main export ────────────────────────────────────────
interface InsightsScreenProps {
  isPremium: boolean
  onBack: () => void
  onUpgrade: (context: string) => void
}

export function InsightsScreen({ isPremium, onBack, onUpgrade }: InsightsScreenProps) {
  const archetype = deriveArchetype(MOCK_AXES)
  const recapRef = useRef<HTMLDivElement>(null)
  const [shared, setShared] = useState(false)

  const lockProps = (title: string, sub?: string) => ({
    lockEyebrow: 'Premium',
    lockTitle: title,
    lockSub: sub,
    onUnlock: () => onUpgrade('insights'),
  })

  return (
    <div style={{ width: '100%', maxWidth: 440, margin: '0 auto', padding: '8px 4px 60px' }}>
      <button onClick={onBack} style={backBtnStyle}>← Back</button>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '18px 0 18px' }}>
        <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, color: TEXT_PRIMARY, letterSpacing: '-0.02em' }}>Your Insights</h2>
        {isPremium
          ? <PremiumBadge />
          : <span style={{ fontSize: '0.72rem', fontWeight: 800, color: TEXT_SUB, letterSpacing: '0.04em' }}>FREE</span>}
      </div>

      {/* Archetype hero — free sees name only */}
      <ArchetypeHero archetype={archetype} nameOnly={!isPremium} />

      {!isPremium && (
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 10, padding: '13px 15px', background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 14 }}>
          <span style={{ fontSize: '1.3rem' }}>👀</span>
          <span style={{ fontSize: '0.86rem', color: TEXT_PRIMARY, fontWeight: 600, lineHeight: 1.4, flex: 1 }}>
            You know <strong>who</strong> you are. Unlock <strong>why</strong> — and watch it change.
          </span>
        </div>
      )}

      {/* Axis breakdown */}
      <InsightSection
        title="The Breakdown" subtitle="The 5 axes behind your archetype"
        locked={!isPremium}
        {...lockProps(
          `See your 5-axis breakdown`,
          `The exact taste dimensions that make you a ${archetype.name.replace('The ', '')}.`,
        )}
      >
        <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 18, padding: 18 }}>
          <FlavorRadar data={MOCK_AXES} />
          <div style={{ height: 14, marginTop: 14, borderTop: `1px solid ${BORDER}` }} />
          <AxisBars axes={MOCK_AXES} />
        </div>
      </InsightSection>

      {/* Drift */}
      <InsightSection
        title="Drift Tracking" subtitle="How your palate has moved over 90 days"
        locked={!isPremium}
        {...lockProps('Track how your taste is changing', 'Your Heat climbed and your Adventure surged. See the whole story.')}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <ArchetypeShiftBanner />
          <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 18, padding: '18px 16px 14px' }}>
            <DriftChart />
          </div>
          <DriftDeltas />
        </div>
      </InsightSection>

      {/* Monthly recap */}
      <InsightSection
        title="Monthly Recap" subtitle="Your taste, packaged to share"
        locked={!isPremium}
        {...lockProps('Get your monthly recap', 'A shareable card of how you ate this month — every month.')}
      >
        <div style={{ background: '#FBF6EF', border: `1px solid ${BORDER}`, borderRadius: 18, padding: '20px 16px' }}>
          <div ref={recapRef}>
            <MonthlyRecap />
          </div>
          {isPremium && (
            <button
              onClick={() => { setShared(true); setTimeout(() => setShared(false), 1800) }}
              style={{
                width: '100%', maxWidth: 320, margin: '16px auto 0', display: 'flex',
                alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '13px', border: 'none', borderRadius: 100,
                background: ACCENT, color: '#fff', fontSize: '0.94rem', fontWeight: 800,
                cursor: 'pointer', fontFamily: 'inherit', boxShadow: `0 6px 18px ${archHex(ACCENT, 0.3)}`,
              }}
            >
              {shared ? '✓ Copied to share' : <><ShareGlyph /> Share my recap</>}
            </button>
          )}
        </div>
      </InsightSection>

      {!isPremium && (
        <button
          onClick={() => onUpgrade('insights')}
          style={{
            width: '100%', marginTop: 28, padding: '16px', border: 'none', borderRadius: 100,
            background: ACCENT, color: '#fff', fontSize: '1.02rem', fontWeight: 800, cursor: 'pointer',
            fontFamily: 'inherit', boxShadow: `0 8px 24px ${archHex(ACCENT, 0.34)}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9,
          }}
        >
          <LockGlyph size={16} /> Unlock everything · $4.99 once
        </button>
      )}
    </div>
  )
}

const backBtnStyle: React.CSSProperties = {
  background: 'none', border: 'none', cursor: 'pointer',
  color: '#888', fontSize: '0.88rem', padding: '4px 0',
  display: 'inline-flex', alignItems: 'center', gap: 4,
  fontFamily: 'inherit', fontWeight: 600,
}
