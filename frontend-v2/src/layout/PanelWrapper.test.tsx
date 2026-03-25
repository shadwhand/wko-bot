import { describe, it, expect, vi, beforeEach } from 'vitest'
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
