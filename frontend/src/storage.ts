// Storage seam kept async so a future native/platform backend can slot in; web path is localStorage.
export function get(key: string): Promise<string | null> {
  try {
    return Promise.resolve(localStorage.getItem(key))
  } catch {
    return Promise.resolve(null)
  }
}

export function set(key: string, value: string): Promise<void> {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* ignore */
  }
  return Promise.resolve()
}

export function remove(key: string): Promise<void> {
  try {
    localStorage.removeItem(key)
  } catch {
    /* ignore */
  }
  return Promise.resolve()
}
