import { useState } from 'react'
import { login } from '../api'
import type { UserInfo } from '../api'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#888'
const FIELD_BG = '#FAFAF8'
const FIELD_BORDER = '#E8E0D8'

interface LoginFormProps {
  onSuccess: (user: UserInfo) => void
  onSwitchToRegister: () => void
  onBack: () => void
}

export function LoginForm({ onSuccess, onSwitchToRegister, onBack }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const result = await login(email.trim(), password)
      onSuccess(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ width: '100%', maxWidth: 380, margin: '0 auto', padding: '8px 4px 32px' }}>
      <BackButton onClick={onBack} />

      <h2 style={{ margin: '20px 0 6px', fontSize: '1.7rem', fontWeight: 800, color: TEXT_PRIMARY, letterSpacing: '-0.01em' }}>
        Welcome back
      </h2>
      <p style={{ margin: '0 0 28px', color: TEXT_SUB, fontSize: '0.92rem', lineHeight: 1.5 }}>
        Log in to sync your taste model across devices.
      </p>

      <form onSubmit={(e) => void handleSubmit(e)}>
        <Field label="Email">
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder="you@example.com"
            style={fieldInputStyle}
            onFocus={e => { e.currentTarget.style.borderColor = ACCENT }}
            onBlur={e => { e.currentTarget.style.borderColor = FIELD_BORDER }}
          />
        </Field>
        <Field label="Password">
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            placeholder="••••••••"
            style={fieldInputStyle}
            onFocus={e => { e.currentTarget.style.borderColor = ACCENT }}
            onBlur={e => { e.currentTarget.style.borderColor = FIELD_BORDER }}
          />
        </Field>

        {error && (
          <div style={{
            padding: '10px 12px',
            background: 'rgba(220, 38, 38, 0.08)',
            border: '1px solid rgba(220, 38, 38, 0.25)',
            borderRadius: 8,
            color: '#DC2626',
            fontSize: '0.85rem',
            margin: '4px 0 14px',
          }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            background: loading ? `${ACCENT}AA` : ACCENT,
            color: '#fff',
            border: 'none',
            borderRadius: 100,
            fontSize: '1rem',
            fontWeight: 700,
            cursor: loading ? 'progress' : 'pointer',
            marginTop: 6,
            fontFamily: 'inherit',
            letterSpacing: '0.02em',
            boxShadow: `0 4px 16px rgba(232,93,4,0.3)`,
            transition: 'opacity 0.15s, transform 0.15s',
          }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.transform = 'translateY(-1px)' }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}
        >
          {loading ? 'Logging in…' : 'Log in'}
        </button>
      </form>

      <div style={{
        textAlign: 'center',
        marginTop: 24,
        paddingTop: 20,
        borderTop: `1px solid ${FIELD_BORDER}`,
        fontSize: '0.88rem',
        color: TEXT_SUB,
      }}>
        New here?{' '}
        <button
          onClick={onSwitchToRegister}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: ACCENT, fontWeight: 700, padding: 0,
            fontSize: '0.88rem', fontFamily: 'inherit',
            textDecoration: 'underline', textUnderlineOffset: 3,
          }}
        >
          Create an account
        </button>
      </div>
    </div>
  )
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'none', border: 'none', cursor: 'pointer',
        color: '#888', fontSize: '0.88rem', padding: '4px 0',
        display: 'inline-flex', alignItems: 'center', gap: 4,
        fontFamily: 'inherit', fontWeight: 600,
      }}
    >
      <span style={{ fontSize: '1.1rem', lineHeight: 1 }}>←</span> Back
    </button>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{
        display: 'block', fontSize: '0.72rem', fontWeight: 700, marginBottom: 6,
        color: '#6B6B6B', letterSpacing: '0.08em', textTransform: 'uppercase',
      }}>
        {label}
      </label>
      {children}
    </div>
  )
}

const fieldInputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  border: `1.5px solid ${FIELD_BORDER}`,
  borderRadius: 10,
  fontSize: '1rem',
  outline: 'none',
  boxSizing: 'border-box',
  background: FIELD_BG,
  color: TEXT_PRIMARY,
  fontFamily: 'inherit',
  transition: 'border-color 0.15s ease',
}
