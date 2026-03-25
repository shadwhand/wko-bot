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
