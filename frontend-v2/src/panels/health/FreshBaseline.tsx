import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

interface BaselineRow {
  duration: string
  exists: boolean
  value: number | null
  date: string | null
  staleness_days: number | null
  stale: boolean
  [key: string]: unknown
}

export function FreshBaseline() {
  const baseline = useDataStore(s => s.freshBaseline)
  const loading = useDataStore(s => s.loading.has('freshBaseline'))
  const error = useDataStore(s => s.errors['freshBaseline'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!baseline) return <PanelEmpty message="No baseline data" />

  // Convert Record<string, {...}> to array
  const rows: BaselineRow[] = Object.entries(baseline).map(([duration, data]) => ({
    duration,
    exists: data.exists,
    value: data.value,
    date: data.date,
    staleness_days: data.staleness_days,
    stale: (data.staleness_days ?? 0) > 90,
  }))

  const columns = [
    { key: 'duration', label: 'Duration' },
    {
      key: 'value',
      label: 'Power (W)',
      render: (row: BaselineRow) =>
        row.value != null ? `${Math.round(row.value)}W` : '--',
    },
    {
      key: 'date',
      label: 'Date',
      render: (row: BaselineRow) => row.date ?? '--',
    },
    {
      key: 'staleness_days',
      label: 'Staleness',
      render: (row: BaselineRow) => {
        const v = row.staleness_days
        if (v == null || !row.exists) return 'No data'
        const color = v > 90 ? 'var(--color-danger, #f85149)'
          : v > 42 ? 'var(--color-warning, #d29922)'
          : 'var(--color-success, #3fb950)'
        return <span style={{ color }}>{v}d</span>
      },
    },
  ]

  return (
    <Tooltip
      label="FreshBaseline"
      fullName="Fresh Baseline Efforts"
      derivation="Days since last max effort at key durations (5s, 1min, 5min, 20min, 60min)."
      context="Stale baselines (>90 days) mean the PD model may be inaccurate. Test key durations."
    >
      <DataTable data={rows} columns={columns} keyField="duration" />
    </Tooltip>
  )
}

registerPanel({
  id: 'fresh-baseline',
  label: 'Fresh Baseline',
  category: 'health',
  description: 'Staleness of max efforts at key durations',
  component: FreshBaseline,
  dataKeys: ['freshBaseline'],
})
