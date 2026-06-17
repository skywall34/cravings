// PaywallSheet.tsx — Mock Stripe payment sheet.
// Slides up from the bottom, shows $4.99 one-time unlock, a realistic
// (non-functional) card form, processing + success states.
// No real Stripe — onSuccess fires the unlock.

import { useState, useEffect } from 'react'
import { LockGlyph, archHex, archShift } from './Archetype'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#8A7E72'
const FIELD_BG = '#FAF7F3'
const FIELD_BORDER = '#EAE0D5'
const SHEET_BG = '#FFFFFF'

const PAYWALL_FEATURES = [
  { emoji: '🧬', title: 'Your full Taste Archetype',  sub: 'The named identity, the one-liner, and the 5-axis breakdown behind it.' },
  { emoji: '📈', title: 'Drift tracking',             sub: 'Watch your palate change over time, axis by axis.' },
  { emoji: '🗓️', title: 'Monthly recap',              sub: 'A shareable "this month in your taste" card, every month.' },
]

type Phase = 'form' | 'processing' | 'success'

interface PaywallSheetProps {
  open: boolean
  context?: string
  price?: string
  onClose: () => void
  onSuccess: () => void
}

export function PaywallSheet({ open, context, price = '4.99', onClose, onSuccess }: PaywallSheetProps) {
  const [phase, setPhase] = useState<Phase>('form')
  const [card, setCard] = useState('')
  const [exp, setExp] = useState('')
  const [cvc, setCvc] = useState('')
  const [zip, setZip] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPhase('form'); setCard(''); setExp(''); setCvc(''); setZip('')
      requestAnimationFrame(() => setMounted(true))
    } else {
      setMounted(false)
    }
  }, [open])

  if (!open) return null

  function pay(e: React.FormEvent) {
    e.preventDefault()
    setPhase('processing')
    setTimeout(() => setPhase('success'), 1500)
    setTimeout(() => { onSuccess() }, 2900)
  }

  return (
    <div
      onClick={phase === 'form' ? onClose : undefined}
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

            {/* mock card form */}
            <form onSubmit={pay}>
              <div style={{ fontSize: '0.7rem', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: TEXT_SUB, marginBottom: 8 }}>
                Card details
              </div>
              <div style={{ borderRadius: 13, border: `1.5px solid ${FIELD_BORDER}`, overflow: 'hidden', background: FIELD_BG, marginBottom: 14 }}>
                <div style={{ position: 'relative' }}>
                  <input
                    inputMode="numeric" placeholder="Card number" value={card}
                    onChange={e => setCard(formatCard(e.target.value))}
                    style={{ ...pwField, borderBottom: `1px solid ${FIELD_BORDER}` }}
                  />
                  <div style={{ position: 'absolute', right: 13, top: '50%', transform: 'translateY(-50%)', display: 'flex', gap: 4 }}>
                    <CardBrandDot c1="#EB4B3C" c2="#F7A823" />
                    <CardBrandDot c1="#1A1F71" c2="#2566AF" single />
                  </div>
                </div>
                <div style={{ display: 'flex' }}>
                  <input inputMode="numeric" placeholder="MM / YY" value={exp}
                    onChange={e => setExp(formatExp(e.target.value))}
                    style={{ ...pwField, borderRight: `1px solid ${FIELD_BORDER}` }} />
                  <input inputMode="numeric" placeholder="CVC" value={cvc}
                    onChange={e => setCvc(e.target.value.replace(/\D/g, '').slice(0, 4))}
                    style={{ ...pwField, borderRight: `1px solid ${FIELD_BORDER}` }} />
                  <input inputMode="numeric" placeholder="ZIP" value={zip}
                    onChange={e => setZip(e.target.value.replace(/\D/g, '').slice(0, 5))}
                    style={pwField} />
                </div>
              </div>

              <button
                type="submit"
                disabled={phase === 'processing'}
                style={{
                  width: '100%', padding: '15px', border: 'none', borderRadius: 100,
                  background: phase === 'processing' ? archShift(ACCENT, 40) : ACCENT, color: '#fff',
                  fontSize: '1.02rem', fontWeight: 800, cursor: phase === 'processing' ? 'progress' : 'pointer',
                  fontFamily: 'inherit', boxShadow: `0 6px 20px ${archHex(ACCENT, 0.32)}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 9,
                }}
              >
                {phase === 'processing'
                  ? <><Spinner /> Processing…</>
                  : <><LockGlyph size={15} /> Pay ${price}</>}
              </button>
            </form>

            {/* trust row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 15 }}>
              <LockGlyph size={12} />
              <span style={{ fontSize: '0.72rem', color: TEXT_SUB, fontWeight: 600 }}>
                Secure checkout · Powered by{' '}
                <span style={{ fontWeight: 900, color: '#635BFF', letterSpacing: '-0.01em' }}>stripe</span>
              </span>
            </div>
            <p style={{ textAlign: 'center', margin: '12px 0 0', fontSize: '0.7rem', color: TEXT_SUB, opacity: 0.8 }}>
              Demo only — no card is charged.
            </p>
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

function CardBrandDot({ c1, c2, single }: { c1: string; c2: string; single?: boolean }) {
  return (
    <span style={{ display: 'inline-flex' }}>
      <span style={{ width: 16, height: 11, borderRadius: 3, background: c1 }} />
      {!single && <span style={{ width: 16, height: 11, borderRadius: 3, background: c2, marginLeft: -6 }} />}
    </span>
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

const pwField: React.CSSProperties = {
  flex: 1, width: '100%', minWidth: 0, padding: '14px 13px',
  background: 'transparent', border: 'none', outline: 'none',
  fontSize: '0.95rem', fontWeight: 600, color: TEXT_PRIMARY, fontFamily: 'inherit',
}

function formatCard(v: string): string {
  const d = v.replace(/\D/g, '').slice(0, 16)
  return d.replace(/(.{4})/g, '$1 ').trim()
}

function formatExp(v: string): string {
  const d = v.replace(/\D/g, '').slice(0, 4)
  return d.length >= 3 ? `${d.slice(0, 2)} / ${d.slice(2)}` : d
}
