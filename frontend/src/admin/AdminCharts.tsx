import React from 'react'
import type { AdminDim, AdminFoodMetric, AdminRetentionMetrics, AdminEngagementMetrics } from '../api'
import { hexToRgba as adminHexToRgba, shiftHex as adminShift } from '../colorUtils'
import { CUISINE_EMOJI as ADMIN_CUISINE_EMOJI } from '../cuisineEmoji'
import { prettyKey, fmtDate } from './adminFormat'

// ── Design tokens ────────────────────────────────────────────────────────────
const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#2C2C2C'
const TEXT_SUB = '#888'
const CARD_BG = '#FAFAF8'
const BORDER = '#F0E8E0'
const TRACK = '#EEE7DF'

export { ADMIN_CUISINE_EMOJI }

// ── Panel wrapper ────────────────────────────────────────────────────────────
export function Panel({ title, children, fullWidth }: { title: string; children: React.ReactNode; fullWidth?: boolean }) {
  return (
    <div style={{
      background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 16,
      padding: '18px 20px', gridColumn: fullWidth ? '1 / -1' : undefined,
    }}>
      <div style={{ fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: TEXT_SUB, marginBottom: 14 }}>
        {title}
      </div>
      {children}
    </div>
  )
}

// ── Stat tile ────────────────────────────────────────────────────────────────
export function StatTile({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '8px 4px' }}>
      <div style={{ fontSize: '1.9rem', fontWeight: 900, letterSpacing: '-0.03em', color: TEXT_PRIMARY, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: TEXT_SUB, marginTop: 5 }}>{label}</div>
      {sub && <div style={{ fontSize: '0.72rem', color: TEXT_SUB, marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

// ── Right-rate horizontal bars ───────────────────────────────────────────────
export function RightRateBars({ dims, emoji }: { dims: AdminDim[]; emoji?: Record<string, string> }) {
  const top = dims.slice(0, 8)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
      {top.map(d => (
        <div key={d.key} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 90, fontSize: '0.78rem', fontWeight: 600, color: TEXT_PRIMARY, textAlign: 'right', flexShrink: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {emoji?.[d.key] ? `${emoji[d.key]} ` : ''}{d.key.replace(/_/g, ' ')}
          </div>
          <div style={{ flex: 1, height: 10, background: TRACK, borderRadius: 99, overflow: 'hidden' }}>
            <div style={{ width: `${d.right_rate}%`, height: '100%', background: ACCENT, borderRadius: 99 }} />
          </div>
          <div style={{ width: 36, fontSize: '0.78rem', fontWeight: 700, color: TEXT_SUB, flexShrink: 0 }}>{d.right_rate}%</div>
        </div>
      ))}
    </div>
  )
}

// ── Daily volume sparkline (bar chart) ───────────────────────────────────────
export function DailyVolume({ days }: { days: AdminEngagementMetrics['swipes_per_day'] }) {
  if (!days.length) return <div style={{ color: TEXT_SUB, fontSize: '0.82rem' }}>No data</div>
  const W = 440, H = 80, BAR_GAP = 2
  const maxN = Math.max(...days.map(d => d.n), 1)
  const barW = Math.max(3, Math.floor((W - BAR_GAP * (days.length - 1)) / days.length))
  const step = barW + BAR_GAP
  const visibleDays = days.slice(-Math.floor(W / step))

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg viewBox={`0 0 ${W} ${H + 20}`} width="100%" style={{ display: 'block', minWidth: 200 }}>
        {visibleDays.map((d, i) => {
          const h = Math.max(3, (d.n / maxN) * H)
          const x = i * step
          const rightH = Math.round((d.right / d.n) * h) || 0
          return (
            <g key={d.day}>
              <rect x={x} y={H - h} width={barW} height={h - rightH} fill={adminHexToRgba(ACCENT, 0.25)} rx={2} />
              <rect x={x} y={H - rightH} width={barW} height={rightH} fill={ACCENT} rx={2} />
              {i % Math.ceil(visibleDays.length / 6) === 0 && (
                <text x={x + barW / 2} y={H + 14} textAnchor="middle" fontSize={9} fill={TEXT_SUB}>{fmtDate(d.day)}</text>
              )}
            </g>
          )
        })}
      </svg>
      <div style={{ display: 'flex', gap: 16, fontSize: '0.72rem', color: TEXT_SUB, marginTop: 4 }}>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, background: ACCENT, borderRadius: 2, marginRight: 4 }} />Right swipes</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, background: adminHexToRgba(ACCENT, 0.25), borderRadius: 2, marginRight: 4 }} />Other</span>
      </div>
    </div>
  )
}

// ── Swipe-count histogram ────────────────────────────────────────────────────
export function Histogram({ buckets }: { buckets: AdminEngagementMetrics['swipes_per_user_histogram'] }) {
  const maxUsers = Math.max(...buckets.map(b => b.users), 1)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 80 }}>
      {buckets.map(b => {
        const h = (b.users / maxUsers) * 72
        return (
          <div key={b.bucket} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: TEXT_PRIMARY }}>{b.users}</div>
            <div style={{ width: '100%', height: Math.max(h, 3), background: ACCENT, borderRadius: '4px 4px 0 0', opacity: b.users ? 1 : 0.18 }} />
            <div style={{ fontSize: '0.62rem', color: TEXT_SUB, textAlign: 'center', lineHeight: 1.2 }}>{b.bucket}</div>
          </div>
        )
      })}
    </div>
  )
}

