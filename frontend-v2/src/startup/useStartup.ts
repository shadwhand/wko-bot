import { useState, useEffect } from 'react'
import { type WarmupStatusResponse } from '../api/types'
import { getWarmupStatus, bootstrapToken } from '../api/client'
import { useDataStore } from '../store/data-store'

export type StartupPhase = 'warming' | 'loading' | 'ready' | 'error'

interface StartupState {
  phase: StartupPhase
  warmupStatus: WarmupStatusResponse | null
  error: string | null
}

const POLL_INTERVAL_MS = 1000

export function useStartup(): StartupState {
  const [phase, setPhase] = useState<StartupPhase>('warming')
  const [warmupStatus, setWarmupStatus] = useState<WarmupStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fetchCore = useDataStore((s) => s.fetchCore)
  const fetchSecondary = useDataStore((s) => s.fetchSecondary)
  const checkForUpdates = useDataStore((s) => s.checkForUpdates)
  useEffect(() => {
    let cancelled = false
    let timeoutId: ReturnType<typeof setTimeout>

    async function pollWarmup() {
      try {
        // Bootstrap auth token from /api/runtime (localhost-only, no auth)
        await bootstrapToken()

        console.log('[startup] polling warmup...')
        const status = await getWarmupStatus()
        console.log('[startup] warmup response:', status.done, status.running, 'cancelled:', cancelled)
        if (cancelled) return
        setWarmupStatus(status)

        if (status.done) {
          // Warmup complete — fetch core data
          console.log('[startup] warmup done, fetching core...')
          setPhase('loading')
          await fetchCore()
          console.log('[startup] fetchCore complete')
          if (cancelled) return

          // Record initial data version
          await checkForUpdates()

          setPhase('ready')

          // Kick off secondary data in background (non-blocking)
          fetchSecondary()
          return
        }

        // Still warming — poll again
        timeoutId = setTimeout(pollWarmup, POLL_INTERVAL_MS)
      } catch (err) {
        console.error('[startup] error:', err)
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Connection failed')
        setPhase('error')

        // Retry after a longer delay on error
        timeoutId = setTimeout(pollWarmup, POLL_INTERVAL_MS * 3)
      }
    }

    pollWarmup()

    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [fetchCore, fetchSecondary, checkForUpdates])

  return { phase, warmupStatus, error }
}
