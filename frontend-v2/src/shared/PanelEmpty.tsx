import styles from './PanelEmpty.module.css'

interface PanelEmptyProps {
  message?: string
}

export function PanelEmpty({ message = 'No data available' }: PanelEmptyProps) {
  return (
    <div className={styles.empty}>
      <p>{message}</p>
    </div>
  )
}
