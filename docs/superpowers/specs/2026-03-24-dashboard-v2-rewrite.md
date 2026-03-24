# WKO5 Dashboard v2 — Full Frontend Rewrite

## Goal

Replace the current plain-JS dashboard with a React + TypeScript application that combines WKO5-depth analytics with Intervals.icu-clean UX, featuring an AI analysis panel powered by Claude Code via MCP bridge.

## Audience

Coach + athlete pair. Athlete view is built first; coach layer is designed in from day one (multi-athlete routing, role-based default layouts). The system is generic — not built for a single user.

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | React 18 + TypeScript | Best D3 integration, largest ecosystem for DnD/calendar |
| Build | Vite | Fast dev server, proxy to FastAPI, static build for deployment |
| State | Zustand | Slice-based subscriptions (PMC chart doesn't re-render when flags change), works outside React |
| Charts | D3.js v7 | Already proven, full control, reuse existing chart logic |
| Chart builder | Plotly.js (custom charts only, lazy-loaded via React.lazy) | Declarative config, same pattern as Intervals.icu. Code-split — not in Phase 1 bundle. |
| DnD | dnd-kit | React-native, accessible, better than SortableJS for React |
| Styling | CSS Modules + CSS custom properties | Scoped styles, theme tokens carry over |
| AI | Embedded Claude Code terminal + MCP server | Bidirectional — Claude reads dashboard state, pushes annotations |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React App (Vite)                                       │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐│
│  │ API      │→ │ Zustand   │→ │ Panel Components       ││
│  │ Client   │  │ Store     │  │ (prebuilt + custom)    ││
│  │ (typed)  │  │           │  │                        ││
│  └──────────┘  └──────────┘  └────────────────────────┘│
│                     ↕                                    │
│  ┌──────────────────────────────────────────────────────┐│
│  │ Layout Engine (tabs, panels, edit mode, persistence) ││
│  └──────────────────────────────────────────────────────┘│
│                     ↕                                    │
│  ┌──────────────────────────────────────────────────────┐│
│  │ MCP Bridge Server (dashboard state ↔ Claude Code)    ││
│  └──────────────────────────────────────────────────────┘│
│                     ↕                                    │
│  ┌──────────────────────────────────────────────────────┐│
│  │ Embedded Terminal (Claude Code session)               ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
         ↕
┌─────────────────────┐
│ FastAPI Backend      │
│ (34 endpoints,      │
│  SQLite, existing)   │
└─────────────────────┘
```

## Data Flow

### Principle: Compute Once at Upload

Activities are immutable after import. The backend pre-computes all derived metrics (PMC, model, profile, flags, rolling FTP, etc.) at ingest time and stores results in SQLite. The dashboard reads pre-computed results — it does not trigger expensive computation.

### Startup Sequence

1. App loads → poll `GET /warmup-status` (no auth) until `done: true`. Show branded loading screen with progress.
2. Once warm → fetch core data in parallel:
   - `GET /fitness` — current CTL/ATL/TSB
   - `GET /pmc` — full PMC history
   - `GET /clinical-flags` — health alerts
   - `GET /profile` — power profile + rankings
   - `GET /config` — athlete settings + MCP server port
   - `GET /model?days=90` — PD model + MMP envelope
3. Results populate Zustand store. Per-key loading tracked via `loading: Set<string>`.
4. All panels on the active tab render immediately from store
5. Background: lazily fetch secondary data (rolling-ftp, ftp-growth, rolling-pd, performance-trend, activities) and populate store as they arrive
6. On-demand: ride detail, route analysis, glycogen budget — fetched when user navigates to them

### Auto-Refresh

- Poll `GET /health` every 3-4 hours. Backend returns `data_version: number` (incremented on cache invalidation / new data import).
- If `data_version` changed since last check → refetch core data silently.
- Also refresh on window focus if last refresh was >4 hours ago.
- Manual refresh button in header.
- Stale data indicator in header: "Synced 6h ago" — amber if >24h old.

### Store Shape

```typescript
interface DataStore {
  // Core (fetched at startup)
  fitness: FitnessData | null
  pmc: PMCRow[]
  clinicalFlags: ClinicalFlagsResponse | null
  profile: ProfileResponse | null
  config: AthleteConfig | null

  // Secondary (lazy-loaded)
  rollingFtp: RollingFtpRow[]
  ftpGrowth: FtpGrowthResponse | null
  rollingPd: RollingPdRow[]
  ifDistribution: IfDistributionResponse | null
  freshBaseline: FreshBaselineResponse | null
  shortPower: ShortPowerResponse | null
  performanceTrend: PerformanceTrendRow[]

  // Core (also fetched at startup)
  activities: Activity[]
  activitiesTotal: number
  model: ModelResult | null

  // On-demand (keyed by ID, LRU cache max 15 entries)
  rides: Record<number, RideDetail>
  routes: RouteListItem[]
  routeDetail: Record<number, RouteDetail>

  // Cross-panel state
  selectedRouteId: number | null   // Event Prep tab coordination
  athleteSlug: string              // From URL or default; scopes localStorage + future multi-athlete
  globalTimeRange: { start: string, end: string } | null  // null = all time

  // Metadata
  loading: Set<string>             // Per-key loading tracking (e.g., loading.has('fitness'))
  errors: Record<string, string>   // Per-key error messages
  lastRefresh: string | null
  dataVersion: number | null       // From /health endpoint, for change detection

  // Annotations (from Claude via MCP)
  annotations: Record<string, Annotation[]>  // Keyed by panelId, session-only

  // Actions
  fetchCore: (athlete?: string) => Promise<void>
  fetchSecondary: () => Promise<void>
  fetchRide: (id: number) => Promise<void>
  setSelectedRoute: (id: number | null) => void
  setTimeRange: (range: { start: string, end: string } | null) => void
  addAnnotation: (panelId: string, annotation: Annotation) => void
  clearAnnotations: (panelId?: string) => void
  refresh: () => Promise<void>
}

interface Annotation {
  id: string
  source: 'claude' | 'user'
  type: 'region' | 'line' | 'point'
  x?: [string, string] | string   // date range or single date
  y?: number
  label: string                    // Always rendered as textContent, never innerHTML
  color: string
  timestamp: string
}
```

## Typed API Client

Single `src/api/client.ts` file. Every endpoint has a typed function. Response types are generated from the actual API responses captured during design (see Appendix A).

```typescript
// Example
export async function getClinicalFlags(daysBack = 30): Promise<ClinicalFlagsResponse> {
  return fetchApi<ClinicalFlagsResponse>(`/clinical-flags?days_back=${daysBack}`)
}

// The generic fetchApi handles auth, JSON parsing, error wrapping
async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}/api${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, ...options?.headers }
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json()
}
```

Types live in `src/api/types.ts` — one interface per endpoint response.

## Panel System

### Prebuilt Panels

Each panel is a React component in `src/panels/`. It reads from the Zustand store via selectors — no fetching, no loading state (the store is already populated).

```typescript
// src/panels/TSBStatus.tsx
export function TSBStatus() {
  const fitness = useDataStore(s => s.fitness)
  const loading = useDataStore(s => s.loading.has('fitness'))
  const error = useDataStore(s => s.errors['fitness'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!fitness) return <PanelEmpty message="No fitness data available" />

  return (
    <div className={styles.tsbCard}>
      <MetricBig value={fitness.TSB} label="TSB" color={tsbColor(fitness.TSB)} />
      <MetricRow>
        <Metric value={fitness.CTL} label="CTL" />
        <Metric value={fitness.ATL} label="ATL" />
      </MetricRow>
    </div>
  )
}
```

### Panel Registry

```typescript
interface PanelDef {
  id: string
  label: string
  category: 'status' | 'health' | 'fitness' | 'event-prep' | 'history' | 'profile'
  description: string
  component: React.ComponentType
  dataKeys: string[]  // which store keys this panel reads (metadata only — for loading indicators + catalog display; Zustand selectors are runtime truth)
}
```

### Panel Catalog (initial set)

**Status:** tsb-status, recent-rides, clinical-alert
**Health:** clinical-flags, if-distribution, if-floor, panic-training, reds-screen, fresh-baseline
**Fitness:** pmc-chart, mmp-curve, rolling-ftp, ftp-growth, rolling-pd, short-power, power-profile
**Event Prep:** route-selector, segment-profile, demand-heatmap, gap-analysis, pacing, opportunity-cost, glycogen-budget
**History:** rides-table, training-blocks, phase-timeline, weekly-volume, intensity-dist
**Profile:** coggan-ranking, phenotype, athlete-config, posterior-summary, feasibility

### Custom Chart Builder (Phase 3)

Plotly-based. User picks:
- Data source (activities, PMC, rolling FTP, etc.)
- X axis field
- Y axis field(s)
- Color/group by field
- Chart type (line, scatter, bar, histogram)
- Filters (date range, sport type)

Saved as JSON config in localStorage (later: backend).

## Layout Engine

### Structure

```typescript
interface Layout {
  version: number
  tabs: Tab[]
}

interface Tab {
  id: string
  label: string
  panels: string[]  // panel IDs in display order
}
```

### Persistence

- localStorage keyed by user slug: `wko5-layout-{user}`
- Default presets: `athlete` and `coach`
- Layout is a pure data structure — no DOM coupling

### Edit Mode

- Gear icon in header → toggles edit mode
- dnd-kit for panel reorder within tabs
- Add panel: catalog modal grouped by category
- Remove panel: X button on hover
- Add/remove/rename tabs
- Done saves to localStorage, Cancel restores snapshot
- Reset to default preset (with confirmation dialog: "Reset to default? This replaces your current layout.")
- Search/filter in panel catalog modal (30+ panels across 6 categories)

### Default Athlete Layout

```
Today:      [tsb-status, recent-rides, clinical-alert]
Health:     [clinical-flags, if-floor, panic-training, reds-screen] then [if-distribution, fresh-baseline]
Fitness:    [pmc-chart, mmp-curve, rolling-ftp, ftp-growth, rolling-pd]
Event Prep: [route-selector, segment-profile, demand-heatmap, gap-analysis, pacing, opportunity-cost, glycogen-budget]
History:    [rides-table, training-blocks, phase-timeline, intensity-dist]
Profile:    [coggan-ranking, phenotype, power-profile, posterior-summary, feasibility]
Settings:   [athlete-config]
Calendar:   [calendar-view]
```

**Health tab IA:** Flags (severity-ordered: danger first, then warning, then ok) at the top in a card grid. Trend analysis panels (if-distribution, fresh-baseline) below with a "Training Pattern Analysis" section header.

### Event Prep Tab Coordination

The `route-selector` panel writes `selectedRouteId` to the Zustand store. All other Event Prep panels subscribe to `selectedRouteId`:
- If null → show "Select a route to see analysis"
- If set → fetch and render route-specific data

`glycogen-budget` is interactive (form inputs) — its form state is local to the component, not in the store. On form change (debounced 500ms), it calls `POST /glycogen-budget` directly.

### Global Time Range Filter

A persistent filter bar sits between the tab nav and panel area:
- Shows current date range (default: "All Time")
- Sport type filter dropdown
- Reset button
- Updates `globalTimeRange` in the Zustand store
- Time-aware panels (PMC, rides-table, training-blocks, etc.) re-filter from store data
- **Critical:** When Claude changes the range via MCP `set_time_range`, the filter bar updates visibly so the user knows what changed

## Calendar Tab (Phase 3)

Full-width calendar view:
- Weekly and monthly toggle
- Each day cell shows: ride name, duration, TSS (color-coded)
- Planned workouts (from TrainingPeaks ingest) shown alongside completed
- Click a day → expands to show ride detail
- TSS heatmap coloring (darker = higher load)
- Week totals in margin (hours, TSS, km)

## AI Chat — Claude Code + MCP Bridge

### Embedded Terminal

- Collapsible side panel (right side, 400px default width, resizable via drag handle, min 300px)
- Runs a Claude Code session in the terminal via xterm.js or similar
- Connected to the wko5-experiments project directory
- Claude Code has access to all wko5-* skills, the database, and Python code

### MCP Bridge Server

A lightweight MCP server (Node.js or Python) spawned by the FastAPI backend as a subprocess at startup. The MCP server port and auth token are returned via `GET /config` so the frontend can discover them automatically.

**Authentication:** Per-session shared secret generated at startup, required on every MCP tool invocation. Bound to `127.0.0.1` only (not `0.0.0.0`).

**Lifecycle:** Backend spawns MCP server → MCP server registers with `.mcp.json` → Claude Code connects automatically. If MCP server crashes, backend restarts it. On backend shutdown, MCP server dies with it.

Claude Code connects to it via `.mcp.json`.

**Tools exposed to Claude Code:**

```
get_dashboard_state()
  → { activeTab, visiblePanels, timeRange, selectedRide, selectedRoute }

get_panel_data(panelId: string)
  → The current data rendered by that panel (from Zustand store)

get_all_metrics()
  → Snapshot of entire Zustand store (fitness, pmc, flags, etc.)

highlight_chart(panelId: string, annotation: { type, x?, y?, label, color })
  → Pushes a visual annotation onto a chart (vertical line, region, point)

show_panel(panelId: string)
  → Navigates to the tab containing that panel and scrolls to it

set_time_range(start: string, end: string)
  → Updates the global time range filter
```

**Flow:**
1. User looks at PMC chart, opens Claude panel, types "why did my CTL drop in February?"
2. Claude Code reads dashboard state via MCP → sees PMC is visible, gets the full PMC data
3. Claude uses wko5-analyzer skill knowledge + the data to identify the CTL drop
4. Claude calls `highlight_chart('pmc-chart', { type: 'region', x: ['2026-02-01', '2026-02-15'], label: 'CTL plateau', color: 'red' })`
5. Dashboard receives the annotation via MCP and renders it on the PMC chart
6. Claude responds: "Your CTL dropped from 52 to 44 between Feb 1-15. Looking at your activities..." (continues analysis)

### Annotation Lifecycle

Annotations pushed by Claude via `highlight_chart`:
- Stored in `annotations` slice of Zustand store, keyed by panelId
- Each annotation has: source label ("Claude"), timestamp, dismiss button
- Session-only — cleared on page reload, never persisted to localStorage
- "Clear all annotations" button in chart toolbar
- Labels are always rendered via `textContent` / D3's `.text()` — never `innerHTML` (XSS prevention)
- Labels length-bounded to 200 chars; color validated as CSS color literal

### Safety Boundary

Claude can read data and push visual annotations via MCP. Claude **cannot** modify activities, delete data, or change athlete config via MCP tools. All MCP tools are read-only or visual-only. Data mutations only happen through the authenticated FastAPI endpoints.

### MCP Server Location

`tools/mcp-dashboard/` — spawned by FastAPI backend as subprocess.

## Error Handling

### Typed Errors

```typescript
class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`API ${status}: ${body}`)
  }
}
```

### Error Boundaries

Every panel wrapped in an error boundary:
```typescript
<PanelErrorBoundary panelId={id} onRetry={refresh}>
  <PanelComponent />
