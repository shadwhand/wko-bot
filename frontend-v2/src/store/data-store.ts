import { create } from 'zustand'
import type {
  FitnessData,
  PMCRow,
  ClinicalFlagsResponse,
  ProfileResponse,
  AthleteConfig,
  ModelResult,
  Activity,
  RollingFtpRow,
  FtpGrowthResponse,
  RollingPdRow,
  IfDistributionResponse,
  FreshBaselineResponse,
  ShortPowerResponse,
  PerformanceTrendRow,
  RideDetail,
  RouteListItem,
  Annotation,
  HealthResponse,
} from '../api/types'
import * as api from '../api/client'

// ─── Store interface ──────────────────────────────────────────────

export interface DataStore {
  // Core (fetched at startup)
  fitness: FitnessData | null
  pmc: PMCRow[]
  clinicalFlags: ClinicalFlagsResponse | null
  profile: ProfileResponse | null
  config: AthleteConfig | null
  activities: Activity[]
  activitiesTotal: number
  model: ModelResult | null

  // Secondary (lazy-loaded)
  rollingFtp: RollingFtpRow[]
  ftpGrowth: FtpGrowthResponse | null
  rollingPd: RollingPdRow[]
  ifDistribution: IfDistributionResponse | null
  freshBaseline: FreshBaselineResponse | null
  shortPower: ShortPowerResponse | null
  performanceTrend: PerformanceTrendRow[]

  // On-demand (keyed by ID)
  rides: Record<number, RideDetail>
  routes: RouteListItem[]

  // Cross-panel state
  selectedRouteId: number | null
  athleteSlug: string
  globalTimeRange: { start: string; end: string } | null

  // Metadata
  loading: Set<string>
  errors: Record<string, string>
  lastRefresh: string | null
  dataVersion: number | null

  // Annotations (from Claude via MCP)
  annotations: Record<string, Annotation[]>

  // Actions
  fetchCore: () => Promise<void>
  fetchSecondary: () => Promise<void>
  fetchRide: (id: number) => Promise<void>
  setSelectedRoute: (id: number | null) => void
  setTimeRange: (range: { start: string; end: string } | null) => void
  addAnnotation: (panelId: string, annotation: Annotation) => void
  clearAnnotations: (panelId?: string) => void
  refresh: () => Promise<void>
  checkForUpdates: () => Promise<boolean>
}

// ─── Helpers ──────────────────────────────────────────────────────

function addLoading(set: (fn: (s: DataStore) => Partial<DataStore>) => void, key: string) {
  set((s) => {
    const next = new Set(s.loading)
    next.add(key)
    return { loading: next }
  })
}

function removeLoading(set: (fn: (s: DataStore) => Partial<DataStore>) => void, key: string) {
  set((s) => {
    const next = new Set(s.loading)
    next.delete(key)
    return { loading: next }
  })
}

function setError(
  set: (fn: (s: DataStore) => Partial<DataStore>) => void,
  key: string,
  error: unknown,
) {
  const message = error instanceof Error ? error.message : String(error)
  set((s) => ({ errors: { ...s.errors, [key]: message } }))
}

function clearError(set: (fn: (s: DataStore) => Partial<DataStore>) => void, key: string) {
  set((s) => {
    const next = { ...s.errors }
    delete next[key]
    return { errors: next }
  })
}

/** Wrap an async fetch with loading + error tracking. */
async function tracked<T>(
  set: (fn: (s: DataStore) => Partial<DataStore>) => void,
  key: string,
  fetcher: () => Promise<T>,
  onSuccess: (data: T) => Partial<DataStore>,
): Promise<void> {
  addLoading(set, key)
  clearError(set, key)
  try {
    const data = await fetcher()
    set(() => onSuccess(data))
  } catch (err) {
    setError(set, key, err)
  } finally {
    removeLoading(set, key)
  }
}

// ─── Store ────────────────────────────────────────────────────────