// ── Cohort retention table ───────────────────────────────────────────────────
export function CohortRetention({ retention }: { retention: AdminRetentionMetrics }) {
  const tiers: Array<'D1' | 'D7' | 'D30'> = ['D1', 'D7', 'D30']
  return (
    <div style={{ display: 'flex', gap: 12 }}>
      {tiers.map(t => {
        const pct = retention.cohort_retention[t]
        const eligible = retention.cohort_eligible[t]
        const fill = ACCENT
        return (
          <div key={t} style={{ flex: 1, textAlign: 'center', background: '#fff', border: `1px solid ${BORDER}`, borderRadius: 12, padding: '14px 8px' }}>
            <svg viewBox="0 0 56 56" width={56} height={56} style={{ overflow: 'visible', display: 'block', margin: '0 auto 8px' }}>
              <circle cx={28} cy={28} r={24} fill="none" stroke={TRACK} strokeWidth={5} />
              <circle cx={28} cy={28} r={24} fill="none" stroke={fill} strokeWidth={5}
                strokeDasharray={`${(pct / 100) * 150.8} 150.8`}
                strokeLinecap="round" transform="rotate(-90 28 28)" />
              <text x={28} y={33} textAnchor="middle" fontSize={13} fontWeight={900} fill={TEXT_PRIMARY}>{pct}%</text>
            </svg>
            <div style={{ fontSize: '0.82rem', fontWeight: 800, color: TEXT_PRIMARY }}>{t}</div>
            <div style={{ fontSize: '0.68rem', color: TEXT_SUB, marginTop: 2 }}>{eligible} eligible</div>
          </div>
        )
      })}
    </div>
  )
}

// ── Signup bar chart ─────────────────────────────────────────────────────────
export function SignupBars({ signups }: { signups: AdminRetentionMetrics['signups'] }) {
  if (!signups.length) return <div style={{ color: TEXT_SUB, fontSize: '0.82rem' }}>No signups in window</div>
  const maxN = Math.max(...signups.map(d => d.n), 1)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 70 }}>
      {signups.map(d => {
        const h = (d.n / maxN) * 56
        return (
          <div key={d.day} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, minWidth: 0 }}>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: TEXT_PRIMARY }}>{d.n}</div>
            <div style={{ width: '100%', height: Math.max(h, 3), background: adminShift(ACCENT, 40), borderRadius: '3px 3px 0 0' }} />
            <div style={{ fontSize: '0.6rem', color: TEXT_SUB, textAlign: 'center', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>{fmtDate(d.day)}</div>
          </div>
        )
      })}
    </div>
  )
}

// ── Attribute radar (octagon) ────────────────────────────────────────────────
export function AttrRadar({ attrs }: { attrs: Record<string, number> }) {
  const keys = Object.keys(attrs)
  const n = keys.length
  if (!n) return null
  const CX = 100, CY = 100, R = 80
  const angle = (i: number) => (2 * Math.PI * i) / n - Math.PI / 2

  const gridPcts = [25, 50, 75, 100]
  const polyPoints = (pct: number) =>
    keys.map((_, i) => {
      const r = (pct / 100) * R
      return `${CX + r * Math.cos(angle(i))},${CY + r * Math.sin(angle(i))}`
    }).join(' ')

  const valuePoints = keys.map((k, i) => {
    const r = (attrs[k] / 100) * R
    return `${CX + r * Math.cos(angle(i))},${CY + r * Math.sin(angle(i))}`
  }).join(' ')

  return (
    <svg viewBox="0 0 200 200" width="100%" style={{ maxWidth: 220, display: 'block', margin: '0 auto' }}>
      {gridPcts.map(p => (
        <polygon key={p} points={polyPoints(p)} fill="none" stroke={TRACK} strokeWidth={0.8} />
      ))}
      {keys.map((_, i) => {
        const lx = CX + R * Math.cos(angle(i))
        const ly = CY + R * Math.sin(angle(i))
        return <line key={i} x1={CX} y1={CY} x2={lx} y2={ly} stroke={TRACK} strokeWidth={0.8} />
      })}
      <polygon points={valuePoints} fill={adminHexToRgba(ACCENT, 0.18)} stroke={ACCENT} strokeWidth={1.5} />
      {keys.map((k, i) => {
        const lx = CX + (R + 14) * Math.cos(angle(i))
        const ly = CY + (R + 14) * Math.sin(angle(i))
        return (
          <text key={k} x={lx} y={ly + 4} textAnchor="middle" fontSize={8.5} fontWeight={700} fill={TEXT_SUB}>
            {prettyKey(k)}
          </text>
        )
      })}
    </svg>
  )
}

// ── Food performance table ───────────────────────────────────────────────────
export function FoodTable({ foods, label }: { foods: AdminFoodMetric[]; label: string }) {
  if (!foods.length) return <div style={{ color: TEXT_SUB, fontSize: '0.82rem' }}>No data</div>
  return (
    <div>
      <div style={{ fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.09em', textTransform: 'uppercase', color: TEXT_SUB, marginBottom: 8 }}>{label}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {foods.slice(0, 10).map(f => (
          <div key={f.food_id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 10px', background: '#fff', border: `1px solid ${BORDER}`, borderRadius: 10 }}>
            <div style={{ width: 38, height: 38, borderRadius: 9, background: adminHexToRgba(ACCENT, 0.1), display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.82rem', fontWeight: 900, color: ACCENT, flexShrink: 0 }}>
              {f.right_rate}%
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: TEXT_PRIMARY, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</div>
              <div style={{ fontSize: '0.7rem', color: TEXT_SUB }}>{ADMIN_CUISINE_EMOJI[f.cuisine_type] ?? '🍽️'} {f.cuisine_type?.replace(/_/g, ' ')} · {f.total} swipes</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
