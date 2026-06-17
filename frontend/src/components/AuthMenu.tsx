import { useState, useRef, useEffect } from 'react'
import type { UserInfo } from '../api'

interface AuthMenuProps {
  user: UserInfo | null
  isPremium: boolean
  onLogin: () => void
  onRegister: () => void
  onProfile: () => void
  onInsights: () => void
  onLogout: () => void
}

export function AuthMenu({ user, isPremium, onLogin, onRegister, onProfile, onInsights, onLogout }: AuthMenuProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontSize: '1.4rem',
          padding: '4px 8px',
          lineHeight: 1,
        }}
        aria-label="Account menu"
      >
        {user?.is_registered ? '👤' : '☰'}
      </button>

      {open && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          background: '#fff',
          border: '1px solid #E8E0D8',
          borderRadius: 10,
          boxShadow: '0 4px 16px rgba(0,0,0,0.10)',
          minWidth: 160,
          zIndex: 100,
          overflow: 'hidden',
        }}>
          {user?.is_registered ? (
            <>
              <div style={{ padding: '10px 16px', fontSize: '0.82rem', color: '#888', borderBottom: '1px solid #F0E8E0' }}>
                {user.email}
              </div>
              <MenuItem onClick={() => { setOpen(false); onProfile() }}>Profile &amp; Stats</MenuItem>
              <MenuItem onClick={() => { setOpen(false); onInsights() }}>
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                  <span>Insights</span>
                  {isPremium
                    ? <span style={{ fontSize: '0.72rem' }}>✨</span>
                    : <span style={{
                        fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.08em',
                        padding: '2px 6px', borderRadius: 100,
                        background: 'linear-gradient(120deg, #F0B429, #D97706)',
                        color: '#4A3000',
                      }}>UPGRADE</span>
                  }
                </span>
              </MenuItem>
              <MenuItem onClick={() => { setOpen(false); onLogout() }} danger>Log out</MenuItem>
            </>
          ) : (
            <>
              <MenuItem onClick={() => { setOpen(false); onLogin() }}>Log in</MenuItem>
              <MenuItem onClick={() => { setOpen(false); onRegister() }}>Register</MenuItem>
            </>
          )}
        </div>
      )}
    </div>
  )
}

function MenuItem({ onClick, danger, children }: { onClick: () => void; danger?: boolean; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        background: 'none',
        border: 'none',
        padding: '11px 16px',
        cursor: 'pointer',
        fontSize: '0.9rem',
        color: danger ? '#C0392B' : '#2C2C2C',
      }}
    >
      {children}
    </button>
  )
}
