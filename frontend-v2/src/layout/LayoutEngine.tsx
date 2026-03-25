import { useLayoutStore } from './layoutStore'
import { getPanelComponent } from './PanelRegistry'
import { PanelWrapper } from './PanelWrapper'
import styles from './LayoutEngine.module.css'

export function LayoutEngine() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const editMode = useLayoutStore(s => s.editMode)
  const removePanel = useLayoutStore(s => s.removePanel)

  const activeTab = layout.tabs.find(t => t.id === activeTabId)

  if (!activeTab) {
    return (
      <div className={styles.emptyState}>
        <p>No tab selected</p>
      </div>
    )
  }

  if (activeTab.panels.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>This tab has no panels.</p>
        {editMode && <p>Click the + button below to add some.</p>}
      </div>
    )
  }

  return (
    <div className={styles.panelGrid}>
      {activeTab.panels.map(panelId => {
        const Component = getPanelComponent(panelId)

        return (
          <PanelWrapper
            key={panelId}
            panelId={panelId}
            editMode={editMode}
            onRemove={() => removePanel(activeTabId, panelId)}
          >
            {Component ? (
              <Component />
            ) : (
              <div className={styles.placeholder}>
                <span>Panel "{panelId}" not yet implemented</span>
              </div>
            )}
          </PanelWrapper>
        )
      })}
    </div>
  )
}
