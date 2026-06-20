import { useState, useEffect, useRef } from 'react'
import * as storage from './storage'

const DISMISS_KEY = 'cravings_install_dismissed'

function isIosSafari(): boolean {
  const ua = navigator.userAgent
  const isIosDevice =
    /iPhone|iPad|iPod/.test(ua) ||
    (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)
  return isIosDevice && !(/CriOS|FxiOS/.test(ua))
}

function getInitialBucket(): InstallBucket {
  const standalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  if (!standalone && isIosSafari()) return 'ios-safari'
  return 'other'
}

export type InstallBucket = 'event' | 'ios-safari' | 'other'

export interface UseInstallResult {
  bucket: InstallBucket
  isStandalone: boolean
  promptInstall: () => void
  dismissed: boolean
  dismiss: () => void
  forceShow: () => void
}

export function useInstall(): UseInstallResult {
  const [bucket, setBucket] = useState<InstallBucket>(getInitialBucket)
  const [dismissed, setDismissed] = useState(true) // hidden until storage loaded
  const [forced, setForced] = useState(false)
  const deferredPrompt = useRef<(Event & { prompt: () => void }) | null>(null)

  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true

  useEffect(() => {
    void storage.get(DISMISS_KEY).then(v => setDismissed(v === '1'))
  }, [])

  useEffect(() => {
    if (isStandalone) return

    const handler = (e: Event) => {
      e.preventDefault()
      deferredPrompt.current = e as Event & { prompt: () => void }
      setBucket('event')
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [isStandalone])

  function promptInstall() {
    deferredPrompt.current?.prompt()
  }

  function dismiss() {
    setForced(false)
    setDismissed(true)
    void storage.set(DISMISS_KEY, '1')
  }

  function forceShow() {
    setForced(true)
    setDismissed(false)
  }

  return { bucket, isStandalone, promptInstall, dismissed: dismissed && !forced, dismiss, forceShow }
}
