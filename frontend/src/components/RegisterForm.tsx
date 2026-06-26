import { useState, useMemo } from 'react'
import { register } from '../api'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#888'
const FIELD_BG = '#FAFAF8'
const FIELD_BORDER = '#E8E0D8'

interface RegisterFormProps {
  // Fired once the account is created; the email still needs verification, so
  // the app routes to the verify step rather than starting a session here.
  onNeedsVerification: (email: string) => void
  onSwitchToLogin: () => void
  onBack: () => void
  isGuest: boolean
  onOpenTerms?: () => void
  onOpenPrivacy?: () => void
}

export function RegisterForm({ onNeedsVerification, onSwitchToLogin, onBack, isGuest, onOpenTerms, onOpenPrivacy }: RegisterFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    const normalizedEmail = email.trim()
    try {
      await register(normalizedEmail, password, isGuest ? undefined : name.trim() || undefined)
      onNeedsVerification(normalizedEmail)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed'
      if (msg.toLowerCase().includes('already registered')) {
        setError('Email already registered. ')
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ width: '100%', maxWidth: 380, margin: '0 auto', padding: '8px 4px 32px' }}>
      <BackButton onClick={onBack} />

      <h2 style={{ margin: '20px 0 6px', fontSize: '1.7rem', fontWeight: 800, color: TEXT_PRIMARY, letterSpacing: '-0.01em' }}>
        Create account
      </h2>
      <p style={{ margin: '0 0 24px', color: TEXT_SUB, fontSize: '0.92rem', lineHeight: 1.5 }}>
        {isGuest
          ? 'Save your swipes and taste model — your current session carries over.'
          : 'Get started with Cravings.'}
      </p>

      {isGuest && (
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 10,
          padding: '12px 14px', marginBottom: 20,
          background: `rgba(232,93,4,0.06)`,
          border: `1px solid rgba(232,93,4,0.2)`,
          borderRadius: 12,
        }}>
          <span style={{ fontSize: '1.1rem', lineHeight: 1.1 }}>✨</span>
          <div style={{ fontSize: '0.82rem', color: '#5A4A3F', lineHeight: 1.45 }}>
            Your guest session will be linked to this account — nothing is lost.
          </div>
        </div>
      )}

      <form onSubmit={(e) => void handleSubmit(e)}>
        {!isGuest && (
          <Field label="Name">
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              required
              autoComplete="name"
              placeholder="Jamie"
              style={fieldInputStyle}
              onFocus={e => { e.currentTarget.style.borderColor = ACCENT }}
              onBlur={e => { e.currentTarget.style.borderColor = FIELD_BORDER }}
            />
          </Field>
        )}
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
            minLength={8}
            autoComplete="new-password"
            placeholder="At least 8 characters"
            style={fieldInputStyle}
            onFocus={e => { e.currentTarget.style.borderColor = ACCENT }}
            onBlur={e => { e.currentTarget.style.borderColor = FIELD_BORDER }}
          />
          <PasswordStrength value={password} />
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
            {error.includes('already registered') && (
              <button onClick={onSwitchToLogin} style={inlineAccentBtn}>Log in instead</button>
            )}
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
            transition: 'transform 0.15s',
          }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.transform = 'translateY(-1px)' }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}
        >
          {loading ? 'Creating account…' : 'Create account'}
        </button>

        <p style={{ margin: '14px 2px 0', fontSize: '0.74rem', lineHeight: 1.5, color: TEXT_SUB, textAlign: 'center' }}>
          By creating an account, you agree to our{' '}
          <button type="button" onClick={onOpenTerms} style={legalLinkStyle}>Terms</button>
          {' '}and{' '}
          <button type="button" onClick={onOpenPrivacy} style={legalLinkStyle}>Privacy Policy</button>.
        </p>
      </form>

      <div style={{
        textAlign: 'center',
        marginTop: 24,
        paddingTop: 20,
        borderTop: `1px solid ${FIELD_BORDER}`,
        fontSize: '0.88rem',
        color: TEXT_SUB,
      }}>
        Already have an account?{' '}
        <button
          onClick={onSwitchToLogin}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: ACCENT, fontWeight: 700, padding: 0,
            fontSize: '0.88rem', fontFamily: 'inherit',
            textDecoration: 'underline', textUnderlineOffset: 3,
          }}
        >
          Log in
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

function PasswordStrength({ value }: { value: string }) {
  const score = useMemo(() => {
    if (!value) return 0
    let s = 0
    if (value.length >= 8) s++
    if (value.length >= 12) s++
    if (/[A-Z]/.test(value) && /[a-z]/.test(value)) s++
    if (/[0-9]/.test(value)) s++
    if (/[^A-Za-z0-9]/.test(value)) s++
    return Math.min(s, 4)
  }, [value])

  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong']
  const colors = [FIELD_BORDER, '#DC2626', '#F59E0B', '#10B981', ACCENT]

  return (
    <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, display: 'flex', gap: 3 }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} style={{
            flex: 1, height: 3, borderRadius: 2,
            background: i <= score ? colors[score] : FIELD_BORDER,
            transition: 'background 0.2s',
          }} />
        ))}
      </div>
      <span style={{
        fontSize: '0.7rem', fontWeight: 700,
        color: score > 0 ? colors[score] : '#B0A89E',
        minWidth: 40, textAlign: 'right', letterSpacing: '0.04em',
      }}>
        {value ? labels[score] : '8+ chars'}
      </span>
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

const legalLinkStyle: React.CSSProperties = {
  background: 'none', border: 'none', padding: 0, cursor: 'pointer',
  fontFamily: 'inherit', fontSize: '0.74rem', fontWeight: 700,
  color: ACCENT, textDecoration: 'underline', textUnderlineOffset: 2,
}

const inlineAccentBtn: React.CSSProperties = {
  background: 'none', border: 'none', cursor: 'pointer',
  color: ACCENT, fontWeight: 600, padding: 0,
  fontSize: '0.85rem', fontFamily: 'inherit',
}
