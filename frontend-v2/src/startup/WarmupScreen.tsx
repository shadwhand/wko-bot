import { type WarmupStatusResponse } from '../api/types'
import styles from './WarmupScreen.module.css'

interface WarmupScreenProps {
  status: WarmupStatusResponse | null
  error: string | null
}

export function WarmupScreen({ status, error }: WarmupScreenProps) {
  const completedCount = status ? Object.keys(status.results).length : 0
  const errorCount = status ? Object.keys(status.errors).length : 0
  const totalTasks = 8 // fitness, pmc, model_90, profile_90, rolling_ftp, clinical, ftp_growth, rolling_pd
  const progress = status ? Math.round(((completedCount + errorCount) / totalTasks) * 100) : 0

  return (
    <div className={styles.screen}>
      <div className={styles.content}>
        <h1 className={styles.title}>WKO5 Analyzer</h1>
        <p className={styles.subtitle}>Cycling Performance Analytics</p>

        {error ? (
          <div className={styles.error}>
            <p>Unable to connect to backend</p>
            <p className={styles.errorDetail}>{error}</p>
            <p className={styles.hint}>
              Start the API server: <code>python run_api.py</code>
            </p>
          </div>
        ) : (
          <>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className={styles.status}>
              {!status && 'Connecting...'}
              {status?.running && `Pre-computing models... ${completedCount}/${totalTasks}`}
              {status?.done && 'Loading dashboard...'}
            </p>
            {errorCount > 0 && (
              <p className={styles.warnings}>
                {errorCount} warmup task{errorCount > 1 ? 's' : ''} failed (non-critical)
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