</PanelErrorBoundary>
```

Displays: panel title, error message, retry button. Other panels continue working.

### Store Errors

Fetch failures stored in `errors` map by endpoint key. Panels check for their dependencies:
```typescript
const error = useDataStore(s => s.errors['fitness'])
if (error) return <PanelError message={error} />
```

## Security

### Content Security Policy

Define before Phase 2: `default-src 'self'; connect-src 'self' ws://127.0.0.1:*; script-src 'self'; style-src 'self' 'unsafe-inline'`. Adjust for xterm.js and Plotly requirements. Embedded terminal runs in a sandboxed iframe with its own CSP.

### Token Handling

- Bearer token delivered via `<meta>` tag in initial HTML (not URL query string)
- Stored in httpOnly cookie for API calls (not localStorage) when possible
- Token printed to startup log on its own line, not embedded in URL
- No token expiry for local use; session-based tokens required for coach layer

### Chart Design System Tokens

Defined in `src/shared/tokens.ts` before any chart is built:
- Color palette: 8 semantic colors for chart elements
- TSB color mapping: green (>5), yellow (-10 to 5), red (<-10)
- CTL/ATL/TSB line colors consistent across PMC + TSB status + any chart showing these
- Axis label typography, gridline opacity, tooltip template
- Annotation visual style (dashed border, source badge)

