import { useDataStore } from '../store/data-store'
import styles from './SyncIndicator.module.css'

function formatTimeAgo(isoDate: string): string {
  const ms = Date.now() - new Date(isoDate).getTime()
  const minutes = Math.floor(ms / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function staleness(isoDate: string): 'fresh' | 'stale' | 'old' {
  const ms = Date.now() - new Date(isoDate).getTime()
  const hours = ms / (1000 * 60 * 60)
  if (hours < 4) return 'fresh'
  if (hours < 24) return 'stale'
  return 'old'
}

export function SyncIndicator() {
  const lastRefresh = useDataStore((s) => s.lastRefresh)
  const loading = useDataStore((s) => s.loading)
  const refresh = useDataStore((s) => s.refresh)
  const isRefreshing = loading.size > 0

  if (!lastRefresh) return null

  const age = staleness(lastRefresh)
  const label = `Synced ${formatTimeAgo(lastRefresh)}`

  return (
    <div className={styles.indicator}>
      <span className={`${styles.dot} ${styles[age]}`} />
      <span className={`${styles.label} ${styles[age]}`}>{label}</span>
      <button
        className={styles.refreshBtn}
        onClick={() => refresh()}
        disabled={isRefreshing}
        title="Refresh data"
      >
        {isRefreshing ? '\u21BB' : '\u21BB'}
      </button>
    </div>
  )
}
