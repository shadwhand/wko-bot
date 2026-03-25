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
