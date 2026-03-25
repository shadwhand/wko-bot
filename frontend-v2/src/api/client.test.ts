import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ApiError } from './types'

// Must be imported after mocking fetch
let getHealth: typeof import('./client').getHealth
let getFitness: typeof import('./client').getFitness
let getWarmupStatus: typeof import('./client').getWarmupStatus
let setToken: typeof import('./client').setToken

beforeEach(async () => {
  vi.stubGlobal('fetch', vi.fn())
  // Dynamic import to get fresh module per test
  const mod = await import('./client')
  getHealth = mod.getHealth
  getFitness = mod.getFitness
  getWarmupStatus = mod.getWarmupStatus
  setToken = mod.setToken
  setToken('test-token-123')
})

afterEach(() => {
  vi.restoreAllMocks()
})

function mockFetch(body: unknown, status = 200) {
  ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(JSON.stringify(body)),
    json: () => Promise.resolve(body),
  })
}

describe('fetchApi', () => {
  it('sends Authorization header', async () => {
    mockFetch({ status: 'ok', cache_warm: true, warmup_errors: null, data_version: 1 })
    await getHealth()
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/health',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token-123',
        }),
      }),
    )
  })

  it('throws ApiError on non-2xx', async () => {
    mockFetch('Unauthorized', 401)
    await expect(getFitness()).rejects.toThrow(ApiError)
    mockFetch('Unauthorized', 401) // re-mock needed for second call
    await expect(getFitness()).rejects.toThrow(ApiError)
  })

  it('parses JSON response', async () => {
    mockFetch({ CTL: 55, ATL: 60, TSB: -5, date: '2026-03-24' })
    const data = await getFitness()
    expect(data.CTL).toBe(55)
    expect(data.TSB).toBe(-5)
  })
})

describe('getWarmupStatus', () => {
  it('does not send auth header', async () => {
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: () =>
        Promise.resolve(
          JSON.stringify({ running: false, done: true, results: {}, errors: {} }),
        ),
      json: () =>
        Promise.resolve({ running: false, done: true, results: {}, errors: {} }),
    })
    await getWarmupStatus()
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/warmup-status')
  })
})
