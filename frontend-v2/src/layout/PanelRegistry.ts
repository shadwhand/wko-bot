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
