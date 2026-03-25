import { describe, it, expect, beforeEach, vi } from 'vitest'
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
