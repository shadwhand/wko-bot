import { useEffect, useRef } from 'react'
import { useDataStore } from '../store/data-store'

/** Interval between /health polls: 3.5 hours in ms. */
const POLL_INTERVAL_MS = 3.5 * 60 * 60 * 1000

/** Maximum staleness before refresh on window focus: 4 hours. */
const STALE_THRESHOLD_MS = 4 * 60 * 60 * 1000

/**
 * Auto-refresh hook. Polls /health periodically, checks data_version,
 * and refreshes on window focus if stale.
 *
 * Only activate after startup is complete (phase === 'ready').
 */
export function useAutoRefresh(active: boolean) {
  const checkForUpdates = useDataStore((s) => s.checkForUpdates)
  const refresh = useDataStore((s) => s.refresh)
  const lastRefresh = useDataStore((s) => s.lastRefresh)
  const intervalRef = useRef<ReturnType<typeof setInterval>>()

  // Periodic /health poll
  useEffect(() => {
    if (!active) return
    intervalRef.current = setInterval(async () => {
      const changed = await checkForUpdates()
      if (changed) {
        await refresh()
      }
    }, POLL_INTERVAL_MS)

    return () => clearInterval(intervalRef.current)
  }, [active, checkForUpdates, refresh])

  // Window focus refresh
  useEffect(() => {
    if (!active) return

    function handleFocus() {
      if (!lastRefresh) return
      const age = Date.now() - new Date(lastRefresh).getTime()
      if (age > STALE_THRESHOLD_MS) {
        refresh()
      }
    }

    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [active, lastRefresh, refresh])
}