## Coach Layer (Designed In, Built Later)

### URL-Based Identity

- `/athlete/jshin` — athlete view for jshin
- `/coach/elena` — coach view for elena
- No auth beyond the bearer token for now (single-user local)
- Later: proper user model in SQLite, session management

### Layout Per Role

- Athlete and coach get different default layouts
- Coach default: Health tab first, clinical flags prominent
- Layout stored per user slug in localStorage

### Multi-Athlete (Future)

- Coach sees athlete switcher in header
- Each athlete has their own database (or schema)
- API adds `?athlete=` param
- Zustand store scoped per athlete

## File Structure

```
frontend-v2/
  src/
    api/
      client.ts          — typed fetch wrapper
      types.ts           — all response interfaces
    store/
      data-store.ts      — Zustand store definition
    panels/
      status/
        TSBStatus.tsx
        RecentRides.tsx
        ClinicalAlert.tsx
      health/
        ClinicalFlags.tsx
        IFDistribution.tsx
        IFFloor.tsx
        PanicTraining.tsx
        RedsScreen.tsx
        FreshBaseline.tsx
      fitness/
        PMCChart.tsx
        MMPCurve.tsx
        RollingFtp.tsx
        FtpGrowth.tsx
        RollingPd.tsx
        ShortPower.tsx
        PowerProfile.tsx
      event-prep/
        RouteSelector.tsx
        SegmentProfile.tsx
        GapAnalysis.tsx
        OpportunityCost.tsx
        GlycogenBudget.tsx
      history/
        RidesTable.tsx
        TrainingBlocks.tsx
        PhaseTimeline.tsx
        IntensityDist.tsx
      profile/
        CogganRanking.tsx
        Phenotype.tsx
        AthleteConfig.tsx
        PosteriorSummary.tsx
    layout/
      LayoutEngine.tsx   — tab/panel rendering from layout config
      EditMode.tsx       — edit mode UI + dnd-kit integration
      PanelRegistry.ts   — panel catalog (id → component mapping)
      PanelWrapper.tsx   — error boundary + chrome (title bar, drag handle)
    calendar/
      CalendarView.tsx   — full calendar tab (Phase 3)
    chat/
      ChatPanel.tsx      — embedded terminal (Phase 2)
    shared/
      Metric.tsx         — reusable metric card component
      DataTable.tsx      — reusable sortable table
      ChartContainer.tsx — D3 chart wrapper with resize observer
    App.tsx
    main.tsx
  public/
  index.html
  vite.config.ts         — proxy /api to FastAPI
  tsconfig.json
  package.json

tools/
  mcp-dashboard/
    server.ts            — MCP server exposing dashboard state tools
    mcp.json             — MCP server config for Claude Code
```

