import { useCallback, useState } from 'react'
import * as storage from '../storage'

const LOCATION_CONSENT_KEY = 'cravings_location_consent'

interface Gated {
  action: () => void | Promise<void>
  onDeny?: () => void
}

// Owns location-consent state and the gated-action queue. Replaces the
// callback-in-state pattern that lived in App.tsx: gate() runs the action
// immediately if consent was already granted, otherwise queues it and surfaces
// the modal; allow()/deny() resolve the queued action.
export function useLocationConsent(): {
  needsConsent: boolean
  gate: (action: () => void | Promise<void>, onDeny?: () => void) => Promise<void>
  allow: () => Promise<void>
  deny: () => Promise<void>
} {
  const [gated, setGated] = useState<Gated | null>(null)

  const gate = useCallback(async (action: () => void | Promise<void>, onDeny?: () => void) => {
    const granted = await storage.get(LOCATION_CONSENT_KEY)
    if (granted) {
      await action()
      return
    }
    setGated({ action, onDeny })
  }, [])

  const allow = useCallback(async () => {
    await storage.set(LOCATION_CONSENT_KEY, 'granted')
    const g = gated
    setGated(null)
    if (g) await g.action()
  }, [gated])

  const deny = useCallback(async () => {
    await storage.set(LOCATION_CONSENT_KEY, 'denied')
    const g = gated
    setGated(null)
    g?.onDeny?.()
  }, [gated])

  return { needsConsent: gated !== null, gate, allow, deny }
}
