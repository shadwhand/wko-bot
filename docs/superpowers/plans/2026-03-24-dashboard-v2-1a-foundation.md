# Dashboard v2 — Plan 1A: Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the React + TypeScript frontend-v2 app, build the typed API client, Zustand data store, startup sequence, auto-refresh, theme system, shared components, and app shell. Prove the data flow end-to-end with a TSBStatus test panel.

**Architecture:** Vite dev server proxies `/api` to the existing FastAPI backend on port 8000. Zustand store is the single source of truth — panels read from store via selectors, never fetch directly. Startup polls `/warmup-status`, then fetches core data in parallel, populates store, and renders the app shell.

**Tech Stack:** React 18, TypeScript 5, Vite 6, Zustand 5, D3.js v7, Vitest + React Testing Library, CSS Modules + CSS custom properties

**Spec:** `docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md`

**Backend:** All endpoints already implemented. One small backend change: add `data_version` to `/health`.

**Existing frontend (v1):** `frontend/` — plain JS, no bundler. Will remain working. v2 is a parallel app in `frontend-v2/`.

**Python env:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python run_api.py`

**Node version:** 20+ (check with `node -v`)

**Test command (frontend):** `cd frontend-v2 && npx vitest run`

**Test command (backend):** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/ -v`

**Exit criteria:** App loads in browser at `http://localhost:5173`, fetches all core data from FastAPI, populates Zustand store, shows branded loading screen during warmup, renders app shell with header + tab bar + "Synced X ago" indicator. TSBStatus panel renders from the store to prove the data flow works.

---

## File Structure

```
frontend-v2/                          # NEW directory — entire tree is new
  package.json
  tsconfig.json
  tsconfig.node.json
  vite.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    App.module.css
    api/
      client.ts                       # Typed fetch wrapper + all endpoint functions
      types.ts                        # All response interfaces from Appendix A
      client.test.ts                  # Vitest tests for API client
    store/
      data-store.ts                   # Zustand store — full shape from spec
      data-store.test.ts              # Vitest tests for store actions
    shared/
      tokens.ts                       # Chart design tokens — colors, TSB mapping, typography
      PanelSkeleton.tsx               # Loading placeholder
      PanelSkeleton.module.css
      PanelError.tsx                  # Error state with retry
      PanelError.module.css
      PanelEmpty.tsx                  # Empty data state
      PanelEmpty.module.css
      Metric.tsx                      # Compact metric display
      MetricBig.tsx                   # Hero metric display
      Metric.module.css
      DataTable.tsx                   # Sortable data table
      DataTable.module.css
      ChartContainer.tsx              # D3 wrapper with resize observer
      ChartContainer.module.css
    panels/
      status/
        TSBStatus.tsx                 # Proof-of-concept panel
        TSBStatus.module.css
        TSBStatus.test.tsx            # Vitest + RTL test
    theme/
      theme.ts                       # Theme toggle logic + OS preference
      theme.module.css                # CSS custom properties for dark/light
      variables.css                   # Global CSS variables
    startup/
      WarmupScreen.tsx                # Branded loading screen
      WarmupScreen.module.css
      useStartup.ts                   # Startup sequence hook
    header/
      Header.tsx                      # App header with sync indicator
      Header.module.css
      SyncIndicator.tsx               # "Synced X ago" + status dot
      SyncIndicator.module.css
    layout/
      TabBar.tsx                      # Tab bar placeholder
      TabBar.module.css
    footer/
      Footer.tsx                      # Connection status footer
      Footer.module.css
  vitest.config.ts
  vitest.setup.ts

wko5/api/routes.py                    # MODIFY — add data_version to /health
tests/test_api_health.py              # NEW — pytest for data_version field
```

---

## Task 1: Vite + React + TypeScript scaffold

### Step 1: Create project with Vite

- [ ] **1.1: Scaffold Vite project**

```bash
cd /Users/jshin/Documents/wko5-experiments
npm create vite@latest frontend-v2 -- --template react-ts
```

Expected output: scaffolded project in `frontend-v2/`.

- [ ] **1.2: Install dependencies**

```bash
cd /Users/jshin/Documents/wko5-experiments/frontend-v2
npm install
npm install zustand d3
npm install -D @types/d3 @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom vitest
```

- [ ] **1.3: Verify dev server starts**

```bash
cd /Users/jshin/Documents/wko5-experiments/frontend-v2
npx vite --port 5173 &
sleep 3
curl -s http://localhost:5173 | head -5
kill %1
```

Expected: HTML response from Vite dev server.

- [ ] **1.4: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/
git commit -m "feat(v2): scaffold Vite + React + TypeScript project"
```

---

## Task 2: Vite config with FastAPI proxy

### Step 1: Write vite.config.ts

- [ ] **2.1: Replace vite.config.ts**

Write to `frontend-v2/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

- [ ] **2.2: Write vitest.config.ts**

Write to `frontend-v2/vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    css: {
      modules: {
        classNameStrategy: 'non-scoped',
      },
    },
  },
})
```

- [ ] **2.3: Write vitest.setup.ts**

Write to `frontend-v2/vitest.setup.ts`:

```typescript
import '@testing-library/jest-dom/vitest'
```

- [ ] **2.4: Update tsconfig.json for strict mode**

Write to `frontend-v2/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "types": ["vitest/globals"]
  },
  "include": ["src", "vitest.setup.ts"]
}
```

- [ ] **2.5: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/vite.config.ts frontend-v2/vitest.config.ts frontend-v2/vitest.setup.ts frontend-v2/tsconfig.json
git commit -m "feat(v2): Vite proxy config + Vitest setup with jsdom"
```

---

## Task 3: API types — every endpoint typed

### Step 1: Write all response interfaces

- [ ] **3.1: Create src/api/types.ts**

Write to `frontend-v2/src/api/types.ts`:

```typescript
// ─── Shared / utility ─────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: string,
  ) {
    super(`API ${status}: ${body}`)
    this.name = 'ApiError'
  }
}

// ─── /health ──────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  cache_warm: boolean
  warmup_errors: Record<string, string> | null
  data_version: number
}

// ─── /warmup-status ───────────────────────────────────────────────

export interface WarmupStatusResponse {
  running: boolean
  done: boolean
  results: Record<string, string>
  errors: Record<string, string>
}

// ─── /fitness ─────────────────────────────────────────────────────

export interface FitnessData {
  CTL: number
  ATL: number
  TSB: number
  date: string
}

// ─── /pmc ─────────────────────────────────────────────────────────

export interface PMCRow {
  date: string
  TSS: number
  CTL: number
  ATL: number
  TSB: number
}

// ─── /clinical-flags ──────────────────────────────────────────────

export interface ClinicalFlag {
  name: string
  status: 'ok' | 'warning' | 'danger'
  value: string | number
  threshold: string
  detail: string
}

export interface ClinicalFlagsResponse {
  flags: ClinicalFlag[]
  alert_level: string
  error?: string
}

// ─── /profile ─────────────────────────────────────────────────────

export interface PowerProfileValues {
  watts: Record<string, number>
  wkg: Record<string, number>
}

