import React, { useEffect, useState } from 'react'
import {
  getAdminFoods, getAdminCatalog, getAdminRetention, getAdminEngagement, logout,
  type AdminFoodsMetrics, type AdminCatalogMetrics, type AdminRetentionMetrics, type AdminEngagementMetrics,
} from '../api'
import {
  Panel, StatTile, RightRateBars, DailyVolume, Histogram,
  CohortRetention, SignupBars, AttrRadar, FoodTable, ADMIN_CUISINE_EMOJI,
} from './AdminCharts'
import { CravingsLogo } from './CravingsLogo'

const ACCENT = '#E85D04'
const BORDER = '#F0E8E0'
const TEXT_SUB = '#888'

function Skeleton({ height = 120 }: { height?: number }) {
  return (
    <div style={{ height, background: 'linear-gradient(90deg,#F0E8E0 25%,#F8F2EC 50%,#F0E8E0 75%)', backgroundSize: '400% 100%', borderRadius: 10, animation: 'shimmer 1.4s infinite' }} />
  )
}

function PanelError({ msg }: { msg: string }) {
  return <div style={{ color: '#C0392B', fontSize: '0.82rem', fontWeight: 600 }}>⚠ {msg}</div>
}

type S<T> = { status: 'idle' | 'loading' | 'ok' | 'err'; data?: T; error?: string }

function loading<T>(): S<T> { return { status: 'loading' } }
function ok<T>(data: T): S<T> { return { status: 'ok', data } }
function err<T>(e: unknown): S<T> { return { status: 'err', error: e instanceof Error ? e.message : 'Error' } }

