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

    // -- Tab mutations --

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

    // -- Panel mutations --

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
