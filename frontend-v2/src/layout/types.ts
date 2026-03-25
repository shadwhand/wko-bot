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