export const useDataStore = create<DataStore>()((set, get) => ({
  // Core
  fitness: null,
  pmc: [],
  clinicalFlags: null,
  profile: null,
  config: null,
  activities: [],
  activitiesTotal: 0,
  model: null,

  // Secondary
  rollingFtp: [],
  ftpGrowth: null,
  rollingPd: [],
  ifDistribution: null,
  freshBaseline: null,
  shortPower: null,
  performanceTrend: [],

  // On-demand
  rides: {},
  routes: [],

  // Cross-panel
  selectedRouteId: null,
  athleteSlug: 'default',
  globalTimeRange: null,

  // Metadata
  loading: new Set<string>(),
  errors: {},
  lastRefresh: null,
  dataVersion: null,

  // Annotations
  annotations: {},

  // ── Actions ──────────────────────────────────────────────────

  fetchCore: async () => {
    const fetches = [
      tracked(set, 'fitness', api.getFitness, (d) => ({ fitness: d })),
      tracked(set, 'pmc', api.getPmc, (d) => ({ pmc: d })),
      tracked(set, 'clinicalFlags', api.getClinicalFlags, (d) => ({ clinicalFlags: d })),
      tracked(set, 'profile', () => api.getProfile(), (d) => ({ profile: d })),
      tracked(set, 'config', api.getConfig, (d) => ({ config: d })),
      tracked(set, 'model', () => api.getModel(90), (d) => ({ model: d })),
      tracked(set, 'activities', () => api.getActivities({ limit: 50 }), (d) => ({
        activities: d.activities,
        activitiesTotal: d.total,
      })),
    ]
    await Promise.allSettled(fetches)
    set(() => ({ lastRefresh: new Date().toISOString() }))
  },

  fetchSecondary: async () => {
    const fetches = [
      tracked(set, 'rollingFtp', api.getRollingFtp, (d) => ({ rollingFtp: d })),
      tracked(set, 'ftpGrowth', api.getFtpGrowth, (d) => ({ ftpGrowth: d })),
      tracked(set, 'rollingPd', api.getRollingPdProfile, (d) => ({ rollingPd: d.data })),
      tracked(set, 'ifDistribution', api.getIfDistribution, (d) => ({ ifDistribution: d })),
      tracked(set, 'freshBaseline', api.getFreshBaseline, (d) => ({ freshBaseline: d })),
      tracked(set, 'shortPower', api.getShortPowerConsistency, (d) => ({ shortPower: d })),
      tracked(set, 'performanceTrend', api.getPerformanceTrend, (d) => ({
        performanceTrend: d.data,
      })),
    ]
    await Promise.allSettled(fetches)
  },

  fetchRide: async (id: number) => {
    await tracked(set, `ride:${id}`, () => api.getRide(id), (d) => ({
      rides: { ...get().rides, [id]: d },
    }))
  },

  setSelectedRoute: (id) => set(() => ({ selectedRouteId: id })),

  setTimeRange: (range) => set(() => ({ globalTimeRange: range })),

  addAnnotation: (panelId, annotation) =>
    set((s) => ({
      annotations: {
        ...s.annotations,
        [panelId]: [...(s.annotations[panelId] ?? []), annotation],
      },
    })),

  clearAnnotations: (panelId) =>
    set((s) => {
      if (panelId) {
        const next = { ...s.annotations }
        delete next[panelId]
        return { annotations: next }
      }
      return { annotations: {} }
    }),

  refresh: async () => {
    const store = get()
    await store.fetchCore()
    // Background secondary refresh
    store.fetchSecondary()
  },

  checkForUpdates: async () => {
    try {
      const health: HealthResponse = await api.getHealth()
      const currentVersion = get().dataVersion
      if (health.data_version !== currentVersion) {
        set(() => ({ dataVersion: health.data_version }))
        if (currentVersion !== null) {
          // Version changed since last check — need refresh
          return true
        }
      }
      return false
    } catch {
      return false
    }
  },
}))
