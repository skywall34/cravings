import { useState, useEffect } from 'react'
import { fetchStats, changePassword, deleteAccount, exportData } from '../api'
import type { UserInfo, SwipeStats } from '../api'
import {
  deriveTasteProfile,
  TastePersonaCard, InsightCard, FlavorRadar,
  YesRateGauge, CuisineAffinity, MoodDonut, PeakTimesChart,
} from './StatsCharts'

const MIN_SWIPES_FOR_PROFILE = 15

interface ProfilePageProps {
  user: UserInfo
  onBack: () => void
  onDeleteAccount?: () => void
}

export function ProfilePage({ user, onBack, onDeleteAccount }: ProfilePageProps) {
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
    <div style={{ maxWidth: 400, margin: '0 auto', padding: '24px 20px', paddingBottom: 60 }}>
      <button
        onClick={onBack}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888', fontSize: '0.9rem', padding: 0, marginBottom: 20 }}
      >
        ← Back
      </button>

      <div style={{ marginBottom: 28 }}>
        <h2 style={{ margin: '0 0 4px', fontSize: '1.5rem', fontWeight: 700 }}>Your Profile</h2>
        <p style={{ margin: 0, color: '#888', fontSize: '0.9rem' }}>{user.email}</p>
      </div>

      {loadingStats && <div style={{ color: '#AAA', textAlign: 'center', padding: 40 }}>Loading stats…</div>}
      {statsError && <p style={{ color: '#C0392B' }}>{statsError}</p>}

      {stats && <StatsSection stats={stats} />}

      {!showPasswordForm ? (
        <button
          onClick={() => setShowPasswordForm(true)}
          style={{ ...secondaryBtnStyle, marginTop: 24 }}
        >
          Change password
        </button>
      ) : (
        <ChangePasswordForm onDone={() => setShowPasswordForm(false)} />
      )}

      <Section title="Your Data">
        <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <button
            disabled={exportLoading}
            onClick={async () => {
              setExportLoading(true)
              try {
                const blob = await exportData()
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = 'cravings-data.json'
                a.click()
                URL.revokeObjectURL(url)
              } catch (e) {
                alert(e instanceof Error ? e.message : 'Export failed')
              } finally {
                setExportLoading(false)
              }
            }}
            style={secondaryBtnStyle}
          >
            {exportLoading ? 'Exporting…' : 'Export my data (JSON)'}
          </button>

          {!deleteConfirm ? (
            <button onClick={() => setDeleteConfirm(true)} style={dangerBtnStyle}>
              Delete my account
            </button>
          ) : (
            <div style={{ padding: '12px', background: '#FFF5F5', border: '1px solid #FCA5A5', borderRadius: 8 }}>
              <p style={{ margin: '0 0 10px', fontSize: '0.85rem', color: '#B91C1C', fontWeight: 600 }}>
                This will permanently delete your account and swipe history. This cannot be undone.
              </p>
              {deleteError && <p style={{ color: '#C0392B', fontSize: '0.82rem', margin: '0 0 8px' }}>{deleteError}</p>}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  disabled={deleteLoading}
                  onClick={async () => {
                    setDeleteLoading(true)
                    setDeleteError(null)
                    try {
                      await deleteAccount()
                      localStorage.removeItem('cravings_token')
                      onDeleteAccount?.()
                    } catch (e) {
                      setDeleteError(e instanceof Error ? e.message : 'Deletion failed')
                      setDeleteLoading(false)
                    }
                  }}
                  style={{ ...submitMiniStyle, background: '#DC2626' }}
                >
                  {deleteLoading ? 'Deleting…' : 'Yes, delete'}
                </button>
                <button onClick={() => setDeleteConfirm(false)} style={secondaryBtnStyle}>Cancel</button>
              </div>
            </div>
          )}
        </div>
      </Section>
    </div>
  )
}

