import { useState, useCallback } from 'react'

interface Location {
  lat: number
  lng: number
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
    return new Promise((resolve, reject) => {
      if (location) {
        resolve(location)
        return
      }
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
