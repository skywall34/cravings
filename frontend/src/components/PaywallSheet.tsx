import { useState, useEffect } from 'react'
import { createCheckout } from '../api'
import { LockGlyph, archHex, archShift } from './Archetype'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#8A7E72'
const SHEET_BG = '#FFFFFF'

const PAYWALL_FEATURES = [
  { emoji: '🧬', title: 'Your full Taste Archetype',  sub: 'The named identity, the one-liner, and the 5-axis breakdown behind it.' },
  { emoji: '📈', title: 'Drift tracking',             sub: 'Watch your palate change over time, axis by axis.' },
  { emoji: '🗓️', title: 'Monthly recap',              sub: 'A shareable "this month in your taste" card, every month.' },
]

type Phase = 'idle' | 'loading' | 'redirecting' | 'success'

interface PaywallSheetProps {
  open: boolean
  context?: string
  price?: string
  onClose: () => void
  onSuccess: () => void
}

export function PaywallSheet({ open, context, price = '4.99', onClose, onSuccess }: PaywallSheetProps) {
  const [phase, setPhase] = useState<Phase>('idle')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPhase('idle')
      requestAnimationFrame(() => setMounted(true))
    } else {
      setMounted(false)
    }
  }, [open])

  if (!open) return null

  async function pay() {
    setPhase('loading')
    try {
      const result = await createCheckout()
      if (result.url) {
        setPhase('redirecting')
        window.location.assign(result.url)
      } else {
        // Mock path: self-fired webhook will flip premium ~1.5s later
        setTimeout(() => setPhase('success'), 1500)
        setTimeout(() => { onSuccess() }, 2900)
      }
    } catch {
      setPhase('idle')
    }
  }

  return (
    <div
      onClick={phase === 'idle' ? onClose : undefined}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
        background: mounted ? 'rgba(20,12,6,0.5)' : 'rgba(20,12,6,0)',
        backdropFilter: mounted ? 'blur(3px)' : 'none',
        transition: 'background 0.3s ease',
        padding: '0',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 460, background: SHEET_BG,
          borderTopLeftRadius: 26, borderTopRightRadius: 26,
          boxShadow: '0 -10px 50px rgba(0,0,0,0.28)',
          transform: mounted ? 'translateY(0)' : 'translateY(100%)',
          transition: 'transform 0.36s cubic-bezier(0.22,1,0.36,1)',
          maxHeight: '94vh', overflowY: 'auto',
          padding: '10px 22px 32px',
        }}
      >
        {/* grabber */}
        <div style={{ display: 'flex', justifyContent: 'center', padding: '6px 0 14px' }}>
          <div style={{ width: 38, height: 4, borderRadius: 2, background: '#E2D6C8' }} />
        </div>

        {phase === 'success' ? (
          <PaywallSuccess />
        ) : (
          <>
            {/* header */}
            <div style={{ textAlign: 'center', marginBottom: 18 }}>
              <PremiumBadgeMini />
              <h2 style={{ margin: '12px 0 4px', fontSize: '1.4rem', fontWeight: 900, color: TEXT_PRIMARY, letterSpacing: '-0.02em' }}>
                Unlock Cravings Insights
              </h2>
              <p style={{ margin: 0, fontSize: '0.9rem', color: TEXT_SUB, lineHeight: 1.45 }}>
                {context === 'drift'
                  ? 'See how your palate is shifting over time.'
                  : 'Go beyond your name — see the why, and the change.'}
              </p>
            </div>

            {/* price chip */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              padding: '13px', borderRadius: 16, marginBottom: 18,
              background: archHex(ACCENT, 0.09), border: `1px solid ${archHex(ACCENT, 0.28)}`,
            }}>
              <span style={{ fontSize: '1.9rem', fontWeight: 900, color: TEXT_PRIMARY, letterSpacing: '-0.02em' }}>${price}</span>
              <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, color: TEXT_PRIMARY }}>one-time</div>
                <div style={{ fontSize: '0.74rem', color: TEXT_SUB, fontWeight: 600 }}>yours forever · no subscription</div>
              </div>
            </div>

            {/* features */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 11, marginBottom: 22 }}>
              {PAYWALL_FEATURES.map((f, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <span style={{
                    width: 34, height: 34, flexShrink: 0, borderRadius: 10, fontSize: '1.05rem',
                    background: archHex(ACCENT, 0.1), display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>{f.emoji}</span>
                  <div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 800, color: TEXT_PRIMARY, lineHeight: 1.3 }}>{f.title}</div>
                    <div style={{ fontSize: '0.78rem', color: TEXT_SUB, lineHeight: 1.4, marginTop: 1 }}>{f.sub}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Stripe checkout button */}
            <button
              type="button"
              onClick={() => { void pay() }}
              disabled={phase === 'loading' || phase === 'redirecting'}
              style={{
                width: '100%', padding: '15px', border: 'none', borderRadius: 100,
                background: (phase === 'loading' || phase === 'redirecting') ? archShift(ACCENT, 40) : ACCENT, color: '#fff',
                fontSize: '1.02rem', fontWeight: 800, cursor: (phase === 'loading' || phase === 'redirecting') ? 'progress' : 'pointer',
                fontFamily: 'inherit', boxShadow: `0 6px 20px ${archHex(ACCENT, 0.32)}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9,
              }}
            >
              {phase === 'redirecting'
                ? <><Spinner /> Redirecting to Stripe…</>
                : phase === 'loading'
                ? <><Spinner /> Processing…</>
                : <><LockGlyph size={15} /> Pay ${price} with Stripe</>}
            </button>

            {/* trust row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 15 }}>
              <LockGlyph size={12} />
              <span style={{ fontSize: '0.72rem', color: TEXT_SUB, fontWeight: 600 }}>
                Secure checkout · Powered by{' '}
                <span style={{ fontWeight: 900, color: '#635BFF', letterSpacing: '-0.01em' }}>stripe</span>
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function PaywallSuccess() {
  return (
    <div style={{ textAlign: 'center', padding: '14px 10px 26px' }}>
      <div style={{
        width: 72, height: 72, borderRadius: '50%', margin: '0 auto 18px',
        background: ACCENT, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: `0 10px 30px ${archHex(ACCENT, 0.42)}`, animation: 'fadeInUp 0.4s ease',
      }}>
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 style={{ margin: '0 0 6px', fontSize: '1.45rem', fontWeight: 900, color: TEXT_PRIMARY, letterSpacing: '-0.02em' }}>
        You&rsquo;re in. ✦
      </h2>
      <p style={{ margin: 0, fontSize: '0.92rem', color: TEXT_SUB, lineHeight: 1.5, maxWidth: 280, marginInline: 'auto' }}>
        Insights unlocked. Let&rsquo;s go meet the eater the model sees.
      </p>
    </div>
  )
}

function PremiumBadgeMini() {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '4px 11px', borderRadius: 100,
      background: 'linear-gradient(120deg, #F0B429, #D97706)',
      color: '#4A3000', fontSize: '0.68rem', fontWeight: 900,
      letterSpacing: '0.08em', textTransform: 'uppercase',
      boxShadow: '0 2px 8px rgba(180,120,0,0.25)',
    }}>
      <span>✦</span>Premium
    </span>
  )
}

function Spinner() {
  return (
    <span style={{
      width: 15, height: 15, borderRadius: '50%',
      border: '2.5px solid rgba(255,255,255,0.4)', borderTopColor: '#fff',
      display: 'inline-block', animation: 'spin 0.7s linear infinite',
    }} />
  )
}
