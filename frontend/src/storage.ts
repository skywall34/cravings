// Storage seam: web proxies localStorage; native (Capacitor) uses Preferences.
// Async everywhere so the native branch can await Preferences.get/set/remove.
import { Capacitor } from '@capacitor/core'
import { Preferences } from '@capacitor/preferences'

const native = Capacitor.isNativePlatform()

export async function get(key: string): Promise<string | null> {
  if (native) {
    const { value } = await Preferences.get({ key })
    return value
  }
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export async function set(key: string, value: string): Promise<void> {
  if (native) {
    await Preferences.set({ key, value })
    return
  }
  try {
    localStorage.setItem(key, value)
  } catch {
    /* ignore */
  }
}

export async function remove(key: string): Promise<void> {
  if (native) {
    await Preferences.remove({ key })
    return
  }
  try {
    localStorage.removeItem(key)
  } catch {
    /* ignore */
  }
}
