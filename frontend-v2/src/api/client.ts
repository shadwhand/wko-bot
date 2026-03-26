import {
  ApiError,
  type HealthResponse,
  type WarmupStatusResponse,
  type FitnessData,
  type PMCRow,
  type ClinicalFlagsResponse,
  type ProfileResponse,
  type AthleteConfig,
  type ModelResult,
  type ActivitiesResponse,
  type RollingFtpRow,
  type FtpGrowthResponse,
  type RollingPdResponse,
  type IfDistributionResponse,
  type FreshBaselineResponse,
  type ShortPowerResponse,
  type PerformanceTrendResponse,
  type DetectedPhase,
  type FeasibilityResponse,
  type TrainingBlock,
  type WeeklySummary,
  type PosteriorSummaryResponse,
  type RideDetail,
  type RouteListItem,
  type RouteDetail,
  type GlycogenBudgetRequest,
  type GlycogenBudgetResponse,
} from './types'

// ─── Configuration ────────────────────────────────────────────────

/** Base URL — empty string means same-origin (Vite proxy handles /api). */
const BASE_URL = ''

/** Resolve bearer token from meta tag, URL param, or localStorage. */
function resolveToken(): string | null {
  // 1. Try <meta name="wko5-token" content="...">
  const meta = document.querySelector<HTMLMetaElement>('meta[name="wko5-token"]')
  if (meta?.content) return meta.content

  // 2. Try URL param (legacy v1 compat) — save and strip
  try {
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    if (urlToken) {
      localStorage.setItem('wko5_token', urlToken)
      const url = new URL(window.location.href)
      url.searchParams.delete('token')
      window.history.replaceState({}, '', url.toString())
      return urlToken
    }
  } catch {
    // URL parsing may fail in test environments
  }

  // 3. Try localStorage
  return localStorage.getItem('wko5_token')
}

let _token: string | null | undefined = undefined

/** Get the current auth token, resolving lazily on first call. */
export function getToken(): string | null {
  if (_token === undefined) {
    _token = resolveToken()
  }
  return _token
}

/** Set the auth token (e.g., after receiving it from the backend). */
export function setToken(token: string): void {
  _token = token
  try {
    localStorage.setItem('wko5_token', token)
  } catch {
    // localStorage may be unavailable
  }
}

/**
 * Bootstrap token from /api/runtime (localhost-only, no auth required).
 * Call once during app startup before any authenticated API calls.
 * Returns true if a token was obtained.
 */
export async function bootstrapToken(): Promise<boolean> {
  // Already have a token — skip
  if (getToken()) return true

  try {
    const res = await fetch(`${BASE_URL}/api/runtime`)
    if (!res.ok) return false
    const data = (await res.json()) as { token?: string }
    if (data.token) {
      setToken(data.token)
      return true
    }
  } catch {
    // Backend may not be reachable yet — caller can retry
  }
  return false
}

