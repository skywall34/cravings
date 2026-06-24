import React, { useEffect, useState } from 'react'
import { getMe, getToken } from '../api'
import { AdminLogin } from './AdminLogin'
import { Dashboard } from './Dashboard'

type AuthState = 'checking' | 'login' | 'dashboard'

export function AdminApp() {
  const [authState, setAuthState] = useState<AuthState>('checking')

  useEffect(() => {
    async function check() {
      const token = await getToken()
      if (!token) { setAuthState('login'); return }
      try {
        const me = await getMe()
        setAuthState(me.is_admin ? 'dashboard' : 'login')
      } catch {
        setAuthState('login')
      }
    }
    void check()
  }, [])

  if (authState === 'checking') {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Nunito, sans-serif', background: '#FFF8F0' }}>
        <div style={{ fontSize: '2rem' }}>🍽️</div>
      </div>
    )
  }

  if (authState === 'login') {
    return <AdminLogin onLogin={() => setAuthState('dashboard')} />
  }

  return <Dashboard onSignOut={() => setAuthState('login')} />
}
