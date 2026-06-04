import { useState, useCallback } from 'react'
import { Capacitor } from '@capacitor/core'
import { Geolocation } from '@capacitor/geolocation'

interface Location {
  lat: number
  lng: number
}

// Native path: Capacitor Geolocation with coarse accuracy (enableHighAccuracy:false).
// Requests runtime permission if not yet granted. Throws on denial/unavailable.
async function getNativeLocation(): Promise<Location> {
  let perm = await Geolocation.checkPermissions()
  if (perm.location !== 'granted' && perm.coarseLocation !== 'granted') {
    perm = await Geolocation.requestPermissions({ permissions: ['coarseLocation'] })
  }
  if (perm.location === 'denied' && perm.coarseLocation === 'denied') {
    throw new Error('Location access denied — restaurant suggestions unavailable')
  }
  const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: false })
  return { lat: pos.coords.latitude, lng: pos.coords.longitude }
}

interface UseLocationReturn {
  location: Location | null
  error: string | null
  requestLocation: () => Promise<Location>
}

export function useLocation(): UseLocationReturn {
  const [location, setLocation] = useState<Location | null>(null)
  const [error, setError] = useState<string | null>(null)

  const requestLocation = useCallback((): Promise<Location> => {
    if (location) return Promise.resolve(location)

    if (Capacitor.isNativePlatform()) {
      return getNativeLocation().then(
        loc => { setLocation(loc); return loc },
        err => {
          const msg = err instanceof Error ? err.message : 'Location unavailable'
          setError(msg)
          throw new Error(msg)
        },
      )
    }

    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        const err = 'Geolocation not supported by your browser'
        setError(err)
        reject(new Error(err))
        return
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const loc: Location = { lat: pos.coords.latitude, lng: pos.coords.longitude }
          setLocation(loc)
          resolve(loc)
        },
        () => {
          const msg = 'Location access denied — restaurant suggestions unavailable'
          setError(msg)
          reject(new Error(msg))
        },
      )
    })
  }, [location])

  return { location, error, requestLocation }
}
