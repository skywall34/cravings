import { describe, it, expect, vi, beforeEach } from 'vitest'
import { effectivePremium } from './api'
import type { UserInfo } from './api'

// Mock storage so tests don't need localStorage/Capacitor
vi.mock('./storage', () => ({
  get: vi.fn().mockResolvedValue('test-bearer-token'),
  set: vi.fn().mockResolvedValue(undefined),
  remove: vi.fn().mockResolvedValue(undefined),
}))

// ---------------------------------------------------------------------------
// effectivePremium truth table
// ---------------------------------------------------------------------------

const base: UserInfo = {
  id: 1, name: 'Test', email: null,
  is_registered: false, onboarding_complete: false,
  is_premium: false, is_admin: false,
}

describe('effectivePremium', () => {
  it('returns false for null user', () => {
    expect(effectivePremium(null)).toBe(false)
  })

  it('returns false for guest (no email)', () => {
    expect(effectivePremium({ ...base })).toBe(false)
  })

  it('returns false for registered non-premium non-admin', () => {
    expect(effectivePremium({ ...base, is_registered: true, email: 'u@x.com' })).toBe(false)
  })

  it('returns true for is_premium', () => {
    expect(effectivePremium({ ...base, is_premium: true })).toBe(true)
  })

  it('returns true for is_admin', () => {
    expect(effectivePremium({ ...base, is_admin: true })).toBe(true)
  })

  it('returns true when both is_premium and is_admin', () => {
    expect(effectivePremium({ ...base, is_premium: true, is_admin: true })).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// createCheckout — posts to /api/billing/checkout, returns both shapes
// ---------------------------------------------------------------------------

describe('createCheckout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('posts to /api/billing/checkout and parses mock shape (url=null)', async () => {
    const mockResponse = {
      session_id: 'mock_cs_abc123',
      amount_cents: 499,
      provider: 'mock',
      url: null,
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    })

    const { createCheckout } = await import('./api')
    const result = await createCheckout()

    expect(global.fetch).toHaveBeenCalledOnce()
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    const calls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls
    const url = calls[0][0] as string
    const opts = calls[0][1] as RequestInit
    expect(url).toContain('/api/billing/checkout')
    expect((opts.headers as Record<string, string>)['Authorization']).toBe('Bearer test-bearer-token')
    expect(opts.method).toBe('POST')

    expect(result.provider).toBe('mock')
    expect(result.url).toBeNull()
    expect(result.session_id).toBe('mock_cs_abc123')
    expect(result.amount_cents).toBe(499)
  })

  it('parses stripe shape (url present)', async () => {
    const mockResponse = {
      session_id: 'cs_test_abc',
      amount_cents: 499,
      provider: 'stripe',
      url: 'https://checkout.stripe.com/pay/cs_test_abc',
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    })

    const { createCheckout } = await import('./api')
    const result = await createCheckout()

    expect(result.provider).toBe('stripe')
    expect(result.url).toBe('https://checkout.stripe.com/pay/cs_test_abc')
  })
})
