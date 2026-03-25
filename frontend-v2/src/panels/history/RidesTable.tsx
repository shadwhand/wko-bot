import { useState, useMemo } from 'react'
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './RidesTable.module.css'

const PAGE_SIZE = 15

type SortKey = 'start_time' | 'training_stress_score' | 'normalized_power' | 'total_elapsed_time'

export function RidesTable() {
  const activities = useDataStore(s => s.activities)
  const loading = useDataStore(s => s.loading.has('activities'))
  const error = useDataStore(s => s.errors['activities'])
  const globalTimeRange = useDataStore(s => s.globalTimeRange)

  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('start_time')
  const [sortAsc, setSortAsc] = useState(false)
  const [page, setPage] = useState(0)

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!activities || activities.length === 0) {
    return <PanelEmpty message="No rides found" />
  }

  // Filter by time range
  const filtered = useMemo(() => {
    let list = [...activities]
    if (globalTimeRange) {
      list = list.filter((a: any) => {
        const d = a.start_time?.slice(0, 10)
        return d >= globalTimeRange.start && d <= globalTimeRange.end
      })
    }
    if (search) {
      const q = search.toLowerCase()
      list = list.filter((a: any) =>
        (a.filename ?? '').toLowerCase().includes(q) ||
        (a.sub_sport ?? '').toLowerCase().includes(q)
      )
    }
    return list
  }, [activities, globalTimeRange, search])

  // Sort
  const sorted = useMemo(() => {
    return [...filtered].sort((a: any, b: any) => {
      const va = a[sortKey] ?? 0
      const vb = b[sortKey] ?? 0
      return sortAsc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1)
    })
  }, [filtered, sortKey, sortAsc])

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const pageData = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(false)
    }
    setPage(0)
  }

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <th
      className={styles.sortable}
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field ? (sortAsc ? '\u25B2' : '\u25BC') : ''}
    </th>
  )

  return (
    <div className={styles.container}>
      <div className={styles.controls}>
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Search rides..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
        />
        <span className={styles.count}>{filtered.length} rides</span>
      </div>

      <table className={styles.table}>
        <thead>
          <tr>
            <SortHeader label="Date" field="start_time" />
            <th>Type</th>
            <SortHeader label="Duration" field="total_elapsed_time" />
            <SortHeader label="NP" field="normalized_power" />
            <SortHeader label="TSS" field="training_stress_score" />
            <th>IF</th>
          </tr>
        </thead>
        <tbody>
          {pageData.map((a: any) => (
            <tr key={a.id} className={styles.row}>
              <td>{new Date(a.start_time).toLocaleDateString()}</td>
              <td>{a.sub_sport ?? 'ride'}</td>
              <td>{formatDuration(a.total_elapsed_time)}</td>
              <td>{a.normalized_power != null ? `${Math.round(a.normalized_power)}W` : '\u2014'}</td>
              <td>{a.training_stress_score != null ? Math.round(a.training_stress_score) : '\u2014'}</td>
              <td>{a.intensity_factor != null ? a.intensity_factor.toFixed(2) : '\u2014'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className={styles.pagination}>
          <button disabled={page === 0} onClick={() => setPage(page - 1)}>&laquo; Prev</button>
          <span>{page + 1} / {totalPages}</span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>Next &raquo;</button>
        </div>
      )}
    </div>
  )
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '\u2014'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

registerPanel({
  id: 'rides-table',
  label: 'Rides Table',
  category: 'history',
  description: 'Sortable, paginated, searchable ride history',
  component: RidesTable,
  dataKeys: ['activities', 'globalTimeRange'],
})