function StatsSection({ stats }: { stats: SwipeStats }) {
  if (stats.total_swipes < MIN_SWIPES_FOR_PROFILE) {
    return (
      <div style={{
        marginTop: 8, marginBottom: 8, padding: '28px 24px', borderRadius: 16,
        background: '#FAFAF8', border: '1px solid #F0E8E0', textAlign: 'center',
      }}>
        <div style={{ fontSize: '2rem', marginBottom: 10 }}>🍽️</div>
        <div style={{ fontWeight: 800, fontSize: '1rem', color: '#2C2C2C', marginBottom: 6 }}>
          Keep swiping to unlock your taste profile
        </div>
        <div style={{ fontSize: '0.85rem', color: '#888', lineHeight: 1.5 }}>
          You've done {stats.total_swipes} swipe{stats.total_swipes !== 1 ? 's' : ''} so far.
          {' '}Reach {MIN_SWIPES_FOR_PROFILE} to see your personalized insights.
        </div>
      </div>
    )
  }

  const profile = deriveTasteProfile(stats)

  return (
    <>
      <TastePersonaCard profile={profile} totalSwipes={stats.total_swipes} />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 16 }}>
        {profile.insights.map((ins, i) => <InsightCard key={i} insight={ins} />)}
      </div>

      <Section title="Flavor Profile" subtitle="How your palate breaks down">
        <div style={{ padding: '16px 8px' }}>
          <FlavorRadar data={stats.flavor_profile} />
        </div>
      </Section>

      <Section title="How You Swipe" subtitle="Decisiveness meter">
        <div style={{ padding: '18px 16px' }}>
          <YesRateGauge value={profile.overallYes} avgToYes={stats.avg_swipes_to_right} />
        </div>
      </Section>

      {stats.cuisine_breakdown.length > 0 && (
        <Section title="Cuisine Affinity" subtitle="Ranked by acceptance rate">
          <CuisineAffinity items={stats.cuisine_breakdown} />
        </Section>
      )}

      {stats.mood_breakdown.length > 0 && (
        <Section title="Mood Mix" subtitle="How you swipe by mood">
          <div style={{ padding: '16px' }}>
            <MoodDonut items={stats.mood_breakdown} />
          </div>
        </Section>
      )}

      {stats.hour_breakdown.length > 0 && (
        <Section title="Peak Craving Times" subtitle="When hunger strikes">
          <div style={{ padding: '16px' }}>
            <PeakTimesChart items={stats.hour_breakdown} />
          </div>
        </Section>
      )}
    </>
  )
}

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
      setTimeout(onDone, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }

  if (success) return <p style={{ color: '#27AE60', marginTop: 16 }}>Password changed. Logging you in with new credentials.</p>

  return (
    <form onSubmit={(e) => void handleSubmit(e)} style={{ marginTop: 20, padding: 16, background: '#FAFAF8', borderRadius: 10, border: '1px solid #E8E0D8' }}>
      <h4 style={{ margin: '0 0 14px', fontSize: '0.95rem' }}>Change password</h4>
      <input
        type="password"
        placeholder="Current password"
        value={oldPw}
        onChange={e => setOldPw(e.target.value)}
        required
        style={{ ...miniInputStyle, marginBottom: 10 }}
      />
      <input
        type="password"
        placeholder="New password (min 8 chars)"
        value={newPw}
        onChange={e => setNewPw(e.target.value)}
        required
        minLength={8}
        style={{ ...miniInputStyle, marginBottom: 10 }}
      />
      {error && <p style={{ color: '#C0392B', fontSize: '0.82rem', margin: '0 0 8px' }}>{error}</p>}
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="submit" disabled={loading} style={{ ...submitMiniStyle }}>
          {loading ? 'Saving…' : 'Save'}
        </button>
        <button type="button" onClick={onDone} style={secondaryBtnStyle}>Cancel</button>
      </div>
    </form>
  )
}

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div style={{ marginTop: 20 }}>
      <h3 style={{ margin: '0 0 2px', fontSize: '0.85rem', fontWeight: 700, color: '#B0A89E', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
        {title}
      </h3>
      {subtitle && (
        <p style={{ margin: '0 0 8px', fontSize: '0.75rem', color: '#C0B8B0', letterSpacing: '0.04em', textTransform: 'uppercase', fontWeight: 600 }}>
          {subtitle}
        </p>
      )}
      <div style={{ background: '#FAFAF8', borderRadius: 10, border: '1px solid #F0E8E0', overflow: 'hidden' }}>
        {children}
      </div>
    </div>
  )
}

const secondaryBtnStyle: React.CSSProperties = {
  background: 'none',
  border: '1.5px solid #E8E0D8',
  borderRadius: 8,
  padding: '9px 16px',
  fontSize: '0.88rem',
  cursor: 'pointer',
  color: '#555',
}

const dangerBtnStyle: React.CSSProperties = {
  background: 'none',
  border: '1.5px solid #FCA5A5',
  borderRadius: 8,
  padding: '9px 16px',
  fontSize: '0.88rem',
  cursor: 'pointer',
  color: '#DC2626',
}

const miniInputStyle: React.CSSProperties = {
  width: '100%',
  padding: '9px 12px',
  border: '1.5px solid #E8E0D8',
  borderRadius: 8,
  fontSize: '0.9rem',
  outline: 'none',
  boxSizing: 'border-box',
  background: '#fff',
  display: 'block',
}

const submitMiniStyle: React.CSSProperties = {
  padding: '9px 20px',
  background: '#E85D04',
  color: '#fff',
  border: 'none',
  borderRadius: 8,
  fontSize: '0.88rem',
  fontWeight: 700,
  cursor: 'pointer',
}