## Phasing

### Phase 1: Dashboard Core + Prebuilt Charts
- Vite + React + TypeScript scaffold
- Typed API client + Zustand store
- Layout engine with tab/panel rendering + edit mode
- All prebuilt panels (port existing render logic to React components)
- Error boundaries
- Theme (dark/light)
- Proxy to FastAPI backend

**Exit criteria:** All existing panels render correctly, data loads instantly from store, edit mode works, PMC chart supports annotation overlays (proof-of-concept for Phase 2 MCP integration).

### Phase 2: AI Chat + MCP Bridge
- MCP server in `tools/mcp-dashboard/`
- Embedded terminal component (xterm.js)
- Claude Code session management
- Bidirectional: Claude reads state, pushes annotations
- "Ask about this" context buttons on panels

**Exit criteria:** User can ask Claude about their data, Claude can highlight charts.

### Phase 3: Calendar + Custom Chart Builder
- Calendar tab (weekly/monthly view)
- Activity cells with TSS color coding
- Planned vs completed overlay
- Custom chart builder (Plotly-based)
- Save/load custom chart configs

**Exit criteria:** Full calendar view, custom charts saveable to layout.

## Backend Changes Required

Small changes to the existing FastAPI backend to support the v2 frontend:

1. **`GET /health`** — add `data_version: int` field (counter incremented on cache invalidation)
2. **`GET /config`** — add `mcp_port: int` and `mcp_token: string` fields (from MCP subprocess)
3. **`POST /plan-ride`, `POST /glycogen-budget`** — replace `body: dict` with Pydantic models for validation
4. **SPA catch-all** — exclude `/api/` prefix from catch-all route (return 404 JSON for unknown API paths)
5. **`run_api.py`** — stop printing token in URL format; spawn MCP subprocess
6. **`rwgps.py`** — remove hardcoded API credential defaults (require env vars)

