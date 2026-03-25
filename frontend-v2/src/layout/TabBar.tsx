import styles from './TabBar.module.css'

const DEFAULT_TABS = [
  { id: 'today', label: 'Today' },
  { id: 'health', label: 'Health' },
  { id: 'fitness', label: 'Fitness' },
  { id: 'event-prep', label: 'Event Prep' },
  { id: 'history', label: 'History' },
  { id: 'profile', label: 'Profile' },
]

interface TabBarProps {
  activeTab: string
  onTabChange: (tabId: string) => void
}

export function TabBar({ activeTab, onTabChange }: TabBarProps) {
  return (
    <nav className={styles.tabBar}>
      {DEFAULT_TABS.map((tab) => (
        <button
          key={tab.id}
          className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
