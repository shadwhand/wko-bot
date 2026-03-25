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