export interface CogganRanking {
  [duration: string]: string
}

export interface StrengthsLimiters {
  strengths: string[]
  limiters: string[]
}

export interface ProfileResponse {
  profile: PowerProfileValues
  ranking: CogganRanking
  strengths_limiters: StrengthsLimiters
  error?: string
}

// ─── /config ──────────────────────────────────────────────────────

export interface AthleteConfig {
  id: number
  name: string
  sex: string
  weight_kg: number
  max_hr: number
  lthr: number | null
  ftp_manual: number
  bike_weight_kg: number
  cda: number
  crr: number
  pd_pmax_low: number
  pd_pmax_high: number
  pd_mftp_low: number
  pd_mftp_high: number
  pd_frc_low: number
  pd_frc_high: number
  pd_tau_low: number
  pd_tau_high: number
  pd_t0_low: number
  pd_t0_high: number
  spike_threshold_watts: number
  resting_hr_baseline: number | null
  hrv_baseline: number | null
  resting_hr_alert_delta: number
  ctl_ramp_rate_yellow: number
  ctl_ramp_rate_red: number
  tsb_floor_alert: number
  collapse_kj_threshold: number | null
  intensity_ceiling_if: number
  fueling_rate_g_hr: number
  energy_deficit_alert_kcal: number
  ctl_time_constant: number
  atl_time_constant: number
}

// ─── /model ───────────────────────────────────────────────────────

export interface ModelResult {
  Pmax: number
  FRC: number
  mFTP: number
  TTE: number
  mVO2max_L_min: number
  mVO2max_ml_min_kg: number
  tau: number
  t0: number
  sub_cp_note: string
  mmp: [number, number][]  // [seconds, power]
  error?: string
}

// ─── /activities ──────────────────────────────────────────────────

export interface Activity {
  id: number
  filename: string
  sport: string
  sub_sport: string
  start_time: string
  total_elapsed_time: number
  total_timer_time: number
  total_distance: number
  avg_power: number | null
  max_power: number | null
  normalized_power: number | null
  intensity_factor: number | null
  training_stress_score: number | null
  avg_heart_rate: number | null
  max_heart_rate: number | null
  avg_cadence: number | null
  avg_speed: number | null
  total_ascent: number | null
  total_calories: number | null
}

export interface ActivitiesResponse {
  activities: Activity[]
  total: number
  limit: number
  offset: number
}

// ─── /rolling-ftp ─────────────────────────────────────────────────

export interface RollingFtpRow {
  date: string
  mFTP: number
  Pmax: number
  FRC: number
  TTE_min: number
}

// ─── /ftp-growth ──────────────────────────────────────────────────

export interface FtpGrowthResponse {
  slope: number
  intercept: number
  r_squared: number
  improvement_rate_w_per_year: number
  plateau_detected: boolean
  growth_phase: string
  training_age_weeks: number
  data_points: { date: string; mFTP: number }[]
  error?: string
}

// ─── /rolling-pd-profile ──────────────────────────────────────────

export interface RollingPdRow {
  date: string
  mFTP: number
  Pmax: number
  FRC: number
  TTE_min: number
}

export interface RollingPdResponse {
  data: RollingPdRow[]
}

// ─── /if-distribution ─────────────────────────────────────────────

export interface IfDistributionResponse {
  histogram: Record<string, number>
  floor: number
  ceiling: number
  spread: number
  compressed: boolean
  rides_analyzed: number
}

// ─── /fresh-baseline ──────────────────────────────────────────────

export interface FreshBaselineEntry {
  exists: boolean
  value: number | null
  date: string | null
  staleness_days: number | null
}

export type FreshBaselineResponse = Record<string, FreshBaselineEntry>

// ─── /short-power-consistency ─────────────────────────────────────

export interface ShortPowerResponse {
  peak: number
  typical: number
  ratio: number
  diagnosis: string
  efforts_analyzed: number
  message: string
}

// ─── /performance-trend ───────────────────────────────────────────

export interface PerformanceTrendRow {
  date: string
  metric: string
  value: number
}

export interface PerformanceTrendResponse {
  data: PerformanceTrendRow[]
}

// ─── /detect-phase ────────────────────────────────────────────────

export interface DetectedPhase {
  phase: string
  confidence: number
  reasoning: string
}

// ─── /feasibility ─────────────────────────────────────────────────

export interface FeasibilityResponse {
  current_ctl: number
  target_ctl: number
  ctl_gap: number
  weeks_available: number
  required_ramp_rate: number
  max_sustainable_ramp: number
  feasible: boolean
  margin_weeks: number
}

// ─── /training-blocks ─────────────────────────────────────────────

export interface TrainingBlock {
  start: string
  end: string
  volume: number
  intensity: number
  power: number
  tp: number
}

// ─── /weekly-summary ──────────────────────────────────────────────

export interface WeeklySummary {
  week: string
  hours: number
  km: number
  tss: number
  ride_count: number
  avg_if: number
  elevation: number
  avg_power: number
}

// ─── /posterior-summary ───────────────────────────────────────────

export interface PosteriorParam {
  median: number
  ci_95: [number, number]
  std: number
  ci_width: number
}

export interface PosteriorSummaryResponse {
  pd_model: Record<string, PosteriorParam>
  durability: Record<string, PosteriorParam>
}

// ─── /ride/{id} ───────────────────────────────────────────────────

export interface RideSummary {
  id: number
  filename: string
  sport: string
  start_time: string
  total_elapsed_time: number
  total_timer_time: number
  total_distance: number
  avg_power: number | null
  max_power: number | null
  normalized_power: number | null
  intensity_factor: number | null
  training_stress_score: number | null
  avg_heart_rate: number | null
  max_heart_rate: number | null
}

export interface RideRecord {
  elapsed_seconds: number
  power: number | null
  heart_rate: number | null
  cadence: number | null
  speed: number | null
  altitude: number | null
}

export interface RideInterval {
  start: number
  end: number
  avg_power: number
  max_power: number
  avg_hr: number | null
  duration: number
}

export interface RideDetail {
  summary: RideSummary
  records: RideRecord[]
  intervals: RideInterval[]
  error?: string
}

// ─── /routes ──────────────────────────────────────────────────────

export interface RouteListItem {
  id: number
  name: string
  distance_km: number
  elevation_m: number
  source: string
}

export interface RoutePoint {
  lat: number
  lon: number
  elevation: number
  km: number
}

export interface RouteDetail {
  id: number
  name: string
  distance_km: number
  elevation_m: number
  source: string
  history: Record<string, unknown>[]
  plans: Record<string, unknown>[]
  points: RoutePoint[]
}

// ─── /glycogen-budget (POST) ──────────────────────────────────────

export interface GlycogenBudgetRequest {
  ride_kj: number
  ride_duration_h: number
  on_bike_carbs_g: number
  post_ride_delay_h: number
  daily_carb_target_g_kg: number
  weight_kg: number
}

export interface GlycogenBudgetResponse {
  timeline: { hour: number; glycogen_g: number }[]
  bonk_risk: boolean
  nadir_g: number
  nadir_hour: number
  recovery_hours: number
}

