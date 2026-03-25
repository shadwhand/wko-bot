import styles from './PanelError.module.css'

interface PanelErrorProps {
  message: string
  onRetry?: () => void
}

export function PanelError({ message, onRetry }: PanelErrorProps) {
  return (
    <div className={styles.error}>
      <span className={styles.icon}>!</span>
      <p className={styles.message}>{message}</p>
      {onRetry && (
        <button className={styles.retry} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
