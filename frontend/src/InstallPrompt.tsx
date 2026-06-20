import type { UseInstallResult } from './useInstall'

interface Props extends UseInstallResult {
  gated: boolean
}

export function InstallPrompt({ bucket, isStandalone, promptInstall, dismissed, dismiss, gated }: Props) {
  if (isStandalone || dismissed || !gated) return null

  if (bucket === 'event') {
    return (
      <div style={bannerStyle}>
        <button onClick={promptInstall} style={installBtnStyle}>Install Cravings</button>
        <button onClick={dismiss} style={dismissBtnStyle} aria-label="Dismiss">✕</button>
      </div>
    )
  }

  if (bucket === 'ios-safari') {
    return (
      <div style={bannerStyle}>
        <span style={{ fontSize: '0.88rem', color: '#2C2C2C', flex: 1 }}>
          Tap <strong>Share</strong> ⬆ then <strong>Add to Home Screen</strong>
        </span>
        <button onClick={dismiss} style={dismissBtnStyle} aria-label="Dismiss">✕</button>
      </div>
    )
  }

  return null
}

const bannerStyle: React.CSSProperties = {
  position: 'fixed',
  bottom: 0,
  left: 0,
  right: 0,
  paddingBottom: 'env(safe-area-inset-bottom, 0px)',
  background: '#FFF8F0',
  borderTop: '1px solid #E8E0D8',
  padding: '12px 16px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 12,
  zIndex: 200,
  boxShadow: '0 -2px 12px rgba(0,0,0,0.08)',
}

const installBtnStyle: React.CSSProperties = {
  background: '#E85D04',
  color: '#fff',
  border: 'none',
  borderRadius: 100,
  padding: '8px 20px',
  fontWeight: 700,
  cursor: 'pointer',
  fontSize: '0.9rem',
  fontFamily: 'inherit',
}

const dismissBtnStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  cursor: 'pointer',
  fontSize: '1.2rem',
  color: '#888',
  padding: '4px 8px',
  flexShrink: 0,
}
