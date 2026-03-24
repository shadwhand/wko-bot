# Review: WKO5 Dashboard v2 — Full Frontend Rewrite

**Date:** 2026-03-24
**Document:** docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md
**Reviewers:** Principal Engineer (opus), Product Designer (sonnet), Security Engineer (opus)
**Synthesizer:** opus

---

## 1. Cross-Review Consensus

Eight issues were flagged independently by two or more reviewers. These are the highest-confidence findings.

### C1. MCP bridge trust boundary is undefined (Principal 3, Security CRITICAL-1)

The spec describes an embedded Claude Code terminal that communicates with the dashboard via a local MCP server. The MCP server exposes `get_all_metrics()`, `highlight_chart()`, `show_panel()`, and `set_time_range()`. There is no defined trust boundary: any process on localhost that discovers the MCP server port can call these tools. The Principal flags that a rogue Claude Code tool could call `set_time_range()` to silently mutate dashboard state. The Security reviewer escalates: if the MCP server has no auth, a SSRF vulnerability elsewhere in the app (or any malicious npm package loaded by Vite dev server) could pivot to the MCP port and exfiltrate the full Zustand store via `get_all_metrics()`.

### C2. Startup data fetch has no loading states for panels (Principal 5, Designer 4)

The spec states: "All panels on the active tab render immediately from store." But the store starts empty — `fitness`, `pmc`, and `clinicalFlags` are all `null` at mount time. `TSBStatus` returns `null` when `fitness` is null (per the spec's own code sample), which means panels silently disappear during startup. There is no skeleton, spinner, or "loading" indicator specified. The Designer adds: the spec defines `loading: boolean` in the store but never specifies when it is set or which panels observe it.

### C3. `GlycogenBudget` and `OpportunityCost` require interactive inputs, not passive panels (Principal 7, Designer 8)

The panel spec for `glycogen-budget` and `opportunity-cost` assumes data is fetched when "user navigates to them." `GlycogenBudget` requires `ride_kj`, `ride_duration_h`, `on_bike_carbs_g`, `body_weight_kg` — none of which exist in the Zustand store. `OpportunityCost` requires a `route_id`. Neither panel has a defined input form in the spec. They will render empty or error immediately. This is carried forward from the P3 review (D3, C4) and remains unresolved in v2.

### C4. `if-floor` and `panic-training` still missing from panel catalog implementation (Principal 8, Designer 5)

The default athlete Health tab layout includes `if-floor` and `panic-training`. The panel catalog lists them under Health (`IFFloor.tsx`, `PanicTraining.tsx`). The file structure section includes `IFFloor.tsx` and `PanicTraining.tsx` under `src/panels/health/`. However, there is no specification of what these panels render, which store keys they depend on, or which API endpoint they call. The `dataKeys` field in `PanelDef` is left undefined for these two panels. They will render as error boundaries on first load.

### C5. Vite dev proxy leaks auth token to browser memory and dev tools (Principal 2, Security HIGH-1)

The typed API client stores the bearer token as `const token = ...` in `src/api/client.ts`. In Vite dev mode, this is a hot-module-replacement module that can be inspected via browser devtools. More critically, the spec gives no guidance on where the token comes from (env var? config file? hardcoded?). If sourced from `import.meta.env.VITE_TOKEN`, it is bundled into the static build and visible in the dist output. The Principal adds: the `fetchApi` function sends `Authorization: Bearer ${token}` on every request including preflight — the token travels in plain text on localhost, which is acceptable, but the storage mechanism needs specification.

### C6. No migration path from the existing JS dashboard (Principal 4, Designer 2)

The spec describes a `frontend-v2/` directory alongside the existing `frontend/`. There is no cutover plan: which URL serves which? Does `frontend-v2/` completely replace `frontend/`, or do they coexist? The Principal notes that the existing `frontend/js/dashboard.js` (1,250 lines per P3 review) has existing users who depend on it. The Designer observes that during the migration period, coach and athlete may be on different versions. No feature flag, redirect, or parallel-run plan is specified.

### C7. React + D3 ownership conflict (Principal 1, Designer 9)

The spec uses React for all panels but D3.js v7 for chart rendering, with `ChartContainer.tsx` as a `ResizeObserver` wrapper. This is a well-known conflict: D3 wants to own the DOM, React wants to own the DOM. The spec does not define the integration strategy. Both reviewers have seen this cause subtle bugs in production (stale closures on re-render, ResizeObserver callback triggering re-mount, D3 selection surviving React unmount). The spec should declare one of: (a) React-controlled D3 (use D3 for math only, React for rendering), or (b) D3-controlled DOM within a `useEffect` ref, with explicit cleanup.

### C8. Calendar tab and custom chart builder are Phase 3 — but their store keys are in Phase 1 (Principal 6, Designer 6)

The Zustand store shape includes `rides: Record<number, RideDetail>` and `routes: RouteListItem[]` which are needed for the calendar and custom builder. Phase 1 specifies fetching these lazily. However, the store also includes `performanceTrend: PerformanceTrendRow[]` which has no corresponding Phase 1 panel. Including future-phase keys in the Phase 1 store shape creates dead store fields and confuses the Phase 1 test surface. Both reviewers recommend separating the store into core (Phase 1) and extended (Phase 2+) slices, matching the Zustand slice pattern the spec already implies.

---

## 2. Conflicts and Disagreements

### D1. dnd-kit vs. SortableJS

The spec specifies dnd-kit. The P3 review recommended SortableJS. The v2 spec correctly overrides this: dnd-kit is purpose-built for React, has full TypeScript support, and handles accessibility natively. SortableJS is better for vanilla-JS contexts. dnd-kit is the right call for a React+TypeScript app. **No conflict — spec is correct.**

### D2. Auth bug status

The P3 review flagged `auth.py` lines 16-17 as fail-open. The current `auth.py` now raises `HTTPException(status_code=503)` when `_token is None` — the bug is fixed. Security Engineer notes that `auto_error=False` on `HTTPBearer` means unauthenticated requests get `credentials=None` passed through to `verify_token`, which correctly handles it. **Resolved in codebase — no action needed.**

### D3. localStorage vs. backend layout storage

The v2 spec already adopts localStorage (resolving the P3 D1 conflict): `localStorage keyed by user slug: wko5-layout-{user}`. Security Engineer accepts this. Principal accepts this. Designer notes it prevents cross-device sync — acceptable for a local-first tool. **Consensus: localStorage is correct for current deployment model.**

### D4. Severity of MCP server exposure

Principal rates MCP port exposure as HIGH (architectural risk). Security rates it CRITICAL (active attack surface). The difference: Principal focuses on developer workflow risk (stale state), Security focuses on network attack surface (SSRF, process injection). Both agree auth is needed; they disagree on whether `localhost`-only binding is sufficient mitigation.

**Resolution:** Localhost binding is necessary but not sufficient. The MCP server should also require a session token that the dashboard generates at startup and passes to Claude Code via a secure channel (not the `.mcp.json` which may be committed to the repo). This satisfies both reviewers.

### D5. D3 integration approach

Principal prefers D3-math-only / React-renders-SVG (approach a). Designer has no preference but wants smooth animations. Approach (a) loses D3's built-in transition system; approach (b) retains it but requires careful `useEffect` discipline. For a cycling analytics tool where chart smoothness matters for readability (PMC, MMP curve), approach (b) with strict cleanup discipline is preferable. **Recommend approach (b) with documented cleanup contract in `ChartContainer.tsx`.**

---

## 3. Prioritized Action List

All findings from all three reviews, deduplicated and ranked. P0 = must resolve before implementation begins. P1 = must fix during Phase 1. P2 = should fix before Phase 2. P3 = nice to have.

| # | Pri | Finding | Source | Action |
|---|-----|---------|--------|--------|
| 1 | P0 | MCP server has no auth — any localhost process can read all metrics and mutate dashboard state | C1, Security CRITICAL-1 | Add session token: dashboard generates UUID at startup, passes to Claude Code via env var or secure IPC. MCP server validates token on each call. |
| 2 | P0 | No migration cutover plan — `frontend-v2/` and `frontend/` coexist with no routing strategy | C6, Principal 4 | Define: (a) `frontend-v2/` replaces `frontend/` at same URL, with a `?legacy=1` escape hatch, OR (b) new port/path for v2 during development. Specify in spec before implementation. |
| 3 | P0 | D3 + React DOM ownership is undefined — will cause production bugs | C7, Principal 1 | Choose approach (b): D3 owns DOM in `useEffect` ref with `return () => d3.select(ref.current).selectAll('*').remove()` cleanup. Document this contract in `ChartContainer.tsx` header comment. |
| 4 | P0 | `GlycogenBudget` and `OpportunityCost` have no input form design — cannot render as passive panels | C3, Principal 7 | Either: (a) design input form component (ride_kj, carbs, weight, route selector), or (b) defer these two panels to Phase 2. Cannot ship Phase 1 with panels that immediately error. |
| 5 | P1 | `loading: boolean` in store is defined but never specified — which panels observe it? | C2, Designer 4 | Replace single `loading` bool with per-key loading map: `loading: Record<string, boolean>`. Each panel checks `loading['fitness']`. Document in store shape section. |
| 6 | P1 | Panel loading state — no skeleton/spinner specified for null store data | C2, Designer 4 | Add `PanelSkeleton` component to `shared/`. `PanelWrapper` renders skeleton when `dataKeys` have `loading[key] === true`. |
| 7 | P1 | `IFFloor.tsx` and `PanicTraining.tsx` have no spec: no store keys, no endpoint, no render description | C4, Principal 8 | Define both panels: endpoint, store key, render logic. Or remove from default Health tab layout and add to catalog as "coming soon." |
| 8 | P1 | Token storage mechanism unspecified — env var vs. config file vs. hardcoded, with bundling implications | C5, Principal 2 | Specify: token comes from `localStorage('wko5-token')` set via a login-once flow, OR from `VITE_API_TOKEN` env var (document: never commit `.env`). |
| 9 | P1 | MCP server port is unspecified — hardcoded? Configurable? Discoverable? | Security HIGH-2 | Add `MCP_PORT` to `tools/mcp-dashboard/` config. Default to a non-standard port (not 3000, 8080). Document in README. |
| 10 | P1 | `get_all_metrics()` MCP tool returns entire Zustand store — excessive data exposure | Security MEDIUM-1 | Scope to `{ fitness, clinicalFlags, activeTab, visiblePanels }`. Remove `rides` (contains full activity records) and `routeDetail` from MCP output. |
| 11 | P1 | Phase 1 Zustand store includes Phase 3 keys (`performanceTrend`, `routes`, `routeDetail`) | C8, Principal 6 | Split into `useCoreStore` (Phase 1: fitness, pmc, clinicalFlags, profile, config) and `useExtendedStore` (Phase 2+). Merge at `App.tsx` level. |
| 12 | P2 | No `Cancel` behavior for Edit Mode is incomplete — spec says "Cancel restores snapshot" but `EditMode.tsx` has no undo state design | Designer 3 | Add explicit: `layoutSnapshot: Layout \| null` to Zustand store. Set on edit mode enter, restore on Cancel, clear on Done. |
| 13 | P2 | Plotly.js (Phase 3 custom builder) and D3.js both in bundle — ~500KB overlap in rendering primitives | Principal 9 | Accept for Phase 3 (Plotly is specified as-is). Note in spec: custom builder panels are lazy-loaded via React.lazy to avoid bundle impact on Phase 1. |
| 14 | P2 | `warmup-status` endpoint has no auth — exposes internal timing and error details | Security LOW-1 | Add auth or strip error details from unauthenticated response. Current: `"warmup_errors": {"clinical": "connection refused"}` leaks internals. |
| 15 | P2 | No rate limit or debounce on `refresh()` store action | Principal 10 | Add 30-second debounce on manual refresh. Auto-refresh (if any) should use a configurable interval, not fire on every tab focus. |
| 16 | P2 | `highlight_chart()` MCP tool has no persistence model — annotation disappears on re-render | Designer 7 | Add `annotations: Record<panelId, Annotation[]>` to Zustand store. `highlight_chart()` writes to store. `ChartContainer` reads from store. Cleared on `refresh()`. |
| 17 | P2 | No validation on tab label rename — empty, duplicate, >20 chars | Designer 10 | Add `validateTabLabel(label: string): string \| null` returning error message. Enforce in `EditMode.tsx`. |
| 18 | P2 | CSS Modules + CSS custom properties gives no theming system for D3 charts — D3 will use hardcoded colors | Designer 11 | Export theme tokens as JS constants from `src/shared/theme.ts` (read from CSS custom properties at runtime). D3 charts import from `theme.ts` not hardcode hex values. |
| 19 | P3 | Coach URL routing (`/coach/elena`, `/athlete/jshin`) — no 404 for unknown slugs | Principal 11 | Add slug validation: if slug not in known athletes list, redirect to default. Or defer URL-based identity entirely to Phase 2. |
| 20 | P3 | `xterm.js` bundle size (~250KB) impacts Phase 2 initial load | Principal 12 | Lazy-load `ChatPanel.tsx` via `React.lazy()`. Terminal only instantiates when panel is opened. |
| 21 | P3 | Panel `description` field in `PanelDef` is defined but not used anywhere in the spec's component code | Designer 12 | Show description in catalog modal tooltip/subtitle. Implement in add-panel catalog modal. |
| 22 | P3 | No "Reset to default" confirmation dialog — one click destroys custom layout | Designer 13 | Add confirmation: "Reset to default athlete layout? This cannot be undone." |

---

## 4. Open Questions

The spec author should resolve these before Phase 1 implementation begins.

**Q1. D3 integration strategy.** Which approach: React renders SVG (D3 math-only) or D3 owns DOM in `useEffect` refs? This decision affects every chart component and must be made before any chart is written.

**Q2. MCP session token protocol.** How does the dashboard pass the MCP session token to Claude Code? Options: (a) Write to a temp file that Claude Code reads via an MCP tool, (b) Environment variable set in Claude Code's launch command, (c) stdin on startup. Each has different security properties.

**Q3. `IFFloor` and `PanicTraining` panels — what do they render?** These appear in the default Health layout but have no spec. Are they existing panels being promoted from the current JS dashboard, or new designs? If existing, document which current JS file implements them.

**Q4. Frontend v2 cutover strategy.** Does `frontend-v2/` run on a different port during development, or does it replace `frontend/` at the same port? What is the rollback plan if v2 has regressions?

**Q5. Token sourcing.** Where does the API bearer token come from in the React app? This determines the security model for the entire frontend. Options: env var (bundled into dist), localStorage (set at runtime), or session management. Each has different implications.

**Q6. `GlycogenBudget` ride data source.** Does this panel use post-ride data (actual ride metrics from the store), pre-ride planning (user inputs estimates), or both? If post-ride, which store key contains the needed fields? If pre-ride, an input form is required.

**Q7. Annotation persistence across refresh.** When Claude calls `highlight_chart()`, should the annotation survive a page refresh? If yes, annotations must be stored in localStorage with an expiry. If no, they are cleared on refresh — document this behavior for users.

---

## 5. Implementation Cost Estimate

### Files Created (Phase 1)

| Category | New Files | Notes |
|----------|-----------|-------|
| Scaffold | `vite.config.ts`, `tsconfig.json`, `package.json`, `index.html` | One-time setup |
| API layer | `src/api/client.ts`, `src/api/types.ts` | ~34 typed functions, ~50 interfaces |
| Store | `src/store/data-store.ts` | Zustand store + actions |
| Panel components | ~30 `.tsx` files across 6 category folders | Port existing render logic |
| Layout engine | `LayoutEngine.tsx`, `EditMode.tsx`, `PanelRegistry.ts`, `PanelWrapper.tsx` | Core system — highest risk |
| Shared | `Metric.tsx`, `DataTable.tsx`, `ChartContainer.tsx`, `PanelSkeleton.tsx` | Reusable primitives |
| App shell | `App.tsx`, `main.tsx` | Routing, theme, store init |
| **Phase 1 total** | **~45 new files** | |

### Files Created (Phase 2)

| Category | New Files | Notes |
|----------|-----------|-------|
| MCP server | `tools/mcp-dashboard/server.ts`, `mcp.json` | IPC surface — requires security review |
| Chat panel | `src/chat/ChatPanel.tsx` | xterm.js integration |
| **Phase 2 total** | **~3 new files** | Plus npm dependencies: `xterm`, `@modelcontextprotocol/sdk` |

### Files Modified (Phase 1)

No existing backend files need modification for Phase 1. The backend already has all required endpoints; `warmup_cache()` already includes `ftp_growth` and `rolling_pd`. Auth is fixed. The frontend rewrite is greenfield in `frontend-v2/`.

### Integration Surfaces (where things break)

1. **D3 + React in `ChartContainer.tsx`** — Highest architectural risk. Every D3 chart must follow the same pattern. One inconsistency (e.g., a chart that doesn't clean up its selection on unmount) causes ghost SVG nodes and double-render bugs that are hard to reproduce.

2. **Zustand store startup sequence** — `fetchCore()` runs in parallel, but panels must handle `null` gracefully until data arrives. Any panel that does `fitness.TSB` without null-checking will crash the error boundary on mount. A full audit of all panel components against the `null` store state is required before Phase 1 exit.

3. **dnd-kit layout engine** — Panel reorder within a tab is straightforward. Tab reorder is more complex (nested DnD contexts). The spec mentions "Add/remove/rename tabs" in Edit Mode — these are three distinct interaction patterns that dnd-kit handles differently.

4. **MCP bridge <-> Zustand store** — The MCP server needs read access to the Zustand store without being a React component. The standard pattern is to use Zustand's `getState()` outside React. This works but the MCP server (`tools/mcp-dashboard/server.ts`) is a separate Node.js process — it cannot call `getState()` directly. It needs a message channel (WebSocket, EventEmitter, or shared state file). The spec says the bridge "runs as a sidecar process" but does not specify the IPC mechanism from MCP server to Zustand store.

5. **Vite proxy to FastAPI** — Dev proxy is well-understood. Production build requires a reverse proxy (nginx, Caddy) or serving from FastAPI's static file handler. The spec does not address the production serving strategy, which affects how the bearer token flows.

### Suggested Implementation Order

| Phase | Work | Estimated Complexity | Blocks |
|-------|------|---------------------|--------|
| **0. Decisions** | Resolve Q1 (D3 strategy), Q4 (cutover), Q5 (token source), Q7 (annotations). Fix C3 (design GlycogenBudget/OpportunityCost forms or defer). | 1 day design | Everything |
| **1a. Scaffold** | Vite + React + TS + Zustand + dnd-kit. Proxy to FastAPI. Token wired. All panels show "placeholder". | Low | 1b |
| **1b. API + Store** | `client.ts`, `types.ts`, `data-store.ts`. `fetchCore()` + `fetchSecondary()` wired. | Medium | 1c |
| **1c. Panel skeleton** | `PanelWrapper`, `PanelSkeleton`, `PanelErrorBoundary`, loading states. | Low | 1d |
| **1d. Layout engine** | `LayoutEngine`, `PanelRegistry`, localStorage persistence. Tabs render from config. | Medium | 1e |
| **1e. Panel components** | Port all ~30 panels from existing JS. D3 charts follow `ChartContainer` contract. | High — most labor | 1f |
| **1f. Edit mode** | `EditMode.tsx` + dnd-kit integration. Add/remove/rename tabs. Cancel/Done flow. | Medium | — |
| **2. MCP bridge** | Design IPC (WebSocket from React → MCP server → Claude Code). Auth token. `highlight_chart` → Zustand annotation store. | High — new surface | 3 |
| **3. Calendar + Builder** | Phase 3. Do not start until Phase 2 is stable. | Medium | — |

### Risk Summary

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| D3+React DOM conflict causes ghost SVG nodes | High | Medium | Strict `ChartContainer` cleanup contract; PR checklist item for every D3 component |
| MCP IPC mechanism undefined — Phase 2 blocked | High | High | Resolve Q2 before Phase 2 begins; prototype IPC in isolation first |
| `GlycogenBudget`/`OpportunityCost` ship as error-boundary panels | Near-certain if unaddressed | Medium | Defer or design input forms before Phase 1 exit |
| Panel null-state crashes on startup | High | Low | Add null-state audit to Phase 1 exit criteria |
| Token in static dist bundle | Medium if env var used | Medium | Use runtime token (localStorage), not build-time env var |
| xterm.js + Claude Code session lifecycle | Unknown | High | Prototype Phase 2 terminal in isolation before integrating with MCP |

---

<details>
<summary>Principal Engineer Review (full text)</summary>

## Principal Engineer Review: WKO5 Dashboard v2 Full Frontend Rewrite

**Reviewer role:** Principal Full-Stack Engineer (IC7/IC8), 25+ years shipping production systems. Direct, surgical, pragmatic.

**Files read:** `docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md`, `wko5/api/routes.py`, `wko5/api/auth.py`

---

### 1. Architectural Risks

**AR-1. React + D3 DOM ownership conflict is the highest architectural risk in the spec.**

The spec specifies D3.js v7 for chart rendering and React 18 for all components. The `ChartContainer.tsx` is described as a "D3 chart wrapper with resize observer." This setup requires a disciplined integration strategy: D3 must own the DOM within its container (via `useEffect` and a ref), React must never touch that DOM subtree, and the D3 selection must be explicitly destroyed on unmount.

The spec does not specify this. A developer implementing `PMCChart.tsx` without this guidance will do something like:

```tsx
// Anti-pattern — React re-renders will conflict with D3 updates
return <svg ref={ref} />;
// ...
useEffect(() => {
  d3.select(ref.current).append('g')... // leaks on re-render
}, [data]);
```

Without an explicit cleanup strategy (`return () => d3.select(ref.current).selectAll('*').remove()`), every hot-module reload and React strict-mode double-mount will produce ghost SVG nodes. This will manifest as intermittent "double chart" bugs that are difficult to reproduce and hard to debug in production.

**Action:** Before any chart component is written, establish and document the `ChartContainer` contract in `src/shared/ChartContainer.tsx`. The contract should be: D3 owns DOM inside the container, useEffect with full cleanup is mandatory, and a code example is provided in the component header.

---

**AR-2. MCP bridge IPC mechanism is unspecified but is the load-bearing piece of Phase 2.**

The spec describes a "lightweight MCP server (Node.js or Python) that the dashboard runs locally" and that "Claude Code connects to it via `.mcp.json`." The MCP server exposes `get_all_metrics()` which returns "a snapshot of the entire Zustand store."

Problem: the MCP server is a separate process (`tools/mcp-dashboard/server.ts`). It cannot import `useDataStore` — that's a React hook. To read Zustand state from outside React, the store must use `store.getState()` (Zustand supports this). But the MCP server is not in the same process as the React app.

The IPC must be one of:
- WebSocket from React app to MCP server (dashboard pushes state on change)
- Shared state file written by React app, read by MCP server (polling or inotify)
- HTTP endpoint on the React dev server proxying store reads (complex, couples Vite to MCP)

None of these is specified. This is not a detail — it is the architecture of Phase 2. The spec cannot be implemented as written without resolving this.

**Action:** Add an "MCP IPC Design" section to the spec. Recommend WebSocket: React app connects to MCP server WebSocket on startup, sends store snapshot on each relevant state change, MCP server holds latest snapshot in memory. This is simple, reliable, and testable in isolation.

---

**AR-3. MCP server has no authentication — any localhost process can call all tools.**

The MCP server binds to a local port (unspecified in spec). There is no session token, no process identity check, no allowlist. A malicious npm package in the project's `node_modules` (or any process running as the same user) can call `get_all_metrics()` and extract the full athlete dataset, or call `highlight_chart()` to inject misleading annotations.

This is not a theoretical risk. The Claude Code terminal itself runs tools from the project directory — any `./tools/*.sh` script could make HTTP calls to the MCP server.

**Action:** The dashboard should generate a UUID session token at startup, write it to an environment variable passed to Claude Code's process, and the MCP server should validate this token on every request. This adds one line to each MCP tool handler and closes the attack surface.

---

**AR-4. Startup loading state is underspecified — panels will silently show nothing.**

The store initializes with `fitness: null`, `pmc: []`, `clinicalFlags: null`. The `TSBStatus` example in the spec returns `null` when `fitness` is null. On a cold start (before `fetchCore()` completes), the entire active tab renders empty panels.

The spec defines `loading: boolean` in the store shape but never specifies when it transitions to `true` or `false`, or which panels observe it. The `PanelErrorBoundary` handles thrown errors, not loading state.

This means: on first load, the user sees a dashboard full of blank panels for 1-3 seconds (depending on backend response time). On a slow machine or a cold FastAPI startup, this could be 5-10 seconds of blank panels.

**Action:** Replace `loading: boolean` with `loading: Record<string, boolean>` keyed by store key (matching `DataStore` field names). `fetchCore()` sets `loading.fitness = true` before the fetch, `false` after. `PanelWrapper` checks `loading[dataKeys[0]]` and renders `<PanelSkeleton />` if true. This is a 2-hour implementation change that dramatically improves perceived performance.

---

**AR-5. Phase 1 store includes Phase 3 data shapes — pollutes the contract.**

The Zustand store shape in the spec includes `rides: Record<number, RideDetail>`, `routes: RouteListItem[]`, `routeDetail: Record<number, RouteDetail>`, and `performanceTrend: PerformanceTrendRow[]`. Phase 1 has no panel that uses `performanceTrend`. Calendar (Phase 3) uses `rides`. Custom chart builder (Phase 3) uses `routes`.

Including these in Phase 1 means: Phase 1 tests need to account for these keys, TypeScript types need to be defined upfront for Phase 3 data shapes, and the store initialization is larger than needed.

**Action:** Split into `useCoreStore` (Phase 1 keys) and `useExtendedStore` (Phase 2+). Both can be merged in `App.tsx` for convenience, but the split makes Phase 1 easier to test and reason about.

---

**AR-6. `GlycogenBudget` and `OpportunityCost` panels have no input mechanism.**

`GlycogenBudget` requires: `ride_kj`, `ride_duration_h`, `on_bike_carbs_g`, `body_weight_kg`. The spec lists this panel under "Event Prep" and says it is "fetched when user navigates to them." But the store has no key for glycogen budget parameters — they are not derived from existing store data.

`OpportunityCost` requires `route_id` from `GET /opportunity-cost/{route_id}`, but the spec lists no route selection UI in Phase 1. The `RouteSelector.tsx` panel is the selector, but its interaction with `OpportunityCost.tsx` is unspecified.

Both panels will render as empty error boundaries in Phase 1 unless input forms are designed.

**Action:** Either (a) design the input forms as part of the panel spec (what fields, what defaults, what validation), or (b) explicitly defer these panels to Phase 2 and remove them from the Phase 1 exit criteria.

---

**AR-7. `if-floor` and `panic-training` panels are listed in the default layout but have no implementation spec.**

The Health tab default includes `if-floor` and `panic-training`. The file structure lists `IFFloor.tsx` and `PanicTraining.tsx`. The panel catalog lists them. But no section of the spec describes what these panels render, which API endpoint they call, or what store keys they depend on.

In the P3 review, these same panels were flagged as missing from the registry. They remain unspecified in v2.

**Action:** Add a subsection for each panel under "Panel Catalog" specifying: endpoint, store key, render description, empty state. If they are ports of existing JS panels, cite the source file.

---

**AR-8. No frontend migration plan — `frontend-v2/` and existing `frontend/` coexist with undefined routing.**

The spec creates a `frontend-v2/` directory. The existing dashboard is in `frontend/`. No cutover strategy is specified. During development, which URL serves which? The Vite dev server serves `frontend-v2/` on (presumably) port 5173. The existing FastAPI server serves `frontend/` as static files. These can coexist, but the spec should document:

- Dev: two servers (`npm run dev` for v2, existing FastAPI for v1)
- Production: when does `frontend-v2/` replace `frontend/` at the primary URL?
- Rollback: if v2 has regressions, how is v1 restored?

Without this, the implementation team will make ad-hoc decisions that may conflict with the spec's intent.

---

**AR-9. Plotly.js and D3.js in the same bundle — ~500KB of rendering libraries.**

Phase 3 adds Plotly.js for the custom chart builder. D3.js is already in Phase 1. Together, minified: D3 v7 (~250KB), Plotly.js (~3.5MB, or ~900KB for the dist/plotly-basic bundle). This is a significant initial load for a local tool, but becomes a problem if the app is ever deployed.

**Action:** Document in the spec that `CalendarView.tsx` and the custom chart builder components are loaded via `React.lazy()` and `Suspense`. Phase 1 and 2 users pay no cost for Phase 3 code until they navigate to Phase 3 panels.

---

**AR-10. Token sourcing for `fetchApi` is unspecified — has security implications.**

`src/api/client.ts` uses `Authorization: Bearer ${token}`. Where does `token` come from? If `import.meta.env.VITE_API_TOKEN`, it is embedded in the compiled bundle — anyone who downloads the built app can extract it. If from `localStorage`, it requires a "first-time setup" flow not described in the spec. If hardcoded, it's a credential in version control.

**Action:** Specify: token is stored in `localStorage('wko5-api-token')`. On first load, if not set, show a token entry modal. This is a one-time setup for a local tool and avoids all bundling concerns.

---

**AR-11. Coach URL routing has no auth — `/athlete/jshin` and `/coach/elena` differ only by path.**

The spec describes URL-based identity: `/athlete/jshin` loads the athlete layout for jshin, `/coach/elena` loads the coach layout for elena. These are served to anyone who knows the URL — there is no additional auth beyond the bearer token.

This is acceptable for a local tool. However, the spec should acknowledge: the bearer token does not verify which user is requesting which layout. Any authenticated client can access any URL path and see any layout.

**Action:** Add a note to the "Coach Layer" section: "URL-based identity is for layout differentiation only. Auth is enforced by the bearer token at the API level. The frontend trusts the URL slug as a layout key, not as a user identity claim."

---

**AR-12. `warmup_cache()` already covers `ftp_growth` and `rolling_pd` — no action needed.**

The P3 review recommended adding these to warmup. Checking `routes.py` lines 102-103: both `ftp_growth` and `rolling_pd_profile` are already in `warmup_cache()` tasks. This item from the P3 review is resolved.

---

### 2. Over-Engineering Concerns

**OE-1. The Zustand store slice for Phase 3 data is premature.** Including `performanceTrend`, `rides`, `routes`, `routeDetail` in the Phase 1 store definition is speculative. Define these in Phase 2/3 when needed.

**OE-2. `dataKeys: string[]` in `PanelDef` is a good idea but needs a runtime enforcement mechanism.** Listing `dataKeys` as metadata is only useful if something validates that the listed keys exist in the store. Without a runtime check or TypeScript enforcement, this becomes documentation that drifts from implementation.

---

### 3. Missing Pieces

- No test strategy for React components. The spec mentions the existing 214 backend tests but says nothing about frontend testing. At minimum: what is the test framework (Vitest + Testing Library?), and what is the coverage expectation?
- No error recovery strategy beyond "retry button." If `fetchCore()` fails completely, what does the user see? An empty dashboard with a retry button? A full-page error?
- No service worker / offline plan — acceptable for v1, but should be explicitly out of scope.

---

### 4. Sequencing Issues

**SE-1.** The D3 + React integration decision (AR-1) must be made before the first chart is written. If not resolved at the start, the first chart component sets the de-facto standard and later components follow it — correct or not.

**SE-2.** The MCP IPC mechanism (AR-2) must be prototyped before Phase 2 begins. Building Phase 2 panels while the IPC is undefined will produce a Phase 2 that cannot be wired to Claude Code.

**SE-3.** `PanelWrapper` + `PanelSkeleton` + `PanelErrorBoundary` must exist before any panel component is written, so that every panel is wrapped correctly from the start.

---

### 5. Feasibility Assessment

**Phase 1 is feasible.** The React + TypeScript + Zustand + dnd-kit stack is well-understood. The 34 existing backend endpoints have clean response shapes (captured in Appendix A). Porting ~30 panel components from the existing JS dashboard is labor-intensive but not architecturally risky — most panels are just data display.

**Highest-risk items in Phase 1:**
- D3 + React integration (every chart component)
- `LayoutEngine.tsx` + dnd-kit nested context for tab reorder
- `EditMode.tsx` cancel/restore snapshot flow

**Phase 2 is feasible but requires the MCP IPC to be designed first.** xterm.js + Claude Code session management has known integration points. The MCP server protocol is well-documented. The IPC between React Zustand store and MCP server process is the novel piece.

**Phase 3 is feasible and lower risk** — calendar is a standard date grid, custom chart builder is Plotly configuration UI.

**Implementation complexity estimate:** Phase 1: 4-6 weeks for a single developer using AI agents. Phase 2: 2-3 weeks. Phase 3: 2-3 weeks. Total: 8-12 weeks.

---

### 6. Concrete Recommendations (ranked by impact)

**R1 (P0): Define the D3+React contract in `ChartContainer.tsx` before writing any chart.** Highest-leverage decision. One page of documentation prevents weeks of debugging.

**R2 (P0): Add MCP IPC design to the spec.** Recommend WebSocket. Unblocks Phase 2.

**R3 (P0): Add MCP session token.** Dashboard generates UUID at startup, passes to Claude Code via env var. MCP server validates per-call.

**R4 (P0): Fix `frontend-v2/` cutover strategy.** Spec: v2 runs on port 5173 during dev, replaces `frontend/` at existing URL when Phase 1 exits criteria are met.

**R5 (P1): Replace `loading: boolean` with `loading: Record<string, boolean>`.** Per-key loading state enables per-panel skeleton rendering.

**R6 (P1): Either design `GlycogenBudget`/`OpportunityCost` input forms or defer panels.** Cannot ship as passive panels — they have no static data source.

**R7 (P1): Specify `IFFloor` and `PanicTraining` panel implementations.** Or remove from default layout.

**R8 (P2): Split store into Phase 1 and Phase 2+ slices.** Cleaner test surface for Phase 1.

**R9 (P2): Lazy-load Phase 3 components** (`CalendarView`, custom chart builder, `ChatPanel`) via `React.lazy()`.

**R10 (P2): Specify token storage mechanism** — recommend `localStorage('wko5-api-token')` with first-run modal.

</details>

<details>
<summary>Product Designer Review (full text)</summary>

## Product Designer Review: WKO5 Dashboard v2 Full Frontend Rewrite

**Reviewer role:** World-class Product Designer (IC6/IC7), 20+ years across consumer products, B2B SaaS, developer tools, AI-powered interfaces. Focus: the experience of coach + athlete reviewing training data.

**File read:** `docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md`

---

### 1. UX Strengths

**S1. The Zustand selector pattern is exactly right for this dashboard.** "PMC chart doesn't re-render when flags change" — this is the right instinct. A coach reviewing a PMC trend should not see chart jitter when the clinical flags panel updates. Slice-based subscriptions prevent this class of visual noise.

**S2. The panel catalog architecture solves the right problem.** Grouping panels by category (status, health, fitness, event-prep, history, profile) matches how coaches and athletes mentally organize training data. The catalog-first model (panels exist in the registry before they exist in any layout) is the correct separation of concerns.

**S3. Error boundaries per panel are correct for clinical data.** If `ClinicalFlags.tsx` errors, the rest of the dashboard should continue working. An athlete should not lose their PMC chart because a clinical endpoint is down. Per-panel error boundaries are the right call.

**S4. LocalStorage layout persistence resolves the P3 identity problem cleanly.** Using `wko5-layout-{user}` slug keying is simple, correct for the current 2-user case, and avoids all the credential-at-rest problems from the P3 backend layout approach.

**S5. The MCP bidirectional flow is the most interesting design in the spec.** "User looks at PMC chart, types 'why did my CTL drop in February,' Claude highlights the region" — this is a genuinely novel interaction for a sports analytics tool. The flow is well-described and the tool surface (`highlight_chart`, `show_panel`, `set_time_range`) is appropriately scoped.

---

### 2. UX Concerns

**UC-1. No loading state means the dashboard appears broken on first load.**

The store initializes empty. `TSBStatus` returns `null` when `fitness` is null. On startup, the user sees a set of blank panels for 1-3 seconds. For a coach reviewing an athlete's data in a meeting, this is embarrassing. For an athlete with high cognitive load (just finished a hard week), blank panels read as "the app is broken."

The spec defines `loading: boolean` but does not wire it to any panel behavior. There is no skeleton component specified.

**Recommendation:** Every panel must have three states: loading (skeleton), data (normal render), error (error boundary with retry). The skeleton should mirror the panel's shape — the PMC chart skeleton is a rectangle with shimmer, the TSB status skeleton is three metric cards with shimmer. This is a 1-2 hour implementation per panel category and is essential for perceived performance.

---

**UC-2. Edit mode's Cancel/Done flow needs explicit state design.**

The spec says "Cancel restores snapshot." This implies a snapshot is taken when Edit Mode is entered. But where is this snapshot stored? If it's in local component state (`useState` in `EditMode.tsx`), it will be lost on hot-module reload. If it's in Zustand, it needs a `layoutSnapshot` key.

The UX implication: if a coach is customizing the athlete layout, accidentally removes a panel, and then presses Cancel, the layout should restore exactly. If the snapshot is in component state and the page reloads (or Vite HMR fires), Cancel will have nothing to restore.

**Recommendation:** Store `layoutSnapshot: Layout | null` in Zustand. Set it to the current layout when Edit Mode is entered (`gear icon → set snapshot → enter edit mode`). Cancel copies snapshot back to active layout. Done clears snapshot and saves to localStorage. This also enables a "Compare to original" view if desired later.

---

**UC-3. The Health tab has five panels with no visual hierarchy.**

The default Health layout: `[clinical-flags, if-distribution, if-floor, panic-training]`. These are presented in a flat list with no hierarchy signal. `clinical-flags` is the most urgent panel (it contains actual health alerts) but has no visual priority over `if-distribution` (a statistical chart).

For coach + athlete clinical review, the hierarchy must be explicit: clinical alerts first, full-width, with color coding (red/yellow/green) prominent. Distribution charts are secondary — useful for context but not urgent.

**Recommendation:** Specify `clinical-flags` as a full-width panel at the top of the Health tab by default. `if-distribution`, `if-floor`, and `panic-training` are below, in a 3-column grid. This is a layout configuration change, not a code change.

---

**UC-4. `IFFloor` and `PanicTraining` have no description in the spec.**

These panels appear in the default Health tab layout but are never described. A coach reviewing the Health tab will see two unnamed panels (or panels rendering their `label` field without explanation). The add-panel catalog modal uses the `description` field in `PanelDef` — but these panels have no documented description.

For a clinical panel — one that a coach might use to make training decisions — "I have no idea what this panel means" is a serious usability failure.

**Recommendation:** Document both panels fully in the spec. If `if-floor` is "the intensity factor floor below which rides are considered recovery," say so in the panel description. If `panic-training` is "sessions where IF exceeded target zone," say so. These descriptions must appear in the catalog modal.

---

**UC-5. No "Ask Claude about this panel" button in the spec — but the flow is described.**

The spec describes the MCP flow: user looks at PMC chart, opens Claude panel, types "why did my CTL drop." But there is no "Ask Claude about this" button on individual panels. The user has to (a) open the Claude panel, (b) type their question, (c) Claude infers which panel they're looking at.

This is a significant friction point. The spec mentions "Ask about this context buttons on panels" under Phase 2 exit criteria, but does not spec the interaction: where is the button (title bar? hover overlay?), what does it inject into the Claude conversation, and does it automatically call `get_panel_data(panelId)`?

**Recommendation:** For Phase 2, add a `?` or "Ask Claude" button to `PanelWrapper`'s title bar. On click: open Claude panel if closed, inject `[PMCChart context: {panel data snapshot}] User question:` as pre-text. This makes the MCP flow discoverable without requiring the user to know about `get_panel_data`.

---

**UC-6. `GlycogenBudget` is the most useful panel for pre-ride planning — but it requires input.**

The glycogen budget panel requires `ride_kj`, `ride_duration_h`, `on_bike_carbs_g`, `body_weight_kg`. These are planning inputs, not historical data. An athlete preparing for a long ride needs to enter these values and see the budget output.

As a passive panel (no input form), `GlycogenBudget` will immediately enter the error boundary state when the user opens Event Prep — because there is no data in the store to feed it.

**Recommendation:** Design `GlycogenBudget` as a form-first panel: four input fields (with defaults from `AthleteConfig` for body weight), a Calculate button, and the output visualization. This is a distinct interaction pattern from the store-subscription panels, but it's the correct one for a planning tool.

---

**UC-7. Annotations from Claude — no persistence model, no dismiss behavior.**

When Claude calls `highlight_chart('pmc-chart', { type: 'region', ... })`, an annotation appears on the PMC chart. The spec does not say: how long does it persist? Does the user see it after navigating away and back? Can the user dismiss it? Can Claude add multiple annotations?

For coaching use: a coach might ask Claude to identify three training blocks in the PMC and annotate each. If annotations accumulate without a dismiss mechanism, the chart becomes unreadable after a few Claude interactions.

**Recommendation:** Annotations should persist in `annotations: Record<panelId, Annotation[]>` in Zustand. Each annotation has an id, so they can be dismissed individually. Add a "Clear annotations" button to the Claude panel (not to each chart — global clear is simpler). Annotations are cleared on `refresh()`.

---

**UC-8. The Embedded Terminal (xterm.js) has no keyboard trap handling.**

An embedded terminal captures all keyboard input when focused. If the user is in the Claude terminal and presses Tab, it should tab-complete in the terminal, not move focus to the next browser element. But if the user needs to leave the terminal (Escape, Shift-Tab, or a custom keybinding), the spec doesn't describe how.

For accessibility and keyboard navigation, this matters. A user who opens the Claude panel by keyboard and can't close it by keyboard is stuck.

**Recommendation:** Define the terminal focus/escape contract: Escape closes the Claude panel (and unfocuses the terminal) if the terminal is empty. Shift-Tab moves focus to the main dashboard. Document this in Phase 2 spec.

---

**UC-9. The Vite dev proxy and production serving — different base URLs break the API client.**

In dev: Vite proxies `/api` to FastAPI at `localhost:8000`. In production (static build): there is no proxy. `src/api/client.ts` uses a `baseUrl`. If `baseUrl` is relative (empty string), it works in both dev and prod only if FastAPI serves the built static files. If deployed separately (nginx serves frontend, FastAPI is on another host), the `baseUrl` must be configured.

This is not a UX issue per se, but it affects deployment UX (the engineer deploying the app). The spec should specify: `baseUrl` comes from `import.meta.env.VITE_API_BASE_URL`, defaulting to empty string (same-origin). Document in `vite.config.ts`.

---

**UC-10. No tab order validation — duplicate tab names are confusing.**

Edit mode allows adding and renaming tabs. There is no validation: a user could create two tabs named "Health" and then be confused about which is which. Tab IDs are slugs (presumably), but labels can be duplicated.

**Recommendation:** In `EditMode.tsx`, validate on tab rename and on Done: labels must be non-empty, ≤ 24 characters, and unique within the layout. Show an inline error if validation fails (don't silently fail).

---

**UC-11. The panel catalog modal needs more than just `label` and `category`.**

The panel catalog modal (add-panel) groups panels by category. `PanelDef` includes `description`. But the spec does not show how the modal is laid out. For a coach seeing 30+ panels in a catalog, just seeing "TSBStatus" and "Tracks CTL/ATL/TSB" is enough to make a decision. But "IFFloor" with an empty description is not.

**Recommendation:** Catalog modal: two-column layout. Left: category list. Right: panel cards (label, description, "Add" button). Description is mandatory before Phase 1 exit — a panel without a description blocks its addition to the catalog.

---

**UC-12. No "view as other user" for coach — lower priority but worth noting.**

The spec defers this to "Multi-Athlete (Future)." For a coach reviewing an athlete's layout during a meeting, being able to quickly switch to the athlete's persisted layout (without requiring the athlete to be present) is a common coaching workflow. This is a localStorage read: `localStorage.getItem('wko5-layout-jshin')` — it just requires the coach and athlete to be on the same machine.

**Recommendation:** For Phase 1, add a "View as: [athlete | coach]" toggle in the header that switches the active layout slug. No auth change needed — just reads a different localStorage key.

---

### 3. Design System Feedback

**DS-1. CSS Modules + CSS custom properties is the right choice for this project.** Scoped styles prevent accidental specificity conflicts across 30+ panel components. Custom properties enable dark/light theming. The theme token approach should be established early: `src/shared/tokens.css` defines all `--color-*`, `--spacing-*`, `--radius-*`, `--font-*` tokens.

**DS-2. D3 charts will not automatically use CSS custom properties.** D3 sets colors via JS (`.attr('fill', '#1a73e8')`). These hardcoded colors will not respond to the dark/light theme switch. Solution: export a `theme.ts` file that reads CSS custom property values at runtime (`getComputedStyle(document.documentElement).getPropertyValue('--color-primary')`). D3 charts import colors from `theme.ts`.

**DS-3. Typography is not specified.** The spec mentions "professional visual design matching analytics quality" but specifies no typeface. For a data-dense analytics dashboard, a monospace or tabular numeric font is important for metric alignment. Recommendation: `Inter` for UI, `JetBrains Mono` or `Roboto Mono` for metric values and numbers. Both are free and work at all screen densities.

**DS-4. No specified spacing scale.** Without a spacing scale, developers will use arbitrary pixel values (`margin: 13px`) that produce visually incoherent layouts. Recommendation: define an 8px base grid in `tokens.css`: `--space-1: 4px`, `--space-2: 8px`, `--space-3: 12px`, `--space-4: 16px`, `--space-6: 24px`, `--space-8: 32px`.

---

### 4. Information Architecture

**IA-1. The "Today" tab is the correct entry point.** TSB, recent rides, clinical alerts — this is the right information for a coach opening the dashboard before a training session. The hierarchy matches the coaching workflow: status first, then drill down.

**IA-2. "Event Prep" tab design has an identity problem.** The tab contains: `route-selector`, `segment-profile`, `demand-heatmap`, `gap-analysis`, `pacing`, `opportunity-cost`, `glycogen-budget`. This is seven panels for one event. The spec mentions "unified analysis view" but does not define it. How are these panels related? Is there a selected route that drives all of them? If yes, the route-selector panel should be sticky at the top of the tab, not one of seven equal peers.

**IA-3. Calendar tab is the most useful tab for a coach.** Weekly TSS, planned vs. completed, day-by-day view — this is how coaches monitor athlete compliance. Deferring it to Phase 3 is acceptable for an MVP, but it should be Phase 2 priority #1, not Phase 3 item #1 alongside the custom chart builder.

---

### 5. Workflow Gaps

**WG-1. No confirmation on layout reset.** "Reset to default preset" destroys a custom layout with one click. Add a confirmation dialog: "Reset to default athlete layout? Your custom layout will be lost."

**WG-2. No "panel added" feedback in catalog modal.** After clicking "Add" in the panel catalog, the modal should either close and scroll to the new panel, or show an "Added to [Tab Name]" confirmation in the modal. Currently, the user doesn't know if the action succeeded.

**WG-3. Panel removal — no confirmation, no "undo."** Clicking X on a panel removes it. If the user removes the wrong panel, there is no undo (unless they click Cancel in Edit Mode). The X button should require hover-then-click confirmation: on hover, the X turns red and the panel dims; on click, it removes. Or add an undo toast: "Removed PMCChart. [Undo]" with a 5-second timeout.

---

### 6. Recommendations (ranked by user impact)

**R1 (P0):** Define panel loading states — skeleton renders for all panels. The difference between "loading" and "broken" is invisible to users without explicit loading indicators.

**R2 (P0):** Fix Edit Mode cancel/snapshot storage to Zustand. Component-state snapshots will not survive HMR or page reload.

**R3 (P0):** Design `GlycogenBudget` as a form-first panel. As a passive panel it is immediately broken.

**R4 (P1):** Specify `IFFloor` and `PanicTraining` panel descriptions. Clinical panels without documentation are a coaching liability.

**R5 (P1):** Define annotation persistence model (`annotations` store key, dismiss behavior, clear-all in Claude panel).

**R6 (P1):** Define "Event Prep" unified view — route-selector drives all other panels in that tab.

**R7 (P2):** Add `theme.ts` for D3 color tokens. Without it, charts will not respect dark/light theme.

**R8 (P2):** Add "View as: [athlete | coach]" toggle in header (localStorage slug switch).

**R9 (P2):** Design "Ask Claude" button in `PanelWrapper` title bar for Phase 2.

**R10 (P3):** Add panel remove undo toast (5-second window).

</details>

<details>
<summary>Security Engineer Review (full text)</summary>

## Security Engineer Review: WKO5 Dashboard v2 Full Frontend Rewrite

**Reviewer role:** Security Engineer (IC5), 20+ years across application security, cloud infrastructure security, and secure SDLC. Focus: MCP bridge trust boundary and embedded terminal attack surface.

**Files read:** `docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md`, `wko5/api/routes.py`, `wko5/api/auth.py`

---

### Positive Notes Before Findings

- `auth.py` fail-open bug (P3 review C5) is fixed: line 16 now raises `HTTPException(503)` when `_token is None`. No action needed.
- `auto_error=False` on `HTTPBearer` is now safe because `verify_token` correctly handles `credentials=None`. The P3 LOW-1 finding is resolved.
- localStorage layout storage (vs. backend DB with raw token as PK) eliminates P3 CRITICAL-1 and HIGH-2. Good call.
- Per-panel error boundaries prevent error state leakage between panels.

---

### Findings

---

**CRITICAL-1: MCP Server Has No Authentication**

**Vulnerability:** The MCP server (`tools/mcp-dashboard/server.ts`) is a local process binding to a TCP port (unspecified). The spec says "Claude Code connects to it via `.mcp.json`." No session token, process identity check, or connection allowlist is defined.

**Impact:** Any process running as the same user — a compromised npm package, a malicious script in the project directory, or another application — can connect to the MCP server and:
- Call `get_all_metrics()` to extract the full Zustand store (contains fitness data, clinical flags, all route details)
- Call `highlight_chart()` to inject misleading annotations onto clinical panels — a coach could act on a fake "REDS flag" annotation injected by a malicious process
- Call `set_time_range()` to silently mutate the dashboard state, causing the user to review the wrong time period without noticing

This is an active attack surface, not a theoretical one. The Claude Code terminal itself runs tools that may exec shell scripts in the project directory. Any `tools/*.sh` script can make HTTP calls to the MCP server.

**Remediation:** The dashboard generates a UUID session token at startup (using `crypto.randomUUID()`). This token is:
1. Stored in Zustand (never serialized to localStorage)
2. Passed to Claude Code's process via an environment variable set in the Claude Code launch command
3. Validated by the MCP server on every tool call via an `Authorization: Bearer <token>` header

The MCP server should also bind to `127.0.0.1` only (not `0.0.0.0`) and use a non-default port documented in the project config.

---

**CRITICAL-2: `get_all_metrics()` Returns Full Zustand Store Including Sensitive Data**

**Vulnerability:** The `get_all_metrics()` MCP tool is specified to return "a snapshot of the entire Zustand store (fitness, pmc, flags, etc.)." The store includes `rides: Record<number, RideDetail>` — full ride records including GPS traces, power data, heart rate, and location data. It also includes `routeDetail: Record<number, RouteDetail>` which contains route geography.

**Impact:** Any process that can call `get_all_metrics()` (see CRITICAL-1) gets the athlete's complete activity history, health flags, and location data in one call. This is a bulk exfiltration surface.

**Remediation:** Scope `get_all_metrics()` to a health-check snapshot: `{ activeTab, visiblePanels, fitness, clinicalFlags, timeRange }`. Remove `rides`, `routeDetail`, `profile`, and secondary data. If Claude needs ride data, it should call `get_panel_data('rides-table')` which returns only the currently-displayed data, not the full store.

---

**HIGH-1: Bearer Token Storage Mechanism Is Undefined**

**Vulnerability:** `src/api/client.ts` uses `Authorization: Bearer ${token}`. The spec does not specify where `token` comes from. If sourced from `import.meta.env.VITE_API_TOKEN`, the token is embedded in the compiled JavaScript bundle — visible in `dist/assets/client-[hash].js` to anyone with filesystem access to the build output. If committed to `.env`, it is in version control.

**Impact:** For a locally-run tool, this is a lower-severity issue (only the local user has filesystem access). However, if the built frontend is ever served from a web server (even locally via nginx), the bundle is accessible via HTTP and the token is extractable without authentication.

**Remediation:** Token comes from `localStorage('wko5-api-token')`. On first load, if not set, show a one-time setup modal: "Enter your API token." The token is written to localStorage and read at runtime by `client.ts`. It is never bundled. Document: do not set `VITE_API_TOKEN` in any env file.

---

**HIGH-2: MCP Server Port Is Unspecified — Port Conflict and Discovery Risk**

**Vulnerability:** The spec says the MCP server "runs as a sidecar process" but does not specify which port. If it defaults to a common port (3000, 8080, 8000), it will conflict with Vite dev server (5173) or the FastAPI backend (8000). Worse, if it uses a port that other applications commonly use, other tools on the machine may attempt to connect to it.

**Impact:** Port conflict causes silent startup failure of the MCP server (Phase 2 doesn't work). Port discovery by other processes enables CRITICAL-1 exploitation.

**Remediation:** Use a non-standard port (e.g., 47821). Make it configurable via `tools/mcp-dashboard/config.json`. Document the port in the project README. Add a port-in-use check at startup with a clear error message.

---

**MEDIUM-1: `highlight_chart()` MCP Tool Accepts Arbitrary Annotation Content**

**Vulnerability:** `highlight_chart(panelId, annotation)` where `annotation: { type, x?, y?, label, color }`. The `label` field is rendered on the chart. If this label is rendered as HTML (even via D3's `.text()` → later `.html()` or a framework component), it's an XSS vector. The `color` field is passed to D3 `.attr('fill', color)` — CSS injection if not validated.

**Impact:** A process with access to the MCP server can inject chart annotations with misleading labels ("MEDICAL EMERGENCY: STOP TRAINING") or malformed color values that break chart rendering.

**Remediation:** Validate `annotation.label` as a plain string (max 100 chars, no HTML). Validate `annotation.color` against a CSS color regex (`/^#[0-9a-f]{6}$|^[a-z]+$/i`). Reject invalid inputs with an error response. Never render annotation labels as HTML — use D3 `.text()` only.

---

**MEDIUM-2: Vite Dev Server Exposes Full Source Code on Local Network**

**Vulnerability:** Vite dev server by default binds to `0.0.0.0` (all interfaces), not just `127.0.0.1`. Anyone on the local network (home network, coffee shop WiFi) can access `http://{local-ip}:5173` and receive the full source map, including `src/api/client.ts` with the token sourcing logic.

**Impact:** Source exposure in a local tool is low severity. However, if the token is stored in a way that makes it visible in the source (e.g., a `console.log` left in during dev), it leaks to the network.

**Remediation:** Add to `vite.config.ts`: `server: { host: '127.0.0.1' }`. This binds the dev server to localhost only. Document this setting.

---

**MEDIUM-3: `warmup-status` Endpoint Exposes Internal Error Details Without Auth**

**Vulnerability:** `GET /warmup-status` is unauthenticated (by design — the spec says "no auth needed so dashboard can poll during startup"). It returns `"warmup_errors": {"clinical": "connection refused to /path/to/db"}` — internal filesystem paths and service names in error messages.

**Impact:** For a local tool, this is low severity. If the API is ever exposed beyond localhost, it leaks internal architecture details. An attacker learns: which Python modules exist, what the database path is, which endpoints are slow.

**Remediation:** Strip error messages from the unauthenticated endpoint. Return `"warmup_errors": {"clinical": "failed"}` (boolean, no detail). Authenticated `GET /health` can return full error details.

---

**LOW-1: `.mcp.json` May Be Committed to Version Control**

**Vulnerability:** `.mcp.json` configures Claude Code's MCP server connections. If it contains the MCP server port (and potentially an API token if the MCP auth recommendation in CRITICAL-1 is implemented), committing it to the repo exposes configuration.

**Impact:** If the repo is public, MCP configuration leaks. If private, lower risk. But establishing good habits early prevents future leaks.

**Remediation:** Add `tools/mcp-dashboard/mcp.json` to `.gitignore`. Provide `mcp.json.example` with placeholder values. Document the setup step in the project README.

---

**LOW-2: xterm.js Terminal Has No Input Sanitization**

**Vulnerability:** The embedded xterm.js terminal renders Claude Code's output. If Claude Code produces ANSI escape sequences that xterm.js processes (which it does by design), a malformed sequence could potentially execute terminal escape codes that trigger unintended actions.

**Impact:** This is an accepted risk for any terminal emulator — xterm.js is specifically designed to handle ANSI sequences safely. The risk is low because Claude Code's output is generated by the model, not by untrusted external input. However, if Claude Code reads a file containing malicious ANSI sequences and prints it, xterm.js will process them.

**Remediation:** Accept this risk with documentation. Note in Phase 2 spec: "The embedded terminal is trusted for Claude Code output. Avoid using `cat` on untrusted files within the terminal — use Claude Code's file reading tools instead." This is a developer education mitigation, not a code fix.

---

### Summary Table

| Severity | Finding | Action |
|----------|---------|--------|
| CRITICAL | MCP server has no auth | Session token: UUID generated at startup, validated per call |
| CRITICAL | `get_all_metrics()` returns full store including location/health data | Scope to health-check snapshot only |
| HIGH | Token storage mechanism unspecified — risk of bundle embedding | Specify: localStorage, never env var |
| HIGH | MCP port unspecified — conflict and discovery risk | Specify non-standard port, bind to 127.0.0.1 |
| MEDIUM | `highlight_chart` label/color fields are injection vectors | Validate: plain string, CSS color regex |
| MEDIUM | Vite dev server binds to all interfaces | `server: { host: '127.0.0.1' }` in vite.config.ts |
| MEDIUM | `warmup-status` leaks internal error details without auth | Strip error details from unauthenticated response |
| LOW | `.mcp.json` may be committed | Add to `.gitignore`, provide `.example` |
| LOW | xterm.js ANSI escape processing | Document: avoid cat on untrusted files in terminal |

</details>
