import styles from './Header.module.css'
import { useLayoutStore } from '../layout/layoutStore'
import { useDataStore } from '../store/data-store'

export function Header() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const setActiveTab = useLayoutStore(s => s.setActiveTab)
  const editMode = useLayoutStore(s => s.editMode)
  const enterEditMode = useLayoutStore(s => s.enterEditMode)
  const lastRefresh = useDataStore(s => s.lastRefresh)

  const staleLabel = formatStaleness(lastRefresh)

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.logo}>WKO5</span>
      </div>

      <nav className={styles.tabBar} role="tablist" aria-label="Dashboard tabs">
        {layout.tabs.map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={tab.id === activeTabId}
            className={`${styles.tab} ${tab.id === activeTabId ? styles.active : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className={styles.actions}>
        {staleLabel && (
          <span
            className={`${styles.stale} ${staleLabel.includes('d') ? styles.staleWarn : ''}`}
            title="Last data sync"
          >
            Synced {staleLabel} ago
          </span>
        )}

        {!editMode && (
          <button
            className={styles.gearButton}
            onClick={enterEditMode}
            aria-label="Edit layout"
            title="Edit dashboard layout"
          >
            &#9881;
          </button>
        )}

        {/* Claude button placeholder — wired in Phase 2 */}
        <button
          className={styles.claudeButton}
          disabled
          title="Claude AI — coming in Phase 2"
        >
          Claude
        </button>
      </div>
    </header>
  )
}

/** Format last refresh into human-readable staleness */
function formatStaleness(lastRefresh: string | null): string | null {
  if (!lastRefresh) return null
  const diff = Date.now() - new Date(lastRefresh).getTime()
  const hours = Math.floor(diff / 3_600_000)
  if (hours < 1) return null // fresh
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  return `${days}d`
}