// ─── Generic fetch wrapper ────────────────────────────────────────

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string> | undefined),
  }

  const res = await fetch(`${BASE_URL}/api${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new ApiError(res.status, body)
  }

  const text = await res.text()
  return text ? (JSON.parse(text) as T) : (null as T)
}

/** Build query string from params, omitting null/undefined. */
function qs(params: Record<string, string | number | boolean | null | undefined>): string {
  const parts: string[] = []
  for (const [key, value] of Object.entries(params)) {
    if (value != null) {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    }
  }
  return parts.length ? `?${parts.join('&')}` : ''
}

// ─── No-auth endpoints ────────────────────────────────────────────

export async function getWarmupStatus(): Promise<WarmupStatusResponse> {
  // No auth needed — dashboard polls this during startup before token is known
  const res = await fetch(`${BASE_URL}/api/warmup-status`)
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json() as Promise<WarmupStatusResponse>
}

// ─── Core data endpoints ──────────────────────────────────────────

export async function getHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/health')
}

export async function getFitness(): Promise<FitnessData> {
  return fetchApi<FitnessData>('/fitness')
}

export async function getPmc(params?: {
  start?: string
  end?: string
}): Promise<PMCRow[]> {
  return fetchApi<PMCRow[]>(`/pmc${qs(params ?? {})}`)
}

export async function getClinicalFlags(daysBack = 30): Promise<ClinicalFlagsResponse> {
  return fetchApi<ClinicalFlagsResponse>(`/clinical-flags${qs({ days_back: daysBack })}`)
}

export async function getProfile(days = 90): Promise<ProfileResponse> {
  return fetchApi<ProfileResponse>(`/profile${qs({ days })}`)
}

export async function getConfig(): Promise<AthleteConfig> {
  return fetchApi<AthleteConfig>('/config')
}

export async function getModel(days = 90): Promise<ModelResult> {
  return fetchApi<ModelResult>(`/model${qs({ days })}`)
}

export async function getActivities(params?: {
  start?: string
  end?: string
  sub_sport?: string
  limit?: number
  offset?: number
}): Promise<ActivitiesResponse> {
  return fetchApi<ActivitiesResponse>(`/activities${qs(params ?? {})}`)
}

// ─── Secondary data endpoints ─────────────────────────────────────

export async function getRollingFtp(params?: {
  window?: number
  step?: number
}): Promise<RollingFtpRow[]> {
  return fetchApi<RollingFtpRow[]>(`/rolling-ftp${qs(params ?? {})}`)
}

export async function getFtpGrowth(): Promise<FtpGrowthResponse> {
  return fetchApi<FtpGrowthResponse>('/ftp-growth')
}

export async function getRollingPdProfile(): Promise<RollingPdResponse> {
  return fetchApi<RollingPdResponse>('/rolling-pd-profile')
}

export async function getIfDistribution(): Promise<IfDistributionResponse> {
  return fetchApi<IfDistributionResponse>('/if-distribution')
}

export async function getFreshBaseline(): Promise<FreshBaselineResponse> {
  return fetchApi<FreshBaselineResponse>('/fresh-baseline')
}

export async function getShortPowerConsistency(): Promise<ShortPowerResponse> {
  return fetchApi<ShortPowerResponse>('/short-power-consistency')
}

export async function getPerformanceTrend(): Promise<PerformanceTrendResponse> {
  return fetchApi<PerformanceTrendResponse>('/performance-trend')
}

// ─── On-demand endpoints ──────────────────────────────────────────

export async function getRide(activityId: number): Promise<RideDetail> {
  return fetchApi<RideDetail>(`/ride/${activityId}`)
}

export async function getRideIntervals(activityId: number): Promise<unknown[]> {
  return fetchApi<unknown[]>(`/ride/${activityId}/intervals`)
}

export async function getRideEfforts(activityId: number): Promise<unknown[]> {
  return fetchApi<unknown[]>(`/ride/${activityId}/efforts`)
}

export async function getRoutes(): Promise<RouteListItem[]> {
  return fetchApi<RouteListItem[]>('/routes')
}

export async function getRouteDetail(routeId: number): Promise<RouteDetail> {
  return fetchApi<RouteDetail>(`/routes/${routeId}`)
}

// ─── Analysis endpoints ───────────────────────────────────────────

export async function getTrainingBlocks(params?: {
  start?: string
  end?: string
}): Promise<TrainingBlock[]> {
  return fetchApi<TrainingBlock[]>(`/training-blocks${qs(params ?? {})}`)
}

export async function getWeeklySummary(params?: {
  start?: string
  end?: string
}): Promise<WeeklySummary[]> {
  return fetchApi<WeeklySummary[]>(`/weekly-summary${qs(params ?? {})}`)
}

export async function getDetectPhase(params?: {
  start?: string
  end?: string
}): Promise<DetectedPhase> {
  return fetchApi<DetectedPhase>(`/detect-phase${qs(params ?? {})}`)
}

export async function getFeasibility(params?: {
  target_ctl?: number
  weeks?: number
}): Promise<FeasibilityResponse> {
  return fetchApi<FeasibilityResponse>(`/feasibility${qs(params ?? {})}`)
}

export async function getPosteriorSummary(): Promise<PosteriorSummaryResponse> {
  return fetchApi<PosteriorSummaryResponse>('/posterior-summary')
}

// ─── POST endpoints ───────────────────────────────────────────────

export async function postGlycogenBudget(
  body: GlycogenBudgetRequest,
): Promise<GlycogenBudgetResponse> {
  return fetchApi<GlycogenBudgetResponse>('/glycogen-budget', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function postUpdateModels(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/update-models', { method: 'POST' })
}
