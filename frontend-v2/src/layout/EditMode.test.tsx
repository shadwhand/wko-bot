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
    // Text appears in both panel header and catalog; check panel wrappers via data-panel-id
    const panels = document.querySelectorAll('[data-panel-id]')
    const panelIds = Array.from(panels).map(el => el.getAttribute('data-panel-id'))
    expect(panelIds).toContain('tsb-status')
    expect(panelIds).toContain('recent-rides')
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
