// Presentational location-consent overlay. State + gating live in
// hooks/useLocationConsent; this only renders and reports allow/deny.
interface LocationConsentModalProps {
  open: boolean
  onAllow: () => void
  onDeny: () => void
  onOpenPrivacy: () => void
}

export function LocationConsentModal({ open, onAllow, onDeny, onOpenPrivacy }: LocationConsentModalProps) {
  if (!open) return null
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
      display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
      zIndex: 8000, padding: '0 12px calc(24px + env(safe-area-inset-bottom, 0px))',
    }}>
      <div style={{
        width: '100%', maxWidth: 480, background: '#fff',
        borderRadius: 20, padding: '24px 20px 20px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%',
            background: 'rgba(232,93,4,0.10)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, margin: '0 auto 12px',
          }}>📍</div>
          <h3 style={{ margin: '0 0 6px', fontSize: '1.1rem', fontWeight: 800, color: '#1A1A1A' }}>
            Use your location?
          </h3>
          <p style={{ margin: '0 auto', maxWidth: 320, fontSize: '0.86rem', lineHeight: 1.55, color: '#6B6B6B' }}>
            Cravings uses your approximate location to find nearby restaurants. We don't store
            precise coordinates.{' '}
            <button
              onClick={onOpenPrivacy}
              style={{ background: 'none', border: 'none', padding: 0, color: '#E85D04', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', fontSize: '0.86rem', textDecoration: 'underline', textUnderlineOffset: 2 }}
            >
              Privacy Policy
            </button>.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            onClick={onAllow}
            style={{
              width: '100%', padding: '13px', background: '#E85D04', color: '#fff',
              border: 'none', borderRadius: 100, fontSize: '0.95rem', fontWeight: 700,
              cursor: 'pointer', fontFamily: 'inherit',
              boxShadow: '0 4px 16px rgba(232,93,4,0.33)',
            }}
          >
            Allow location
          </button>
          <button
            onClick={onDeny}
            style={{
              width: '100%', padding: '11px', background: 'transparent',
              color: '#6B6B6B', border: 'none', borderRadius: 100,
              fontSize: '0.88rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            Not now
          </button>
        </div>
      </div>
    </div>
  )
}
