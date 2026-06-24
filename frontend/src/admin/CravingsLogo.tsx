import React from 'react'

export function CravingsLogo({ size = 32 }: { size?: number }) {
  return (
    <span style={{ fontSize: size * 0.9, lineHeight: 1 }} aria-label="Cravings">
      🍽️
    </span>
  )
}
