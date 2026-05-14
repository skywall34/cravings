import { useState } from 'react'
import { register } from '../api'
import type { UserInfo } from '../api'

interface RegisterFormProps {
  onSuccess: (user: UserInfo) => void
  onSwitchToLogin: () => void
  onBack: () => void
  isGuest: boolean
}

export function RegisterForm({ onSuccess, onSwitchToLogin, onBack, isGuest }: RegisterFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const result = await register(email.trim(), password, isGuest ? undefined : name.trim() || undefined)
      onSuccess(result)
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
    <div style={{ maxWidth: 360, margin: '0 auto', padding: '32px 20px' }}>
      <button
        onClick={onBack}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888', fontSize: '0.9rem', padding: 0, marginBottom: 24 }}
      >
        ← Back
      </button>
      <h2 style={{ margin: '0 0 6px', fontSize: '1.6rem', fontWeight: 700 }}>Create account</h2>
      <p style={{ margin: '0 0 28px', color: '#888', fontSize: '0.9rem' }}>
        {isGuest ? 'Save your swiping history and preferences' : 'Get started with Cravings'}
      </p>

      <form onSubmit={(e) => void handleSubmit(e)}>
        {!isGuest && (
          <Field label="Name">
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              required
              autoComplete="name"
              style={inputStyle}
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
            style={inputStyle}
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
            style={inputStyle}
          />
          <span style={{ fontSize: '0.75rem', color: '#AAA', marginTop: 4, display: 'block' }}>Minimum 8 characters</span>
        </Field>

        {error && (
          <p style={{ color: '#C0392B', fontSize: '0.85rem', margin: '0 0 12px' }}>
            {error}
            {error.includes('already registered') && (
              <button onClick={onSwitchToLogin} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#E85D04', fontWeight: 600, padding: 0, fontSize: '0.85rem' }}>
                Log in instead
              </button>
            )}
          </p>
        )}

        <button type="submit" disabled={loading} style={submitStyle}>
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p style={{ textAlign: 'center', marginTop: 20, fontSize: '0.85rem', color: '#888' }}>
        Already have an account?{' '}
        <button onClick={onSwitchToLogin} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#E85D04', fontWeight: 600, padding: 0 }}>
          Log in
        </button>
      </p>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, marginBottom: 6, color: '#555', letterSpacing: '0.04em' }}>
        {label.toUpperCase()}
      </label>
      {children}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  border: '1.5px solid #E8E0D8',
  borderRadius: 8,
  fontSize: '1rem',
  outline: 'none',
  boxSizing: 'border-box',
  background: '#FAFAF8',
}

const submitStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px',
  background: '#E85D04',
  color: '#fff',
  border: 'none',
  borderRadius: 8,
  fontSize: '1rem',
  fontWeight: 700,
  cursor: 'pointer',
  marginTop: 8,
}
