import { describe, it, expect } from 'vitest'
import { initialScreenFromPath } from './deepLink'

describe('initialScreenFromPath', () => {
  it('matches privacy', () => {
    expect(initialScreenFromPath('/cravings/privacy')).toBe('privacy')
  })

  it('matches terms with trailing slash', () => {
    expect(initialScreenFromPath('/cravings/terms/')).toBe('terms')
  })

  it('matches account-deletion', () => {
    expect(initialScreenFromPath('/cravings/account-deletion')).toBe('deletion')
  })

  it('falls back to swipe for the app root with trailing slash', () => {
    expect(initialScreenFromPath('/cravings/')).toBe('swipe')
  })

  it('falls back to swipe for the bare root', () => {
    expect(initialScreenFromPath('/')).toBe('swipe')
  })

  it('falls back to swipe for garbage paths', () => {
    expect(initialScreenFromPath('/cravings/nonsense')).toBe('swipe')
  })
})
