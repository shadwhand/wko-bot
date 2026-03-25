import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LayoutEngine } from './LayoutEngine'
import { registerPanel, _clearRegistry } from './PanelRegistry'
import { initLayoutStore, useLayoutStore } from './layoutStore'

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
    // Add an empty tab and switch to it
    useLayoutStore.getState().addTab('Empty Tab')
    // addTab auto-selects the new tab

    render(<LayoutEngine />)
    expect(screen.getByText('This tab has no panels.')).toBeInTheDocument()
  })
})
