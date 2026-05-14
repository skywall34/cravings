import { useState } from 'react'
import { login } from '../api'
import type { UserInfo } from '../api'

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
    <div style={{ maxWidth: 360, margin: '0 auto', padding: '32px 20px' }}>
      <button
        onClick={onBack}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888', fontSize: '0.9rem', padding: 0, marginBottom: 24 }}
      >
        ← Back
      </button>
      <h2 style={{ margin: '0 0 6px', fontSize: '1.6rem', fontWeight: 700 }}>Welcome back</h2>
      <p style={{ margin: '0 0 28px', color: '#888', fontSize: '0.9rem' }}>Log in to access your preferences</p>

      <form onSubmit={(e) => void handleSubmit(e)}>
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
            autoComplete="current-password"
            style={inputStyle}
          />
        </Field>

        {error && <p style={{ color: '#C0392B', fontSize: '0.85rem', margin: '0 0 12px' }}>{error}</p>}

        <button type="submit" disabled={loading} style={submitStyle}>
          {loading ? 'Logging in…' : 'Log in'}
        </button>
      </form>

      <p style={{ textAlign: 'center', marginTop: 20, fontSize: '0.85rem', color: '#888' }}>
        Don't have an account?{' '}
        <button onClick={onSwitchToRegister} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#E85D04', fontWeight: 600, padding: 0 }}>
          Register
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
