import React, { useState } from 'react'
import { login, logout } from '../api'
import { CravingsLogo } from './CravingsLogo'

const ACCENT = '#E85D04'
const BORDER = '#F0E8E0'

export function AdminLogin({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [shake, setShake] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(email, password)
      if (!user.is_admin) {
        await logout()
        triggerShake('403 · not authorized')
        return
      }
      onLogin()
    } catch (err) {
      triggerShake(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  function triggerShake(msg: string) {
    setError(msg)
    setShake(true)
    setTimeout(() => setShake(false), 500)
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#FFF8F0', fontFamily: 'Nunito, sans-serif', padding: 24,
    }}>
      <style>{`
        @keyframes shake {
          0%,100%{transform:translateX(0)}
          20%{transform:translateX(-8px)}
          40%{transform:translateX(8px)}
          60%{transform:translateX(-6px)}
          80%{transform:translateX(6px)}
        }
      `}</style>
      <div style={{
        width: '100%', maxWidth: 360, background: '#fff',
        borderRadius: 24, padding: '36px 32px',
        border: `1px solid ${BORDER}`,
        boxShadow: '0 8px 40px rgba(232,93,4,0.10)',
        animation: shake ? 'shake 0.45s ease' : undefined,
      }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <CravingsLogo size={40} />
          <div style={{ fontSize: '0.65rem', fontWeight: 800, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#aaa', marginTop: 8 }}>
            Admin Console
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#2C2C2C', marginTop: 6, letterSpacing: '-0.02em' }}>
            Sign in
          </div>
        </div>

        {error && (
          <div style={{ background: '#FFF0EE', border: `1px solid #F8BCAC`, borderRadius: 10, padding: '10px 14px', fontSize: '0.82rem', color: '#C0392B', marginBottom: 18, fontWeight: 600 }}>
            {error}
          </div>
        )}

        <form onSubmit={(e) => { void handleSubmit(e) }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <input
            type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="Email" required autoComplete="username"
            style={{ padding: '12px 16px', borderRadius: 12, border: `1px solid ${BORDER}`, fontSize: '0.92rem', fontFamily: 'Nunito, sans-serif', outline: 'none', background: '#FAFAF8' }}
          />
          <input
            type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="Password" required autoComplete="current-password"
            style={{ padding: '12px 16px', borderRadius: 12, border: `1px solid ${BORDER}`, fontSize: '0.92rem', fontFamily: 'Nunito, sans-serif', outline: 'none', background: '#FAFAF8' }}
          />
          <button
            type="submit" disabled={loading}
            style={{
              marginTop: 4, padding: '13px 0', borderRadius: 14, border: 'none',
              background: ACCENT, color: '#fff', fontSize: '0.96rem', fontWeight: 800,
              fontFamily: 'Nunito, sans-serif', cursor: loading ? 'wait' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
