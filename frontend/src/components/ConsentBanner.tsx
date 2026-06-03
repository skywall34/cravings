import { useState, useEffect } from 'react'
import * as storage from '../storage'

const CONSENT_KEY = 'cravings_consent'

interface ConsentBannerProps {
  onOpenPrivacy: () => void
}

export function ConsentBanner({ onOpenPrivacy }: ConsentBannerProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined
    void storage.get(CONSENT_KEY).then(stored => {
      if (cancelled || stored) return
      timer = setTimeout(() => setVisible(true), 600)
    })
    return () => { cancelled = true; if (timer) clearTimeout(timer) }
  }, [])

  function decide(choice: 'all' | 'essential') {
    void storage.set(CONSENT_KEY, choice)
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div style={{
      position: 'fixed',
      left: 0, right: 0, bottom: 0,
      display: 'flex',
      justifyContent: 'center',
      padding: '0 12px 12px',
      zIndex: 9000,
      pointerEvents: 'none',
    }}>
      <div style={{
        pointerEvents: 'auto',
        width: '100%',
        maxWidth: 480,
        background: '#FFFFFF',
        border: '1px solid #EADFD3',
        borderRadius: 16,
        boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
        padding: '16px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
          <span style={{ fontSize: '1.15rem', lineHeight: 1.1 }} aria-hidden="true">🍪</span>
          <p style={{ margin: 0, fontSize: '0.84rem', lineHeight: 1.5, color: '#6B6B6B' }}>
            <strong style={{ color: '#1A1A1A', fontWeight: 800 }}>We use cookies &amp; local storage.</strong>{' '}
            Essential storage keeps you signed in and remembers your taste model. Optional analytics help us
            improve recommendations. See our{' '}
            <button
              onClick={onOpenPrivacy}
              style={{
                background: 'none', border: 'none', padding: 0, color: '#E85D04',
                fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
                fontSize: '0.84rem', textDecoration: 'underline', textUnderlineOffset: 2,
              }}
            >
              Privacy Policy
            </button>.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
          <button
            onClick={() => decide('essential')}
            style={{
              padding: '9px 18px', background: 'transparent',
              border: '1.5px solid #EADFD3', borderRadius: 100,
              fontSize: '0.85rem', fontWeight: 700, color: '#1A1A1A',
              cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            Essential only
          </button>
          <button
            onClick={() => decide('all')}
            style={{
              padding: '9px 22px', background: '#E85D04', color: '#fff',
              border: 'none', borderRadius: 100, fontSize: '0.85rem',
              fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
              boxShadow: '0 4px 14px rgba(232,93,4,0.33)',
            }}
          >
            Accept all
          </button>
        </div>
      </div>
    </div>
  )
}
