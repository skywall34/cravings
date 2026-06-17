import { useState, useEffect } from 'react'
import { fetchStats, changePassword, deleteAccount, exportData } from '../api'
import * as storage from '../storage'
import type { UserInfo, SwipeStats } from '../api'
import { deriveTasteProfile, YesRateGauge, CuisineAffinity, PeakTimesChart } from './StatsCharts'
import { deriveArchetype, PremiumBadge, type AxesMap } from './Archetype'

const BALANCED_AXES: AxesMap = { Heat: 50, Indulgence: 50, Texture: 50, Adventure: 50, Tempo: 50 }

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#888'
const CARD_BG = '#FAFAF8'
const CARD_BORDER = '#F0E8E0'

const MIN_SWIPES_FOR_PROFILE = 15

interface ProfilePageProps {
  user: UserInfo
  isPremium: boolean
  onBack: () => void
  onViewInsights: () => void
  onDeleteAccount?: () => void
}

export function ProfilePage({ user, isPremium, onBack, onViewInsights, onDeleteAccount }: ProfilePageProps) {
  const [stats, setStats] = useState<SwipeStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(true)
  const [statsError, setStatsError] = useState<string | null>(null)
  const [showPasswordForm, setShowPasswordForm] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [exportLoading, setExportLoading] = useState(false)

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(e => setStatsError(e instanceof Error ? e.message : 'Failed to load stats'))
      .finally(() => setLoadingStats(false))
  }, [])

  return (
    <div style={{ width: '100%', maxWidth: 420, margin: '0 auto', padding: '8px 4px 60px' }}>
      <button onClick={onBack} style={backBtnStyle}>← Back</button>

      {/* Identity row */}
      <div style={{ marginTop: 20, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{
          width: 56, height: 56, borderRadius: '50%',
          background: ACCENT, color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1.6rem', fontWeight: 900,
          boxShadow: `0 4px 14px rgba(232,93,4,0.3)`,
          flexShrink: 0,
        }}>
          {(user.name || user.email || '?').charAt(0).toUpperCase()}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h2 style={{ margin: '0 0 2px', fontSize: '1.3rem', fontWeight: 800, color: TEXT_PRIMARY, letterSpacing: '-0.01em' }}>
            {user.name && user.name !== 'guest' ? user.name : 'Your profile'}
          </h2>
          <p style={{ margin: 0, color: TEXT_SUB, fontSize: '0.88rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {user.email}
          </p>
        </div>
      </div>

      {loadingStats && (
        <div style={{ color: TEXT_SUB, textAlign: 'center', padding: 40, fontSize: '0.9rem' }}>Loading stats…</div>
      )}
      {statsError && <p style={{ color: '#C0392B' }}>{statsError}</p>}

      {stats && <StatsSection stats={stats} isPremium={isPremium} onViewInsights={onViewInsights} />}

      {/* Change password */}
      <div style={{ marginTop: 28 }}>
        {!showPasswordForm ? (
          <button onClick={() => setShowPasswordForm(true)} style={outlineBtnStyle}>
            Change password
          </button>
        ) : (
          <ChangePasswordForm onDone={() => setShowPasswordForm(false)} />
        )}
      </div>

      {/* Data rights (GDPR / CCPA) */}
      <div style={{ marginTop: 28 }}>
        <h3 style={{ margin: '0 0 10px', fontSize: '0.72rem', fontWeight: 700, color: TEXT_SUB, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Your Data
        </h3>
        <div style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 14, overflow: 'hidden' }}>
          <button
            disabled={exportLoading}
            onClick={() => {
              void (async () => {
                setExportLoading(true)
                try {
                  const blob = await exportData()
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url; a.download = 'cravings-data.json'
                  a.click(); URL.revokeObjectURL(url)
                } catch (e) {
                  alert(e instanceof Error ? e.message : 'Export failed')
                } finally {
                  setExportLoading(false)
                }
              })()
            }}
            style={dataRowBtnStyle}
          >
            <span>
              <span style={{ display: 'block', fontSize: '0.92rem', fontWeight: 700, color: TEXT_PRIMARY }}>
                {exportLoading ? 'Exporting…' : 'Export my data'}
              </span>
              <span style={{ display: 'block', fontSize: '0.76rem', color: TEXT_SUB, marginTop: 1 }}>
                Download account &amp; swipe history (JSON)
              </span>
            </span>
            <span style={{ color: TEXT_SUB, fontSize: '1.05rem' }}>↓</span>
          </button>

          {!deleteConfirm ? (
            <button onClick={() => setDeleteConfirm(true)} style={{ ...dataRowBtnStyle, borderTop: `1px solid ${CARD_BORDER}` }}>
              <span>
                <span style={{ display: 'block', fontSize: '0.92rem', fontWeight: 700, color: '#DC2626' }}>Delete my account</span>
                <span style={{ display: 'block', fontSize: '0.76rem', color: TEXT_SUB, marginTop: 1 }}>Erase your profile &amp; all swipe history</span>
              </span>
              <span style={{ color: '#DC2626', fontSize: '1.05rem' }}>×</span>
            </button>
          ) : (
            <div style={{ padding: '14px 16px', background: 'rgba(220,38,38,0.05)', borderTop: `1px solid ${CARD_BORDER}` }}>
              <p style={{ margin: '0 0 12px', fontSize: '0.84rem', lineHeight: 1.5, color: TEXT_PRIMARY, fontWeight: 600 }}>
                This permanently erases your account and swipe history within 30 days. This can&rsquo;t be undone.
              </p>
              {deleteError && <p style={{ color: '#DC2626', fontSize: '0.82rem', margin: '0 0 8px' }}>{deleteError}</p>}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  disabled={deleteLoading}
                  onClick={() => {
                    void (async () => {
                    setDeleteLoading(true)
                    setDeleteError(null)
                    try {
                      await deleteAccount()
                      await storage.remove('cravings_token')
                      onDeleteAccount?.()
                    } catch (e) {
                      setDeleteError(e instanceof Error ? e.message : 'Deletion failed')
                      setDeleteLoading(false)
                    }
                    })()
                  }}
                  style={{ flex: 1, padding: '10px', background: '#DC2626', color: '#fff', border: 'none', borderRadius: 100, fontSize: '0.86rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' }}
                >
                  {deleteLoading ? 'Deleting…' : 'Delete forever'}
                </button>
                <button onClick={() => setDeleteConfirm(false)} style={outlineBtnStyle}>Cancel</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Stats section ──────────────────────────────────────────────────────
function StatsSection({ stats, isPremium, onViewInsights }: { stats: SwipeStats; isPremium: boolean; onViewInsights: () => void }) {
  if (stats.total_swipes < MIN_SWIPES_FOR_PROFILE) {
    return (
      <div style={{ marginTop: 8, marginBottom: 8, padding: '28px 24px', borderRadius: 16, background: CARD_BG, border: `1px solid ${CARD_BORDER}`, textAlign: 'center' }}>
        <div style={{ fontSize: '2rem', marginBottom: 10 }}>🍽️</div>
        <div style={{ fontWeight: 800, fontSize: '1rem', color: '#2C2C2C', marginBottom: 6 }}>Keep swiping to unlock your taste profile</div>
        <div style={{ fontSize: '0.85rem', color: TEXT_SUB, lineHeight: 1.5 }}>
          {stats.total_swipes} swipe{stats.total_swipes !== 1 ? 's' : ''} so far. Reach {MIN_SWIPES_FOR_PROFILE} to see your personalized insights.
        </div>
      </div>
    )
  }

  const profile = deriveTasteProfile(stats)

  return (
    <>
      {/* 3-up stat grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        <BigStat value={stats.total_swipes} label="Swipes" />
        <BigStat value={`${Math.round(profile.overallYes * 100)}%`} label="Say yes" />
        <BigStat value={stats.avg_swipes_to_right !== null ? stats.avg_swipes_to_right : '—'} label="Swipes/yes" />
      </div>

      {/* Archetype teaser */}
      <ArchetypeTeaser isPremium={isPremium} onViewInsights={onViewInsights} />

      {/* How You Swipe */}
      <Section title="How You Swipe" subtitle="Your overall decisiveness" pad>
        <YesRateGauge value={profile.overallYes} avgToYes={stats.avg_swipes_to_right} />
      </Section>

      {stats.cuisine_breakdown.length > 0 && (
        <Section title="Cuisine Affinity" subtitle="Ranked by acceptance rate">
          <CuisineAffinity items={stats.cuisine_breakdown} />
        </Section>
      )}

      {stats.hour_breakdown.length > 0 && (
        <Section title="Peak Craving Times" subtitle="When hunger strikes" pad>
          <PeakTimesChart items={stats.hour_breakdown} />
        </Section>
      )}
    </>
  )
}

// ── ArchetypeTeaser — routes to Insights ───────────────────────────────
function ArchetypeTeaser({ isPremium, onViewInsights }: { isPremium: boolean; onViewInsights: () => void }) {
  const archetype = deriveArchetype(BALANCED_AXES)
  return (
    <button
      onClick={onViewInsights}
      style={{
        width: '100%', marginTop: 14, display: 'flex', alignItems: 'center', gap: 13,
        padding: '14px 16px', textAlign: 'left', cursor: 'pointer', fontFamily: 'inherit',
        background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 16,
        transition: 'border-color 0.15s',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = ACCENT }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = CARD_BORDER }}
    >
      <span style={{
        width: 42, height: 42, flexShrink: 0, borderRadius: 12, fontSize: '1.35rem',
        background: 'rgba(232,93,4,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {isPremium ? archetype.emoji : '🧬'}
      </span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <span style={{ fontSize: '0.66rem', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: TEXT_SUB }}>
            Taste Archetype
          </span>
          {!isPremium && <PremiumBadge small />}
        </span>
        <span style={{ display: 'block', fontSize: '0.98rem', fontWeight: 800, color: TEXT_PRIMARY, marginTop: 3, lineHeight: 1.2 }}>
          {isPremium ? archetype.name : 'Discover who you are as an eater'}
        </span>
      </span>
      <span style={{ color: ACCENT, fontSize: '1.1rem', fontWeight: 800, flexShrink: 0 }}>→</span>
    </button>
  )
}

// ── BigStat card ────────────────────────────────────────────────────────
function BigStat({ value, label }: { value: string | number; label: string }) {
  return (
    <div style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 14, padding: '14px 10px', textAlign: 'center' }}>
      <div style={{ fontSize: '1.6rem', fontWeight: 900, color: TEXT_PRIMARY, lineHeight: 1, letterSpacing: '-0.02em' }}>{value}</div>
      <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#B0A89E', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 6 }}>{label}</div>
    </div>
  )
}

// ── Section wrapper ─────────────────────────────────────────────────────
function Section({ title, subtitle, children, pad }: { title: string; subtitle?: string; children: React.ReactNode; pad?: boolean }) {
  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ margin: '0 0 2px', fontSize: '0.72rem', fontWeight: 800, color: TEXT_SUB, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{title}</h3>
      {subtitle && <p style={{ margin: '0 0 10px', fontSize: '0.8rem', color: TEXT_SUB, lineHeight: 1.4 }}>{subtitle}</p>}
      {!subtitle && <div style={{ height: 10 }} />}
      <div style={{ background: CARD_BG, borderRadius: 16, border: `1px solid ${CARD_BORDER}`, overflow: 'hidden', padding: pad ? 18 : 0 }}>
        {children}
      </div>
    </div>
  )
}

// ── Change password form ────────────────────────────────────────────────
function ChangePasswordForm({ onDone }: { onDone: () => void }) {
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await changePassword(oldPw, newPw)
      setSuccess(true)
      setTimeout(onDone, 1400)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div style={{ padding: '14px 16px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 12, color: '#10B981', fontSize: '0.9rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
        ✓ Password updated.
      </div>
    )
  }

  return (
    <form onSubmit={(e) => void handleSubmit(e)} style={{ padding: 16, background: CARD_BG, borderRadius: 14, border: `1px solid ${CARD_BORDER}` }}>
      <h4 style={{ margin: '0 0 12px', fontSize: '0.95rem', color: TEXT_PRIMARY, fontWeight: 700 }}>Change password</h4>
      <input type="password" placeholder="Current password" value={oldPw} onChange={e => setOldPw(e.target.value)} required style={{ ...miniInput, marginBottom: 8 }} />
      <input type="password" placeholder="New password (min 8 chars)" value={newPw} onChange={e => setNewPw(e.target.value)} required minLength={8} style={{ ...miniInput, marginBottom: 12 }} />
      {error && <p style={{ color: '#C0392B', fontSize: '0.82rem', margin: '0 0 8px' }}>{error}</p>}
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="submit" disabled={loading} style={{ flex: 1, padding: '10px 16px', background: ACCENT, color: '#fff', border: 'none', borderRadius: 100, fontSize: '0.88rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' }}>
          {loading ? 'Saving…' : 'Save'}
        </button>
        <button type="button" onClick={onDone} style={outlineBtnStyle}>Cancel</button>
      </div>
    </form>
  )
}

const backBtnStyle: React.CSSProperties = {
  background: 'none', border: 'none', cursor: 'pointer',
  color: '#888', fontSize: '0.9rem', padding: 0,
  display: 'inline-flex', alignItems: 'center', gap: 4,
  fontFamily: 'inherit', fontWeight: 600,
}

const outlineBtnStyle: React.CSSProperties = {
  background: 'transparent', border: `1.5px solid ${CARD_BORDER}`,
  borderRadius: 100, padding: '10px 18px', fontSize: '0.88rem',
  cursor: 'pointer', color: TEXT_PRIMARY, fontWeight: 700, fontFamily: 'inherit',
}

const dataRowBtnStyle: React.CSSProperties = {
  width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  padding: '14px 16px', background: 'transparent', border: 'none',
  cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left',
}

const miniInput: React.CSSProperties = {
  width: '100%', padding: '10px 12px', border: `1.5px solid ${CARD_BORDER}`,
  borderRadius: 8, fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
  background: '#fff', display: 'block', fontFamily: 'inherit',
}
