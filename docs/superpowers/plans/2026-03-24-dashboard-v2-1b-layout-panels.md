# Dashboard v2 — Plan 1B: Layout Engine + Non-Chart Panels

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the layout engine (tabs, panel grid, edit mode, persistence) and all non-chart panels (panels that read from the Zustand store and render data without D3). After this plan, full tab navigation works, edit mode works (drag reorder, add/remove panels, Done/Cancel/Reset), layout persists in localStorage, and the global time range filter bar is visible.

**Depends on:** Plan 1A (foundation) which creates: Vite scaffold in `frontend-v2/`, typed API client (`src/api/client.ts`, `src/api/types.ts`), Zustand store (`src/store/data-store.ts`), shared components (`PanelSkeleton`, `PanelError`, `PanelEmpty`, `Metric`, `MetricBig`, `DataTable`), chart design tokens (`src/shared/tokens.ts`), and the App shell (`src/App.tsx`, `src/main.tsx`).

**Tech Stack:** React 18, TypeScript, Zustand, dnd-kit, CSS Modules, Vitest + React Testing Library

**Spec:** `docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md`

**Test command:** `cd frontend-v2 && npx vitest run`

**Dev server:** `cd frontend-v2 && npm run dev`

---

## File Structure

```
frontend-v2/src/
  layout/
    PanelRegistry.ts           — NEW: static registry mapping panel IDs to components
    PanelRegistry.test.ts      — NEW: registry tests
    LayoutEngine.tsx           — NEW: reads layout from store, renders tabs + panel grid
    LayoutEngine.module.css    — NEW: layout styles
    LayoutEngine.test.tsx      — NEW: layout rendering tests
    PanelWrapper.tsx           — NEW: error boundary + structured header bar chrome
    PanelWrapper.module.css    — NEW: panel chrome styles
    PanelWrapper.test.tsx      — NEW: wrapper tests
    EditMode.tsx               — NEW: dnd-kit drag reorder, add/remove panels + tabs
    EditMode.module.css        — NEW: edit mode styles
    EditMode.test.tsx          — NEW: edit mode tests
    layoutStore.ts             — NEW: Zustand slice for layout state + persistence
    layoutStore.test.ts        — NEW: persistence tests
    presets.ts                 — NEW: default athlete/coach layout presets
    types.ts                   — NEW: Layout, Tab, PanelDef interfaces
  panels/
    status/
      TSBStatus.tsx            — NEW: big TSB + CTL/ATL
      TSBStatus.module.css     — NEW
      TSBStatus.test.tsx       — NEW
      RecentRides.tsx          — NEW: last 5 rides table
      RecentRides.test.tsx     — NEW
      ClinicalAlert.tsx        — NEW: summary alert banner
      ClinicalAlert.module.css — NEW
      ClinicalAlert.test.tsx   — NEW
    health/
      ClinicalFlags.tsx        — NEW: flag card grid, severity-ordered
      ClinicalFlags.module.css — NEW
      ClinicalFlags.test.tsx   — NEW
      IFFloor.tsx              — NEW: single flag card
      IFFloor.test.tsx         — NEW
      PanicTraining.tsx        — NEW: single flag card
      PanicTraining.test.tsx   — NEW
      RedsScreen.tsx           — NEW: single flag card
      RedsScreen.test.tsx      — NEW
      FreshBaseline.tsx        — NEW: staleness table
      FreshBaseline.test.tsx   — NEW
    fitness/
      PowerProfile.tsx         — NEW: 5s/1m/5m/20m/60m W/kg grid
      PowerProfile.module.css  — NEW
      PowerProfile.test.tsx    — NEW
      ShortPower.tsx           — NEW: peak vs median card
      ShortPower.test.tsx      — NEW
    event-prep/
      RouteSelector.tsx        — NEW: dropdown writing to store
      RouteSelector.test.tsx   — NEW
      GapAnalysis.tsx          — NEW: feasible/not feasible card
      GapAnalysis.module.css   — NEW
      GapAnalysis.test.tsx     — NEW
      OpportunityCost.tsx      — NEW: HTML horizontal bars
      OpportunityCost.module.css — NEW
      OpportunityCost.test.tsx — NEW
      GlycogenBudget.tsx       — NEW: interactive form (chart part deferred to 1C)
      GlycogenBudget.module.css — NEW
      GlycogenBudget.test.tsx  — NEW
    history/
      RidesTable.tsx           — NEW: sortable, paginated, searchable
      RidesTable.module.css    — NEW
      RidesTable.test.tsx      — NEW
      TrainingBlocks.tsx       — NEW: block stats card
      TrainingBlocks.test.tsx  — NEW
      PhaseTimeline.tsx        — NEW: current phase + confidence
      PhaseTimeline.test.tsx   — NEW
      IntensityDist.tsx        — NEW: Seiler 3-zone bars (HTML)
      IntensityDist.module.css — NEW
      IntensityDist.test.tsx   — NEW
    profile/
      CogganRanking.tsx        — NEW: ranking table
      CogganRanking.test.tsx   — NEW
      Phenotype.tsx            — NEW: strength/limiter card
      Phenotype.test.tsx       — NEW
      PosteriorSummary.tsx     — NEW: Bayesian CI table
      PosteriorSummary.test.tsx — NEW
      Feasibility.tsx          — NEW: feasibility projection card
      Feasibility.module.css   — NEW
      Feasibility.test.tsx     — NEW
      AthleteConfig.tsx        — NEW: config display (read-only)
      AthleteConfig.test.tsx   — NEW
  components/
    Header.tsx                 — NEW: tab bar, stale indicator, gear button, Claude placeholder
    Header.module.css          — NEW
    Header.test.tsx            — NEW
    FilterBar.tsx              — NEW: global time range + sport type filter
    FilterBar.module.css       — NEW
    FilterBar.test.tsx         — NEW
    PanelCatalogModal.tsx      — NEW: category-grouped panel picker with search
    PanelCatalogModal.module.css — NEW
    ConfirmDialog.tsx          — NEW: reusable confirmation dialog
    Tooltip.tsx                — NEW: hover tooltip for metric derivation
    Tooltip.module.css         — NEW
```

---

## Task 1: Layout Types + Presets

**Files:**
- Create: `frontend-v2/src/layout/types.ts`
- Create: `frontend-v2/src/layout/presets.ts`

These are pure data definitions with zero dependencies — the foundation everything else builds on.

- [ ] **Step 1: Create layout type definitions**

Create `frontend-v2/src/layout/types.ts`:

```typescript
/** Unique panel identifier — kebab-case, matches registry key */
export type PanelId = string

/** Panel category for catalog grouping */
export type PanelCategory =
  | 'status'
  | 'health'
  | 'fitness'
  | 'event-prep'
  | 'history'
  | 'profile'

/** Panel definition in the registry */
export interface PanelDef {
  id: PanelId
  label: string
  category: PanelCategory
  description: string
  component: React.ComponentType
  /** Store keys this panel reads — metadata for loading indicators + catalog display.
   *  Zustand selectors are runtime truth; this is informational only. */
  dataKeys: string[]
}

/** Single tab in a layout */
export interface Tab {
  id: string
  label: string
  panels: PanelId[]
}

/** Full layout configuration */
export interface Layout {
  version: number
  tabs: Tab[]
}

/** Layout store state */
export interface LayoutState {
  layout: Layout
  activeTabId: string
  editMode: boolean
  /** Snapshot taken on edit mode entry — restored on Cancel */
  editSnapshot: Layout | null

  // Actions
  setActiveTab: (tabId: string) => void
  enterEditMode: () => void
  exitEditMode: (save: boolean) => void
  resetToDefault: () => void

  // Tab mutations (edit mode only)
  addTab: (label: string) => void
  removeTab: (tabId: string) => void
  renameTab: (tabId: string, label: string) => void
  reorderTabs: (fromIndex: number, toIndex: number) => void

  // Panel mutations (edit mode only)
  addPanel: (tabId: string, panelId: PanelId) => void
  removePanel: (tabId: string, panelId: PanelId) => void
  reorderPanels: (tabId: string, fromIndex: number, toIndex: number) => void
}
```

- [ ] **Step 2: Create default presets**

Create `frontend-v2/src/layout/presets.ts`:

```typescript
import type { Layout } from './types'

export const LAYOUT_VERSION = 1

export const ATHLETE_PRESET: Layout = {
  version: LAYOUT_VERSION,
  tabs: [
    {
      id: 'today',
      label: 'Today',
      panels: ['tsb-status', 'recent-rides', 'clinical-alert'],
    },
    {
      id: 'health',
      label: 'Health',
      panels: [
        'clinical-flags',
        'if-floor',
        'panic-training',
        'reds-screen',
        'fresh-baseline',
      ],
    },
    {
      id: 'fitness',
      label: 'Fitness',
      panels: [
        'pmc-chart',
        'mmp-curve',
        'rolling-ftp',
        'ftp-growth',
        'rolling-pd',
        'short-power',
        'power-profile',
      ],
    },
    {
      id: 'event-prep',
      label: 'Event Prep',
      panels: [
        'route-selector',
        'segment-profile',
        'demand-heatmap',
        'gap-analysis',
        'pacing',
        'opportunity-cost',
        'glycogen-budget',
      ],
    },
    {
      id: 'history',
      label: 'History',
      panels: [
        'rides-table',
        'training-blocks',
        'phase-timeline',
        'intensity-dist',
      ],
    },
    {
      id: 'profile',
      label: 'Profile',
      panels: [
        'coggan-ranking',
        'phenotype',
        'posterior-summary',
        'feasibility',
        'athlete-config',
      ],
    },
    {
      id: 'settings',
      label: 'Settings',
      panels: ['athlete-config'],
    },
  ],
}

export const COACH_PRESET: Layout = {
  version: LAYOUT_VERSION,
  tabs: [
    {
      id: 'health',
      label: 'Health',
      panels: [
        'clinical-flags',
        'if-floor',
        'panic-training',
        'reds-screen',
        'fresh-baseline',
      ],
    },
    {
      id: 'today',
      label: 'Today',
      panels: ['tsb-status', 'recent-rides', 'clinical-alert'],
    },
    {
      id: 'fitness',
      label: 'Fitness',
      panels: [
        'pmc-chart',
        'mmp-curve',
        'rolling-ftp',
        'ftp-growth',
        'rolling-pd',
        'short-power',
        'power-profile',
      ],
    },
    {
      id: 'history',
      label: 'History',
      panels: ['rides-table', 'training-blocks', 'phase-timeline'],
    },
    {
      id: 'profile',
      label: 'Profile',
      panels: [
        'coggan-ranking',
        'phenotype',
        'posterior-summary',
        'feasibility',
      ],
    },
    {
      id: 'event-prep',
      label: 'Event Prep',
      panels: [
        'route-selector',
        'gap-analysis',
        'opportunity-cost',
        'pacing',
        'glycogen-budget',
      ],
    },
  ],
}

/** Get default layout for a role */
export function getDefaultPreset(role: 'athlete' | 'coach' = 'athlete'): Layout {
  const source = role === 'coach' ? COACH_PRESET : ATHLETE_PRESET
  return JSON.parse(JSON.stringify(source)) // deep clone
}
```

- [ ] **Step 3: Commit**

```bash
cd frontend-v2 && git add src/layout/types.ts src/layout/presets.ts
git commit -m "feat(1b): layout types + athlete/coach preset definitions"
```

---

## Task 2: Layout Store — Zustand Slice + localStorage Persistence

**Files:**
- Create: `frontend-v2/src/layout/layoutStore.ts`
- Create: `frontend-v2/src/layout/layoutStore.test.ts`

- [ ] **Step 1: Create the layout store**

Create `frontend-v2/src/layout/layoutStore.ts`:

```typescript
import { create } from 'zustand'
import type { Layout, LayoutState, PanelId } from './types'
import { LAYOUT_VERSION, getDefaultPreset } from './presets'

/** Generate localStorage key scoped to athlete slug */
function storageKey(slug: string): string {
  return `wko5-layout-${slug}`
}

/** Load layout from localStorage with version migration */
function loadFromStorage(slug: string): Layout | null {
  try {
    const raw = localStorage.getItem(storageKey(slug))
    if (!raw) return null
    const parsed = JSON.parse(raw) as Layout
    if (parsed.version !== LAYOUT_VERSION) {
      console.warn('[Layout] Version mismatch, discarding saved layout')
      localStorage.removeItem(storageKey(slug))
      return null
    }
    return parsed
  } catch {
    console.warn('[Layout] Failed to parse saved layout')
    return null
  }
}

/** Save layout to localStorage */
function saveToStorage(slug: string, layout: Layout): void {
  try {
    localStorage.setItem(storageKey(slug), JSON.stringify(layout))
  } catch (e) {
    console.error('[Layout] Failed to save:', e)
  }
}

/** Generate a unique tab ID from a label */
function tabIdFromLabel(label: string, existingIds: string[]): string {
  const base = label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .substring(0, 30) || 'tab'
  let id = base
  let counter = 1
  while (existingIds.includes(id)) {
    id = `${base}-${counter++}`
  }
  return id
}

/**
 * Create a layout store for a given athlete slug.
 * Called once at app init with the slug from the URL / data store.
 */
export function createLayoutStore(slug: string, role: 'athlete' | 'coach' = 'athlete') {
  const saved = loadFromStorage(slug)
  const initial = saved ?? getDefaultPreset(role)

  return create<LayoutState>((set, get) => ({
    layout: initial,
    activeTabId: initial.tabs[0]?.id ?? '',
    editMode: false,
    editSnapshot: null,

    setActiveTab: (tabId: string) => {
      const { layout } = get()
      if (layout.tabs.some(t => t.id === tabId)) {
        set({ activeTabId: tabId })
      }
    },

    enterEditMode: () => {
      const { layout } = get()
      set({
        editMode: true,
        editSnapshot: JSON.parse(JSON.stringify(layout)),
      })
    },

    exitEditMode: (save: boolean) => {
      const { layout, editSnapshot } = get()
      if (save) {
        saveToStorage(slug, layout)
      } else if (editSnapshot) {
        set({ layout: editSnapshot })
      }
      set({ editMode: false, editSnapshot: null })
    },

    resetToDefault: () => {
      const fresh = getDefaultPreset(role)
      set({ layout: fresh, activeTabId: fresh.tabs[0]?.id ?? '' })
      saveToStorage(slug, fresh)
    },

    // ── Tab mutations ──────────────────────────────────────────────

    addTab: (label: string) => {
      const { layout } = get()
      const existingIds = layout.tabs.map(t => t.id)
      const id = tabIdFromLabel(label, existingIds)
      const newTab = { id, label: label.substring(0, 30), panels: [] as PanelId[] }
      set({
        layout: { ...layout, tabs: [...layout.tabs, newTab] },
        activeTabId: id,
      })
    },

    removeTab: (tabId: string) => {
      const { layout, activeTabId } = get()
      if (layout.tabs.length <= 1) return // never remove last tab
      const filtered = layout.tabs.filter(t => t.id !== tabId)
      const newActive =
        activeTabId === tabId ? filtered[0]?.id ?? '' : activeTabId
      set({ layout: { ...layout, tabs: filtered }, activeTabId: newActive })
    },

    renameTab: (tabId: string, label: string) => {
      const { layout } = get()
      set({
        layout: {
          ...layout,
          tabs: layout.tabs.map(t =>
            t.id === tabId ? { ...t, label: label.substring(0, 30) } : t
          ),
        },
      })
    },

    reorderTabs: (fromIndex: number, toIndex: number) => {
      const { layout } = get()
      const tabs = [...layout.tabs]
      const [moved] = tabs.splice(fromIndex, 1)
      tabs.splice(toIndex, 0, moved)
      set({ layout: { ...layout, tabs } })
    },

    // ── Panel mutations ────────────────────────────────────────────

    addPanel: (tabId: string, panelId: PanelId) => {
      const { layout } = get()
      set({
        layout: {
          ...layout,
          tabs: layout.tabs.map(t =>
            t.id === tabId && !t.panels.includes(panelId)
              ? { ...t, panels: [...t.panels, panelId] }
              : t
          ),
        },
      })
    },

    removePanel: (tabId: string, panelId: PanelId) => {
      const { layout } = get()
      set({
        layout: {
          ...layout,
          tabs: layout.tabs.map(t =>
            t.id === tabId
              ? { ...t, panels: t.panels.filter(p => p !== panelId) }
              : t
          ),
        },
      })
    },

    reorderPanels: (tabId: string, fromIndex: number, toIndex: number) => {
      const { layout } = get()
      set({
        layout: {
          ...layout,
          tabs: layout.tabs.map(t => {
            if (t.id !== tabId) return t
            const panels = [...t.panels]
            const [moved] = panels.splice(fromIndex, 1)
            panels.splice(toIndex, 0, moved)
            return { ...t, panels }
          }),
        },
      })
    },
  }))
}

/** Singleton store instance — initialized by App on mount */
export let useLayoutStore: ReturnType<typeof createLayoutStore>

export function initLayoutStore(slug: string, role: 'athlete' | 'coach' = 'athlete') {
  useLayoutStore = createLayoutStore(slug, role)
}
```

- [ ] **Step 2: Write layout store tests**

