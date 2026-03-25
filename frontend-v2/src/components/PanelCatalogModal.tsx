import { useState, useEffect, useRef } from 'react'
import { getPanelCatalog } from '../layout/PanelRegistry'
import type { PanelId } from '../layout/types'
import styles from './PanelCatalogModal.module.css'

interface PanelCatalogModalProps {
  open: boolean
  /** Panel IDs already on the current tab (shown as disabled) */
  existingPanels: PanelId[]
  onSelect: (panelId: PanelId) => void
  onClose: () => void
}

export function PanelCatalogModal({
  open,
  existingPanels,
  onSelect,
  onClose,
}: PanelCatalogModalProps) {
  const [search, setSearch] = useState('')
  const dialogRef = useRef<HTMLDialogElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) {
      dialog.showModal()
      setSearch('')
      // Focus search input
      setTimeout(() => searchRef.current?.focus(), 50)
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  const catalog = getPanelCatalog()
  const query = search.toLowerCase().trim()

  return (
    <dialog ref={dialogRef} className={styles.modal} onClose={onClose}>
      <div className={styles.header}>
        <h3 className={styles.title}>Add Panel</h3>
        <button className={styles.closeButton} onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>

      <input
        ref={searchRef}
        type="text"
        className={styles.searchInput}
        placeholder="Search panels..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      <div className={styles.catalog}>
        {catalog.map(group => {
          const filtered = group.panels.filter(p =>
            !query ||
            p.label.toLowerCase().includes(query) ||
            p.description.toLowerCase().includes(query)
          )
          if (filtered.length === 0) return null

          return (
            <div key={group.category} className={styles.categoryGroup}>
              <div className={styles.categoryLabel}>{group.label}</div>
              {filtered.map(panel => {
                const alreadyAdded = existingPanels.includes(panel.id)
                return (
                  <button
                    key={panel.id}
                    className={`${styles.panelItem} ${alreadyAdded ? styles.disabled : ''}`}
                    onClick={() => {
                      if (!alreadyAdded) {
                        onSelect(panel.id)
                        onClose()
                      }
                    }}
                    disabled={alreadyAdded}
                  >
                    <div className={styles.panelLabel}>{panel.label}</div>
                    <div className={styles.panelDesc}>{panel.description}</div>
                    {alreadyAdded && (
                      <span className={styles.addedBadge}>Added</span>
                    )}
                  </button>
                )
              })}
            </div>
          )
        })}
      </div>
    </dialog>
  )
}
