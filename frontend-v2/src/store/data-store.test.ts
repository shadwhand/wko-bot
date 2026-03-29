import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useDataStore } from './data-store'

// Mock the API module
vi.mock('../api/client', () => ({
  getFitness: vi.fn().mockResolvedValue({ CTL: 55, ATL: 60, TSB: -5, date: '2026-03-24' }),
  getPmc: vi.fn().mockResolvedValue([
    { date: '2026-03-24', TSS: 80, CTL: 55, ATL: 60, TSB: -5 },
  ]),
  getClinicalFlags: vi.fn().mockResolvedValue({ flags: [], alert_level: 'green' }),
  getProfile: vi.fn().mockResolvedValue({ profile: {}, ranking: {}, strengths_limiters: {} }),
  getConfig: vi.fn().mockResolvedValue({ id: 1, name: 'default', weight_kg: 78 }),
  getModel: vi.fn().mockResolvedValue({ Pmax: 1100, FRC: 18, mFTP: 292, mmp: [] }),
  getActivities: vi.fn().mockResolvedValue({ activities: [], total: 0, limit: 50, offset: 0 }),
  getRollingFtp: vi.fn().mockResolvedValue([]),
  getFtpGrowth: vi.fn().mockResolvedValue(null),
  getRollingPdProfile: vi.fn().mockResolvedValue({ data: [] }),
  getIfDistribution: vi.fn().mockResolvedValue(null),
  getFreshBaseline: vi.fn().mockResolvedValue(null),
  getShortPowerConsistency: vi.fn().mockResolvedValue(null),
  getPerformanceTrend: vi.fn().mockResolvedValue({ data: [] }),
  getHealth: vi.fn().mockResolvedValue({ status: 'ok', cache_warm: true, data_version: 1 }),
  getRide: vi.fn().mockResolvedValue({ summary: {}, records: [], intervals: [] }),
  getRouteAnalysis: vi.fn().mockResolvedValue({
    route: { id: 42, name: 'Test Route', distance_km: 100, elevation_m: 1500, source: 'rwgps', history: [], plans: [], points: [] },
    demand: { segments: [], summary: {} },
    gap_analysis: { feasible: true, bottleneck: null },
    opportunity_cost: [],
  }),
}))

beforeEach(() => {
  // Reset store state before each test
  useDataStore.setState({
    fitness: null,
    pmc: [],
    clinicalFlags: null,
    profile: null,
    config: null,
    activities: [],
    activitiesTotal: 0,
    model: null,
    loading: new Set(),
    errors: {},
    lastRefresh: null,
    dataVersion: null,
    annotations: {},
    rides: {},
  })
})

describe('DataStore', () => {
  it('starts with null/empty state', () => {
    const state = useDataStore.getState()
    expect(state.fitness).toBeNull()
    expect(state.pmc).toEqual([])
    expect(state.loading.size).toBe(0)
    expect(state.errors).toEqual({})
  })

  it('fetchCore populates fitness, pmc, flags, profile, config, model, activities', async () => {
    await useDataStore.getState().fetchCore()
    const state = useDataStore.getState()
    expect(state.fitness).toEqual({ CTL: 55, ATL: 60, TSB: -5, date: '2026-03-24' })
    expect(state.pmc).toHaveLength(1)
    expect(state.clinicalFlags).toEqual({ flags: [], alert_level: 'green' })
    expect(state.config).toBeDefined()
    expect(state.model).toBeDefined()
    expect(state.lastRefresh).toBeTruthy()
  })

  it('fetchCore clears loading set when done', async () => {
    await useDataStore.getState().fetchCore()
    expect(useDataStore.getState().loading.size).toBe(0)
  })

  it('fetchCore stores errors per-key on failure', async () => {
    const { getFitness } = await import('../api/client')
    vi.mocked(getFitness).mockRejectedValueOnce(new Error('Network error'))
    await useDataStore.getState().fetchCore()
    const state = useDataStore.getState()
    expect(state.errors['fitness']).toBe('Network error')
    // Other keys should still succeed
    expect(state.pmc).toHaveLength(1)
  })

  it('setSelectedRoute updates state', () => {
    useDataStore.getState().setSelectedRoute(42)
    expect(useDataStore.getState().selectedRouteId).toBe(42)
  })

  it('setTimeRange updates state', () => {
    useDataStore.getState().setTimeRange({ start: '2026-01-01', end: '2026-03-01' })
    expect(useDataStore.getState().globalTimeRange).toEqual({
      start: '2026-01-01',
      end: '2026-03-01',
    })
  })

  it('addAnnotation appends to panelId key', () => {
    const annotation = {
      id: 'a1',
      source: 'claude' as const,
      type: 'region' as const,
      label: 'CTL drop',
      color: 'red',
      timestamp: new Date().toISOString(),
    }
    useDataStore.getState().addAnnotation('pmc-chart', annotation)
    expect(useDataStore.getState().annotations['pmc-chart']).toHaveLength(1)
    // Add another
    useDataStore.getState().addAnnotation('pmc-chart', { ...annotation, id: 'a2' })
    expect(useDataStore.getState().annotations['pmc-chart']).toHaveLength(2)
  })

  it('clearAnnotations clears specific panel or all', () => {
    const a = {
      id: 'a1',
      source: 'claude' as const,
      type: 'line' as const,
      label: 'Test',
      color: 'blue',
      timestamp: new Date().toISOString(),
    }
    useDataStore.getState().addAnnotation('pmc', a)
    useDataStore.getState().addAnnotation('mmp', a)

    useDataStore.getState().clearAnnotations('pmc')
    expect(useDataStore.getState().annotations['pmc']).toBeUndefined()
    expect(useDataStore.getState().annotations['mmp']).toHaveLength(1)

    useDataStore.getState().clearAnnotations()
    expect(useDataStore.getState().annotations).toEqual({})
  })

  it('checkForUpdates detects version change', async () => {
    // First call — sets initial version, no refresh needed
    const changed = await useDataStore.getState().checkForUpdates()
    expect(changed).toBe(false)
    expect(useDataStore.getState().dataVersion).toBe(1)

    // Simulate backend version bump
    const { getHealth } = await import('../api/client')
    vi.mocked(getHealth).mockResolvedValueOnce({
      status: 'ok',
      cache_warm: true,
      warmup_errors: null,
      data_version: 2,
    })
    const changed2 = await useDataStore.getState().checkForUpdates()
    expect(changed2).toBe(true)
    expect(useDataStore.getState().dataVersion).toBe(2)
  })
})