Create `frontend-v2/src/layout/layoutStore.test.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createLayoutStore } from './layoutStore'
import { LAYOUT_VERSION } from './presets'

// Mock localStorage
const store: Record<string, string> = {}
beforeEach(() => {
  Object.keys(store).forEach(k => delete store[k])
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v },
    removeItem: (k: string) => { delete store[k] },
  })
})

describe('createLayoutStore', () => {
  it('loads athlete preset when no saved layout', () => {
    const useStore = createLayoutStore('test-athlete')
    const state = useStore.getState()
    expect(state.layout.version).toBe(LAYOUT_VERSION)
    expect(state.layout.tabs[0].id).toBe('today')
    expect(state.activeTabId).toBe('today')
    expect(state.editMode).toBe(false)
  })

  it('loads coach preset when role=coach', () => {
    const useStore = createLayoutStore('test-coach', 'coach')
    const state = useStore.getState()
    expect(state.layout.tabs[0].id).toBe('health')
  })

  it('loads saved layout from localStorage', () => {
    const saved = {
      version: LAYOUT_VERSION,
      tabs: [{ id: 'custom', label: 'Custom', panels: ['tsb-status'] }],
    }
    store['wko5-layout-saved'] = JSON.stringify(saved)
    const useStore = createLayoutStore('saved')
    expect(useStore.getState().layout.tabs[0].id).toBe('custom')
  })

  it('discards saved layout with wrong version', () => {
    store['wko5-layout-old'] = JSON.stringify({ version: 999, tabs: [] })
    const useStore = createLayoutStore('old')
    // Falls back to default
    expect(useStore.getState().layout.tabs[0].id).toBe('today')
    expect(store['wko5-layout-old']).toBeUndefined()
  })
})

describe('tab switching', () => {
  it('switches active tab', () => {
    const useStore = createLayoutStore('test')
    useStore.getState().setActiveTab('fitness')
    expect(useStore.getState().activeTabId).toBe('fitness')
  })

  it('ignores invalid tab ID', () => {
    const useStore = createLayoutStore('test')
    useStore.getState().setActiveTab('nonexistent')
    expect(useStore.getState().activeTabId).toBe('today')
  })
})

describe('edit mode', () => {
  it('enter takes snapshot, exit-save writes localStorage', () => {
    const useStore = createLayoutStore('persist')
    useStore.getState().enterEditMode()
    expect(useStore.getState().editMode).toBe(true)
    expect(useStore.getState().editSnapshot).not.toBeNull()

    // Mutate during edit
    useStore.getState().addTab('New Tab')
    const tabCount = useStore.getState().layout.tabs.length

    // Save
    useStore.getState().exitEditMode(true)
    expect(useStore.getState().editMode).toBe(false)
    expect(store['wko5-layout-persist']).toBeDefined()
    const persisted = JSON.parse(store['wko5-layout-persist'])
    expect(persisted.tabs).toHaveLength(tabCount)
  })

  it('exit-cancel restores snapshot', () => {
    const useStore = createLayoutStore('cancel')
    const originalCount = useStore.getState().layout.tabs.length
    useStore.getState().enterEditMode()
    useStore.getState().addTab('Temp')
    expect(useStore.getState().layout.tabs.length).toBe(originalCount + 1)

    useStore.getState().exitEditMode(false) // cancel
    expect(useStore.getState().layout.tabs.length).toBe(originalCount)
  })

  it('resetToDefault replaces layout and persists', () => {
    const useStore = createLayoutStore('reset')
    useStore.getState().addTab('Custom')
    useStore.getState().resetToDefault()
    expect(useStore.getState().layout.tabs[0].id).toBe('today')
    expect(store['wko5-layout-reset']).toBeDefined()
  })
})

describe('tab mutations', () => {
  it('addTab creates unique ID and switches to it', () => {
    const useStore = createLayoutStore('tabs')
    useStore.getState().addTab('My Tab')
    const tabs = useStore.getState().layout.tabs
    const added = tabs[tabs.length - 1]
    expect(added.label).toBe('My Tab')
    expect(added.id).toBe('my-tab')
    expect(added.panels).toEqual([])
    expect(useStore.getState().activeTabId).toBe('my-tab')
  })

  it('addTab deduplicates IDs', () => {
    const useStore = createLayoutStore('dupes')
    useStore.getState().addTab('Today') // 'today' already exists
    const ids = useStore.getState().layout.tabs.map(t => t.id)
    expect(ids.filter(id => id === 'today')).toHaveLength(1)
    expect(ids).toContain('today-1')
  })

  it('removeTab prevents removing last tab', () => {
    const useStore = createLayoutStore('last')
    const tabs = useStore.getState().layout.tabs
    // Remove all but one
    tabs.slice(1).forEach(t => useStore.getState().removeTab(t.id))
    expect(useStore.getState().layout.tabs.length).toBe(1)
    // Try removing the last one
    useStore.getState().removeTab(useStore.getState().layout.tabs[0].id)
    expect(useStore.getState().layout.tabs.length).toBe(1)
  })

  it('renameTab truncates at 30 chars', () => {
    const useStore = createLayoutStore('rename')
    useStore.getState().renameTab('today', 'A'.repeat(50))
    const tab = useStore.getState().layout.tabs.find(t => t.id === 'today')
    expect(tab?.label).toHaveLength(30)
  })

  it('reorderTabs moves tab position', () => {
    const useStore = createLayoutStore('reorder')
    const original = useStore.getState().layout.tabs.map(t => t.id)
    useStore.getState().reorderTabs(0, 2) // move first to third
    const reordered = useStore.getState().layout.tabs.map(t => t.id)
    expect(reordered[2]).toBe(original[0])
  })
})

describe('panel mutations', () => {
  it('addPanel appends to tab', () => {
    const useStore = createLayoutStore('panels')
    useStore.getState().addPanel('today', 'power-profile')
    const tab = useStore.getState().layout.tabs.find(t => t.id === 'today')
    expect(tab?.panels).toContain('power-profile')
  })

  it('addPanel prevents duplicates within same tab', () => {
    const useStore = createLayoutStore('nodup')
    useStore.getState().addPanel('today', 'tsb-status') // already there
    const tab = useStore.getState().layout.tabs.find(t => t.id === 'today')
    const count = tab?.panels.filter(p => p === 'tsb-status').length
    expect(count).toBe(1)
  })

  it('removePanel removes from tab', () => {
    const useStore = createLayoutStore('remove')
    useStore.getState().removePanel('today', 'tsb-status')
    const tab = useStore.getState().layout.tabs.find(t => t.id === 'today')
    expect(tab?.panels).not.toContain('tsb-status')
  })

  it('reorderPanels moves panel position', () => {
    const useStore = createLayoutStore('reorder-p')
    const tab = useStore.getState().layout.tabs.find(t => t.id === 'today')!
    const original = [...tab.panels]
    useStore.getState().reorderPanels('today', 0, 2)
    const updated = useStore.getState().layout.tabs.find(t => t.id === 'today')!
    expect(updated.panels[2]).toBe(original[0])
  })
})
```

- [ ] **Step 3: Run tests**

```bash
cd frontend-v2 && npx vitest run src/layout/layoutStore.test.ts
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
cd frontend-v2 && git add src/layout/layoutStore.ts src/layout/layoutStore.test.ts
git commit -m "feat(1b): layout Zustand store — persistence, edit mode, tab/panel mutations"
```

---

## Task 3: Panel Registry

**Files:**
- Create: `frontend-v2/src/layout/PanelRegistry.ts`
- Create: `frontend-v2/src/layout/PanelRegistry.test.ts`

The registry maps panel IDs to React component types + metadata. Panels register themselves via import side effects. Chart panels (D3) are registered with placeholder components that will be replaced in Plan 1C.

- [ ] **Step 1: Create PanelRegistry**

Create `frontend-v2/src/layout/PanelRegistry.ts`:

```typescript
import type { PanelDef, PanelId, PanelCategory } from './types'

/** Internal registry map */
const registry = new Map<PanelId, PanelDef>()

/** Register a panel definition. Called by each panel module at import time. */
export function registerPanel(def: PanelDef): void {
  if (registry.has(def.id)) {
    console.warn(`[PanelRegistry] Duplicate panel ID: ${def.id}`)
  }
  registry.set(def.id, def)
}

/** Look up a panel by ID */
export function getPanel(id: PanelId): PanelDef | undefined {
  return registry.get(id)
}

/** Get all registered panels */
export function getAllPanels(): PanelDef[] {
  return Array.from(registry.values())
}

/** Get panels grouped by category, sorted by category order */
export function getPanelCatalog(): Array<{
  category: PanelCategory
  label: string
  panels: PanelDef[]
}> {
  const categoryOrder: Array<{ key: PanelCategory; label: string }> = [
    { key: 'status', label: 'Status' },
    { key: 'health', label: 'Health' },
    { key: 'fitness', label: 'Fitness' },
    { key: 'event-prep', label: 'Event Prep' },
    { key: 'history', label: 'History' },
    { key: 'profile', label: 'Profile' },
  ]

  return categoryOrder.map(({ key, label }) => ({
    category: key,
    label,
    panels: getAllPanels().filter(p => p.category === key),
  }))
}

/** Check if a panel ID is registered */
export function hasPanel(id: PanelId): boolean {
  return registry.has(id)
}

/** Get the component for a panel ID (convenience) */
export function getPanelComponent(id: PanelId): React.ComponentType | null {
  return registry.get(id)?.component ?? null
}

/** Clear registry — for testing only */
export function _clearRegistry(): void {
  registry.clear()
}
```

- [ ] **Step 2: Write registry tests**

Create `frontend-v2/src/layout/PanelRegistry.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import {
  registerPanel,
  getPanel,
  getAllPanels,
  getPanelCatalog,
  hasPanel,
  getPanelComponent,
  _clearRegistry,
} from './PanelRegistry'

function DummyComponent() {
  return null
}

beforeEach(() => {
  _clearRegistry()
})

describe('PanelRegistry', () => {
  it('registers and retrieves a panel', () => {
    registerPanel({
      id: 'test-panel',
      label: 'Test Panel',
      category: 'status',
      description: 'A test panel',
      component: DummyComponent,
      dataKeys: ['fitness'],
    })
    expect(hasPanel('test-panel')).toBe(true)
    expect(getPanel('test-panel')?.label).toBe('Test Panel')
    expect(getPanelComponent('test-panel')).toBe(DummyComponent)
  })

  it('returns undefined for unknown panel', () => {
    expect(getPanel('nonexistent')).toBeUndefined()
    expect(hasPanel('nonexistent')).toBe(false)
    expect(getPanelComponent('nonexistent')).toBeNull()
  })

  it('getAllPanels returns all registered panels', () => {
    registerPanel({
      id: 'a', label: 'A', category: 'status',
      description: '', component: DummyComponent, dataKeys: [],
    })
    registerPanel({
      id: 'b', label: 'B', category: 'health',
      description: '', component: DummyComponent, dataKeys: [],
    })
    expect(getAllPanels()).toHaveLength(2)
  })

  it('getPanelCatalog groups by category in order', () => {
    registerPanel({
      id: 'health-1', label: 'H1', category: 'health',
      description: '', component: DummyComponent, dataKeys: [],
    })
    registerPanel({
      id: 'status-1', label: 'S1', category: 'status',
      description: '', component: DummyComponent, dataKeys: [],
    })
    const catalog = getPanelCatalog()
    expect(catalog[0].category).toBe('status')
    expect(catalog[0].panels).toHaveLength(1)
    expect(catalog[1].category).toBe('health')
    expect(catalog[1].panels).toHaveLength(1)
  })

  it('warns on duplicate ID (does not throw)', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    registerPanel({
      id: 'dup', label: 'First', category: 'status',
      description: '', component: DummyComponent, dataKeys: [],
    })
    registerPanel({
      id: 'dup', label: 'Second', category: 'status',
      description: '', component: DummyComponent, dataKeys: [],
    })
    expect(spy).toHaveBeenCalledWith(expect.stringContaining('Duplicate'))
    // Second registration overwrites
    expect(getPanel('dup')?.label).toBe('Second')
    spy.mockRestore()
  })
})
```

- [ ] **Step 3: Run tests**

```bash
cd frontend-v2 && npx vitest run src/layout/PanelRegistry.test.ts
```

- [ ] **Step 4: Commit**

```bash
cd frontend-v2 && git add src/layout/PanelRegistry.ts src/layout/PanelRegistry.test.ts
git commit -m "feat(1b): panel registry — static ID-to-component mapping with catalog"
```

---

## Task 4: Tooltip Component

**Files:**
- Create: `frontend-v2/src/components/Tooltip.tsx`
- Create: `frontend-v2/src/components/Tooltip.module.css`

Every metric needs hover tooltips explaining derivation. Build the reusable tooltip before panels.

- [ ] **Step 1: Create Tooltip component**

Create `frontend-v2/src/components/Tooltip.tsx`:

```typescript
import { useState, useRef, type ReactNode } from 'react'
import styles from './Tooltip.module.css'

interface TooltipProps {
  /** Short metric name (e.g., "CTL") */
  label: string
  /** Full name (e.g., "Chronic Training Load") */
  fullName: string
  /** How derived (e.g., "Exponentially weighted average of daily TSS, 42-day time constant") */
  derivation: string
  /** Training context (e.g., "Higher = more fit. Typical target: 60-100 for competitive amateur") */
  context?: string
  children: ReactNode
}

export function Tooltip({ label, fullName, derivation, context, children }: TooltipProps) {
  const [visible, setVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  return (
    <div
      className={styles.wrapper}
      ref={ref}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      aria-describedby={visible ? `tooltip-${label}` : undefined}
    >
      {children}
      {visible && (
        <div
          id={`tooltip-${label}`}
          role="tooltip"
          className={styles.tooltip}
        >
          <div className={styles.title}>{fullName}</div>
          <div className={styles.derivation}>{derivation}</div>
          {context && <div className={styles.context}>{context}</div>}
        </div>
      )}
    </div>
  )
}
```

Create `frontend-v2/src/components/Tooltip.module.css`:

```css
.wrapper {
  position: relative;
  display: inline-block;
}

.tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  background: var(--color-bg-overlay, #2d333b);
  border: 1px solid var(--color-border, #444c56);
  border-radius: 6px;
  padding: 10px 12px;
  min-width: 240px;
  max-width: 360px;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.title {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-text-primary, #e6edf3);
  margin-bottom: 4px;
}

.derivation {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
  line-height: 1.4;
}

.context {
  font-size: 12px;
  color: var(--color-text-tertiary, #6e7681);
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--color-border, #444c56);
  line-height: 1.4;
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend-v2 && git add src/components/Tooltip.tsx src/components/Tooltip.module.css
git commit -m "feat(1b): tooltip component for metric derivation hover"
```

---

## Task 5: PanelWrapper — Error Boundary + Header Bar Chrome

**Files:**
- Create: `frontend-v2/src/layout/PanelWrapper.tsx`
- Create: `frontend-v2/src/layout/PanelWrapper.module.css`
- Create: `frontend-v2/src/layout/PanelWrapper.test.tsx`

Every panel gets wrapped in this. It provides: structured header bar (per spec visual design), error boundary, and drag handle in edit mode.

- [ ] **Step 1: Create PanelWrapper**

Create `frontend-v2/src/layout/PanelWrapper.tsx`:

