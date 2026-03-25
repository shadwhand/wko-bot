import { Tooltip } from '../../components/Tooltip'
import styles from './FlagCard.module.css'

interface FlagCardProps {
  name: string
  status: 'ok' | 'warning' | 'danger'
  value: number | string
  threshold?: number | string
  detail?: string
  tooltip: {
    fullName: string
    derivation: string
    context?: string
  }
}

/** Convert SCREAMING_SNAKE or snake_case to Title Case */
function cleanName(raw: string): string {
  return raw
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

export function FlagCard({ name, status, value, threshold, detail, tooltip }: FlagCardProps) {
  const displayName = cleanName(name)
  const displayValue = (value === '--' || value === '') ? (detail || 'No data') : value

  return (
    <Tooltip label={displayName} {...tooltip}>
      <div className={`${styles.card} ${styles[status]}`}>
        <div className={styles.header}>
          <span className={styles.statusDot} />
          <span className={styles.name}>{displayName}</span>
        </div>
        <div className={styles.value}>{displayValue}</div>
        {threshold != null && (
          <div className={styles.threshold}>
            Threshold: {threshold}
          </div>
        )}
        {detail && <div className={styles.detail}>{detail}</div>}
      </div>
    </Tooltip>
  )
}