## Appendix A: API Response Types

See endpoint catalog in the brainstorming session. All 34 endpoints were hit with real data and response shapes captured. Types will be generated from these captures.

Key shapes:
- `FitnessData: { CTL, ATL, TSB, date }`
- `PMCRow: { date, TSS, CTL, ATL, TSB }`
- `ClinicalFlag: { name, status: 'ok'|'warning'|'danger', value, threshold, detail }`
- `Activity: { id, filename, sport, sub_sport, start_time, total_elapsed_time, avg_power, normalized_power, intensity_factor, training_stress_score, ... }`
- `ModelResult: { Pmax, FRC, mFTP, TTE, mVO2max_L_min, mVO2max_ml_min_kg, tau, t0, sub_cp_note, mmp: [seconds, power][] }`
- `RollingFtpRow: { date, mFTP, Pmax, FRC, TTE_min }`
- `ProfileResponse: { profile: { watts, wkg }, ranking, strengths_limiters }`
- `IfDistribution: { histogram: Record<string, number>, floor, ceiling, spread, compressed, rides_analyzed }`
- `FtpGrowth: { slope, intercept, r_squared, improvement_rate_w_per_year, plateau_detected, growth_phase, training_age_weeks, data_points }`
- `FreshBaseline: Record<string, { exists, value, date, staleness_days }>`
- `ShortPower: { peak, typical, ratio, diagnosis, efforts_analyzed, message }`
- `DetectedPhase: { phase, confidence, reasoning }`
- `Feasibility: { current_ctl, target_ctl, ctl_gap, weeks_available, required_ramp_rate, max_sustainable_ramp, feasible, margin_weeks }`
- `TrainingBlock: { start, end, volume, intensity, power, tp }`
- `WeeklySummary: { week, hours, km, tss, ride_count, avg_if, elevation, avg_power }`
- `PosteriorSummary: { pd_model: Record<string, { median, ci_95, std, ci_width }>, durability: Record<string, ...> }`