// ─── Annotations (MCP) ───────────────────────────────────────────

export interface Annotation {
  id: string
  source: 'claude' | 'user'
  type: 'region' | 'line' | 'point'
  x?: [string, string] | string
  y?: number
  label: string
  color: string
  timestamp: string
}
```

- [ ] **3.2: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/api/types.ts
git commit -m "feat(v2): typed API response interfaces for all 34 endpoints"
```

---

## Task 4: Typed API client

### Step 1: Write the client

- [ ] **4.1: Create src/api/client.ts**

Write to `frontend-v2/src/api/client.ts`:

```typescript
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

/** Resolve bearer token from meta tag, then localStorage. */
function resolveToken(): string | null {
  // Try <meta name="wko5-token" content="...">
  const meta = document.querySelector<HTMLMetaElement>('meta[name="wko5-token"]')
  if (meta?.content) return meta.content

  // Try URL param (legacy v1 compat) — save and strip
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

  return localStorage.getItem('wko5_token')
}

let _token: string | null = null

/** Get the current auth token, resolving lazily on first call. */
export function getToken(): string | null {
  if (_token === null) {
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
```

- [ ] **4.2: Write API client tests**

Write to `frontend-v2/src/api/client.test.ts`:

```typescript
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
    await expect(getFitness()).rejects.toThrow(ApiError) // coverage: re-mock needed
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
```

- [ ] **4.3: Run tests**

```bash
cd /Users/jshin/Documents/wko5-experiments/frontend-v2
npx vitest run src/api/client.test.ts
```

Expected: 3-4 tests passing.

- [ ] **4.4: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/api/
git commit -m "feat(v2): typed API client with fetchApi wrapper + auth + tests"
```

---

## Task 5: Chart design tokens

### Step 1: Write design tokens

- [ ] **5.1: Create src/shared/tokens.ts**

Write to `frontend-v2/src/shared/tokens.ts`:

```typescript
/** Chart design tokens — colors, TSB mapping, axis typography, tooltip template. */

// ─── Semantic chart palette ───────────────────────────────────────

export const COLORS = {
  ctl: '#4dabf7',       // blue — fitness / CTL line
  atl: '#ff6b6b',       // red — fatigue / ATL line
  tsb: '#51cf66',       // green — form / TSB line
  power: '#ffd43b',     // yellow — power data
  hr: '#ff6b6b',        // red — heart rate
  cadence: '#b197fc',   // purple — cadence
  speed: '#38d9a9',     // teal — speed
  elevation: '#868e96', // gray — elevation
  primary: '#4dabf7',   // blue — primary accent
  danger: '#ff6b6b',    // red — danger state
  warning: '#ffd43b',   // amber — warning state
  success: '#51cf66',   // green — ok/success state
  muted: '#868e96',     // gray — secondary text / gridlines
} as const

// ─── TSB color mapping ───────────────────────────────────────────

export function tsbColor(tsb: number): string {
  if (tsb > 5) return COLORS.success    // fresh / green
  if (tsb >= -10) return COLORS.warning // neutral / amber
  return COLORS.danger                  // fatigued / red
}

export function tsbLabel(tsb: number): string {
  if (tsb > 25) return 'Very Fresh'
  if (tsb > 5) return 'Fresh'
  if (tsb >= -10) return 'Neutral'
  if (tsb >= -25) return 'Tired'
  return 'Very Tired'
}

// ─── Alert severity colors ───────────────────────────────────────

export const SEVERITY_COLORS = {
  danger: '#ff6b6b',
  warning: '#ffd43b',
  ok: '#51cf66',
  info: '#4dabf7',
} as const

export type Severity = keyof typeof SEVERITY_COLORS

// ─── Axis typography ─────────────────────────────────────────────

export const AXIS = {
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontSize: 11,
  fontColor: '#868e96',
  gridColor: '#30363d',
  gridOpacity: 0.4,
  tickPadding: 8,
} as const

// ─── Tooltip ─────────────────────────────────────────────────────

export const TOOLTIP = {
  background: '#1c2128',
  border: '#30363d',
  textColor: '#e6edf3',
  fontSize: 12,
  padding: 8,
  borderRadius: 6,
  maxWidth: 240,
} as const

// ─── Annotation visual style ─────────────────────────────────────

export const ANNOTATION = {
  regionOpacity: 0.15,
  lineDash: '6,4',
  lineWidth: 2,
  pointRadius: 5,
  badgeFontSize: 10,
  maxLabelLength: 200,
} as const

// ─── Breakpoints ─────────────────────────────────────────────────

export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const
```

- [ ] **5.2: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/shared/tokens.ts
git commit -m "feat(v2): chart design tokens — colors, TSB mapping, axis typography"
```

---

## Task 6: Zustand data store

### Step 1: Write the full store

- [ ] **6.1: Create src/store/data-store.ts**

Write to `frontend-v2/src/store/data-store.ts`:

```typescript
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
```

- [ ] **6.2: Write store tests**

Write to `frontend-v2/src/store/data-store.test.ts`:

```typescript
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
```

- [ ] **6.3: Run store tests**

```bash
cd /Users/jshin/Documents/wko5-experiments/frontend-v2
npx vitest run src/store/data-store.test.ts
```

Expected: 8 tests passing.

- [ ] **6.4: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/store/
git commit -m "feat(v2): Zustand data store — full shape, fetchCore, tracked loading, annotations"
```

---

## Task 7: Theme system

### Step 1: CSS variables + toggle logic

- [ ] **7.1: Create src/theme/variables.css**

Write to `frontend-v2/src/theme/variables.css`:

```css
/* ─── Dark theme (default) ──────────────────────────────────────── */

:root,
[data-theme='dark'] {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;
  --bg-panel: #161b22;
  --bg-panel-header: #21262d;
  --bg-input: #0d1117;
  --bg-hover: #30363d;

  --border-primary: #30363d;
  --border-secondary: #21262d;

  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --text-tertiary: #6e7681;

  --accent-blue: #4dabf7;
  --accent-green: #51cf66;
  --accent-red: #ff6b6b;
  --accent-amber: #ffd43b;
  --accent-purple: #b197fc;
  --accent-teal: #38d9a9;

  --danger: #ff6b6b;
  --warning: #ffd43b;
  --success: #51cf66;
  --info: #4dabf7;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);

  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;

  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', 'Fira Mono', Menlo, Consolas, monospace;

  --font-size-xs: 11px;
  --font-size-sm: 12px;
  --font-size-md: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 20px;
  --font-size-2xl: 28px;
  --font-size-hero: 48px;

  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
}

/* ─── Light theme ────────────────────────────────────────────────── */

