// Insights.tsx — Paid hub: full archetype, 5-axis breakdown, drift tracking, monthly recap.
// Free users see the archetype name only; premium sections are blurred behind LockOverlay.

import { useEffect, useRef, useState } from 'react'
import {
  AXIS_META, AXIS_KEYS,
  deriveArchetype, deriveArchetypeAt,
  ArchetypeHero, AxisBars, LockOverlay, LockGlyph, PremiumBadge,
  archHex, archShift,
  type AxisKey, type AxesMap, type ArchetypeInfo,
} from './Archetype'
import { FlavorRadar } from './StatsCharts'
import { fetchInsights, type InsightsDrift, type InsightsData } from '../api'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#8A7E72'
const CARD_BG = '#FFFFFF'
const BORDER = '#F0E8E0'

const FALLBACK_AXES: AxesMap = { Heat: 50, Indulgence: 50, Texture: 50, Adventure: 50, Tempo: 50 }

// ── Drift line chart ───────────────────────────────────────────────────
function DriftChart({ drift }: { drift: InsightsDrift }) {
  const { windows, series } = drift
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
          const vals = (series[k] ?? []) as number[]
          if (!vals.length) return null
          const pts = vals.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`)
          const d = 'M' + pts.join(' L')
          const last = vals[n - 1]
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

// ── Helpers for axis-specific chip content ────────────────────────────
function tempoLabel(score: number): string {
  if (score >= 70) return 'mostly nights'
  if (score >= 30) return `${score}% at night`
  return 'mostly daytime'
}

function cuisineDisplay(cuisines: string[]): { primary: string; secondary: string } {
  const fmt = (c: string) => c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  const shown = cuisines.slice(0, 2).map(fmt)
  const rest = cuisines.length - shown.length
  const primary = shown.join(' · ') + (rest > 0 ? ` +${rest}` : '')
  const secondary = `${cuisines.length} cuisine${cuisines.length !== 1 ? 's' : ''}`
  return { primary, secondary }
}

// ── Delta callout chips (biggest movers, axis-aware) ───────────────────
function DriftDeltas({ drift, axes, topCuisines }: {
  drift: InsightsDrift
  axes: AxesMap
  topCuisines: string[]
}) {
  const { series, windows } = drift
  const deltas = AXIS_KEYS.map(k => {
    const s = (series[k] ?? []) as number[]
    return { k, delta: s.length >= 2 ? s[s.length - 1] - s[0] : 0 }
  }).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
  const cardBg = '#FFFFFF'
  const border = '#F0E8E0'

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(92px, 1fr))', gap: 8 }}>
      {deltas.slice(0, 3).map(({ k, delta }) => {
        const up = delta >= 0
        const m = AXIS_META[k]

        let bigContent: React.ReactNode
        let subContent: React.ReactNode

        if (k === 'Tempo') {
          bigContent = (
            <span style={{ fontSize: '1.05rem', fontWeight: 900, color: m.color, lineHeight: 1.2 }}>
              {tempoLabel(axes[k])}
            </span>
          )
          subContent = `${up ? '↑' : '↓'} since ${windows[0]}`
        } else if (k === 'Adventure') {
          const { primary, secondary } = cuisineDisplay(topCuisines)
          bigContent = (
            <span style={{ fontSize: '0.88rem', fontWeight: 900, color: m.color, lineHeight: 1.3, wordBreak: 'break-word' }}>
              {primary}
            </span>
          )
          subContent = secondary
        } else {
          bigContent = (
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span style={{ fontSize: '1.35rem', fontWeight: 900, color: m.color, letterSpacing: '-0.02em' }}>
                {up ? '+' : '−'}{Math.abs(delta)}
              </span>
              <span style={{ fontSize: '0.9rem', color: m.color, fontWeight: 800 }}>{up ? '↑' : '↓'}</span>
            </div>
          )
          subContent = `since ${windows[0]}`
        }

        return (
          <div key={k} style={{ background: cardBg, border: `1px solid ${border}`, borderRadius: 13, padding: '11px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.74rem', fontWeight: 800, color: TEXT_SUB, marginBottom: 6 }}>
              <span style={{ fontSize: '0.85rem' }}>{m.emoji}</span>{m.label}
            </div>
            <div style={{ marginBottom: 4 }}>{bigContent}</div>
            <div style={{ fontSize: '0.64rem', color: TEXT_SUB, fontWeight: 600 }}>{subContent}</div>
          </div>
        )
      })}
    </div>
  )
}

// ── "Your archetype evolved" banner ────────────────────────────────────
function ArchetypeShiftBanner({ drift }: { drift: InsightsDrift }) {
  const s = drift.series as Record<AxisKey, number[]>
  const past = deriveArchetypeAt(0, s)
  const now = deriveArchetypeAt(drift.windows.length - 1, s)
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
function MonthlyRecap({ axes, drift, recap, month }: {
  axes: AxesMap
  drift: InsightsDrift | null | undefined
  recap: InsightsData['recap']
  month?: string
}) {
  const currentMonth = month ?? new Date().toLocaleString('default', { month: 'long' })
  const now = deriveArchetype(axes)
  const top = drift ? deriveArchetypeAt(0, drift.series as Record<AxisKey, number[]>) : now
  const grad = `linear-gradient(165deg, ${archShift(ACCENT, 8)} 0%, ${archShift(ACCENT, -34)} 62%, ${archShift(ACCENT, -54)} 100%)`

  const biggestMoverLabel = recap.biggest_mover
    ? `${AXIS_META[recap.biggest_mover as AxisKey]?.label ?? recap.biggest_mover} this month`
    : null
  const sayYesBig = `${recap.say_yes_rate}%`
  const topCuisineBig = recap.top_cuisine ? `🍽️ ${recap.top_cuisine.charAt(0).toUpperCase() + recap.top_cuisine.slice(1)}` : '—'

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
            {currentMonth} · in your taste
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
          {biggestMoverLabel && <RecapStat big={`+${recap.biggest_mover}`} label={biggestMoverLabel} />}
          <RecapStat big={topCuisineBig} label="Top cuisine" />
          <RecapStat big={sayYesBig} label="Say-yes rate" />
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

// ── Progress gate (< 20 right swipes) ─────────────────────────────────
function ProgressGate({ remaining }: { remaining: number }) {
  return (
    <div style={{
      background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 18,
      padding: '32px 24px', textAlign: 'center',
    }}>
      <div style={{ fontSize: '2rem', marginBottom: 12 }}>🍽️</div>
      <div style={{ fontSize: '1rem', fontWeight: 800, color: TEXT_PRIMARY, marginBottom: 6 }}>
        Keep swiping
      </div>
      <div style={{ fontSize: '0.88rem', color: TEXT_SUB, lineHeight: 1.5 }}>
        {remaining} more right swipe{remaining !== 1 ? 's' : ''} to unlock your taste insights
      </div>
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
  const [insights, setInsights] = useState<InsightsData | null>(null)
  const [loading, setLoading] = useState(false)
  const recapRef = useRef<HTMLDivElement>(null)
  const [shared, setShared] = useState(false)

  useEffect(() => {
    if (!isPremium) return
    setLoading(true)
    fetchInsights()
      .then(setInsights)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isPremium])

  const axes = (insights?.axes as AxesMap | undefined) ?? FALLBACK_AXES
  const archetype = deriveArchetype(axes)
  const ready = insights?.ready ?? false
  const remaining = insights ? Math.max(0, 20 - insights.total_right_swipes) : 20
  const drift = insights?.drift ?? null
  const currentMonth = new Date().toLocaleString('default', { month: 'long' })
  const canShare = typeof navigator !== 'undefined' && 'share' in navigator

  const handleShare = async () => {
    const recap = insights?.recap
    const topCuisines = recap?.top_cuisines?.slice(0, 2)
      .map(c => c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))
      .join(' · ') ?? ''
    const lines = [
      `My Cravings recap for ${currentMonth} 🍽️`,
      `${archetype.emoji} ${archetype.name}`,
      topCuisines ? `Top cuisine: ${topCuisines}` : null,
      recap ? `Say-yes rate: ${recap.say_yes_rate}%` : null,
    ].filter(Boolean).join('\n')
    try {
      await navigator.share({ text: lines })
      setShared(true)
      setTimeout(() => setShared(false), 1800)
    } catch {
      // user cancelled or share failed — no-op
    }
  }

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

      {loading && (
        <div style={{ textAlign: 'center', padding: '20px 0', color: TEXT_SUB, fontSize: '0.88rem' }}>
          Loading your insights…
        </div>
      )}

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
        {isPremium && !ready ? (
          <ProgressGate remaining={remaining} />
        ) : (
          <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 18, padding: 18 }}>
            <FlavorRadar data={axes} />
            <div style={{ height: 14, marginTop: 14, borderTop: `1px solid ${BORDER}` }} />
            <AxisBars axes={axes} />
          </div>
        )}
      </InsightSection>

      {/* Drift */}
      <InsightSection
        title="Drift Tracking" subtitle="How your palate has moved over 90 days"
        locked={!isPremium}
        {...lockProps('Track how your taste is changing', 'Your Heat climbed and your Adventure surged. See the whole story.')}
      >
        {isPremium && !ready ? (
          <ProgressGate remaining={remaining} />
        ) : drift ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <ArchetypeShiftBanner drift={drift} />
            <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 18, padding: '18px 16px 14px' }}>
              <DriftChart drift={drift} />
            </div>
            <DriftDeltas drift={drift} axes={axes} topCuisines={insights?.recap?.top_cuisines ?? []} />
          </div>
        ) : (
          <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 18, padding: '24px', textAlign: 'center', color: TEXT_SUB, fontSize: '0.88rem' }}>
            Drift data will appear once you have swipes across multiple months.
          </div>
        )}
      </InsightSection>

      {/* Monthly recap */}
      <InsightSection
        title="Monthly Recap" subtitle="Your taste, packaged to share"
        locked={!isPremium}
        {...lockProps('Get your monthly recap', 'A shareable card of how you ate this month — every month.')}
      >
        {isPremium && !ready ? (
          <ProgressGate remaining={remaining} />
        ) : (
          <div style={{ background: '#FBF6EF', border: `1px solid ${BORDER}`, borderRadius: 18, padding: '20px 16px' }}>
            <div ref={recapRef}>
              <MonthlyRecap axes={axes} drift={drift} recap={insights?.recap ?? { top_cuisine: null, top_cuisines: [], say_yes_rate: 0, biggest_mover: null }} month={currentMonth} />
            </div>
            {isPremium && canShare && (
              <button
                onClick={handleShare}
                style={{
                  width: '100%', maxWidth: 320, margin: '16px auto 0', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '13px', border: 'none', borderRadius: 100,
                  background: ACCENT, color: '#fff', fontSize: '0.94rem', fontWeight: 800,
                  cursor: 'pointer', fontFamily: 'inherit', boxShadow: `0 6px 18px ${archHex(ACCENT, 0.3)}`,
                }}
              >
                {shared ? '✓ Shared!' : <><ShareGlyph /> Share my recap</>}
              </button>
            )}
          </div>
        )}
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
