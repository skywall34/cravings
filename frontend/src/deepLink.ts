export type DeepLinkScreen = 'swipe' | 'privacy' | 'terms' | 'deletion'

export function initialScreenFromPath(pathname: string): DeepLinkScreen {
  const path = pathname.replace(/\/$/, '')
  if (path.endsWith('/account-deletion')) return 'deletion'
  if (path.endsWith('/privacy')) return 'privacy'
  if (path.endsWith('/terms')) return 'terms'
  return 'swipe'
}
