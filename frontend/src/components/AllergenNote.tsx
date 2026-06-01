export function AllergenNote({ style }: { style?: React.CSSProperties }) {
  return (
    <div
      role="note"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 8,
        padding: '9px 12px',
        borderRadius: 10,
        background: 'rgba(245,158,11,0.09)',
        border: '1px solid rgba(245,158,11,0.28)',
        ...style,
      }}
    >
      <span style={{ fontSize: '0.92rem', lineHeight: 1.2, flexShrink: 0 }} aria-hidden="true">⚠️</span>
      <p style={{ margin: 0, fontSize: '0.72rem', lineHeight: 1.45, color: '#8A6A1F', fontWeight: 600 }}>
        Diet &amp; allergen tags are best-effort, not certified safe. Not medical advice — always confirm
        ingredients with the restaurant directly.
      </p>
    </div>
  )
}
