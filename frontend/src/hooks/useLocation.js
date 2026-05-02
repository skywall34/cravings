import { useState, useCallback } from 'react'

export function useLocation() {
  const [location, setLocation] = useState(null)
  const [error, setError] = useState(null)

  // Returns {lat, lng} — prompts the browser if not yet granted.
  const requestLocation = useCallback(() => {
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
          const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude }
          setLocation(loc)
          resolve(loc)
        },
        (err) => {
          const msg = 'Location access denied — restaurant suggestions unavailable'
          setError(msg)
          reject(new Error(msg))
        }
      )
    })
  }, [location])

  return { location, error, requestLocation }
}
