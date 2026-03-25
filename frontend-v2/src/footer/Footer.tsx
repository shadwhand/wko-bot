import { useDataStore } from '../store/data-store'
import styles from './Footer.module.css'

export function Footer() {
  const loading = useDataStore((s) => s.loading)
  const errors = useDataStore((s) => s.errors)
  const errorCount = Object.keys(errors).length

  return (
    <footer className={styles.footer}>
      <div className={styles.left}>
        {loading.size > 0 && (
          <span className={styles.loading}>
            Loading {Array.from(loading).join(', ')}...
          </span>
        )}
        {errorCount > 0 && (
          <span className={styles.errors}>
            {errorCount} error{errorCount > 1 ? 's' : ''}
          </span>
        )}
        {loading.size === 0 && errorCount === 0 && (
          <span className={styles.connected}>Connected</span>
        )}
      </div>
      <div className={styles.right}>
        <span className={styles.version}>WKO5 Analyzer v2</span>
      </div>
    </footer>
  )
}