[data-theme='light'] {
  --bg-primary: #ffffff;
  --bg-secondary: #f6f8fa;
  --bg-tertiary: #eaeef2;
  --bg-panel: #ffffff;
  --bg-panel-header: #f6f8fa;
  --bg-input: #ffffff;
  --bg-hover: #eaeef2;

  --border-primary: #d0d7de;
  --border-secondary: #eaeef2;

  --text-primary: #1f2328;
  --text-secondary: #656d76;
  --text-tertiary: #8b949e;

  --accent-blue: #0969da;
  --accent-green: #1a7f37;
  --accent-red: #cf222e;
  --accent-amber: #bf8700;
  --accent-purple: #8250df;
  --accent-teal: #0e8a6d;

  --danger: #cf222e;
  --warning: #bf8700;
  --success: #1a7f37;
  --info: #0969da;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* ─── Base resets ────────────────────────────────────────────────── */

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-family: var(--font-sans);
  font-size: var(--font-size-md);
  color: var(--text-primary);
  background-color: var(--bg-primary);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  min-height: 100vh;
}

a {
  color: var(--accent-blue);
  text-decoration: none;
}

button {
  cursor: pointer;
  font-family: inherit;
}
```

- [ ] **7.2: Create src/theme/theme.ts**

Write to `frontend-v2/src/theme/theme.ts`:

```typescript
export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'wko5-theme'

/** Detect OS color scheme preference. */
function getOsTheme(): Theme {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

/** Read persisted theme, falling back to OS preference. */
export function getStoredTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'dark' || stored === 'light') return stored
  } catch {
    // localStorage unavailable
  }
  return getOsTheme()
}

/** Apply theme to the document root. */
export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // localStorage unavailable
  }
}

/** Toggle between dark and light. Returns the new theme. */
export function toggleTheme(): Theme {
  const current = document.documentElement.getAttribute('data-theme') as Theme
  const next: Theme = current === 'dark' ? 'light' : 'dark'
  applyTheme(next)
  return next
}

/** Initialize theme on app start. */
export function initTheme(): Theme {
  const theme = getStoredTheme()
  applyTheme(theme)

  // Listen for OS preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    // Only follow OS if user hasn't manually set a preference
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) {
      applyTheme(e.matches ? 'dark' : 'light')
    }
  })

  return theme
}
```

- [ ] **7.3: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/theme/
git commit -m "feat(v2): dark/light theme system — CSS variables + OS preference detection"
```

---

## Task 8: Shared components

### Step 1: PanelSkeleton, PanelError, PanelEmpty

- [ ] **8.1: Create PanelSkeleton**

Write to `frontend-v2/src/shared/PanelSkeleton.tsx`:

```tsx
import styles from './PanelSkeleton.module.css'

export function PanelSkeleton() {
  return (
    <div className={styles.skeleton}>
      <div className={styles.bar} style={{ width: '60%' }} />
      <div className={styles.bar} style={{ width: '80%' }} />
      <div className={styles.bar} style={{ width: '45%' }} />
    </div>
  )
}
```

Write to `frontend-v2/src/shared/PanelSkeleton.module.css`:

```css
.skeleton {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar {
  height: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
  }
}
```

- [ ] **8.2: Create PanelError**

Write to `frontend-v2/src/shared/PanelError.tsx`:

```tsx
import styles from './PanelError.module.css'

interface PanelErrorProps {
  message: string
  onRetry?: () => void
}

export function PanelError({ message, onRetry }: PanelErrorProps) {
  return (
    <div className={styles.error}>
      <span className={styles.icon}>!</span>
      <p className={styles.message}>{message}</p>
      {onRetry && (
        <button className={styles.retry} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
```

Write to `frontend-v2/src/shared/PanelError.module.css`:

```css
.error {
  padding: 16px;
  text-align: center;
  border: 1px solid var(--danger);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--danger);
  color: white;
  font-weight: 700;
  font-size: var(--font-size-md);
  margin-bottom: 8px;
}

.message {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  margin-bottom: 12px;
}

.retry {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  padding: 6px 16px;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  transition: background var(--transition-fast);
}

.retry:hover {
  background: var(--bg-hover);
}
```

- [ ] **8.3: Create PanelEmpty**

Write to `frontend-v2/src/shared/PanelEmpty.tsx`:

```tsx
import styles from './PanelEmpty.module.css'

interface PanelEmptyProps {
  message?: string
}

export function PanelEmpty({ message = 'No data available' }: PanelEmptyProps) {
  return (
    <div className={styles.empty}>
      <p>{message}</p>
    </div>
  )
}
```

Write to `frontend-v2/src/shared/PanelEmpty.module.css`:

```css
.empty {
  padding: 24px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}
```

- [ ] **8.4: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/shared/PanelSkeleton.tsx frontend-v2/src/shared/PanelSkeleton.module.css \
  frontend-v2/src/shared/PanelError.tsx frontend-v2/src/shared/PanelError.module.css \
  frontend-v2/src/shared/PanelEmpty.tsx frontend-v2/src/shared/PanelEmpty.module.css
git commit -m "feat(v2): shared panel states — PanelSkeleton, PanelError, PanelEmpty"
```

### Step 2: Metric + MetricBig

- [ ] **8.5: Create Metric + MetricBig**

Write to `frontend-v2/src/shared/Metric.tsx`:

```tsx
import styles from './Metric.module.css'

interface MetricProps {
  value: number | string | null | undefined
  label: string
  unit?: string
  color?: string
  decimals?: number
}

export function Metric({ value, label, unit, color, decimals = 0 }: MetricProps) {
  const display =
    value == null
      ? '--'
      : typeof value === 'number'
        ? value.toFixed(decimals)
        : value

  return (
    <div className={styles.metric}>
      <span className={styles.value} style={color ? { color } : undefined}>
        {display}
        {unit && <span className={styles.unit}>{unit}</span>}
      </span>
      <span className={styles.label}>{label}</span>
    </div>
  )
}
```

Write to `frontend-v2/src/shared/MetricBig.tsx`:

```tsx
import styles from './Metric.module.css'

interface MetricBigProps {
  value: number | string | null | undefined
  label: string
  unit?: string
  color?: string
  decimals?: number
}

export function MetricBig({ value, label, unit, color, decimals = 0 }: MetricBigProps) {
  const display =
    value == null
      ? '--'
      : typeof value === 'number'
        ? value.toFixed(decimals)
        : value

  return (
    <div className={styles.metricBig}>
      <span className={styles.bigValue} style={color ? { color } : undefined}>
        {display}
        {unit && <span className={styles.bigUnit}>{unit}</span>}
      </span>
      <span className={styles.bigLabel}>{label}</span>
    </div>
  )
}
```

Write to `frontend-v2/src/shared/Metric.module.css`:

```css
/* ─── Compact metric ─────────────────────────────────────────────── */

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
}

