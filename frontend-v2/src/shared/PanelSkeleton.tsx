import styles from './PanelSkeleton.module.css'

export function PanelSkeleton() {
  return (
    <div className={styles.skeleton}>
      <div className={styles.bar} style={{ width: '60%' }} />
      <div className={styles.bar} style={{ width: '80%' }} />
      <div className={styles.bar} style={{ width: '45%' }} />
    </div>
  )
}