export function Dashboard({ onSignOut }: { onSignOut: () => void }) {
  const [days, setDays] = useState<30 | 90>(30)
  const [refreshKey, setRefreshKey] = useState(0)

  const [foods, setFoods] = useState<S<AdminFoodsMetrics>>(loading)
  const [catalog, setCatalog] = useState<S<AdminCatalogMetrics>>(loading)
  const [retention, setRetention] = useState<S<AdminRetentionMetrics>>(loading)
  const [engagement, setEngagement] = useState<S<AdminEngagementMetrics>>(loading)

  useEffect(() => {
    Promise.resolve().then(() => {
      setFoods(loading())
      setCatalog(loading())
    }).catch(() => undefined)
    getAdminFoods({ min_swipes: 2, limit: 10 }).then(d => setFoods(ok(d))).catch((e: unknown) => setFoods(err(e)))
    getAdminCatalog().then(d => setCatalog(ok(d))).catch((e: unknown) => setCatalog(err(e)))
  }, [refreshKey])

  useEffect(() => {
    Promise.resolve().then(() => {
      setRetention(loading())
      setEngagement(loading())
    }).catch(() => undefined)
    getAdminRetention(days).then(d => setRetention(ok(d))).catch((e: unknown) => setRetention(err(e)))
    getAdminEngagement(days).then(d => setEngagement(ok(d))).catch((e: unknown) => setEngagement(err(e)))
  }, [days, refreshKey])

  function handleSignOut() { void logout().then(() => onSignOut()) }

  return (
    <div style={{ fontFamily: 'Nunito, sans-serif', background: '#FFF8F0', minHeight: '100vh' }}>
      <style>{`
        @keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
        * { box-sizing: border-box; }
      `}</style>

      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 24px', background: '#fff', borderBottom: `1px solid ${BORDER}`,
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <CravingsLogo size={28} />
          <div>
            <div style={{ fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', color: TEXT_SUB }}>Admin</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#2C2C2C', lineHeight: 1.1, letterSpacing: '-0.01em' }}>Metrics</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', gap: 4, background: '#F0E8E0', borderRadius: 99, padding: 3 }}>
            {([30, 90] as const).map(d => (
              <button key={d} onClick={() => setDays(d)} style={{
                padding: '5px 14px', borderRadius: 99, border: 'none',
                background: days === d ? ACCENT : 'transparent', color: days === d ? '#fff' : TEXT_SUB,
                fontSize: '0.78rem', fontWeight: 800, cursor: 'pointer', fontFamily: 'Nunito, sans-serif',
              }}>{d}d</button>
            ))}
          </div>
          <button onClick={() => setRefreshKey(k => k + 1)} title="Refresh" style={{ background: 'none', border: `1px solid ${BORDER}`, borderRadius: 8, padding: '5px 10px', cursor: 'pointer', fontSize: '0.9rem' }}>↻</button>
          <button onClick={handleSignOut} style={{ background: 'none', border: `1px solid ${BORDER}`, borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 700, fontFamily: 'Nunito, sans-serif', color: TEXT_SUB }}>Sign out</button>
        </div>
      </div>

      {/* Caveat bar */}
      <div style={{ background: '#FFF0EE', borderBottom: `1px solid #F8BCAC`, padding: '8px 24px', fontSize: '0.72rem', color: '#8B3A2A', fontWeight: 600 }}>
        Registered users only (guests have no DB rows) · "active" = swiped that day (no session/open events) · Aggregates only, no per-user PII
      </div>

      {/* KPI strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 1, background: BORDER, borderBottom: `1px solid ${BORDER}` }}>
        {[
          { label: 'Total Swipes', value: engagement.data ? engagement.data.total_swipes.toLocaleString() : '—' },
          { label: 'Say-Yes Rate', value: engagement.data ? `${engagement.data.global_say_yes_rate}%` : '—' },
          { label: 'Registered', value: engagement.data?.registered_users ?? '—' },
          { label: 'Premium', value: engagement.data?.premium_users ?? '—' },
          { label: 'DAU', value: retention.data?.dau ?? '—' },
          { label: 'WAU', value: retention.data?.wau ?? '—' },
          { label: 'MAU', value: retention.data?.mau ?? '—' },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: '#fff', padding: '14px 20px' }}>
            {engagement.status === 'loading' ? <Skeleton height={50} /> : <StatTile label={label} value={value} />}
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 16, padding: '20px 24px', maxWidth: 1400, margin: '0 auto' }}>

        {/* Daily swipe volume — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <Panel title="Daily Swipe Volume">
            {engagement.status === 'loading' && <Skeleton />}
            {engagement.status === 'err' && <PanelError msg={engagement.error!} />}
            {engagement.status === 'ok' && engagement.data && <DailyVolume days={engagement.data.swipes_per_day} />}
          </Panel>
        </div>

        {/* Swipe histogram */}
        <div style={{ gridColumn: 'span 6' }}>
          <Panel title="Swipes per User">
            {engagement.status === 'loading' && <Skeleton />}
            {engagement.status === 'err' && <PanelError msg={engagement.error!} />}
            {engagement.status === 'ok' && engagement.data && <Histogram buckets={engagement.data.swipes_per_user_histogram} />}
          </Panel>
        </div>

        {/* Cohort retention */}
        <div style={{ gridColumn: 'span 6' }}>
          <Panel title="Cohort Retention">
            {retention.status === 'loading' && <Skeleton />}
            {retention.status === 'err' && <PanelError msg={retention.error!} />}
            {retention.status === 'ok' && retention.data && <CohortRetention retention={retention.data} />}
          </Panel>
        </div>

        {/* Signup bars */}
        <div style={{ gridColumn: 'span 4' }}>
          <Panel title="Daily Signups">
            {retention.status === 'loading' && <Skeleton />}
            {retention.status === 'err' && <PanelError msg={retention.error!} />}
            {retention.status === 'ok' && retention.data && <SignupBars signups={retention.data.signups} />}
          </Panel>
        </div>

        {/* Attribute radar */}
        <div style={{ gridColumn: 'span 4' }}>
          <Panel title="Right-Swipe Attributes">
            {catalog.status === 'loading' && <Skeleton />}
            {catalog.status === 'err' && <PanelError msg={catalog.error!} />}
            {catalog.status === 'ok' && catalog.data && <AttrRadar attrs={catalog.data.right_swipe_attributes} />}
          </Panel>
        </div>

        {/* Cuisine right-rate */}
        <div style={{ gridColumn: 'span 4' }}>
          <Panel title="Cuisine Right-Rate">
            {catalog.status === 'loading' && <Skeleton />}
            {catalog.status === 'err' && <PanelError msg={catalog.error!} />}
            {catalog.status === 'ok' && catalog.data && <RightRateBars dims={catalog.data.by_cuisine} emoji={ADMIN_CUISINE_EMOJI} />}
          </Panel>
        </div>

        {/* Protein right-rate */}
        <div style={{ gridColumn: 'span 4' }}>
          <Panel title="Protein Right-Rate">
            {catalog.status === 'loading' && <Skeleton />}
            {catalog.status === 'err' && <PanelError msg={catalog.error!} />}
            {catalog.status === 'ok' && catalog.data && <RightRateBars dims={catalog.data.by_protein} />}
          </Panel>
        </div>

        {/* Carb right-rate */}
        <div style={{ gridColumn: 'span 4' }}>
          <Panel title="Carb Right-Rate">
            {catalog.status === 'loading' && <Skeleton />}
            {catalog.status === 'err' && <PanelError msg={catalog.error!} />}
            {catalog.status === 'ok' && catalog.data && <RightRateBars dims={catalog.data.by_carb} />}
          </Panel>
        </div>

        {/* Premium conversions */}
        <div style={{ gridColumn: 'span 4' }}>
          <Panel title={`Premium Conversions (${days}d)`}>
            {engagement.status === 'loading' && <Skeleton height={60} />}
            {engagement.status === 'err' && <PanelError msg={engagement.error!} />}
            {engagement.status === 'ok' && engagement.data && (
              <StatTile label="Recent conversions" value={engagement.data.premium_conversions_recent} />
            )}
          </Panel>
        </div>

        {/* Best foods */}
        <div style={{ gridColumn: 'span 6' }}>
          <Panel title="Top Performing Foods">
            {foods.status === 'loading' && <Skeleton />}
            {foods.status === 'err' && <PanelError msg={foods.error!} />}
            {foods.status === 'ok' && foods.data && <FoodTable foods={foods.data.best} label="Best" />}
          </Panel>
        </div>

        {/* Worst foods */}
        <div style={{ gridColumn: 'span 6' }}>
          <Panel title="Worst Performing Foods">
            {foods.status === 'loading' && <Skeleton />}
            {foods.status === 'err' && <PanelError msg={foods.error!} />}
            {foods.status === 'ok' && foods.data && <FoodTable foods={foods.data.worst} label="Worst" />}
          </Panel>
        </div>

      </div>
    </div>
  )
}