.value {
  font-size: var(--font-size-xl);
  font-weight: 600;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.unit {
  font-size: var(--font-size-xs);
  font-weight: 400;
  color: var(--text-tertiary);
  margin-left: 2px;
}

.label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ─── Hero metric ────────────────────────────────────────────────── */

.metricBig {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
}

.bigValue {
  font-size: var(--font-size-hero);
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.bigUnit {
  font-size: var(--font-size-lg);
  font-weight: 400;
  color: var(--text-tertiary);
  margin-left: 4px;
}

.bigLabel {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

- [ ] **8.6: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/shared/Metric.tsx frontend-v2/src/shared/MetricBig.tsx frontend-v2/src/shared/Metric.module.css
git commit -m "feat(v2): Metric + MetricBig components with tabular-nums"
```

### Step 3: DataTable

- [ ] **8.7: Create DataTable**

Write to `frontend-v2/src/shared/DataTable.tsx`:

```tsx
import { useState, useMemo } from 'react'
import styles from './DataTable.module.css'

interface Column<T> {
  key: string
  label: string
  render?: (row: T) => React.ReactNode
  sortable?: boolean
  align?: 'left' | 'center' | 'right'
  width?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyField: string
  maxRows?: number
  onRowClick?: (row: T) => void
  emptyMessage?: string
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  keyField,
  maxRows,
  onRowClick,
  emptyMessage = 'No data',
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const sorted = useMemo(() => {
    if (!sortKey) return data
    return [...data].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [data, sortKey, sortDir])

  const displayed = maxRows ? sorted.slice(0, maxRows) : sorted

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  if (data.length === 0) {
    return <div className={styles.empty}>{emptyMessage}</div>
  }

  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={col.sortable !== false ? styles.sortable : undefined}
                style={{ textAlign: col.align ?? 'left', width: col.width }}
                onClick={() => col.sortable !== false && handleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key && (
                  <span className={styles.arrow}>{sortDir === 'asc' ? ' \u25B2' : ' \u25BC'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayed.map((row) => (
            <tr
              key={String(row[keyField])}
              className={onRowClick ? styles.clickable : undefined}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => (
                <td key={col.key} style={{ textAlign: col.align ?? 'left' }}>
                  {col.render ? col.render(row) : String(row[col.key] ?? '--')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

Write to `frontend-v2/src/shared/DataTable.module.css`:

```css
.wrapper {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
}

.table th {
  padding: 8px 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-size: var(--font-size-xs);
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-primary);
  white-space: nowrap;
  user-select: none;
}

.table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-secondary);
  color: var(--text-primary);
}

.sortable {
  cursor: pointer;
}

.sortable:hover {
  color: var(--text-primary);
}

.arrow {
  font-size: 9px;
}

.clickable {
  cursor: pointer;
}

.clickable:hover td {
  background: var(--bg-hover);
}

.empty {
  padding: 24px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}
```

- [ ] **8.8: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/shared/DataTable.tsx frontend-v2/src/shared/DataTable.module.css
git commit -m "feat(v2): sortable DataTable component"
```

### Step 4: ChartContainer (D3 wrapper)

- [ ] **8.9: Create ChartContainer**

Write to `frontend-v2/src/shared/ChartContainer.tsx`:

```tsx
import { useRef, useEffect, useState, useCallback } from 'react'
import styles from './ChartContainer.module.css'

interface ChartContainerProps {
  /** Render function called when container resizes. Receives SVG element, width, height. */
  renderChart: (svg: SVGSVGElement, width: number, height: number) => void | (() => void)
  /** Minimum height in pixels. Default 200. */
  minHeight?: number
  /** Aspect ratio (width/height). If set, height is computed from width. */
  aspectRatio?: number
  className?: string
}

export function ChartContainer({
  renderChart,
  minHeight = 200,
  aspectRatio,
  className,
}: ChartContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null)

  const measure = useCallback(() => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const width = Math.floor(rect.width)
    const height = aspectRatio
      ? Math.max(Math.floor(width / aspectRatio), minHeight)
      : Math.max(Math.floor(rect.height), minHeight)
    setDimensions((prev) => {
      if (prev?.width === width && prev?.height === height) return prev
      return { width, height }
    })
  }, [aspectRatio, minHeight])

  // ResizeObserver for responsive charts
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const observer = new ResizeObserver(() => {
      measure()
    })
    observer.observe(el)
    measure() // Initial measurement

    return () => observer.disconnect()
  }, [measure])

  // Render chart when dimensions change
  useEffect(() => {
    if (!dimensions || !svgRef.current) return
    const cleanup = renderChart(svgRef.current, dimensions.width, dimensions.height)
    return () => {
      if (typeof cleanup === 'function') cleanup()
    }
  }, [dimensions, renderChart])

  return (
    <div
      ref={containerRef}
      className={`${styles.container} ${className ?? ''}`}
      style={{ minHeight }}
    >
      {dimensions && (
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className={styles.svg}
        />
      )}
    </div>
  )
}
```

Write to `frontend-v2/src/shared/ChartContainer.module.css`:

```css
.container {
  width: 100%;
  position: relative;
}

.svg {
  display: block;
}
```

- [ ] **8.10: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/shared/ChartContainer.tsx frontend-v2/src/shared/ChartContainer.module.css
git commit -m "feat(v2): ChartContainer — D3 wrapper with ResizeObserver"
```

---

## Task 9: Startup sequence — warmup screen + useStartup hook

### Step 1: Warmup screen

- [ ] **9.1: Create WarmupScreen**

Write to `frontend-v2/src/startup/WarmupScreen.tsx`:

```tsx
import { type WarmupStatusResponse } from '../api/types'
import styles from './WarmupScreen.module.css'

interface WarmupScreenProps {
  status: WarmupStatusResponse | null
  error: string | null
}

export function WarmupScreen({ status, error }: WarmupScreenProps) {
  const completedCount = status ? Object.keys(status.results).length : 0
  const errorCount = status ? Object.keys(status.errors).length : 0
  const totalTasks = 8 // fitness, pmc, model_90, profile_90, rolling_ftp, clinical, ftp_growth, rolling_pd
  const progress = status ? Math.round(((completedCount + errorCount) / totalTasks) * 100) : 0

  return (
    <div className={styles.screen}>
      <div className={styles.content}>
        <h1 className={styles.title}>WKO5 Analyzer</h1>
        <p className={styles.subtitle}>Cycling Performance Analytics</p>

        {error ? (
          <div className={styles.error}>
            <p>Unable to connect to backend</p>
            <p className={styles.errorDetail}>{error}</p>
            <p className={styles.hint}>
              Start the API server: <code>python run_api.py</code>
            </p>
          </div>
        ) : (
          <>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className={styles.status}>
              {!status && 'Connecting...'}
              {status?.running && `Pre-computing models... ${completedCount}/${totalTasks}`}
              {status?.done && 'Loading dashboard...'}
            </p>
            {errorCount > 0 && (
              <p className={styles.warnings}>
                {errorCount} warmup task{errorCount > 1 ? 's' : ''} failed (non-critical)
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
```

Write to `frontend-v2/src/startup/WarmupScreen.module.css`:

```css
.screen {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-primary);
}

.content {
  text-align: center;
  max-width: 400px;
  padding: 24px;
}

.title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.subtitle {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.progressBar {
  width: 100%;
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progressFill {
  height: 100%;
  background: var(--accent-blue);
  border-radius: 2px;
  transition: width 300ms ease;
}

.status {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.warnings {
  font-size: var(--font-size-xs);
  color: var(--warning);
  margin-top: 8px;
}

.error {
  color: var(--danger);
  margin-top: 16px;
}

.errorDetail {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-top: 4px;
}

.hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-top: 16px;
}

.hint code {
  font-family: var(--font-mono);
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}
```

- [ ] **9.2: Create useStartup hook**

Write to `frontend-v2/src/startup/useStartup.ts`:

```typescript
import { useState, useEffect, useRef } from 'react'
import { type WarmupStatusResponse } from '../api/types'
import { getWarmupStatus } from '../api/client'
import { useDataStore } from '../store/data-store'

export type StartupPhase = 'warming' | 'loading' | 'ready' | 'error'

interface StartupState {
  phase: StartupPhase
  warmupStatus: WarmupStatusResponse | null
  error: string | null
}

const POLL_INTERVAL_MS = 1000

export function useStartup(): StartupState {
  const [phase, setPhase] = useState<StartupPhase>('warming')
  const [warmupStatus, setWarmupStatus] = useState<WarmupStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fetchCore = useDataStore((s) => s.fetchCore)
  const fetchSecondary = useDataStore((s) => s.fetchSecondary)
  const checkForUpdates = useDataStore((s) => s.checkForUpdates)
  const pollingRef = useRef(false)

  useEffect(() => {
    if (pollingRef.current) return
    pollingRef.current = true

    let cancelled = false
    let timeoutId: ReturnType<typeof setTimeout>

    async function pollWarmup() {
      try {
        const status = await getWarmupStatus()
        if (cancelled) return
        setWarmupStatus(status)

        if (status.done) {
          // Warmup complete — fetch core data
          setPhase('loading')
          await fetchCore()
          if (cancelled) return

          // Record initial data version
          await checkForUpdates()

          setPhase('ready')

          // Kick off secondary data in background (non-blocking)
          fetchSecondary()
          return
        }

        // Still warming — poll again
        timeoutId = setTimeout(pollWarmup, POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Connection failed')
        setPhase('error')

        // Retry after a longer delay on error
        timeoutId = setTimeout(pollWarmup, POLL_INTERVAL_MS * 3)
      }
    }

    pollWarmup()

    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [fetchCore, fetchSecondary, checkForUpdates])

  return { phase, warmupStatus, error }
}
```

- [ ] **9.3: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/startup/
git commit -m "feat(v2): startup sequence — WarmupScreen + useStartup hook polling /warmup-status"
```

---

## Task 10: Auto-refresh — poll /health, window focus check

### Step 1: Auto-refresh hook

- [ ] **10.1: Create src/startup/useAutoRefresh.ts**

Write to `frontend-v2/src/startup/useAutoRefresh.ts`:

```typescript
import { useEffect, useRef } from 'react'
import { useDataStore } from '../store/data-store'

/** Interval between /health polls: 3.5 hours in ms. */
const POLL_INTERVAL_MS = 3.5 * 60 * 60 * 1000

/** Maximum staleness before refresh on window focus: 4 hours. */
const STALE_THRESHOLD_MS = 4 * 60 * 60 * 1000

/**
 * Auto-refresh hook. Polls /health periodically, checks data_version,
 * and refreshes on window focus if stale.
 *
 * Only activate after startup is complete (phase === 'ready').
 */
export function useAutoRefresh(active: boolean) {
  const checkForUpdates = useDataStore((s) => s.checkForUpdates)
  const refresh = useDataStore((s) => s.refresh)
  const lastRefresh = useDataStore((s) => s.lastRefresh)
  const intervalRef = useRef<ReturnType<typeof setInterval>>()

  // Periodic /health poll
  useEffect(() => {
    if (!active) return
    intervalRef.current = setInterval(async () => {
      const changed = await checkForUpdates()
      if (changed) {
        await refresh()
      }
    }, POLL_INTERVAL_MS)

    return () => clearInterval(intervalRef.current)
  }, [active, checkForUpdates, refresh])

  // Window focus refresh
  useEffect(() => {
    if (!active) return

    function handleFocus() {
      if (!lastRefresh) return
      const age = Date.now() - new Date(lastRefresh).getTime()
      if (age > STALE_THRESHOLD_MS) {
        refresh()
      }
    }

    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [active, lastRefresh, refresh])
}
```

- [ ] **10.2: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/startup/useAutoRefresh.ts
git commit -m "feat(v2): auto-refresh — poll /health every 3.5h + window focus check"
```

---

## Task 11: Header with sync indicator

### Step 1: SyncIndicator

- [ ] **11.1: Create SyncIndicator**

Write to `frontend-v2/src/header/SyncIndicator.tsx`:

```tsx
import { useDataStore } from '../store/data-store'
import styles from './SyncIndicator.module.css'

function formatTimeAgo(isoDate: string): string {
  const ms = Date.now() - new Date(isoDate).getTime()
  const minutes = Math.floor(ms / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function staleness(isoDate: string): 'fresh' | 'stale' | 'old' {
  const ms = Date.now() - new Date(isoDate).getTime()
  const hours = ms / (1000 * 60 * 60)
  if (hours < 4) return 'fresh'
  if (hours < 24) return 'stale'
  return 'old'
}

export function SyncIndicator() {
  const lastRefresh = useDataStore((s) => s.lastRefresh)
  const loading = useDataStore((s) => s.loading)
  const refresh = useDataStore((s) => s.refresh)
  const isRefreshing = loading.size > 0

  if (!lastRefresh) return null

  const age = staleness(lastRefresh)
  const label = `Synced ${formatTimeAgo(lastRefresh)}`

  return (
    <div className={styles.indicator}>
      <span className={`${styles.dot} ${styles[age]}`} />
      <span className={`${styles.label} ${styles[age]}`}>{label}</span>
      <button
        className={styles.refreshBtn}
        onClick={() => refresh()}
        disabled={isRefreshing}
        title="Refresh data"
      >
        {isRefreshing ? '\u21BB' : '\u21BB'}
      </button>
    </div>
  )
}
```

Write to `frontend-v2/src/header/SyncIndicator.module.css`:

```css
.indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot.fresh {
  background: var(--success);
}

.dot.stale {
  background: var(--warning);
}

.dot.old {
  background: var(--danger);
}

.label {
  color: var(--text-secondary);
}

.label.stale {
  color: var(--warning);
}

.label.old {
  color: var(--danger);
}

.refreshBtn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 14px;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast);
}

.refreshBtn:hover:not(:disabled) {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.refreshBtn:disabled {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
```

- [ ] **11.2: Create Header**

Write to `frontend-v2/src/header/Header.tsx`:

```tsx
import { useState } from 'react'
import { toggleTheme } from '../theme/theme'
import { SyncIndicator } from './SyncIndicator'
import styles from './Header.module.css'

export function Header() {
  const [theme, setTheme] = useState(
    () => (document.documentElement.getAttribute('data-theme') as 'dark' | 'light') ?? 'dark',
  )

  function handleToggleTheme() {
    const next = toggleTheme()
    setTheme(next)
  }

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <h1 className={styles.logo}>WKO5</h1>
        <span className={styles.version}>v2</span>
      </div>
      <div className={styles.right}>
        <SyncIndicator />
        <button
          className={styles.themeBtn}
          onClick={handleToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? '\u2600' : '\u263D'}
        </button>
      </div>
    </header>
  )
}
```

Write to `frontend-v2/src/header/Header.module.css`:

```css
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
  flex-shrink: 0;
}

.left {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.logo {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.version {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  font-weight: 500;
}

.right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.themeBtn {
  background: none;
  border: none;
  font-size: 18px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  transition: background var(--transition-fast);
}

.themeBtn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
```

- [ ] **11.3: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/header/
git commit -m "feat(v2): Header with SyncIndicator, theme toggle, manual refresh"
```

---

## Task 12: Tab bar placeholder + Footer

### Step 1: TabBar + Footer

- [ ] **12.1: Create TabBar**

Write to `frontend-v2/src/layout/TabBar.tsx`:

```tsx
import styles from './TabBar.module.css'

const DEFAULT_TABS = [
  { id: 'today', label: 'Today' },
  { id: 'health', label: 'Health' },
  { id: 'fitness', label: 'Fitness' },
  { id: 'event-prep', label: 'Event Prep' },
  { id: 'history', label: 'History' },
  { id: 'profile', label: 'Profile' },
]

interface TabBarProps {
  activeTab: string
  onTabChange: (tabId: string) => void
}

export function TabBar({ activeTab, onTabChange }: TabBarProps) {
  return (
    <nav className={styles.tabBar}>
      {DEFAULT_TABS.map((tab) => (
        <button
          key={tab.id}
          className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
```

Write to `frontend-v2/src/layout/TabBar.module.css`:

```css
.tabBar {
  display: flex;
  gap: 0;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
  padding: 0 16px;
  overflow-x: auto;
  flex-shrink: 0;
}

.tab {
  padding: 10px 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  white-space: nowrap;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.tab:hover {
  color: var(--text-primary);
}

.tab.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}
```

- [ ] **12.2: Create Footer**

Write to `frontend-v2/src/footer/Footer.tsx`:

```tsx
import { useDataStore } from '../store/data-store'
import styles from './Footer.module.css'

export function Footer() {
  const loading = useDataStore((s) => s.loading)
  const errors = useDataStore((s) => s.errors)
  const errorCount = Object.keys(errors).length

  return (
    <footer className={styles.footer}>
      <div className={styles.left}>
        {loading.size > 0 && (
          <span className={styles.loading}>
            Loading {Array.from(loading).join(', ')}...
          </span>
        )}
        {errorCount > 0 && (
          <span className={styles.errors}>
            {errorCount} error{errorCount > 1 ? 's' : ''}
          </span>
        )}
        {loading.size === 0 && errorCount === 0 && (
          <span className={styles.connected}>Connected</span>
        )}
      </div>
      <div className={styles.right}>
        <span className={styles.version}>WKO5 Analyzer v2</span>
      </div>
    </footer>
  )
}
```

Write to `frontend-v2/src/footer/Footer.module.css`:

```css
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 28px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
  font-size: var(--font-size-xs);
  flex-shrink: 0;
}

.left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.right {
  color: var(--text-tertiary);
}

.loading {
  color: var(--accent-blue);
}

.errors {
  color: var(--danger);
}

.connected {
  color: var(--success);
}

.version {
  color: var(--text-tertiary);
}
```

- [ ] **12.3: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/layout/ frontend-v2/src/footer/
git commit -m "feat(v2): TabBar placeholder + Footer with connection status"
```

---

## Task 13: TSBStatus proof-of-concept panel

### Step 1: Build the panel + test

- [ ] **13.1: Create TSBStatus panel**

Write to `frontend-v2/src/panels/status/TSBStatus.tsx`:

```tsx
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { MetricBig } from '../../shared/MetricBig'
import { tsbColor, tsbLabel, COLORS } from '../../shared/tokens'
import styles from './TSBStatus.module.css'

export function TSBStatus() {
  const fitness = useDataStore((s) => s.fitness)
  const loading = useDataStore((s) => s.loading.has('fitness'))
  const error = useDataStore((s) => s.errors['fitness'])
  const refresh = useDataStore((s) => s.refresh)

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} onRetry={refresh} />
  if (!fitness) return <PanelEmpty message="No fitness data available" />

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.title}>Today's Form</span>
        <span className={styles.phase} style={{ color: tsbColor(fitness.TSB) }}>
          {tsbLabel(fitness.TSB)}
        </span>
      </div>
      <div className={styles.hero}>
        <MetricBig
          value={fitness.TSB}
          label="TSB"
          color={tsbColor(fitness.TSB)}
        />
      </div>
      <div className={styles.row}>
        <Metric value={fitness.CTL} label="CTL" color={COLORS.ctl} />
        <Metric value={fitness.ATL} label="ATL" color={COLORS.atl} />
      </div>
    </div>
  )
}
```

Write to `frontend-v2/src/panels/status/TSBStatus.module.css`:

```css
.card {
  background: var(--bg-panel);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--bg-panel-header);
  border-bottom: 1px solid var(--border-secondary);
}

.title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.phase {
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.hero {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

.row {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 4px 16px 16px;
}
```

- [ ] **13.2: Write TSBStatus tests**

Write to `frontend-v2/src/panels/status/TSBStatus.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TSBStatus } from './TSBStatus'
import { useDataStore } from '../../store/data-store'

// Mock the API client (store imports it)
vi.mock('../../api/client', () => ({
  getFitness: vi.fn(),
  getPmc: vi.fn(),
  getClinicalFlags: vi.fn(),
  getProfile: vi.fn(),
  getConfig: vi.fn(),
  getModel: vi.fn(),
  getActivities: vi.fn(),
  getRollingFtp: vi.fn(),
  getFtpGrowth: vi.fn(),
  getRollingPdProfile: vi.fn(),
  getIfDistribution: vi.fn(),
  getFreshBaseline: vi.fn(),
  getShortPowerConsistency: vi.fn(),
  getPerformanceTrend: vi.fn(),
  getHealth: vi.fn(),
  getRide: vi.fn(),
}))

beforeEach(() => {
  useDataStore.setState({
    fitness: null,
    loading: new Set(),
    errors: {},
  })
})

describe('TSBStatus', () => {
  it('renders loading skeleton when fitness is loading', () => {
    useDataStore.setState({ loading: new Set(['fitness']) })
    render(<TSBStatus />)
    // PanelSkeleton renders bars
    expect(document.querySelector('[class*="skeleton"]')).toBeTruthy()
  })

  it('renders error with message', () => {
    useDataStore.setState({ errors: { fitness: 'Network error' } })
    render(<TSBStatus />)
    expect(screen.getByText('Network error')).toBeTruthy()
  })

  it('renders empty state when no data', () => {
    render(<TSBStatus />)
    expect(screen.getByText('No fitness data available')).toBeTruthy()
  })

  it('renders TSB, CTL, ATL from store', () => {
    useDataStore.setState({
      fitness: { CTL: 55, ATL: 60, TSB: -5, date: '2026-03-24' },
    })
    render(<TSBStatus />)
    expect(screen.getByText('-5')).toBeTruthy()
    expect(screen.getByText('TSB')).toBeTruthy()
    expect(screen.getByText('55')).toBeTruthy()
    expect(screen.getByText('CTL')).toBeTruthy()
    expect(screen.getByText('60')).toBeTruthy()
    expect(screen.getByText('ATL')).toBeTruthy()
  })

  it('shows "Neutral" label for TSB between -10 and 5', () => {
    useDataStore.setState({
      fitness: { CTL: 55, ATL: 60, TSB: -5, date: '2026-03-24' },
    })
    render(<TSBStatus />)
    expect(screen.getByText('Neutral')).toBeTruthy()
  })

  it('shows "Fresh" label for TSB > 5', () => {
    useDataStore.setState({
      fitness: { CTL: 55, ATL: 40, TSB: 15, date: '2026-03-24' },
    })
    render(<TSBStatus />)
    expect(screen.getByText('Fresh')).toBeTruthy()
  })
})
```

- [ ] **13.3: Run TSBStatus tests**

```bash
cd /Users/jshin/Documents/wko5-experiments/frontend-v2
npx vitest run src/panels/status/TSBStatus.test.tsx
```

Expected: 6 tests passing.

- [ ] **13.4: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/src/panels/
git commit -m "feat(v2): TSBStatus panel — proof-of-concept store-to-render data flow + 6 tests"
```

---

## Task 14: App shell — wire everything together

### Step 1: App.tsx + main.tsx + index.html

- [ ] **14.1: Write App.tsx**

Write to `frontend-v2/src/App.tsx`:

```tsx
import { useState } from 'react'
import { Header } from './header/Header'
import { TabBar } from './layout/TabBar'
import { Footer } from './footer/Footer'
import { WarmupScreen } from './startup/WarmupScreen'
import { useStartup } from './startup/useStartup'
import { useAutoRefresh } from './startup/useAutoRefresh'
import { TSBStatus } from './panels/status/TSBStatus'
import styles from './App.module.css'

export function App() {
  const { phase, warmupStatus, error } = useStartup()
  const [activeTab, setActiveTab] = useState('today')

  // Auto-refresh only when startup is complete
  useAutoRefresh(phase === 'ready')

  if (phase === 'warming' || phase === 'loading' || phase === 'error') {
    return <WarmupScreen status={warmupStatus} error={error} />
  }

  return (
    <div className={styles.app}>
      <Header />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className={styles.main}>
        {activeTab === 'today' && (
          <div className={styles.panelGrid}>
            <TSBStatus />
          </div>
        )}
        {activeTab !== 'today' && (
          <div className={styles.placeholder}>
            <p>{activeTab} tab — panels coming in Phase 1B</p>
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
```

Write to `frontend-v2/src/App.module.css`:

```css
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.panelGrid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  max-width: 1200px;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--text-tertiary);
  font-size: var(--font-size-md);
}
```

- [ ] **14.2: Write main.tsx**

Write to `frontend-v2/src/main.tsx`:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initTheme } from './theme/theme'
import './theme/variables.css'
import { App } from './App'

// Initialize theme before first render
initTheme()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **14.3: Write index.html**

Write to `frontend-v2/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>WKO5 Analyzer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **14.4: Remove Vite boilerplate files**

```bash
rm -f frontend-v2/src/App.css frontend-v2/src/index.css frontend-v2/src/assets/react.svg frontend-v2/public/vite.svg
```

- [ ] **14.5: Run all frontend tests**

```bash
cd /Users/jshin/Documents/wko5-experiments/frontend-v2
npx vitest run
```

Expected: All tests passing (API client + store + TSBStatus).

- [ ] **14.6: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add frontend-v2/
git commit -m "feat(v2): App shell — header, tab bar, footer, warmup screen, TSBStatus wired up"
```

---

## Task 15: Backend change — add data_version to /health

### Step 1: Add version counter

- [ ] **15.1: Add _data_version counter to routes.py**

In `wko5/api/routes.py`, add a `_data_version` counter that increments on cache invalidation. Modify the `/health` endpoint to include it.

After the `_CACHE_TTL = 300` line (around line 51), add:

```python
_data_version = 1
```

Modify `_invalidate_cache()` to increment the counter:

```python
def _invalidate_cache():
    """Clear all cached data (call after sync or model update)."""
    global _data_version
    _cache.clear()
    _data_version += 1
```

Modify the `/health` endpoint to include `data_version`:

```python
@router.get("/health")
def health():
    return {
        "status": "ok",
        "cache_warm": _warmup_status["done"],
        "warmup_errors": _warmup_status["errors"] if _warmup_status["errors"] else None,
        "data_version": _data_version,
    }
```

- [ ] **15.2: Write pytest for data_version**

Write to `tests/test_api_health.py`:

```python
"""Tests for /health endpoint data_version field."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wko5.api.routes import _data_version, _invalidate_cache


def test_data_version_starts_at_one():
    from wko5.api import routes
    assert routes._data_version >= 1


def test_invalidate_cache_increments_version():
    from wko5.api import routes
    before = routes._data_version
    _invalidate_cache()
    assert routes._data_version == before + 1
```

- [ ] **15.3: Run backend test**

```bash
source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_api_health.py -v
```

Expected: 2 tests passing.

- [ ] **15.4: Commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add wko5/api/routes.py tests/test_api_health.py
git commit -m "feat: add data_version to /health endpoint for frontend change detection"
```

---

## Task 16: Integration verification

### Step 1: End-to-end check

- [ ] **16.1: Start backend**

```bash
source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python run_api.py &
```

Wait for warmup to complete (watch stderr for `[warmup] Complete:`). Note the port and token from output.

- [ ] **16.2: Set token for frontend**

In the browser, navigate to `http://localhost:5173?token=<TOKEN_FROM_BACKEND>`.

- [ ] **16.3: Verify startup sequence**

Expected behavior:
1. Branded loading screen shows "WKO5 Analyzer" title
2. Progress bar fills as warmup tasks complete
3. Status text shows "Pre-computing models... N/8"
4. When warmup completes, screen transitions to "Loading dashboard..."
5. App shell appears with header, tab bar, TSBStatus panel

- [ ] **16.4: Verify TSBStatus renders real data**

The TSBStatus panel should show:
- A hero TSB number (e.g., -5)
- Color-coded form label (Fresh/Neutral/Tired)
- CTL and ATL values below

- [ ] **16.5: Verify header**

Check:
- "WKO5 v2" logo in header
- "Synced just now" with green dot
- Theme toggle button (sun/moon icon)
- Click theme toggle — colors change to light mode

- [ ] **16.6: Verify tab bar**

Click through all tabs:
- Today: shows TSBStatus panel
- Health, Fitness, Event Prep, History, Profile: show placeholder text

- [ ] **16.7: Verify footer**

Footer shows "Connected" when API is reachable.

- [ ] **16.8: Verify proxy**

Open browser dev tools Network tab. API calls should go to `localhost:5173/api/...` (Vite proxy) not directly to the backend port.

- [ ] **16.9: Run full test suite**

```bash
cd /Users/jshin/Documents/wko5-experiments/frontend-v2 && npx vitest run
source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/test_api_health.py -v
```

All tests should pass.

- [ ] **16.10: Final commit**

```bash
cd /Users/jshin/Documents/wko5-experiments
git add -A
git commit -m "feat(v2): Phase 1A complete — foundation verified end-to-end"
```