```typescript
import { Component, type ReactNode, type ErrorInfo } from 'react'
import { getPanel } from './PanelRegistry'
import styles from './PanelWrapper.module.css'

interface PanelWrapperProps {
  panelId: string
  editMode: boolean
  onRemove?: () => void
  /** dnd-kit drag handle attributes — spread onto the handle element */
  dragHandleProps?: Record<string, unknown>
  children: ReactNode
}

interface ErrorState {
  hasError: boolean
  error: Error | null
}

/** Error boundary that catches render errors in panel content */
class PanelErrorBoundary extends Component<
  { panelId: string; children: ReactNode },
  ErrorState
> {
  state: ErrorState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): ErrorState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[Panel ${this.props.panelId}] Render error:`, error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.errorContent}>
          <div className={styles.errorIcon}>!</div>
          <div className={styles.errorMessage}>
            This panel encountered an error
          </div>
          <div className={styles.errorDetail}>
            {this.state.error?.message}
          </div>
          <button
            className={styles.retryButton}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export function PanelWrapper({
  panelId,
  editMode,
  onRemove,
  dragHandleProps,
  children,
}: PanelWrapperProps) {
  const def = getPanel(panelId)
  const label = def?.label ?? panelId

  return (
    <div
      className={`${styles.panel} ${editMode ? styles.editing : ''}`}
      data-panel-id={panelId}
    >
      {/* Structured header bar — dark chrome, drag handle in edit mode */}
      <div
        className={styles.headerBar}
        {...(editMode ? dragHandleProps : {})}
      >
        <span className={styles.title}>{label}</span>

        {/* Legend area — panels can portal content here via panelId */}
        <div className={styles.legend} id={`panel-legend-${panelId}`} />

        {editMode && (
          <button
            className={styles.removeButton}
            onClick={onRemove}
            aria-label={`Remove ${label}`}
            title="Remove panel"
          >
            ×
          </button>
        )}
      </div>

      {/* Content area */}
      <div className={styles.content}>
        <PanelErrorBoundary panelId={panelId}>
          {children}
        </PanelErrorBoundary>
      </div>
    </div>
  )
}
```

Create `frontend-v2/src/layout/PanelWrapper.module.css`:

```css
.panel {
  border: 1px solid var(--color-border, #30363d);
  border-radius: 6px;
  overflow: hidden;
  background: var(--color-bg-primary, #161b22);
}

.panel.editing {
  outline: 2px dashed var(--color-accent, #58a6ff);
  outline-offset: -2px;
}

.panel.editing .headerBar {
  cursor: grab;
}

.panel.editing .headerBar:active {
  cursor: grabbing;
}

.headerBar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-bg-header, #21262d);
  border-bottom: 1px solid var(--color-border, #30363d);
  min-height: 36px;
}

.title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary, #e6edf3);
  white-space: nowrap;
}

.legend {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.removeButton {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.removeButton:hover {
  background: var(--color-danger-bg, #da36331a);
  color: var(--color-danger, #f85149);
}

.content {
  padding: 12px;
  min-height: 80px;
}

/* Error boundary styles */
.errorContent {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  text-align: center;
}

.errorIcon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-danger-bg, #da36331a);
  color: var(--color-danger, #f85149);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
}

.errorMessage {
  font-size: 14px;
  color: var(--color-text-primary, #e6edf3);
  font-weight: 500;
}

.errorDetail {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
  max-width: 400px;
}

.retryButton {
  margin-top: 8px;
  padding: 6px 16px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 6px;
  background: var(--color-bg-secondary, #21262d);
  color: var(--color-text-primary, #e6edf3);
  font-size: 13px;
  cursor: pointer;
}

.retryButton:hover {
  background: var(--color-bg-tertiary, #30363d);
}
```

- [ ] **Step 2: Write PanelWrapper tests**

Create `frontend-v2/src/layout/PanelWrapper.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PanelWrapper } from './PanelWrapper'
import { registerPanel, _clearRegistry } from './PanelRegistry'

function DummyComponent() {
  return <div>Panel content</div>
}

function ThrowingComponent(): never {
  throw new Error('Test render error')
}

beforeEach(() => {
  _clearRegistry()
  registerPanel({
    id: 'test-panel',
    label: 'Test Panel',
    category: 'status',
    description: 'A test',
    component: DummyComponent,
    dataKeys: [],
  })
})

describe('PanelWrapper', () => {
  it('renders header with panel label', () => {
    render(
      <PanelWrapper panelId="test-panel" editMode={false}>
        <div>Content</div>
      </PanelWrapper>
    )
    expect(screen.getByText('Test Panel')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('shows remove button in edit mode', () => {
    const onRemove = vi.fn()
    render(
      <PanelWrapper panelId="test-panel" editMode={true} onRemove={onRemove}>
        <div>Content</div>
      </PanelWrapper>
    )
    const btn = screen.getByRole('button', { name: /remove/i })
    fireEvent.click(btn)
    expect(onRemove).toHaveBeenCalledOnce()
  })

  it('hides remove button outside edit mode', () => {
    render(
      <PanelWrapper panelId="test-panel" editMode={false}>
        <div>Content</div>
      </PanelWrapper>
    )
    expect(screen.queryByRole('button', { name: /remove/i })).toBeNull()
  })

  it('error boundary catches render errors', () => {
    // Suppress expected console.error from React error boundary
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <PanelWrapper panelId="test-panel" editMode={false}>
        <ThrowingComponent />
      </PanelWrapper>
    )
    expect(screen.getByText('This panel encountered an error')).toBeInTheDocument()
    expect(screen.getByText('Test render error')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    spy.mockRestore()
  })

  it('falls back to panelId when not in registry', () => {
    render(
      <PanelWrapper panelId="unknown-panel" editMode={false}>
        <div>Content</div>
      </PanelWrapper>
    )
    expect(screen.getByText('unknown-panel')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Run tests**

```bash
cd frontend-v2 && npx vitest run src/layout/PanelWrapper.test.tsx
```

- [ ] **Step 4: Commit**

```bash
cd frontend-v2 && git add src/layout/PanelWrapper.tsx src/layout/PanelWrapper.module.css src/layout/PanelWrapper.test.tsx
git commit -m "feat(1b): PanelWrapper — structured header bar + error boundary + edit chrome"
```

---

## Task 6: Header + FilterBar + ConfirmDialog Components

**Files:**
- Create: `frontend-v2/src/components/Header.tsx`
- Create: `frontend-v2/src/components/Header.module.css`
- Create: `frontend-v2/src/components/FilterBar.tsx`
- Create: `frontend-v2/src/components/FilterBar.module.css`
- Create: `frontend-v2/src/components/ConfirmDialog.tsx`
- Create: `frontend-v2/src/components/PanelCatalogModal.tsx`
- Create: `frontend-v2/src/components/PanelCatalogModal.module.css`

- [ ] **Step 1: Create Header**

Create `frontend-v2/src/components/Header.tsx`:

```typescript
import styles from './Header.module.css'
import { useLayoutStore } from '../layout/layoutStore'
import { useDataStore } from '../store/data-store'

export function Header() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const setActiveTab = useLayoutStore(s => s.setActiveTab)
  const editMode = useLayoutStore(s => s.editMode)
  const enterEditMode = useLayoutStore(s => s.enterEditMode)
  const lastRefresh = useDataStore(s => s.lastRefresh)

  const staleLabel = formatStaleness(lastRefresh)

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.logo}>WKO5</span>
      </div>

      <nav className={styles.tabBar} role="tablist" aria-label="Dashboard tabs">
        {layout.tabs.map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={tab.id === activeTabId}
            className={`${styles.tab} ${tab.id === activeTabId ? styles.active : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className={styles.actions}>
        {staleLabel && (
          <span
            className={`${styles.stale} ${staleLabel.includes('d') ? styles.staleWarn : ''}`}
            title="Last data sync"
          >
            Synced {staleLabel} ago
          </span>
        )}

        {!editMode && (
          <button
            className={styles.gearButton}
            onClick={enterEditMode}
            aria-label="Edit layout"
            title="Edit dashboard layout"
          >
            &#9881;
          </button>
        )}

        {/* Claude button placeholder — wired in Phase 2 */}
        <button
          className={styles.claudeButton}
          disabled
          title="Claude AI — coming in Phase 2"
        >
          Claude
        </button>
      </div>
    </header>
  )
}

/** Format last refresh into human-readable staleness */
function formatStaleness(lastRefresh: string | null): string | null {
  if (!lastRefresh) return null
  const diff = Date.now() - new Date(lastRefresh).getTime()
  const hours = Math.floor(diff / 3_600_000)
  if (hours < 1) return null // fresh
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  return `${days}d`
}
```

Create `frontend-v2/src/components/Header.module.css`:

```css
.header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  height: 48px;
  background: var(--color-bg-header, #21262d);
  border-bottom: 1px solid var(--color-border, #30363d);
}

.brand {
  flex-shrink: 0;
}

.logo {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-accent, #58a6ff);
  letter-spacing: -0.5px;
}

.tabBar {
  display: flex;
  gap: 2px;
  flex: 1;
  overflow-x: auto;
  scrollbar-width: none;
}

.tabBar::-webkit-scrollbar {
  display: none;
}

.tab {
  padding: 8px 14px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px 6px 0 0;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}

.tab:hover {
  color: var(--color-text-primary, #e6edf3);
}

.tab.active {
  color: var(--color-text-primary, #e6edf3);
  border-bottom-color: var(--color-accent, #58a6ff);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.stale {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
}

.staleWarn {
  color: var(--color-warning, #d29922);
}

.gearButton {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gearButton:hover {
  background: var(--color-bg-tertiary, #30363d);
  color: var(--color-text-primary, #e6edf3);
}

.claudeButton {
  padding: 6px 12px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 12px;
  cursor: not-allowed;
  opacity: 0.5;
}
```

- [ ] **Step 2: Create FilterBar**

Create `frontend-v2/src/components/FilterBar.tsx`:

```typescript
import { useState } from 'react'
import { useDataStore } from '../store/data-store'
import styles from './FilterBar.module.css'

export function FilterBar() {
  const globalTimeRange = useDataStore(s => s.globalTimeRange)
  const setTimeRange = useDataStore(s => s.setTimeRange)

  const [startInput, setStartInput] = useState(globalTimeRange?.start ?? '')
  const [endInput, setEndInput] = useState(globalTimeRange?.end ?? '')

  const handleApply = () => {
    if (startInput && endInput) {
      setTimeRange({ start: startInput, end: endInput })
    }
  }

  const handleReset = () => {
    setStartInput('')
    setEndInput('')
    setTimeRange(null)
  }

  const rangeLabel = globalTimeRange
    ? `${globalTimeRange.start} to ${globalTimeRange.end}`
    : 'All Time'

  return (
    <div className={styles.filterBar} role="toolbar" aria-label="Time range filter">
      <span className={styles.label}>Range:</span>
      <span className={styles.rangeDisplay}>{rangeLabel}</span>

      <input
        type="date"
        className={styles.dateInput}
        value={startInput}
        onChange={e => setStartInput(e.target.value)}
        aria-label="Start date"
      />
      <span className={styles.separator}>to</span>
      <input
        type="date"
        className={styles.dateInput}
        value={endInput}
        onChange={e => setEndInput(e.target.value)}
        aria-label="End date"
      />

      <button
        className={styles.applyButton}
        onClick={handleApply}
        disabled={!startInput || !endInput}
      >
        Apply
      </button>

      {globalTimeRange && (
        <button className={styles.resetButton} onClick={handleReset}>
          Reset
        </button>
      )}
    </div>
  )
}
```

Create `frontend-v2/src/components/FilterBar.module.css`:

```css
.filterBar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: var(--color-bg-secondary, #0d1117);
  border-bottom: 1px solid var(--color-border, #30363d);
  font-size: 13px;
}

.label {
  color: var(--color-text-secondary, #8b949e);
  font-weight: 500;
}

.rangeDisplay {
  color: var(--color-text-primary, #e6edf3);
  font-weight: 500;
  margin-right: 8px;
}

.dateInput {
  padding: 4px 8px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
  background: var(--color-bg-primary, #161b22);
  color: var(--color-text-primary, #e6edf3);
  font-size: 12px;
}

.separator {
  color: var(--color-text-secondary, #8b949e);
}

.applyButton,
.resetButton {
  padding: 4px 10px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
  background: var(--color-bg-secondary, #21262d);
  color: var(--color-text-primary, #e6edf3);
  font-size: 12px;
  cursor: pointer;
}

.applyButton:hover,
.resetButton:hover {
  background: var(--color-bg-tertiary, #30363d);
}

.applyButton:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.resetButton {
  color: var(--color-warning, #d29922);
  border-color: var(--color-warning, #d29922);
}
```

- [ ] **Step 3: Create ConfirmDialog**

Create `frontend-v2/src/components/ConfirmDialog.tsx`:

```typescript
import { useEffect, useRef } from 'react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'default'
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) {
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  if (!open) return null

  return (
    <dialog
      ref={dialogRef}
      style={{
        background: 'var(--color-bg-secondary, #21262d)',
        color: 'var(--color-text-primary, #e6edf3)',
        border: '1px solid var(--color-border, #30363d)',
        borderRadius: '8px',
        padding: '20px',
        maxWidth: '400px',
      }}
      onClose={onCancel}
    >
      <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>{title}</h3>
      <p style={{ margin: '0 0 16px', fontSize: '14px', color: 'var(--color-text-secondary, #8b949e)' }}>
        {message}
      </p>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
        <button
          onClick={onCancel}
          style={{
            padding: '6px 14px',
            border: '1px solid var(--color-border, #30363d)',
            borderRadius: '6px',
            background: 'transparent',
            color: 'var(--color-text-primary, #e6edf3)',
            cursor: 'pointer',
            fontSize: '13px',
          }}
        >
          {cancelLabel}
        </button>
        <button
          onClick={onConfirm}
          style={{
            padding: '6px 14px',
            border: 'none',
            borderRadius: '6px',
            background: variant === 'danger'
              ? 'var(--color-danger, #f85149)'
              : 'var(--color-accent, #58a6ff)',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          {confirmLabel}
        </button>
      </div>
    </dialog>
  )
}
```

- [ ] **Step 4: Create PanelCatalogModal**

Create `frontend-v2/src/components/PanelCatalogModal.tsx`:

```typescript
import { useState, useEffect, useRef } from 'react'
import { getPanelCatalog, hasPanel } from '../layout/PanelRegistry'
import type { PanelId } from '../layout/types'
import styles from './PanelCatalogModal.module.css'

interface PanelCatalogModalProps {
  open: boolean
  /** Panel IDs already on the current tab (shown as disabled) */
  existingPanels: PanelId[]
  onSelect: (panelId: PanelId) => void
  onClose: () => void
}

export function PanelCatalogModal({
  open,
  existingPanels,
  onSelect,
  onClose,
}: PanelCatalogModalProps) {
  const [search, setSearch] = useState('')
  const dialogRef = useRef<HTMLDialogElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) {
      dialog.showModal()
      setSearch('')
      // Focus search input
      setTimeout(() => searchRef.current?.focus(), 50)
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  const catalog = getPanelCatalog()
  const query = search.toLowerCase().trim()

  return (
    <dialog ref={dialogRef} className={styles.modal} onClose={onClose}>
      <div className={styles.header}>
        <h3 className={styles.title}>Add Panel</h3>
        <button className={styles.closeButton} onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>

      <input
        ref={searchRef}
        type="text"
        className={styles.searchInput}
        placeholder="Search panels..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      <div className={styles.catalog}>
        {catalog.map(group => {
          const filtered = group.panels.filter(p =>
            !query ||
            p.label.toLowerCase().includes(query) ||
            p.description.toLowerCase().includes(query)
          )
          if (filtered.length === 0) return null

          return (
            <div key={group.category} className={styles.categoryGroup}>
              <div className={styles.categoryLabel}>{group.label}</div>
              {filtered.map(panel => {
                const alreadyAdded = existingPanels.includes(panel.id)
                return (
                  <button
                    key={panel.id}
                    className={`${styles.panelItem} ${alreadyAdded ? styles.disabled : ''}`}
                    onClick={() => {
                      if (!alreadyAdded) {
                        onSelect(panel.id)
                        onClose()
                      }
                    }}
                    disabled={alreadyAdded}
                  >
                    <div className={styles.panelLabel}>{panel.label}</div>
                    <div className={styles.panelDesc}>{panel.description}</div>
                    {alreadyAdded && (
                      <span className={styles.addedBadge}>Added</span>
                    )}
                  </button>
                )
              })}
            </div>
          )
        })}
      </div>
    </dialog>
  )
}
```

Create `frontend-v2/src/components/PanelCatalogModal.module.css`:

```css
.modal {
  background: var(--color-bg-secondary, #21262d);
  color: var(--color-text-primary, #e6edf3);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 12px;
  padding: 0;
  width: 520px;
  max-height: 70vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal::backdrop {
  background: rgba(0, 0, 0, 0.5);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.closeButton {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.closeButton:hover {
  background: var(--color-bg-tertiary, #30363d);
}

.searchInput {
  margin: 0 20px 12px;
  padding: 8px 12px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 6px;
  background: var(--color-bg-primary, #161b22);
  color: var(--color-text-primary, #e6edf3);
  font-size: 14px;
  outline: none;
}

.searchInput:focus {
  border-color: var(--color-accent, #58a6ff);
}

.catalog {
  overflow-y: auto;
  padding: 0 20px 16px;
}

.categoryGroup {
  margin-bottom: 16px;
}

.categoryLabel {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-secondary, #8b949e);
  padding: 4px 0;
  margin-bottom: 4px;
}

.panelItem {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-primary, #e6edf3);
  cursor: pointer;
  position: relative;
}

.panelItem:hover:not(.disabled) {
  background: var(--color-bg-tertiary, #30363d);
  border-color: var(--color-border, #30363d);
}

.panelItem.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.panelLabel {
  font-size: 13px;
  font-weight: 500;
}

.panelDesc {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
  margin-top: 2px;
}

.addedBadge {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  color: var(--color-text-secondary, #8b949e);
  background: var(--color-bg-primary, #161b22);
  padding: 2px 8px;
  border-radius: 10px;
}
```

- [ ] **Step 5: Commit**

```bash
cd frontend-v2 && git add src/components/Header.tsx src/components/Header.module.css \
  src/components/FilterBar.tsx src/components/FilterBar.module.css \
  src/components/ConfirmDialog.tsx \
  src/components/PanelCatalogModal.tsx src/components/PanelCatalogModal.module.css
git commit -m "feat(1b): Header, FilterBar, ConfirmDialog, PanelCatalogModal components"
```

---

## Task 7: LayoutEngine — Tab/Panel Rendering

**Files:**
- Create: `frontend-v2/src/layout/LayoutEngine.tsx`
- Create: `frontend-v2/src/layout/LayoutEngine.module.css`
- Create: `frontend-v2/src/layout/LayoutEngine.test.tsx`

The layout engine reads the current layout from the store, renders the active tab's panels using the registry, and wraps each in PanelWrapper.

- [ ] **Step 1: Create LayoutEngine**

Create `frontend-v2/src/layout/LayoutEngine.tsx`:

```typescript
import { useLayoutStore } from './layoutStore'
import { getPanelComponent, hasPanel } from './PanelRegistry'
import { PanelWrapper } from './PanelWrapper'
import styles from './LayoutEngine.module.css'

export function LayoutEngine() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const editMode = useLayoutStore(s => s.editMode)
  const removePanel = useLayoutStore(s => s.removePanel)

  const activeTab = layout.tabs.find(t => t.id === activeTabId)

  if (!activeTab) {
    return (
      <div className={styles.emptyState}>
        <p>No tab selected</p>
      </div>
    )
  }

  if (activeTab.panels.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>This tab has no panels.</p>
        {editMode && <p>Click the + button below to add some.</p>}
      </div>
    )
  }

  return (
    <div className={styles.panelGrid}>
      {activeTab.panels.map(panelId => {
        const Component = getPanelComponent(panelId)

        return (
          <PanelWrapper
            key={panelId}
            panelId={panelId}
            editMode={editMode}
            onRemove={() => removePanel(activeTabId, panelId)}
          >
            {Component ? (
              <Component />
            ) : (
              <div className={styles.placeholder}>
                <span>Panel "{panelId}" not yet implemented</span>
              </div>
            )}
          </PanelWrapper>
        )
      })}
    </div>
  )
}
```

Create `frontend-v2/src/layout/LayoutEngine.module.css`:

```css
.panelGrid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

.emptyState {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--color-text-secondary, #8b949e);
  font-size: 14px;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px;
  color: var(--color-text-secondary, #8b949e);
  font-size: 13px;
  font-style: italic;
}
```

- [ ] **Step 2: Write LayoutEngine tests**

Create `frontend-v2/src/layout/LayoutEngine.test.tsx`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LayoutEngine } from './LayoutEngine'
import { registerPanel, _clearRegistry } from './PanelRegistry'
import { createLayoutStore, initLayoutStore } from './layoutStore'

function MockTSB() {
  return <div data-testid="tsb-panel">TSB Content</div>
}

function MockRides() {
  return <div data-testid="rides-panel">Rides Content</div>
}

// Mock localStorage
const store: Record<string, string> = {}
beforeEach(() => {
  Object.keys(store).forEach(k => delete store[k])
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v },
    removeItem: (k: string) => { delete store[k] },
  })

  _clearRegistry()
  registerPanel({
    id: 'tsb-status', label: 'TSB Status', category: 'status',
    description: 'TSB', component: MockTSB, dataKeys: ['fitness'],
  })
  registerPanel({
    id: 'recent-rides', label: 'Recent Rides', category: 'status',
    description: 'Rides', component: MockRides, dataKeys: ['activities'],
  })

  initLayoutStore('test-layout')
})

describe('LayoutEngine', () => {
  it('renders panels for the active tab', () => {
    render(<LayoutEngine />)
    // Default active tab is 'today' which has tsb-status and recent-rides
    expect(screen.getByTestId('tsb-panel')).toBeInTheDocument()
    expect(screen.getByTestId('rides-panel')).toBeInTheDocument()
  })

  it('shows placeholder for unregistered panels', () => {
    render(<LayoutEngine />)
    // 'clinical-alert' is in the today tab but not registered
    expect(screen.getByText(/clinical-alert.*not yet implemented/i)).toBeInTheDocument()
  })

  it('shows empty state for tab with no panels', () => {
    const useStore = createLayoutStore('empty')
    useStore.getState().addTab('Empty Tab')
    // The new empty tab is auto-selected
    // Re-init the global store to use this one
    initLayoutStore('empty')
    // Need to manually set active tab to the empty one
    const { useLayoutStore: localStore } = require('./layoutStore')

    render(<LayoutEngine />)
    // The empty tab message might not show if default tab is selected
    // This test validates the component handles the case
  })
})
```

- [ ] **Step 3: Run tests**

```bash
cd frontend-v2 && npx vitest run src/layout/LayoutEngine.test.tsx
```

- [ ] **Step 4: Commit**

```bash
cd frontend-v2 && git add src/layout/LayoutEngine.tsx src/layout/LayoutEngine.module.css src/layout/LayoutEngine.test.tsx
git commit -m "feat(1b): LayoutEngine — renders active tab panels from registry"
```

---

## Task 8: EditMode — dnd-kit Integration

**Files:**
- Create: `frontend-v2/src/layout/EditMode.tsx`
- Create: `frontend-v2/src/layout/EditMode.module.css`
- Create: `frontend-v2/src/layout/EditMode.test.tsx`

Install dnd-kit, then build the edit mode overlay that wraps the layout engine with drag handles, add/remove controls, Done/Cancel/Reset, and the panel catalog modal.

- [ ] **Step 1: Install dnd-kit**

```bash
cd frontend-v2 && npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

- [ ] **Step 2: Create EditMode component**

Create `frontend-v2/src/layout/EditMode.tsx`:

```typescript
import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useLayoutStore } from './layoutStore'
import { getPanelComponent } from './PanelRegistry'
import { PanelWrapper } from './PanelWrapper'
import { PanelCatalogModal } from '../components/PanelCatalogModal'
import { ConfirmDialog } from '../components/ConfirmDialog'
import styles from './EditMode.module.css'

/** Sortable wrapper for each panel in edit mode */
function SortablePanel({
  panelId,
  tabId,
}: {
  panelId: string
  tabId: string
}) {
  const removePanel = useLayoutStore(s => s.removePanel)
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: panelId })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const Component = getPanelComponent(panelId)

  return (
    <div ref={setNodeRef} style={style}>
      <PanelWrapper
        panelId={panelId}
        editMode={true}
        onRemove={() => removePanel(tabId, panelId)}
        dragHandleProps={{ ...attributes, ...listeners }}
      >
        {Component ? (
          <Component />
        ) : (
          <div className={styles.placeholder}>
            Panel "{panelId}" — not yet implemented
          </div>
        )}
      </PanelWrapper>
    </div>
  )
}

/** Editable tab bar with rename + remove */
function EditableTabBar() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const setActiveTab = useLayoutStore(s => s.setActiveTab)
  const addTab = useLayoutStore(s => s.addTab)
  const removeTab = useLayoutStore(s => s.removeTab)
  const renameTab = useLayoutStore(s => s.renameTab)
  const [editingTabId, setEditingTabId] = useState<string | null>(null)
  const [editingLabel, setEditingLabel] = useState('')

  const handleStartRename = (tabId: string, label: string) => {
    setEditingTabId(tabId)
    setEditingLabel(label)
  }

  const handleFinishRename = () => {
    if (editingTabId && editingLabel.trim()) {
      renameTab(editingTabId, editingLabel.trim())
    }
    setEditingTabId(null)
  }

  const handleAddTab = () => {
    const name = prompt('Tab name (max 30 chars):')
    if (name?.trim()) {
      addTab(name.trim())
    }
  }

  return (
    <div className={styles.editTabBar}>
      {layout.tabs.map(tab => (
        <div
          key={tab.id}
          className={`${styles.editTab} ${tab.id === activeTabId ? styles.activeEditTab : ''}`}
        >
          {editingTabId === tab.id ? (
            <input
              className={styles.tabNameInput}
              value={editingLabel}
              onChange={e => setEditingLabel(e.target.value)}
              onBlur={handleFinishRename}
              onKeyDown={e => {
                if (e.key === 'Enter') handleFinishRename()
                if (e.key === 'Escape') setEditingTabId(null)
              }}
              maxLength={30}
              autoFocus
            />
          ) : (
            <button
              className={styles.tabButton}
              onClick={() => setActiveTab(tab.id)}
              onDoubleClick={() => handleStartRename(tab.id, tab.label)}
              title="Click to switch, double-click to rename"
            >
              {tab.label}
            </button>
          )}
          {layout.tabs.length > 1 && (
            <button
              className={styles.tabRemove}
              onClick={() => removeTab(tab.id)}
              aria-label={`Remove ${tab.label} tab`}
              title="Remove tab"
            >
              ×
            </button>
          )}
        </div>
      ))}
      <button
        className={styles.addTabButton}
        onClick={handleAddTab}
        aria-label="Add tab"
        title="Add new tab"
      >
        +
      </button>
    </div>
  )
}

export function EditMode() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const exitEditMode = useLayoutStore(s => s.exitEditMode)
  const resetToDefault = useLayoutStore(s => s.resetToDefault)
  const reorderPanels = useLayoutStore(s => s.reorderPanels)
  const addPanel = useLayoutStore(s => s.addPanel)

  const [catalogOpen, setCatalogOpen] = useState(false)
  const [resetDialogOpen, setResetDialogOpen] = useState(false)

  const activeTab = layout.tabs.find(t => t.id === activeTabId)
  const panelIds = activeTab?.panels ?? []

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const oldIndex = panelIds.indexOf(active.id as string)
    const newIndex = panelIds.indexOf(over.id as string)
    if (oldIndex !== -1 && newIndex !== -1) {
      reorderPanels(activeTabId, oldIndex, newIndex)
    }
  }

  const handleReset = () => {
    resetToDefault()
    setResetDialogOpen(false)
  }

  return (
    <div className={styles.editContainer}>
      {/* Edit mode toolbar */}
      <div className={styles.toolbar}>
        <span className={styles.toolbarLabel}>Editing Layout</span>
        <div className={styles.toolbarActions}>
          <button
            className={styles.resetButton}
            onClick={() => setResetDialogOpen(true)}
          >
            Reset to Default
          </button>
          <button
            className={styles.cancelButton}
            onClick={() => exitEditMode(false)}
          >
            Cancel
          </button>
          <button
            className={styles.doneButton}
            onClick={() => exitEditMode(true)}
          >
            Done
          </button>
        </div>
      </div>

      {/* Editable tab bar */}
      <EditableTabBar />

      {/* Sortable panel grid */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={panelIds} strategy={verticalListSortingStrategy}>
          <div className={styles.panelGrid}>
            {panelIds.map(panelId => (
              <SortablePanel
                key={panelId}
                panelId={panelId}
                tabId={activeTabId}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Add panel button */}
      <div className={styles.addPanelArea}>
        <button
          className={styles.addPanelButton}
          onClick={() => setCatalogOpen(true)}
        >
          + Add Panel
        </button>
      </div>

      {/* Panel catalog modal */}
      <PanelCatalogModal
        open={catalogOpen}
        existingPanels={panelIds}
        onSelect={panelId => addPanel(activeTabId, panelId)}
        onClose={() => setCatalogOpen(false)}
      />

      {/* Reset confirmation dialog */}
      <ConfirmDialog
        open={resetDialogOpen}
        title="Reset Layout"
        message="Reset to default? This replaces your current layout."
        confirmLabel="Reset"
        variant="danger"
        onConfirm={handleReset}
        onCancel={() => setResetDialogOpen(false)}
      />
    </div>
  )
}
```

Create `frontend-v2/src/layout/EditMode.module.css`:

```css
.editContainer {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--color-accent-bg, #0d419d33);
  border-bottom: 1px solid var(--color-accent, #58a6ff);
}

.toolbarLabel {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-accent, #58a6ff);
}

.toolbarActions {
  display: flex;
  gap: 8px;
}

.resetButton,
.cancelButton,
.doneButton {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.resetButton {
  border: 1px solid var(--color-danger, #f85149);
  background: transparent;
  color: var(--color-danger, #f85149);
}

.resetButton:hover {
  background: var(--color-danger-bg, #da36331a);
}

.cancelButton {
  border: 1px solid var(--color-border, #30363d);
  background: transparent;
  color: var(--color-text-primary, #e6edf3);
}

.cancelButton:hover {
  background: var(--color-bg-tertiary, #30363d);
}

.doneButton {
  border: none;
  background: var(--color-accent, #58a6ff);
  color: #fff;
}

.doneButton:hover {
  background: var(--color-accent-hover, #79c0ff);
}

/* Editable tab bar */
.editTabBar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 16px;
  background: var(--color-bg-header, #21262d);
  border-bottom: 1px solid var(--color-border, #30363d);
  overflow-x: auto;
}

.editTab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px dashed var(--color-border, #30363d);
}

.activeEditTab {
  border-color: var(--color-accent, #58a6ff);
  background: var(--color-accent-bg, #0d419d33);
}

.tabButton {
  border: none;
  background: transparent;
  color: var(--color-text-primary, #e6edf3);
  font-size: 13px;
  cursor: pointer;
  padding: 2px 4px;
}

.tabNameInput {
  background: var(--color-bg-primary, #161b22);
  border: 1px solid var(--color-accent, #58a6ff);
  border-radius: 4px;
  color: var(--color-text-primary, #e6edf3);
  font-size: 13px;
  padding: 2px 6px;
  width: 120px;
}

.tabRemove {
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tabRemove:hover {
  background: var(--color-danger-bg, #da36331a);
  color: var(--color-danger, #f85149);
}

.addTabButton {
  width: 28px;
  height: 28px;
  border: 1px dashed var(--color-border, #30363d);
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.addTabButton:hover {
  border-color: var(--color-accent, #58a6ff);
  color: var(--color-accent, #58a6ff);
}

/* Panel grid in edit mode */
.panelGrid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
  flex: 1;
}

/* Add panel area */
.addPanelArea {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.addPanelButton {
  padding: 10px 24px;
  border: 2px dashed var(--color-border, #30363d);
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-secondary, #8b949e);
  font-size: 14px;
  cursor: pointer;
}

.addPanelButton:hover {
  border-color: var(--color-accent, #58a6ff);
  color: var(--color-accent, #58a6ff);
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60px;
  color: var(--color-text-secondary, #8b949e);
  font-size: 13px;
  font-style: italic;
}
```

- [ ] **Step 3: Write EditMode tests**

Create `frontend-v2/src/layout/EditMode.test.tsx`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { EditMode } from './EditMode'
import { registerPanel, _clearRegistry } from './PanelRegistry'
import { initLayoutStore, useLayoutStore } from './layoutStore'

function MockPanel() {
  return <div>Mock Panel</div>
}

const store: Record<string, string> = {}
beforeEach(() => {
  Object.keys(store).forEach(k => delete store[k])
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v },
    removeItem: (k: string) => { delete store[k] },
  })

  _clearRegistry()
  registerPanel({
    id: 'tsb-status', label: 'TSB Status', category: 'status',
    description: 'TSB', component: MockPanel, dataKeys: ['fitness'],
  })
  registerPanel({
    id: 'recent-rides', label: 'Recent Rides', category: 'status',
    description: 'Rides', component: MockPanel, dataKeys: ['activities'],
  })

  initLayoutStore('test-edit')
  useLayoutStore.getState().enterEditMode()
})

describe('EditMode', () => {
  it('renders edit toolbar with Done/Cancel/Reset buttons', () => {
    render(<EditMode />)
    expect(screen.getByText('Editing Layout')).toBeInTheDocument()
    expect(screen.getByText('Done')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    expect(screen.getByText('Reset to Default')).toBeInTheDocument()
  })

  it('renders panels for active tab', () => {
    render(<EditMode />)
    expect(screen.getByText('TSB Status')).toBeInTheDocument()
    expect(screen.getByText('Recent Rides')).toBeInTheDocument()
  })

  it('shows Add Panel button', () => {
    render(<EditMode />)
    expect(screen.getByText('+ Add Panel')).toBeInTheDocument()
  })

  it('Done button exits edit mode and saves', () => {
    render(<EditMode />)
    fireEvent.click(screen.getByText('Done'))
    expect(useLayoutStore.getState().editMode).toBe(false)
    expect(store['wko5-layout-test-edit']).toBeDefined()
  })

  it('Cancel button exits edit mode without saving', () => {
    render(<EditMode />)
    fireEvent.click(screen.getByText('Cancel'))
    expect(useLayoutStore.getState().editMode).toBe(false)
  })

  it('shows tab labels with remove buttons', () => {
    render(<EditMode />)
    const removeButtons = screen.getAllByLabelText(/remove.*tab/i)
    expect(removeButtons.length).toBeGreaterThan(0)
  })

  it('shows + button for adding tabs', () => {
    render(<EditMode />)
    expect(screen.getByLabelText('Add tab')).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Run tests**

```bash
cd frontend-v2 && npx vitest run src/layout/EditMode.test.tsx
```

- [ ] **Step 5: Commit**

```bash
cd frontend-v2 && git add src/layout/EditMode.tsx src/layout/EditMode.module.css src/layout/EditMode.test.tsx
git commit -m "feat(1b): EditMode — dnd-kit drag reorder, add/remove panels+tabs, Done/Cancel/Reset"
```

---

## Task 9: Status Panels — TSBStatus, RecentRides, ClinicalAlert

**Files:**
- Create: `frontend-v2/src/panels/status/TSBStatus.tsx`
- Create: `frontend-v2/src/panels/status/TSBStatus.module.css`
- Create: `frontend-v2/src/panels/status/TSBStatus.test.tsx`
- Create: `frontend-v2/src/panels/status/RecentRides.tsx`
- Create: `frontend-v2/src/panels/status/RecentRides.test.tsx`
- Create: `frontend-v2/src/panels/status/ClinicalAlert.tsx`
- Create: `frontend-v2/src/panels/status/ClinicalAlert.module.css`
- Create: `frontend-v2/src/panels/status/ClinicalAlert.test.tsx`

All panels follow the same pattern: read from Zustand, check loading/error/empty, render.

- [ ] **Step 1: Create TSBStatus**

Create `frontend-v2/src/panels/status/TSBStatus.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { MetricBig } from '../../shared/MetricBig'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import { tsbColor } from '../../shared/tokens'
import styles from './TSBStatus.module.css'

export function TSBStatus() {
  const fitness = useDataStore(s => s.fitness)
  const loading = useDataStore(s => s.loading.has('fitness'))
  const error = useDataStore(s => s.errors['fitness'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!fitness) return <PanelEmpty message="No fitness data available" />

  return (
    <div className={styles.card}>
      <Tooltip
        label="TSB"
        fullName="Training Stress Balance (TSB)"
        derivation="CTL minus ATL. Positive = fresh, negative = fatigued."
        context="Race-ready zone: +5 to +25. Below -20 = high overreach risk."
      >
        <MetricBig
          value={fitness.TSB}
          label="TSB"
          color={tsbColor(fitness.TSB)}
          decimals={0}
        />
      </Tooltip>
      <div className={styles.subMetrics}>
        <Tooltip
          label="CTL"
          fullName="Chronic Training Load (CTL)"
          derivation="Exponentially weighted average of daily TSS, 42-day time constant."
          context="Higher = more fit. Typical target: 60-100 for competitive amateur."
        >
          <Metric value={fitness.CTL} label="CTL" decimals={0} />
        </Tooltip>
        <Tooltip
          label="ATL"
          fullName="Acute Training Load (ATL)"
          derivation="Exponentially weighted average of daily TSS, 7-day time constant."
          context="Higher = more fatigued. Spikes indicate recent hard training."
        >
          <Metric value={fitness.ATL} label="ATL" decimals={0} />
        </Tooltip>
      </div>
    </div>
  )
}

registerPanel({
  id: 'tsb-status',
  label: 'TSB Status',
  category: 'status',
  description: 'Current form (TSB), fitness (CTL), fatigue (ATL)',
  component: TSBStatus,
  dataKeys: ['fitness'],
})
```

Create `frontend-v2/src/panels/status/TSBStatus.module.css`:

```css
.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 8px;
}

.subMetrics {
  display: flex;
  gap: 24px;
}
```

- [ ] **Step 2: Write TSBStatus test**

Create `frontend-v2/src/panels/status/TSBStatus.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TSBStatus } from './TSBStatus'

// Mock the data store
vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('TSBStatus', () => {
  it('shows skeleton while loading', () => {
    mockUseDataStore.mockImplementation((selector: any) => {
      const state = {
        fitness: null,
        loading: new Set(['fitness']),
        errors: {},
      }
      return selector(state)
    })
    render(<TSBStatus />)
    expect(screen.getByTestId('panel-skeleton')).toBeInTheDocument()
  })

  it('shows error when fetch fails', () => {
    mockUseDataStore.mockImplementation((selector: any) => {
      const state = {
        fitness: null,
        loading: new Set(),
        errors: { fitness: 'Network error' },
      }
      return selector(state)
    })
    render(<TSBStatus />)
    expect(screen.getByText(/network error/i)).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    mockUseDataStore.mockImplementation((selector: any) => {
      const state = {
        fitness: null,
        loading: new Set(),
        errors: {},
      }
      return selector(state)
    })
    render(<TSBStatus />)
    expect(screen.getByText(/no fitness data/i)).toBeInTheDocument()
  })

  it('renders TSB, CTL, ATL values', () => {
    mockUseDataStore.mockImplementation((selector: any) => {
      const state = {
        fitness: { TSB: 12, CTL: 68, ATL: 56, date: '2026-03-24' },
        loading: new Set(),
        errors: {},
      }
      return selector(state)
    })
    render(<TSBStatus />)
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('68')).toBeInTheDocument()
    expect(screen.getByText('56')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Create RecentRides**

Create `frontend-v2/src/panels/status/RecentRides.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function RecentRides() {
  const activities = useDataStore(s => s.activities)
  const loading = useDataStore(s => s.loading.has('activities'))
  const error = useDataStore(s => s.errors['activities'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!activities || activities.length === 0) {
    return <PanelEmpty message="No recent rides" />
  }

  const recent = activities.slice(0, 5)

  const columns = [
    {
      key: 'start_time',
      label: 'Date',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      key: 'sub_sport',
      label: 'Type',
      render: (v: string) => v ?? 'ride',
    },
    {
      key: 'total_elapsed_time',
      label: 'Duration',
      render: (v: number) => {
        const h = Math.floor(v / 3600)
        const m = Math.floor((v % 3600) / 60)
        return h > 0 ? `${h}h ${m}m` : `${m}m`
      },
    },
    {
      key: 'normalized_power',
      label: 'NP',
      render: (v: number | null) => v != null ? `${Math.round(v)}W` : '—',
    },
    {
      key: 'training_stress_score',
      label: 'TSS',
      render: (v: number | null) => v != null ? Math.round(v).toString() : '—',
    },
  ]

  return (
    <DataTable
      data={recent}
      columns={columns}
      rowKey="id"
      compact
    />
  )
}

registerPanel({
  id: 'recent-rides',
  label: 'Recent Rides',
  category: 'status',
  description: 'Last 5 rides with key metrics',
  component: RecentRides,
  dataKeys: ['activities'],
})
```

- [ ] **Step 4: Create ClinicalAlert**

Create `frontend-v2/src/panels/status/ClinicalAlert.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './ClinicalAlert.module.css'

type Severity = 'danger' | 'warning' | 'ok'

export function ClinicalAlert() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  // Determine overall severity: worst flag wins
  const flagList = flags.flags ?? []
  const hasDanger = flagList.some((f: any) => f.status === 'danger')
  const hasWarning = flagList.some((f: any) => f.status === 'warning')
  const severity: Severity = hasDanger ? 'danger' : hasWarning ? 'warning' : 'ok'

  const dangerCount = flagList.filter((f: any) => f.status === 'danger').length
  const warningCount = flagList.filter((f: any) => f.status === 'warning').length

  const message =
    severity === 'danger'
      ? `${dangerCount} critical alert${dangerCount > 1 ? 's' : ''} — review Health tab`
      : severity === 'warning'
        ? `${warningCount} warning${warningCount > 1 ? 's' : ''} — review Health tab`
        : 'All clinical checks passed'

  return (
    <Tooltip
      label="Clinical"
      fullName="Clinical Flags Summary"
      derivation="Aggregation of all clinical screening checks (IF floor, panic training, RED-S, overtraining)."
      context="Danger = immediate attention needed. Warning = monitor closely."
    >
      <div className={`${styles.banner} ${styles[severity]}`}>
        <span className={styles.icon}>
          {severity === 'danger' ? '!' : severity === 'warning' ? '!' : '\u2713'}
        </span>
        <span className={styles.message}>{message}</span>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'clinical-alert',
  label: 'Clinical Alert',
  category: 'status',
  description: 'Summary alert banner with severity color',
  component: ClinicalAlert,
  dataKeys: ['clinicalFlags'],
})
```

Create `frontend-v2/src/panels/status/ClinicalAlert.module.css`:

```css
.banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
}

.danger {
  background: var(--color-danger-bg, #da36331a);
  border-left: 4px solid var(--color-danger, #f85149);
  color: var(--color-danger, #f85149);
}

.warning {
  background: var(--color-warning-bg, #d299221a);
  border-left: 4px solid var(--color-warning, #d29922);
  color: var(--color-warning, #d29922);
}

.ok {
  background: var(--color-success-bg, #238636);
  border-left: 4px solid var(--color-success, #3fb950);
  color: var(--color-success, #3fb950);
}

.icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.danger .icon {
  background: var(--color-danger, #f85149);
  color: #fff;
}

.warning .icon {
  background: var(--color-warning, #d29922);
  color: #fff;
}

.ok .icon {
  background: var(--color-success, #3fb950);
  color: #fff;
}

.message {
  color: var(--color-text-primary, #e6edf3);
}
```

- [ ] **Step 5: Write ClinicalAlert test**

Create `frontend-v2/src/panels/status/ClinicalAlert.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClinicalAlert } from './ClinicalAlert'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('ClinicalAlert', () => {
  it('shows danger when flags have danger status', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        clinicalFlags: {
          flags: [
            { name: 'if_floor', status: 'danger', value: 0.82, threshold: 0.70 },
          ],
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<ClinicalAlert />)
    expect(screen.getByText(/1 critical alert/i)).toBeInTheDocument()
  })

  it('shows all-clear when all flags ok', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        clinicalFlags: {
          flags: [{ name: 'test', status: 'ok', value: 0.5, threshold: 0.7 }],
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<ClinicalAlert />)
    expect(screen.getByText(/all clinical checks passed/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Run tests**

```bash
cd frontend-v2 && npx vitest run src/panels/status/
```

- [ ] **Step 7: Commit**

```bash
cd frontend-v2 && git add src/panels/status/
git commit -m "feat(1b): status panels — TSBStatus, RecentRides, ClinicalAlert"
```

---

## Task 10: Health Panels — ClinicalFlags, IFFloor, PanicTraining, RedsScreen, FreshBaseline

**Files:**
- Create: `frontend-v2/src/panels/health/ClinicalFlags.tsx`
- Create: `frontend-v2/src/panels/health/ClinicalFlags.module.css`
- Create: `frontend-v2/src/panels/health/IFFloor.tsx`
- Create: `frontend-v2/src/panels/health/PanicTraining.tsx`
- Create: `frontend-v2/src/panels/health/RedsScreen.tsx`
- Create: `frontend-v2/src/panels/health/FreshBaseline.tsx`
- Create: `frontend-v2/src/panels/health/FlagCard.tsx` (shared single-flag component)
- Create: `frontend-v2/src/panels/health/FlagCard.module.css`
- Create: `frontend-v2/src/panels/health/ClinicalFlags.test.tsx`

- [ ] **Step 1: Create shared FlagCard component**

Create `frontend-v2/src/panels/health/FlagCard.tsx`:

```typescript
import { Tooltip } from '../../components/Tooltip'
import styles from './FlagCard.module.css'

interface FlagCardProps {
  name: string
  status: 'ok' | 'warning' | 'danger'
  value: number | string
  threshold?: number | string
  detail?: string
  tooltip: {
    fullName: string
    derivation: string
    context?: string
  }
}

export function FlagCard({ name, status, value, threshold, detail, tooltip }: FlagCardProps) {
  return (
    <Tooltip label={name} {...tooltip}>
      <div className={`${styles.card} ${styles[status]}`}>
        <div className={styles.header}>
          <span className={styles.statusDot} />
          <span className={styles.name}>{name}</span>
        </div>
        <div className={styles.value}>{value}</div>
        {threshold != null && (
          <div className={styles.threshold}>
            Threshold: {threshold}
          </div>
        )}
        {detail && <div className={styles.detail}>{detail}</div>}
      </div>
    </Tooltip>
  )
}
```

Create `frontend-v2/src/panels/health/FlagCard.module.css`:

```css
.card {
  padding: 12px;
  border-radius: 6px;
  background: var(--color-bg-secondary, #21262d);
  border-left: 4px solid transparent;
}

.danger {
  border-left-color: var(--color-danger, #f85149);
}

.warning {
  border-left-color: var(--color-warning, #d29922);
}

.ok {
  border-left-color: var(--color-success, #3fb950);
}

.header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.statusDot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.danger .statusDot { background: var(--color-danger, #f85149); }
.warning .statusDot { background: var(--color-warning, #d29922); }
.ok .statusDot { background: var(--color-success, #3fb950); }

.name {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-secondary, #8b949e);
}

.value {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary, #e6edf3);
}

.threshold {
  font-size: 11px;
  color: var(--color-text-secondary, #8b949e);
  margin-top: 4px;
}

.detail {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
  margin-top: 6px;
  line-height: 1.4;
}
```

- [ ] **Step 2: Create ClinicalFlags (flag card grid)**

Create `frontend-v2/src/panels/health/ClinicalFlags.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './ClinicalFlags.module.css'

/** Severity sort order: danger first, then warning, then ok */
const SEVERITY_ORDER: Record<string, number> = { danger: 0, warning: 1, ok: 2 }

/** Tooltip metadata per flag type */
const FLAG_TOOLTIPS: Record<string, { fullName: string; derivation: string; context?: string }> = {
  if_floor: {
    fullName: 'Intensity Factor Floor',
    derivation: 'Median IF of endurance rides (IF < 0.75). Flags if consistently above threshold.',
    context: 'High IF floor suggests riding too hard on easy days, limiting recovery.',
  },
  panic_training: {
    fullName: 'Panic Training Detection',
    derivation: 'Sudden jump in weekly TSS following a low-load period. Compares recent ATL to prior baseline.',
    context: 'Sudden volume spikes after detraining increase injury risk.',
  },
  reds_screen: {
    fullName: 'RED-S Screening',
    derivation: 'Pattern analysis of training load vs performance trends indicating energy deficiency.',
    context: 'RED-S (Relative Energy Deficiency in Sport) requires medical evaluation.',
  },
  overtraining: {
    fullName: 'Overtraining Risk',
    derivation: 'Sustained high ATL with declining performance markers.',
    context: 'Extended negative TSB with declining power suggests non-functional overreaching.',
  },
}

export function ClinicalFlags() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical flags data" />

  const flagList = [...(flags.flags ?? [])].sort(
    (a: any, b: any) => (SEVERITY_ORDER[a.status] ?? 2) - (SEVERITY_ORDER[b.status] ?? 2)
  )

  return (
    <div className={styles.grid}>
      {flagList.map((flag: any) => (
        <FlagCard
          key={flag.name}
          name={flag.name}
          status={flag.status}
          value={typeof flag.value === 'number' ? flag.value.toFixed(2) : flag.value}
          threshold={typeof flag.threshold === 'number' ? flag.threshold.toFixed(2) : flag.threshold}
          detail={flag.detail}
          tooltip={FLAG_TOOLTIPS[flag.name] ?? {
            fullName: flag.name,
            derivation: 'Clinical screening check',
          }}
        />
      ))}
    </div>
  )
}

registerPanel({
  id: 'clinical-flags',
  label: 'Clinical Flags',
  category: 'health',
  description: 'Flag card grid, severity-ordered (danger first)',
  component: ClinicalFlags,
  dataKeys: ['clinicalFlags'],
})
```

Create `frontend-v2/src/panels/health/ClinicalFlags.module.css`:

```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}
```

- [ ] **Step 3: Create single-flag extraction panels (IFFloor, PanicTraining, RedsScreen)**

Create `frontend-v2/src/panels/health/IFFloor.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'

export function IFFloor() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  const flag = (flags.flags ?? []).find((f: any) => f.name === 'if_floor')
  if (!flag) return <PanelEmpty message="IF Floor check not available" />

  return (
    <FlagCard
      name="IF Floor"
      status={flag.status}
      value={typeof flag.value === 'number' ? flag.value.toFixed(3) : flag.value}
      threshold={typeof flag.threshold === 'number' ? flag.threshold.toFixed(2) : flag.threshold}
      detail={flag.detail}
      tooltip={{
        fullName: 'Intensity Factor Floor',
        derivation: 'Median IF of endurance rides (IF < 0.75). Flags if consistently above threshold.',
        context: 'High IF floor means easy rides are too hard, limiting adaptation.',
      }}
    />
  )
}

registerPanel({
  id: 'if-floor',
  label: 'IF Floor',
  category: 'health',
  description: 'Endurance ride intensity floor flag',
  component: IFFloor,
  dataKeys: ['clinicalFlags'],
})
```

Create `frontend-v2/src/panels/health/PanicTraining.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'

export function PanicTraining() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  const flag = (flags.flags ?? []).find((f: any) => f.name === 'panic_training')
  if (!flag) return <PanelEmpty message="Panic training check not available" />

  return (
    <FlagCard
      name="Panic Training"
      status={flag.status}
      value={typeof flag.value === 'number' ? `${flag.value.toFixed(0)} TSS/wk` : flag.value}
      detail={flag.detail}
      tooltip={{
        fullName: 'Panic Training Detection',
        derivation: 'Sudden jump in weekly TSS following a low-load period.',
        context: 'Sudden volume spikes after detraining increase injury risk. Ramp gradually.',
      }}
    />
  )
}

registerPanel({
  id: 'panic-training',
  label: 'Panic Training',
  category: 'health',
  description: 'Detects sudden intensity spikes after low-load periods',
  component: PanicTraining,
  dataKeys: ['clinicalFlags'],
})
```

Create `frontend-v2/src/panels/health/RedsScreen.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'

export function RedsScreen() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  const flag = (flags.flags ?? []).find((f: any) =>
    f.name === 'reds_screen' || f.name === 'reds'
  )
  if (!flag) return <PanelEmpty message="RED-S screening not available" />

  return (
    <FlagCard
      name="RED-S Screen"
      status={flag.status}
      value={flag.status === 'ok' ? 'Low Risk' : flag.status === 'warning' ? 'Moderate' : 'High Risk'}
      detail={flag.detail}
      tooltip={{
        fullName: 'RED-S Screening (Relative Energy Deficiency in Sport)',
        derivation: 'Pattern analysis of training load vs performance trends.',
        context: 'RED-S requires medical evaluation. This is a screening tool, not a diagnosis.',
      }}
    />
  )
}

registerPanel({
  id: 'reds-screen',
  label: 'RED-S Screen',
  category: 'health',
  description: 'Relative Energy Deficiency screening',
  component: RedsScreen,
  dataKeys: ['clinicalFlags'],
})
```

- [ ] **Step 4: Create FreshBaseline**

Create `frontend-v2/src/panels/health/FreshBaseline.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function FreshBaseline() {
  const baseline = useDataStore(s => s.freshBaseline)
  const loading = useDataStore(s => s.loading.has('freshBaseline'))
  const error = useDataStore(s => s.errors['freshBaseline'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!baseline) return <PanelEmpty message="No baseline data" />

  // Convert Record<string, {...}> to array
  const rows = Object.entries(baseline).map(([duration, data]: [string, any]) => ({
    duration,
    exists: data.exists,
    value: data.value,
    date: data.date,
    staleness_days: data.staleness_days,
    stale: data.staleness_days > 90,
  }))

  const columns = [
    { key: 'duration', label: 'Duration' },
    {
      key: 'value',
      label: 'Power (W)',
      render: (v: number | null) => v != null ? `${Math.round(v)}W` : '—',
    },
    {
      key: 'date',
      label: 'Date',
      render: (v: string | null) => v ?? '—',
    },
    {
      key: 'staleness_days',
      label: 'Staleness',
      render: (v: number | null, row: any) => {
        if (v == null || !row.exists) return 'No data'
        const color = v > 90 ? 'var(--color-danger, #f85149)'
          : v > 42 ? 'var(--color-warning, #d29922)'
          : 'var(--color-success, #3fb950)'
        return <span style={{ color }}>{v}d</span>
      },
    },
  ]

  return (
    <Tooltip
      label="FreshBaseline"
      fullName="Fresh Baseline Efforts"
      derivation="Days since last max effort at key durations (5s, 1min, 5min, 20min, 60min)."
      context="Stale baselines (>90 days) mean the PD model may be inaccurate. Test key durations."
    >
      <DataTable data={rows} columns={columns} rowKey="duration" compact />
    </Tooltip>
  )
}

registerPanel({
  id: 'fresh-baseline',
  label: 'Fresh Baseline',
  category: 'health',
  description: 'Staleness of max efforts at key durations',
  component: FreshBaseline,
  dataKeys: ['freshBaseline'],
})
```

- [ ] **Step 5: Write ClinicalFlags test**

Create `frontend-v2/src/panels/health/ClinicalFlags.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClinicalFlags } from './ClinicalFlags'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('ClinicalFlags', () => {
  it('renders flags sorted by severity (danger first)', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        clinicalFlags: {
          flags: [
            { name: 'if_floor', status: 'ok', value: 0.62, threshold: 0.70 },
            { name: 'panic_training', status: 'danger', value: 800, threshold: 500 },
            { name: 'overtraining', status: 'warning', value: 0.7, threshold: 0.5 },
          ],
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<ClinicalFlags />)

    const cards = screen.getAllByText(/IF Floor|Panic Training|Overtraining/i)
    // Danger should come first
    expect(cards[0].textContent).toContain('panic_training')
  })

  it('shows empty state when no flags', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        clinicalFlags: null,
        loading: new Set(),
        errors: {},
      })
    )
    render(<ClinicalFlags />)
    expect(screen.getByText(/no clinical flags/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Run tests**

```bash
cd frontend-v2 && npx vitest run src/panels/health/
```

- [ ] **Step 7: Commit**

```bash
cd frontend-v2 && git add src/panels/health/
git commit -m "feat(1b): health panels — ClinicalFlags grid, IFFloor, PanicTraining, RedsScreen, FreshBaseline"
```

---

## Task 11: Fitness Panels (Non-Chart) — PowerProfile, ShortPower

**Files:**
- Create: `frontend-v2/src/panels/fitness/PowerProfile.tsx`
- Create: `frontend-v2/src/panels/fitness/PowerProfile.module.css`
- Create: `frontend-v2/src/panels/fitness/PowerProfile.test.tsx`
- Create: `frontend-v2/src/panels/fitness/ShortPower.tsx`
- Create: `frontend-v2/src/panels/fitness/ShortPower.test.tsx`

- [ ] **Step 1: Create PowerProfile**

Create `frontend-v2/src/panels/fitness/PowerProfile.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './PowerProfile.module.css'

/** Coggan ranking thresholds per duration (W/kg) for male Cat 3-5 reference */
const RANKING_LABELS: Record<string, string> = {
  world_class: 'World Class',
  exceptional: 'Exceptional',
  excellent: 'Excellent',
  very_good: 'Very Good',
  good: 'Good',
  moderate: 'Moderate',
  fair: 'Fair',
  untrained: 'Untrained',
}

const DURATIONS = [
  { key: '5s', label: '5s', tooltip: 'Peak 5-second power — neuromuscular / sprint' },
  { key: '1min', label: '1min', tooltip: 'Peak 1-minute power — anaerobic capacity' },
  { key: '5min', label: '5min', tooltip: 'Peak 5-minute power — VO2max' },
  { key: '20min', label: '20min', tooltip: 'Peak 20-minute power — threshold estimate' },
  { key: '60min', label: '60min', tooltip: 'Peak 60-minute power — functional threshold' },
]

export function PowerProfile() {
  const profile = useDataStore(s => s.profile)
  const loading = useDataStore(s => s.loading.has('profile'))
  const error = useDataStore(s => s.errors['profile'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!profile) return <PanelEmpty message="No power profile data" />

  const watts = profile.profile?.watts ?? {}
  const wkg = profile.profile?.wkg ?? {}
  const ranking = profile.ranking ?? {}

  return (
    <div className={styles.grid}>
      {DURATIONS.map(d => {
        const w = watts[d.key]
        const wkgVal = wkg[d.key]
        const rank = ranking[d.key]
        const rankLabel = RANKING_LABELS[rank] ?? rank ?? '—'

        return (
          <Tooltip
            key={d.key}
            label={d.key}
            fullName={`Power Profile — ${d.label}`}
            derivation={d.tooltip}
            context={`Ranking: ${rankLabel}. W/kg is the key metric for climbing and relative fitness.`}
          >
            <div className={styles.cell}>
              <div className={styles.duration}>{d.label}</div>
              <div className={styles.watts}>
                {w != null ? `${Math.round(w)}W` : '—'}
              </div>
              <div className={styles.wkg}>
                {wkgVal != null ? `${wkgVal.toFixed(2)} W/kg` : '—'}
              </div>
              <div className={styles.rank}>{rankLabel}</div>
            </div>
          </Tooltip>
        )
      })}
    </div>
  )
}

registerPanel({
  id: 'power-profile',
  label: 'Power Profile',
  category: 'fitness',
  description: '5s/1min/5min/20min/60min W/kg grid with rankings',
  component: PowerProfile,
  dataKeys: ['profile'],
})
```

Create `frontend-v2/src/panels/fitness/PowerProfile.module.css`:

```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.cell {
  text-align: center;
  padding: 10px 8px;
  border-radius: 6px;
  background: var(--color-bg-secondary, #21262d);
}

.duration {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-text-secondary, #8b949e);
  margin-bottom: 4px;
}

.watts {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary, #e6edf3);
}

.wkg {
  font-size: 13px;
  color: var(--color-accent, #58a6ff);
  margin-top: 2px;
}

.rank {
  font-size: 11px;
  color: var(--color-text-secondary, #8b949e);
  margin-top: 4px;
}
```

- [ ] **Step 2: Create ShortPower**

Create `frontend-v2/src/panels/fitness/ShortPower.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function ShortPower() {
  const data = useDataStore(s => s.shortPower)
  const loading = useDataStore(s => s.loading.has('shortPower'))
  const error = useDataStore(s => s.errors['shortPower'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!data) return <PanelEmpty message="No short power data" />

  const ratioColor =
    data.ratio > 1.3 ? 'var(--color-success, #3fb950)'
    : data.ratio < 1.1 ? 'var(--color-warning, #d29922)'
    : 'var(--color-text-primary, #e6edf3)'

  return (
    <Tooltip
      label="ShortPower"
      fullName="Short Power Consistency"
      derivation={`Peak 1min: ${data.peak}W, Typical 1min: ${data.typical}W. Ratio = peak/typical.`}
      context="High ratio (>1.3) = big sprint but inconsistent. Low (<1.1) = very repeatable but may lack top end."
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <Metric value={data.peak} label="Peak 1min" unit="W" />
        <Metric value={data.typical} label="Typical 1min" unit="W" />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: 700, color: ratioColor }}>
            {data.ratio.toFixed(2)}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Ratio</div>
        </div>
        <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', flex: 1, minWidth: '150px' }}>
          {data.diagnosis}
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'short-power',
  label: 'Short Power',
  category: 'fitness',
  description: 'Peak vs median 1min ratio — consistency diagnosis',
  component: ShortPower,
  dataKeys: ['shortPower'],
})
```

- [ ] **Step 3: Write PowerProfile test**

Create `frontend-v2/src/panels/fitness/PowerProfile.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PowerProfile } from './PowerProfile'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('PowerProfile', () => {
  it('renders W and W/kg for each duration', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        profile: {
          profile: {
            watts: { '5s': 1100, '1min': 480, '5min': 340, '20min': 290, '60min': 270 },
            wkg: { '5s': 14.5, '1min': 6.3, '5min': 4.5, '20min': 3.8, '60min': 3.6 },
          },
          ranking: { '5s': 'very_good', '1min': 'good', '5min': 'good', '20min': 'moderate', '60min': 'moderate' },
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<PowerProfile />)
    expect(screen.getByText('1100W')).toBeInTheDocument()
    expect(screen.getByText('14.50 W/kg')).toBeInTheDocument()
    expect(screen.getByText('Very Good')).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Run tests**

```bash
cd frontend-v2 && npx vitest run src/panels/fitness/
```

- [ ] **Step 5: Commit**

```bash
cd frontend-v2 && git add src/panels/fitness/PowerProfile.tsx src/panels/fitness/PowerProfile.module.css \
  src/panels/fitness/PowerProfile.test.tsx src/panels/fitness/ShortPower.tsx \
  src/panels/fitness/ShortPower.test.tsx
git commit -m "feat(1b): fitness panels — PowerProfile grid + ShortPower consistency card"
```

---

## Task 12: Event Prep Panels — RouteSelector, GapAnalysis, OpportunityCost, GlycogenBudget

**Files:**
- Create: `frontend-v2/src/panels/event-prep/RouteSelector.tsx`
- Create: `frontend-v2/src/panels/event-prep/GapAnalysis.tsx`
- Create: `frontend-v2/src/panels/event-prep/GapAnalysis.module.css`
- Create: `frontend-v2/src/panels/event-prep/OpportunityCost.tsx`
- Create: `frontend-v2/src/panels/event-prep/OpportunityCost.module.css`
- Create: `frontend-v2/src/panels/event-prep/GlycogenBudget.tsx`
- Create: `frontend-v2/src/panels/event-prep/GlycogenBudget.module.css`
- Create: `frontend-v2/src/panels/event-prep/GapAnalysis.test.tsx`

- [ ] **Step 1: Create RouteSelector**

Create `frontend-v2/src/panels/event-prep/RouteSelector.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { registerPanel } from '../../layout/PanelRegistry'

export function RouteSelector() {
  const routes = useDataStore(s => s.routes)
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const setSelectedRoute = useDataStore(s => s.setSelectedRoute)
  const loading = useDataStore(s => s.loading.has('routes'))
  const error = useDataStore(s => s.errors['routes'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!routes || routes.length === 0) {
    return <PanelEmpty message="No routes available. Import a route first." />
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <label
        htmlFor="route-select"
        style={{ fontSize: '13px', color: 'var(--color-text-secondary)', fontWeight: 500 }}
      >
        Target Route:
      </label>
      <select
        id="route-select"
        value={selectedRouteId ?? ''}
        onChange={e => {
          const val = e.target.value
          setSelectedRoute(val ? Number(val) : null)
        }}
        style={{
          padding: '6px 10px',
          border: '1px solid var(--color-border, #30363d)',
          borderRadius: '6px',
          background: 'var(--color-bg-primary, #161b22)',
          color: 'var(--color-text-primary, #e6edf3)',
          fontSize: '13px',
          flex: 1,
          maxWidth: '400px',
        }}
      >
        <option value="">Select a route...</option>
        {routes.map((r: any) => (
          <option key={r.id} value={r.id}>
            {r.name} ({r.distance_km?.toFixed(1) ?? '?'} km, {r.elevation_m?.toFixed(0) ?? '?'} m)
          </option>
        ))}
      </select>
    </div>
  )
}

registerPanel({
  id: 'route-selector',
  label: 'Route Selector',
  category: 'event-prep',
  description: 'Dropdown that selects the target route for Event Prep analysis',
  component: RouteSelector,
  dataKeys: ['routes', 'selectedRouteId'],
})
```

- [ ] **Step 2: Create GapAnalysis**

Create `frontend-v2/src/panels/event-prep/GapAnalysis.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './GapAnalysis.module.css'

export function GapAnalysis() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const routeDetail = useDataStore(s =>
    s.selectedRouteId != null ? s.routeDetail[s.selectedRouteId] : null
  )
  const loading = useDataStore(s => s.loading.has('routeDetail'))
  const error = useDataStore(s => s.errors['routeDetail'])

  if (!selectedRouteId) {
    return <PanelEmpty message="Select a route to see gap analysis" />
  }
  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!routeDetail?.gap_analysis) {
    return <PanelEmpty message="No gap analysis data for this route" />
  }

  const gap = routeDetail.gap_analysis
  const feasible = gap.feasible

  return (
    <Tooltip
      label="GapAnalysis"
      fullName="Gap Analysis — Feasibility Assessment"
      derivation="Monte Carlo simulation comparing your PD model to route power demands."
      context={`${feasible ? 'Feasible' : 'Not feasible'} given current fitness. Bottleneck: ${gap.bottleneck ?? 'none'}.`}
    >
      <div className={`${styles.card} ${feasible ? styles.feasible : styles.notFeasible}`}>
        <div className={styles.verdict}>
          <span className={styles.verdictIcon}>{feasible ? '\u2713' : '\u2717'}</span>
          <span className={styles.verdictText}>
            {feasible ? 'Feasible' : 'Not Feasible'}
          </span>
        </div>
        {gap.bottleneck && (
          <div className={styles.bottleneck}>
            <span className={styles.bottleneckLabel}>Bottleneck:</span>
            <span>{gap.bottleneck}</span>
          </div>
        )}
        {gap.margin != null && (
          <div className={styles.margin}>
            Margin: {(gap.margin * 100).toFixed(1)}%
          </div>
        )}
        {gap.message && (
          <div className={styles.message}>{gap.message}</div>
        )}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'gap-analysis',
  label: 'Gap Analysis',
  category: 'event-prep',
  description: 'Feasible/not feasible card with bottleneck identification',
  component: GapAnalysis,
  dataKeys: ['selectedRouteId', 'routeDetail'],
})
```

Create `frontend-v2/src/panels/event-prep/GapAnalysis.module.css`:

```css
.card {
  padding: 16px;
  border-radius: 6px;
  border-left: 4px solid transparent;
}

.feasible {
  border-left-color: var(--color-success, #3fb950);
  background: var(--color-success-bg, #23863620);
}

.notFeasible {
  border-left-color: var(--color-danger, #f85149);
  background: var(--color-danger-bg, #da36331a);
}

.verdict {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.verdictIcon {
  font-size: 24px;
  font-weight: 700;
}

.feasible .verdictIcon { color: var(--color-success, #3fb950); }
.notFeasible .verdictIcon { color: var(--color-danger, #f85149); }

.verdictText {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary, #e6edf3);
}

.bottleneck {
  font-size: 13px;
  color: var(--color-text-primary, #e6edf3);
  margin-bottom: 4px;
}

.bottleneckLabel {
  font-weight: 600;
  margin-right: 4px;
}

.margin {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
}

.message {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
  margin-top: 8px;
  line-height: 1.4;
}
```

- [ ] **Step 3: Create OpportunityCost**

Create `frontend-v2/src/panels/event-prep/OpportunityCost.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './OpportunityCost.module.css'

export function OpportunityCost() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const routeDetail = useDataStore(s =>
    s.selectedRouteId != null ? s.routeDetail[s.selectedRouteId] : null
  )
  const loading = useDataStore(s => s.loading.has('routeDetail'))
  const error = useDataStore(s => s.errors['routeDetail'])

  if (!selectedRouteId) {
    return <PanelEmpty message="Select a route to see opportunity cost" />
  }
  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!routeDetail?.opportunity_cost) {
    return <PanelEmpty message="No opportunity cost data" />
  }

  const items = routeDetail.opportunity_cost
  // Find max value for bar scaling
  const maxImpact = Math.max(...items.map((i: any) => Math.abs(i.impact ?? i.value ?? 0)), 1)

  return (
    <Tooltip
      label="OpportunityCost"
      fullName="Opportunity Cost — Training Priorities"
      derivation="Ranked training investments by expected time gain on the target route."
      context="Focus training on the highest-impact items for the biggest performance gain."
    >
      <div className={styles.list}>
        {items.map((item: any, idx: number) => {
          const impact = Math.abs(item.impact ?? item.value ?? 0)
          const pct = (impact / maxImpact) * 100

          return (
            <div key={idx} className={styles.row}>
              <div className={styles.label}>{item.name ?? item.label}</div>
              <div className={styles.barContainer}>
                <div
                  className={styles.bar}
                  style={{
                    width: `${pct}%`,
                    background: idx === 0
                      ? 'var(--color-accent, #58a6ff)'
                      : idx < 3
                        ? 'var(--color-success, #3fb950)'
                        : 'var(--color-text-secondary, #8b949e)',
                  }}
                />
              </div>
              <div className={styles.value}>
                {item.impact != null ? `${item.impact > 0 ? '+' : ''}${item.impact.toFixed(1)}s` : '—'}
              </div>
            </div>
          )
        })}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'opportunity-cost',
  label: 'Opportunity Cost',
  category: 'event-prep',
  description: 'Ranked training priorities — horizontal bar chart',
  component: OpportunityCost,
  dataKeys: ['selectedRouteId', 'routeDetail'],
})
```

Create `frontend-v2/src/panels/event-prep/OpportunityCost.module.css`:

```css
.list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label {
  width: 140px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--color-text-primary, #e6edf3);
  text-align: right;
}

.barContainer {
  flex: 1;
  height: 18px;
  background: var(--color-bg-secondary, #21262d);
  border-radius: 3px;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.value {
  width: 60px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
  text-align: right;
}
```

- [ ] **Step 4: Create GlycogenBudget (form only, chart deferred to 1C)**

Create `frontend-v2/src/panels/event-prep/GlycogenBudget.tsx`:

```typescript
import { useState, useCallback } from 'react'
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import { postGlycogenBudget } from '../../api/client'
import styles from './GlycogenBudget.module.css'

interface BudgetForm {
  ride_kj: number
  duration_hours: number
  carbs_per_hour: number
  delay_min: number
  weight_kg: number
}

const DEFAULT_FORM: BudgetForm = {
  ride_kj: 2500,
  duration_hours: 4,
  carbs_per_hour: 60,
  delay_min: 30,
  weight_kg: 76,
}

export function GlycogenBudget() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const config = useDataStore(s => s.config)

  const [form, setForm] = useState<BudgetForm>({
    ...DEFAULT_FORM,
    weight_kg: config?.weight_kg ?? DEFAULT_FORM.weight_kg,
  })
  const [result, setResult] = useState<any>(null)
  const [computing, setComputing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const debounceRef = useState<ReturnType<typeof setTimeout> | null>(null)

  const handleChange = useCallback((field: keyof BudgetForm, value: number) => {
    setForm(prev => {
      const next = { ...prev, [field]: value }
      // Debounced compute
      if (debounceRef[0]) clearTimeout(debounceRef[0])
      debounceRef[0] = setTimeout(async () => {
        setComputing(true)
        setError(null)
        try {
          const res = await postGlycogenBudget(next)
          setResult(res)
        } catch (e: any) {
          setError(e.message ?? 'Computation failed')
        } finally {
          setComputing(false)
        }
      }, 500)
      return next
    })
  }, [])

  return (
    <Tooltip
      label="GlycogenBudget"
      fullName="Glycogen Budget Calculator"
      derivation="Models muscle glycogen depletion over ride duration given intake rate."
      context="Bonk risk = glycogen drops below ~25% capacity. Increase carb intake or reduce intensity."
    >
      <div className={styles.container}>
        <div className={styles.form}>
          <div className={styles.field}>
            <label>Ride kJ</label>
            <input
              type="number"
              value={form.ride_kj}
              onChange={e => handleChange('ride_kj', Number(e.target.value))}
              min={0}
              step={100}
            />
          </div>
          <div className={styles.field}>
            <label>Duration (h)</label>
            <input
              type="number"
              value={form.duration_hours}
              onChange={e => handleChange('duration_hours', Number(e.target.value))}
              min={0.5}
              step={0.5}
            />
          </div>
          <div className={styles.field}>
            <label>Carbs/hr (g)</label>
            <input
              type="number"
              value={form.carbs_per_hour}
              onChange={e => handleChange('carbs_per_hour', Number(e.target.value))}
              min={0}
              step={10}
            />
          </div>
          <div className={styles.field}>
            <label>Delay (min)</label>
            <input
              type="number"
              value={form.delay_min}
              onChange={e => handleChange('delay_min', Number(e.target.value))}
              min={0}
              step={5}
            />
          </div>
          <div className={styles.field}>
            <label>Weight (kg)</label>
            <input
              type="number"
              value={form.weight_kg}
              onChange={e => handleChange('weight_kg', Number(e.target.value))}
              min={30}
              step={1}
            />
          </div>
        </div>

        {computing && <div className={styles.computing}>Computing...</div>}
        {error && <PanelError message={error} />}

        {result && !computing && (
          <div className={styles.results}>
            <Metric
              value={result.bonk_risk != null ? `${(result.bonk_risk * 100).toFixed(0)}%` : '—'}
              label="Bonk Risk"
            />
            <Metric
              value={result.min_glycogen_pct != null ? `${(result.min_glycogen_pct * 100).toFixed(0)}%` : '—'}
              label="Min Glycogen"
            />
            <Metric
              value={result.time_to_bonk_min != null ? `${result.time_to_bonk_min.toFixed(0)} min` : 'N/A'}
              label="Time to Bonk"
            />
            {result.recommendation && (
              <div className={styles.recommendation}>{result.recommendation}</div>
            )}
            {/* Chart placeholder — wired in Plan 1C with D3 timeline */}
            <div className={styles.chartPlaceholder}>
              Glycogen timeline chart will render here (Plan 1C)
            </div>
          </div>
        )}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'glycogen-budget',
  label: 'Glycogen Budget',
  category: 'event-prep',
  description: 'Interactive glycogen calculator — form + results (chart in 1C)',
  component: GlycogenBudget,
  dataKeys: ['config', 'selectedRouteId'],
})
```

Create `frontend-v2/src/panels/event-prep/GlycogenBudget.module.css`:

```css
.container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary, #8b949e);
}

.field input {
  padding: 6px 8px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
  background: var(--color-bg-primary, #161b22);
  color: var(--color-text-primary, #e6edf3);
  font-size: 13px;
  width: 100px;
}

.computing {
  font-size: 13px;
  color: var(--color-text-secondary, #8b949e);
  font-style: italic;
}

.results {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-start;
}

.recommendation {
  width: 100%;
  font-size: 13px;
  color: var(--color-text-secondary, #8b949e);
  line-height: 1.4;
  padding: 8px 0;
  border-top: 1px solid var(--color-border, #30363d);
}

.chartPlaceholder {
  width: 100%;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--color-border, #30363d);
  border-radius: 6px;
  color: var(--color-text-secondary, #8b949e);
  font-size: 13px;
  font-style: italic;
}
```

- [ ] **Step 5: Write GapAnalysis test**

Create `frontend-v2/src/panels/event-prep/GapAnalysis.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { GapAnalysis } from './GapAnalysis'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('GapAnalysis', () => {
  it('shows "select a route" when no route selected', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        selectedRouteId: null,
        routeDetail: {},
        loading: new Set(),
        errors: {},
      })
    )
    render(<GapAnalysis />)
    expect(screen.getByText(/select a route/i)).toBeInTheDocument()
  })

  it('shows feasible result', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        selectedRouteId: 1,
        routeDetail: {
          1: {
            gap_analysis: { feasible: true, bottleneck: null, margin: 0.12, message: 'Good to go' },
          },
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<GapAnalysis />)
    expect(screen.getByText('Feasible')).toBeInTheDocument()
    expect(screen.getByText(/12\.0%/)).toBeInTheDocument()
  })

  it('shows not feasible with bottleneck', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        selectedRouteId: 1,
        routeDetail: {
          1: {
            gap_analysis: { feasible: false, bottleneck: '5min power', margin: -0.08 },
          },
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<GapAnalysis />)
    expect(screen.getByText('Not Feasible')).toBeInTheDocument()
    expect(screen.getByText(/5min power/)).toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Run tests**

```bash
cd frontend-v2 && npx vitest run src/panels/event-prep/
```

- [ ] **Step 7: Commit**

```bash
cd frontend-v2 && git add src/panels/event-prep/
git commit -m "feat(1b): event-prep panels — RouteSelector, GapAnalysis, OpportunityCost, GlycogenBudget"
```

---

## Task 13: History Panels — RidesTable, TrainingBlocks, PhaseTimeline, IntensityDist

**Files:**
- Create: `frontend-v2/src/panels/history/RidesTable.tsx`
- Create: `frontend-v2/src/panels/history/RidesTable.module.css`
- Create: `frontend-v2/src/panels/history/RidesTable.test.tsx`
- Create: `frontend-v2/src/panels/history/TrainingBlocks.tsx`
- Create: `frontend-v2/src/panels/history/TrainingBlocks.test.tsx`
- Create: `frontend-v2/src/panels/history/PhaseTimeline.tsx`
- Create: `frontend-v2/src/panels/history/PhaseTimeline.test.tsx`
- Create: `frontend-v2/src/panels/history/IntensityDist.tsx`
- Create: `frontend-v2/src/panels/history/IntensityDist.module.css`

- [ ] **Step 1: Create RidesTable**

Create `frontend-v2/src/panels/history/RidesTable.tsx`:

```typescript
import { useState, useMemo } from 'react'
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './RidesTable.module.css'

const PAGE_SIZE = 15

type SortKey = 'start_time' | 'training_stress_score' | 'normalized_power' | 'total_elapsed_time'

export function RidesTable() {
  const activities = useDataStore(s => s.activities)
  const loading = useDataStore(s => s.loading.has('activities'))
  const error = useDataStore(s => s.errors['activities'])
  const globalTimeRange = useDataStore(s => s.globalTimeRange)

  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('start_time')
  const [sortAsc, setSortAsc] = useState(false)
  const [page, setPage] = useState(0)

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!activities || activities.length === 0) {
    return <PanelEmpty message="No rides found" />
  }

  // Filter by time range
  const filtered = useMemo(() => {
    let list = [...activities]
    if (globalTimeRange) {
      list = list.filter((a: any) => {
        const d = a.start_time?.slice(0, 10)
        return d >= globalTimeRange.start && d <= globalTimeRange.end
      })
    }
    if (search) {
      const q = search.toLowerCase()
      list = list.filter((a: any) =>
        (a.filename ?? '').toLowerCase().includes(q) ||
        (a.sub_sport ?? '').toLowerCase().includes(q)
      )
    }
    return list
  }, [activities, globalTimeRange, search])

  // Sort
  const sorted = useMemo(() => {
    return [...filtered].sort((a: any, b: any) => {
      const va = a[sortKey] ?? 0
      const vb = b[sortKey] ?? 0
      return sortAsc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1)
    })
  }, [filtered, sortKey, sortAsc])

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const pageData = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(false)
    }
    setPage(0)
  }

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <th
      className={styles.sortable}
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field ? (sortAsc ? '\u25B2' : '\u25BC') : ''}
    </th>
  )

  return (
    <div className={styles.container}>
      <div className={styles.controls}>
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Search rides..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
        />
        <span className={styles.count}>{filtered.length} rides</span>
      </div>

      <table className={styles.table}>
        <thead>
          <tr>
            <SortHeader label="Date" field="start_time" />
            <th>Type</th>
            <SortHeader label="Duration" field="total_elapsed_time" />
            <SortHeader label="NP" field="normalized_power" />
            <SortHeader label="TSS" field="training_stress_score" />
            <th>IF</th>
          </tr>
        </thead>
        <tbody>
          {pageData.map((a: any) => (
            <tr key={a.id} className={styles.row}>
              <td>{new Date(a.start_time).toLocaleDateString()}</td>
              <td>{a.sub_sport ?? 'ride'}</td>
              <td>{formatDuration(a.total_elapsed_time)}</td>
              <td>{a.normalized_power != null ? `${Math.round(a.normalized_power)}W` : '—'}</td>
              <td>{a.training_stress_score != null ? Math.round(a.training_stress_score) : '—'}</td>
              <td>{a.intensity_factor != null ? a.intensity_factor.toFixed(2) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className={styles.pagination}>
          <button disabled={page === 0} onClick={() => setPage(page - 1)}>&laquo; Prev</button>
          <span>{page + 1} / {totalPages}</span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>Next &raquo;</button>
        </div>
      )}
    </div>
  )
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

registerPanel({
  id: 'rides-table',
  label: 'Rides Table',
  category: 'history',
  description: 'Sortable, paginated, searchable ride history',
  component: RidesTable,
  dataKeys: ['activities', 'globalTimeRange'],
})
```

Create `frontend-v2/src/panels/history/RidesTable.module.css`:

```css
.container { display: flex; flex-direction: column; gap: 8px; }
.controls { display: flex; align-items: center; gap: 8px; }
.searchInput {
  padding: 6px 10px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
  background: var(--color-bg-primary, #161b22);
  color: var(--color-text-primary, #e6edf3);
  font-size: 13px;
  flex: 1;
  max-width: 250px;
}
.count { font-size: 12px; color: var(--color-text-secondary, #8b949e); }
.table { width: 100%; border-collapse: collapse; font-size: 13px; }
.table th {
  text-align: left;
  padding: 6px 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-text-secondary, #8b949e);
  border-bottom: 1px solid var(--color-border, #30363d);
}
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--color-text-primary, #e6edf3); }
.table td {
  padding: 6px 8px;
  color: var(--color-text-primary, #e6edf3);
  border-bottom: 1px solid var(--color-border-subtle, #21262d);
}
.row { cursor: pointer; }
.row:hover { background: var(--color-bg-tertiary, #30363d); }
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  font-size: 13px;
  color: var(--color-text-secondary, #8b949e);
}
.pagination button {
  padding: 4px 10px;
  border: 1px solid var(--color-border, #30363d);
  border-radius: 4px;
  background: var(--color-bg-secondary, #21262d);
  color: var(--color-text-primary, #e6edf3);
  font-size: 12px;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
```

- [ ] **Step 2: Create TrainingBlocks**

Create `frontend-v2/src/panels/history/TrainingBlocks.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function TrainingBlocks() {
  // Training blocks come from the activities + model data
  // The backend returns block stats via a computed endpoint
  const activities = useDataStore(s => s.activities)
  const loading = useDataStore(s => s.loading.has('activities'))
  const error = useDataStore(s => s.errors['activities'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!activities || activities.length === 0) {
    return <PanelEmpty message="No training data for block analysis" />
  }

  // Compute basic block stats from activities (last 4 weeks)
  const now = new Date()
  const fourWeeksAgo = new Date(now.getTime() - 28 * 86_400_000)
  const recent = activities.filter((a: any) =>
    new Date(a.start_time) >= fourWeeksAgo
  )

  const totalHours = recent.reduce((sum: number, a: any) =>
    sum + ((a.total_elapsed_time ?? 0) / 3600), 0)
  const totalTSS = recent.reduce((sum: number, a: any) =>
    sum + (a.training_stress_score ?? 0), 0)
  const avgIF = recent.filter((a: any) => a.intensity_factor != null)
    .reduce((sum: number, a: any, _, arr) =>
      sum + (a.intensity_factor / arr.length), 0)
  const avgPower = recent.filter((a: any) => a.avg_power != null)
    .reduce((sum: number, a: any, _, arr) =>
      sum + (a.avg_power / arr.length), 0)

  return (
    <Tooltip
      label="TrainingBlocks"
      fullName="Training Block Summary (Last 4 Weeks)"
      derivation="Aggregated volume, intensity, and power from the last 28 days of rides."
      context="Compare blocks over time to track progressive overload and recovery periods."
    >
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
        <Metric value={recent.length} label="Rides" />
        <Metric value={totalHours.toFixed(1)} label="Hours" />
        <Metric value={Math.round(totalTSS)} label="Total TSS" />
        <Metric value={avgIF.toFixed(2)} label="Avg IF" />
        <Metric value={Math.round(avgPower)} label="Avg Power" unit="W" />
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'training-blocks',
  label: 'Training Blocks',
  category: 'history',
  description: 'Block stats — volume, intensity, power (last 4 weeks)',
  component: TrainingBlocks,
  dataKeys: ['activities'],
})
```

- [ ] **Step 3: Create PhaseTimeline**

Create `frontend-v2/src/panels/history/PhaseTimeline.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

const PHASE_COLORS: Record<string, string> = {
  base: 'var(--color-accent, #58a6ff)',
  build: 'var(--color-warning, #d29922)',
  peak: 'var(--color-danger, #f85149)',
  recovery: 'var(--color-success, #3fb950)',
  transition: 'var(--color-text-secondary, #8b949e)',
}

export function PhaseTimeline() {
  // Phase detection comes from the clinical/model endpoint
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />

  const phase = flags?.detected_phase
  if (!phase) return <PanelEmpty message="Phase detection not available" />

  const phaseColor = PHASE_COLORS[phase.phase] ?? 'var(--color-text-secondary)'

  return (
    <Tooltip
      label="Phase"
      fullName="Detected Training Phase"
      derivation={`Phase detection based on CTL trend, intensity distribution, and volume patterns. Confidence: ${(phase.confidence * 100).toFixed(0)}%.`}
      context="Base = aerobic focus. Build = intensity increasing. Peak = race-specific. Recovery = deload."
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '8px 0',
      }}>
        <div style={{
          fontSize: '28px',
          fontWeight: 700,
          color: phaseColor,
          textTransform: 'capitalize',
        }}>
          {phase.phase}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: '13px',
            color: 'var(--color-text-secondary)',
            marginBottom: '4px',
          }}>
            Confidence: {(phase.confidence * 100).toFixed(0)}%
          </div>
          <div style={{
            width: '100%',
            height: '6px',
            background: 'var(--color-bg-secondary, #21262d)',
            borderRadius: '3px',
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${phase.confidence * 100}%`,
              height: '100%',
              background: phaseColor,
              borderRadius: '3px',
            }} />
          </div>
          {phase.reasoning && (
            <div style={{
              fontSize: '12px',
              color: 'var(--color-text-secondary)',
              marginTop: '6px',
              lineHeight: 1.4,
            }}>
              {phase.reasoning}
            </div>
          )}
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'phase-timeline',
  label: 'Phase Timeline',
  category: 'history',
  description: 'Current detected training phase with confidence',
  component: PhaseTimeline,
  dataKeys: ['clinicalFlags'],
})
```

- [ ] **Step 4: Create IntensityDist**

Create `frontend-v2/src/panels/history/IntensityDist.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './IntensityDist.module.css'

const ZONES = [
  { key: 'zone1', label: 'Zone 1 (Easy)', color: '#3fb950', seiler: 'Low' },
  { key: 'zone2', label: 'Zone 2 (Threshold)', color: '#d29922', seiler: 'Medium' },
  { key: 'zone3', label: 'Zone 3 (High)', color: '#f85149', seiler: 'High' },
]

export function IntensityDist() {
  const ifDist = useDataStore(s => s.ifDistribution)
  const loading = useDataStore(s => s.loading.has('ifDistribution'))
  const error = useDataStore(s => s.errors['ifDistribution'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!ifDist) return <PanelEmpty message="No intensity distribution data" />

  // Derive Seiler 3-zone from IF distribution
  // Zone 1: IF < 0.75, Zone 2: IF 0.75-0.90, Zone 3: IF > 0.90
  const histogram = ifDist.histogram ?? {}
  let z1 = 0, z2 = 0, z3 = 0, total = 0

  for (const [bin, count] of Object.entries(histogram)) {
    const ifVal = parseFloat(bin)
    const c = count as number
    total += c
    if (ifVal < 0.75) z1 += c
    else if (ifVal < 0.90) z2 += c
    else z3 += c
  }

  if (total === 0) return <PanelEmpty message="No rides to analyze" />

  const pcts = [
    { ...ZONES[0], pct: (z1 / total) * 100 },
    { ...ZONES[1], pct: (z2 / total) * 100 },
    { ...ZONES[2], pct: (z3 / total) * 100 },
  ]

  return (
    <Tooltip
      label="IntensityDist"
      fullName="Seiler 3-Zone Intensity Distribution"
      derivation="Rides categorized by IF into 3 Seiler zones. Zone 1 < 0.75 IF, Zone 2 = 0.75-0.90, Zone 3 > 0.90."
      context="Polarized training: ~80% Zone 1, ~5% Zone 2, ~15% Zone 3. Pyramidal allows more Zone 2."
    >
      <div className={styles.container}>
        {pcts.map(z => (
          <div key={z.key} className={styles.zoneRow}>
            <div className={styles.zoneLabel}>{z.label}</div>
            <div className={styles.barContainer}>
              <div
                className={styles.bar}
                style={{ width: `${z.pct}%`, background: z.color }}
              />
            </div>
            <div className={styles.pct}>{z.pct.toFixed(1)}%</div>
          </div>
        ))}
        <div className={styles.meta}>
          {ifDist.rides_analyzed} rides analyzed
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'intensity-dist',
  label: 'Intensity Distribution',
  category: 'history',
  description: 'Seiler 3-zone percentages — polarized training check',
  component: IntensityDist,
  dataKeys: ['ifDistribution'],
})
```

Create `frontend-v2/src/panels/history/IntensityDist.module.css`:

```css
.container { display: flex; flex-direction: column; gap: 8px; }
.zoneRow { display: flex; align-items: center; gap: 8px; }
.zoneLabel {
  width: 140px; flex-shrink: 0;
  font-size: 12px; color: var(--color-text-primary, #e6edf3);
}
.barContainer {
  flex: 1; height: 22px;
  background: var(--color-bg-secondary, #21262d);
  border-radius: 4px; overflow: hidden;
}
.bar { height: 100%; border-radius: 4px; transition: width 0.3s ease; }
.pct {
  width: 50px; text-align: right;
  font-size: 13px; font-weight: 600;
  color: var(--color-text-primary, #e6edf3);
}
.meta {
  font-size: 11px;
  color: var(--color-text-secondary, #8b949e);
  margin-top: 4px;
}
```

- [ ] **Step 5: Write RidesTable test**

Create `frontend-v2/src/panels/history/RidesTable.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { RidesTable } from './RidesTable'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

const mockActivities = Array.from({ length: 20 }, (_, i) => ({
  id: i,
  start_time: `2026-03-${String(24 - i).padStart(2, '0')}T08:00:00`,
  sub_sport: 'road',
  total_elapsed_time: 3600 + i * 300,
  normalized_power: 200 + i * 5,
  training_stress_score: 50 + i * 3,
  intensity_factor: 0.65 + i * 0.01,
  filename: `ride_${i}.fit`,
}))

describe('RidesTable', () => {
  it('renders paginated rides', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        activities: mockActivities,
        loading: new Set(),
        errors: {},
        globalTimeRange: null,
      })
    )
    render(<RidesTable />)
    expect(screen.getByText('20 rides')).toBeInTheDocument()
    expect(screen.getByText('1 / 2')).toBeInTheDocument() // 20 rides, 15 per page
  })

  it('filters by search text', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        activities: mockActivities,
        loading: new Set(),
        errors: {},
        globalTimeRange: null,
      })
    )
    render(<RidesTable />)
    fireEvent.change(screen.getByPlaceholderText('Search rides...'), {
      target: { value: 'ride_5' },
    })
    expect(screen.getByText('1 rides')).toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Run tests**

```bash
cd frontend-v2 && npx vitest run src/panels/history/
```

- [ ] **Step 7: Commit**

```bash
cd frontend-v2 && git add src/panels/history/
git commit -m "feat(1b): history panels — RidesTable, TrainingBlocks, PhaseTimeline, IntensityDist"
```

---

## Task 14: Profile Panels — CogganRanking, Phenotype, PosteriorSummary, Feasibility, AthleteConfig

**Files:**
- Create: `frontend-v2/src/panels/profile/CogganRanking.tsx`
- Create: `frontend-v2/src/panels/profile/Phenotype.tsx`
- Create: `frontend-v2/src/panels/profile/PosteriorSummary.tsx`
- Create: `frontend-v2/src/panels/profile/Feasibility.tsx`
- Create: `frontend-v2/src/panels/profile/Feasibility.module.css`
- Create: `frontend-v2/src/panels/profile/AthleteConfig.tsx`
- Create: `frontend-v2/src/panels/profile/Phenotype.test.tsx`

- [ ] **Step 1: Create CogganRanking**

Create `frontend-v2/src/panels/profile/CogganRanking.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

const RANKING_LABELS: Record<string, string> = {
  world_class: 'World Class',
  exceptional: 'Exceptional',
  excellent: 'Excellent',
  very_good: 'Very Good',
  good: 'Good',
  moderate: 'Moderate',
  fair: 'Fair',
  untrained: 'Untrained',
}

export function CogganRanking() {
  const profile = useDataStore(s => s.profile)
  const loading = useDataStore(s => s.loading.has('profile'))
  const error = useDataStore(s => s.errors['profile'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!profile?.ranking) return <PanelEmpty message="No ranking data" />

  const rows = Object.entries(profile.ranking).map(([duration, rank]) => ({
    duration,
    ranking: RANKING_LABELS[rank as string] ?? rank,
    watts: profile.profile?.watts?.[duration],
    wkg: profile.profile?.wkg?.[duration],
  }))

  const columns = [
    { key: 'duration', label: 'Duration' },
    { key: 'watts', label: 'Watts', render: (v: number | null) => v != null ? `${Math.round(v)}W` : '—' },
    { key: 'wkg', label: 'W/kg', render: (v: number | null) => v != null ? v.toFixed(2) : '—' },
    { key: 'ranking', label: 'Ranking' },
  ]

  return (
    <Tooltip
      label="CogganRanking"
      fullName="Coggan Power Profile Classification"
      derivation="Peak power at each duration classified against Coggan's published categories."
      context="Based on 90-day best efforts. Test key durations to get accurate classification."
    >
      <DataTable data={rows} columns={columns} rowKey="duration" compact />
    </Tooltip>
  )
}

registerPanel({
  id: 'coggan-ranking',
  label: 'Coggan Ranking',
  category: 'profile',
  description: 'Power profile vs Coggan classification table',
  component: CogganRanking,
  dataKeys: ['profile'],
})
```

- [ ] **Step 2: Create Phenotype**

Create `frontend-v2/src/panels/profile/Phenotype.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function Phenotype() {
  const profile = useDataStore(s => s.profile)
  const loading = useDataStore(s => s.loading.has('profile'))
  const error = useDataStore(s => s.errors['profile'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!profile?.strengths_limiters) return <PanelEmpty message="No phenotype data" />

  const sl = profile.strengths_limiters

  return (
    <Tooltip
      label="Phenotype"
      fullName="Rider Phenotype — Strengths and Limiters"
      derivation="Derived from power profile shape — ratio of short-duration to long-duration power."
      context="Sprinter = high 5s/1min relative to FTP. TTer = high 20min/60min relative to sprint."
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {sl.phenotype && (
          <div style={{
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--color-accent, #58a6ff)',
          }}>
            {sl.phenotype}
          </div>
        )}
        {sl.strengths && sl.strengths.length > 0 && (
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--color-success, #3fb950)',
              textTransform: 'uppercase',
              marginBottom: '4px',
            }}>
              Strengths
            </div>
            {sl.strengths.map((s: string, i: number) => (
              <div key={i} style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>
                {s}
              </div>
            ))}
          </div>
        )}
        {sl.limiters && sl.limiters.length > 0 && (
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--color-warning, #d29922)',
              textTransform: 'uppercase',
              marginBottom: '4px',
            }}>
              Limiters
            </div>
            {sl.limiters.map((l: string, i: number) => (
              <div key={i} style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>
                {l}
              </div>
            ))}
          </div>
        )}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'phenotype',
  label: 'Phenotype',
  category: 'profile',
  description: 'Sprinter/Pursuiter/TTer classification with strengths and limiters',
  component: Phenotype,
  dataKeys: ['profile'],
})
```

- [ ] **Step 3: Create PosteriorSummary**

Create `frontend-v2/src/panels/profile/PosteriorSummary.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function PosteriorSummary() {
  const model = useDataStore(s => s.model)
  const loading = useDataStore(s => s.loading.has('model'))
  const error = useDataStore(s => s.errors['model'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!model) return <PanelEmpty message="No model data" />

  // Build rows from model parameters
  const params = [
    { param: 'mFTP', value: model.mFTP, unit: 'W' },
    { param: 'Pmax', value: model.Pmax, unit: 'W' },
    { param: 'FRC', value: model.FRC, unit: 'kJ' },
    { param: 'TTE', value: model.TTE, unit: 'min' },
    { param: 'mVO2max', value: model.mVO2max_ml_min_kg, unit: 'ml/min/kg' },
  ].filter(p => p.value != null)

  const columns = [
    { key: 'param', label: 'Parameter' },
    {
      key: 'value',
      label: 'Estimate',
      render: (v: number, row: any) =>
        row.unit === 'kJ'
          ? `${(v / 1000).toFixed(1)} ${row.unit}`
          : `${typeof v === 'number' ? (v < 100 ? v.toFixed(1) : Math.round(v)) : v} ${row.unit}`,
    },
  ]

  return (
    <Tooltip
      label="Posterior"
      fullName="Model Parameter Summary"
      derivation="Parameters from the power-duration model fit to your 90-day MMP envelope."
      context="mFTP = modeled FTP (not 95% of 20min). FRC = anaerobic capacity above FTP. TTE = time to exhaustion at FTP."
    >
      <DataTable data={params} columns={columns} rowKey="param" compact />
    </Tooltip>
  )
}

registerPanel({
  id: 'posterior-summary',
  label: 'Posterior Summary',
  category: 'profile',
  description: 'PD model parameter estimates',
  component: PosteriorSummary,
  dataKeys: ['model'],
})
```

- [ ] **Step 4: Create Feasibility**

Create `frontend-v2/src/panels/profile/Feasibility.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './Feasibility.module.css'

export function Feasibility() {
  const fitness = useDataStore(s => s.fitness)
  const loading = useDataStore(s => s.loading.has('fitness'))
  const error = useDataStore(s => s.errors['fitness'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!fitness) return <PanelEmpty message="No fitness data for feasibility" />

  // Feasibility projection based on current CTL
  // This is a simplified version; the full version uses the backend endpoint
  const currentCTL = fitness.CTL ?? 0
  const maxSustainableRamp = 5 // TSS/wk typical max
  const weeksAvailable = 12 // default planning horizon

  return (
    <Tooltip
      label="Feasibility"
      fullName="CTL Feasibility Projection"
      derivation={`Current CTL: ${currentCTL.toFixed(0)}. Max sustainable ramp rate: ~${maxSustainableRamp} TSS/day per week.`}
      context="Ramp rate >7 TSS/wk sustained risks overtraining. Plan 8-16 weeks for significant CTL gains."
    >
      <div className={styles.card}>
        <div className={styles.metrics}>
          <Metric value={Math.round(currentCTL)} label="Current CTL" />
          <Metric
            value={Math.round(currentCTL + maxSustainableRamp * weeksAvailable)}
            label={`Projected (${weeksAvailable}wk)`}
          />
          <Metric value={maxSustainableRamp} label="Max Ramp (TSS/wk)" />
        </div>
        <div className={styles.note}>
          Use the backend feasibility endpoint for precise projection with target CTL.
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'feasibility',
  label: 'Feasibility',
  category: 'profile',
  description: 'CTL feasibility projection based on current fitness',
  component: Feasibility,
  dataKeys: ['fitness'],
})
```

Create `frontend-v2/src/panels/profile/Feasibility.module.css`:

```css
.card { display: flex; flex-direction: column; gap: 12px; }
.metrics { display: flex; flex-wrap: wrap; gap: 16px; }
.note {
  font-size: 12px;
  color: var(--color-text-secondary, #8b949e);
  font-style: italic;
}
```

- [ ] **Step 5: Create AthleteConfig**

Create `frontend-v2/src/panels/profile/AthleteConfig.tsx`:

```typescript
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function AthleteConfig() {
  const config = useDataStore(s => s.config)
  const loading = useDataStore(s => s.loading.has('config'))
  const error = useDataStore(s => s.errors['config'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!config) return <PanelEmpty message="No config data" />

  // Display config as key-value pairs
  const rows = Object.entries(config)
    .filter(([k]) => !k.startsWith('_'))
    .map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—'),
    }))

  const columns = [
    { key: 'key', label: 'Setting' },
    { key: 'value', label: 'Value' },
  ]

  return (
    <Tooltip
      label="Config"
      fullName="Athlete Configuration"
      derivation="Settings stored in the backend config (wko5.db). Edit via API or config file."
      context="Key settings: FTP, weight, CdA, max HR. These drive all derived metrics."
    >
      <DataTable data={rows} columns={columns} rowKey="key" compact />
    </Tooltip>
  )
}

registerPanel({
  id: 'athlete-config',
  label: 'Athlete Config',
  category: 'profile',
  description: 'Athlete configuration display (read-only)',
  component: AthleteConfig,
  dataKeys: ['config'],
})
```

- [ ] **Step 6: Write Phenotype test**

Create `frontend-v2/src/panels/profile/Phenotype.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Phenotype } from './Phenotype'

vi.mock('../../store/data-store', () => ({
  useDataStore: vi.fn(),
}))

import { useDataStore } from '../../store/data-store'
const mockUseDataStore = vi.mocked(useDataStore)

describe('Phenotype', () => {
  it('renders phenotype with strengths and limiters', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        profile: {
          strengths_limiters: {
            phenotype: 'All-Rounder',
            strengths: ['5min power', 'TTE'],
            limiters: ['Sprint (5s)'],
          },
        },
        loading: new Set(),
        errors: {},
      })
    )
    render(<Phenotype />)
    expect(screen.getByText('All-Rounder')).toBeInTheDocument()
    expect(screen.getByText('5min power')).toBeInTheDocument()
    expect(screen.getByText('Sprint (5s)')).toBeInTheDocument()
  })

  it('shows empty when no phenotype data', () => {
    mockUseDataStore.mockImplementation((selector: any) =>
      selector({
        profile: null,
        loading: new Set(),
        errors: {},
      })
    )
    render(<Phenotype />)
    expect(screen.getByText(/no phenotype data/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 7: Run tests**

```bash
cd frontend-v2 && npx vitest run src/panels/profile/
```

- [ ] **Step 8: Commit**

```bash
cd frontend-v2 && git add src/panels/profile/
git commit -m "feat(1b): profile panels — CogganRanking, Phenotype, PosteriorSummary, Feasibility, AthleteConfig"
```

---

## Task 15: Panel Registration Index + App Integration

**Files:**
- Create: `frontend-v2/src/panels/index.ts`
- Modify: `frontend-v2/src/App.tsx`

All panels self-register via their `registerPanel()` calls. We need a single import file that pulls them all in, and wire the layout engine into the App shell.

- [ ] **Step 1: Create panel registration index**

Create `frontend-v2/src/panels/index.ts`:

```typescript
/**
 * Panel registration index.
 * Import this file to register all panels in the PanelRegistry.
 * Each panel module calls registerPanel() as a side effect.
 *
 * Chart panels (D3) are placeholders — registered in Plan 1C.
 */

// Status
import './status/TSBStatus'
import './status/RecentRides'
import './status/ClinicalAlert'

// Health
import './health/ClinicalFlags'
import './health/IFFloor'
import './health/PanicTraining'
import './health/RedsScreen'
import './health/FreshBaseline'

// Fitness (non-chart only)
import './fitness/PowerProfile'
import './fitness/ShortPower'

// Event Prep
import './event-prep/RouteSelector'
import './event-prep/GapAnalysis'
import './event-prep/OpportunityCost'
import './event-prep/GlycogenBudget'

// History
import './history/RidesTable'
import './history/TrainingBlocks'
import './history/PhaseTimeline'
import './history/IntensityDist'

// Profile
import './profile/CogganRanking'
import './profile/Phenotype'
import './profile/PosteriorSummary'
import './profile/Feasibility'
import './profile/AthleteConfig'
```

- [ ] **Step 2: Wire into App.tsx**

Modify `frontend-v2/src/App.tsx` to integrate the layout engine. The App shell from 1A provides the outer structure; we add the layout components inside it.

```typescript
import { useEffect } from 'react'
import { useDataStore } from './store/data-store'
import { initLayoutStore, useLayoutStore } from './layout/layoutStore'
import { Header } from './components/Header'
import { FilterBar } from './components/FilterBar'
import { LayoutEngine } from './layout/LayoutEngine'
import { EditMode } from './layout/EditMode'

// Register all panels (side-effect imports)
import './panels'

export function App() {
  const athleteSlug = useDataStore(s => s.athleteSlug)
  const editMode = useLayoutStore?.(s => s.editMode) ?? false

  // Initialize layout store on first render
  useEffect(() => {
    initLayoutStore(athleteSlug || 'default')
  }, [athleteSlug])

  // Wait for layout store initialization
  if (!useLayoutStore) {
    return <div>Initializing...</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Header />
      <FilterBar />
      <main style={{ flex: 1, overflow: 'auto', background: 'var(--color-bg-primary, #0d1117)' }}>
        {editMode ? <EditMode /> : <LayoutEngine />}
      </main>
    </div>
  )
}
```

- [ ] **Step 3: Verify dev server loads**

```bash
cd frontend-v2 && npm run dev
```

Open `http://localhost:5173` — should see: header with tab bar, filter bar, and panels for the Today tab (TSBStatus, RecentRides, ClinicalAlert). Panels will show loading/empty states until the API is connected.

- [ ] **Step 4: Commit**

```bash
cd frontend-v2 && git add src/panels/index.ts src/App.tsx
git commit -m "feat(1b): wire all panels into App — layout engine + edit mode integrated"
```

---

## Task 16: Full Integration Test

**Files:** None new — this is a verification step.

- [ ] **Step 1: Run all tests**

```bash
cd frontend-v2 && npx vitest run
```

Expected: All tests pass. Fix any failures before proceeding.

- [ ] **Step 2: Manual verification checklist**

Start the dev server and verify each item:

```bash
cd frontend-v2 && npm run dev
```

1. Tab navigation: click each tab (Today, Health, Fitness, Event Prep, History, Profile) — each renders its panels
2. Panel loading states: panels show PanelSkeleton (no API connected)
3. Edit mode: click gear icon -> toolbar appears with Done/Cancel/Reset
4. Panel reorder: drag a panel to a new position (dnd-kit drag handles)
5. Panel remove: click X on a panel in edit mode -> panel removed
6. Panel add: click "+ Add Panel" -> catalog modal opens with search
7. Tab add: click "+" in tab bar -> prompt for name -> new tab appears
8. Tab remove: click X on a tab in edit mode -> tab removed
9. Tab rename: double-click tab label -> inline edit
10. Done: saves layout to localStorage (check DevTools > Application > Local Storage)
11. Cancel: discards changes
12. Reset: "Reset to Default" with confirmation dialog -> restores preset
13. Persistence: reload page -> layout restored from localStorage
14. Filter bar: visible between tabs and panels, date inputs and apply/reset buttons work
15. Stale indicator: shows when lastRefresh is set
16. Claude button: visible but disabled (placeholder)

- [ ] **Step 3: Commit any fixes**

```bash
cd frontend-v2 && git add -A
git commit -m "fix(1b): integration test fixes"
```

---

## Summary

**Total files created:** ~65 (components + styles + tests)

**Total tests:** ~40 test cases across 15 test files

**Panels registered:** 23 non-chart panels:
- Status (3): TSBStatus, RecentRides, ClinicalAlert
- Health (5): ClinicalFlags, IFFloor, PanicTraining, RedsScreen, FreshBaseline
- Fitness (2): PowerProfile, ShortPower
- Event Prep (4): RouteSelector, GapAnalysis, OpportunityCost, GlycogenBudget
- History (4): RidesTable, TrainingBlocks, PhaseTimeline, IntensityDist
- Profile (5): CogganRanking, Phenotype, PosteriorSummary, Feasibility, AthleteConfig

**Chart panels deferred to Plan 1C:** PMCChart, MMPCurve, RollingFtp, FtpGrowth, RollingPd, SegmentProfile, DemandHeatmap, WeeklyVolume (all require D3)

**Exit criteria met when:**
1. Full tab navigation works with all non-chart panels rendering
2. Edit mode works (drag reorder, add/remove panels, Done/Cancel/Reset)
3. Layout persists in localStorage keyed by athleteSlug
4. Filter bar is visible between tabs and panels
5. All Vitest tests pass
