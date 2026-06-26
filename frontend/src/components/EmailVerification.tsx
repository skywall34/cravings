import { useState, useRef, useEffect } from 'react'
import { verifyEmail, resendVerification, RateLimitError } from '../api'
import type { AuthResult } from '../api'

const ACCENT = '#E85D04'
const TEXT_PRIMARY = '#1A1A1A'
const TEXT_SUB = '#888'
const FIELD_BG = '#FAFAF8'
const FIELD_BORDER = '#E8E0D8'
const LEN = 6
const RESEND_COOLDOWN = 30

interface EmailVerificationProps {
  email: string
  onVerified: (user: AuthResult) => void
  onBack: () => void
}

export function EmailVerification({ email, onVerified, onBack }: EmailVerificationProps) {
  const [digits, setDigits] = useState<string[]>(() => Array<string>(LEN).fill(''))
  const [error, setError] = useState<string | null>(null)
  const [verifying, setVerifying] = useState(false)
  const [verified, setVerified] = useState(false)
  const [resendIn, setResendIn] = useState(RESEND_COOLDOWN)
  const inputs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => { inputs.current[0]?.focus() }, [])
  useEffect(() => {
    if (resendIn <= 0) return
    const t = setTimeout(() => setResendIn(r => r - 1), 1000)
    return () => clearTimeout(t)
  }, [resendIn])

  async function attempt(full?: string) {
    const value = full ?? digits.join('')
    if (value.length < LEN) { setError('Enter all 6 digits.'); return }
    setVerifying(true)
    setError(null)
    try {
      const user = await verifyEmail(email, value)
      setVerified(true)
      setTimeout(() => onVerified(user), 950)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Verification failed'
      setError(msg.charAt(0).toUpperCase() + msg.slice(1))
      setDigits(Array<string>(LEN).fill(''))
      inputs.current[0]?.focus()
    } finally {
      setVerifying(false)
    }
  }

  function handleChange(i: number, raw: string) {
    const v = raw.replace(/\D/g, '')
    if (!v) {
      const next = [...digits]; next[i] = ''; setDigits(next)
      return
    }
    // Support pasting / typing several characters at once.
    const next = [...digits]
    let idx = i
    for (const ch of v.split('')) { if (idx < LEN) { next[idx] = ch; idx += 1 } }
    setDigits(next)
    setError(null)
    const focusIdx = Math.min(idx, LEN - 1)
    inputs.current[focusIdx]?.focus()
    if (next.every(d => d !== '')) void attempt(next.join(''))
  }

  function handleKeyDown(i: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace' && !digits[i] && i > 0) {
      e.preventDefault()
      const next = [...digits]; next[i - 1] = ''; setDigits(next)
      inputs.current[i - 1]?.focus()
    } else if (e.key === 'ArrowLeft' && i > 0) {
      inputs.current[i - 1]?.focus()
    } else if (e.key === 'ArrowRight' && i < LEN - 1) {
      inputs.current[i + 1]?.focus()
    }
  }

  async function resend() {
    if (resendIn > 0) return
    setError(null)
    try {
      await resendVerification(email)
      setDigits(Array<string>(LEN).fill(''))
      setResendIn(RESEND_COOLDOWN)
      inputs.current[0]?.focus()
    } catch (err) {
      if (err instanceof RateLimitError) {
        setResendIn(err.retry_after)
      } else {
        setError(err instanceof Error ? err.message : 'Could not resend code')
      }
    }
  }

  if (verified) {
    return (
      <div style={{ width: '100%', maxWidth: 380, margin: '0 auto', padding: '8px 4px 32px', textAlign: 'center' }}>
        <div style={{
          width: 76, height: 76, borderRadius: '50%', margin: '40px auto 22px',
          background: ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 10px 30px rgba(232,93,4,0.27)`, animation: 'fadeInUp 0.4s cubic-bezier(0.22,1,0.36,1)',
        }}>
          <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <h2 style={{ margin: '0 0 8px', fontSize: '1.6rem', fontWeight: 800, color: TEXT_PRIMARY, letterSpacing: '-0.01em' }}>
          Email verified
        </h2>
        <p style={{ margin: 0, color: TEXT_SUB, fontSize: '0.92rem', lineHeight: 1.5 }}>
          You're all set — taking you to Cravings…
        </p>
      </div>
    )
  }

  const boxStyle = (filled: boolean, isError: boolean): React.CSSProperties => ({
    width: 48, height: 56, textAlign: 'center', fontSize: '1.5rem', fontWeight: 800,
    fontFamily: 'inherit', color: TEXT_PRIMARY, background: FIELD_BG,
    border: `1.5px solid ${isError ? '#DC2626' : (filled ? ACCENT : FIELD_BORDER)}`,
    borderRadius: 12, outline: 'none', caretColor: ACCENT,
    transition: 'border-color 0.15s ease', boxSizing: 'border-box',
  })

  const allFilled = digits.every(d => d !== '')

  return (
    <div style={{ width: '100%', maxWidth: 380, margin: '0 auto', padding: '8px 4px 32px' }}>
      <BackButton onClick={onBack} />

      <h2 style={{ margin: '20px 0 6px', fontSize: '1.7rem', fontWeight: 800, color: TEXT_PRIMARY, letterSpacing: '-0.01em' }}>
        Verify your email
      </h2>
      <p style={{ margin: '0 0 24px', color: TEXT_SUB, fontSize: '0.92rem', lineHeight: 1.5 }}>
        We sent a 6-digit code to{' '}
        <strong style={{ color: TEXT_PRIMARY, fontWeight: 800 }}>{email || 'your email'}</strong>. Enter it below to finish creating your account.
      </p>

      <div
        style={{ display: 'flex', gap: 8, justifyContent: 'space-between', marginBottom: 14 }}
        onPaste={e => { e.preventDefault(); handleChange(0, e.clipboardData.getData('text') || '') }}
      >
        {Array.from({ length: LEN }).map((_, i) => (
          <input
            key={i}
            ref={el => { inputs.current[i] = el }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digits[i]}
            disabled={verifying}
            onChange={e => handleChange(i, e.target.value)}
            onKeyDown={e => handleKeyDown(i, e)}
            onFocus={e => e.currentTarget.select()}
            style={boxStyle(digits[i] !== '', !!error)}
          />
        ))}
      </div>

      {error && (
        <div style={{
          padding: '10px 12px', background: 'rgba(220, 38, 38, 0.08)',
          border: '1px solid rgba(220, 38, 38, 0.25)', borderRadius: 8,
          color: '#DC2626', fontSize: '0.85rem', margin: '0 0 14px',
        }}>
          {error}
        </div>
      )}

      <button
        type="button"
        onClick={() => void attempt()}
        disabled={verifying || !allFilled}
        style={{
          width: '100%', padding: '14px',
          background: (verifying || !allFilled) ? `${ACCENT}AA` : ACCENT,
          color: '#fff', border: 'none', borderRadius: 100, fontSize: '1rem', fontWeight: 700,
          cursor: verifying ? 'progress' : (!allFilled ? 'not-allowed' : 'pointer'),
          marginTop: 4, fontFamily: 'inherit', letterSpacing: '0.02em',
          boxShadow: `0 4px 16px rgba(232,93,4,0.2)`, transition: 'transform 0.15s',
        }}
      >
        {verifying ? 'Verifying…' : 'Verify & continue'}
      </button>

      <div style={{ textAlign: 'center', marginTop: 18, fontSize: '0.86rem', color: TEXT_SUB }}>
        Didn't get it?{' '}
        {resendIn > 0 ? (
          <span style={{ color: TEXT_SUB, fontWeight: 600 }}>Resend in {resendIn}s</span>
        ) : (
          <button
            onClick={() => void resend()}
            style={{
              background: 'none', border: 'none', cursor: 'pointer', color: ACCENT,
              fontWeight: 700, padding: 0, fontSize: '0.86rem', fontFamily: 'inherit',
              textDecoration: 'underline', textUnderlineOffset: 3,
            }}
          >
            Resend code
          </button>
        )}
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
