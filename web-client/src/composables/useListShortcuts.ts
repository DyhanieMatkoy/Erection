import { onMounted, onUnmounted, type Ref } from 'vue'

export interface ListShortcutsOptions {
  onCreate?: () => void
  onCopy?: () => void
  onEdit?: () => void
  onDelete?: () => void
  onRefresh?: () => void
  onPrint?: () => void
  enabled?: Ref<boolean> | boolean
}

export function useListShortcuts(options: ListShortcutsOptions) {
  function handleKeydown(event: KeyboardEvent) {
    // Check if enabled (default true)
    const isEnabled = options.enabled === undefined || (typeof options.enabled === 'boolean' ? options.enabled : options.enabled.value)
    if (!isEnabled) return

    // Ignore if focus is in an input/textarea (except specific function keys if needed, but usually safe to ignore all)
    // However, F-keys might be desired even if focus is in search field?
    // F5 (Refresh) - yes.
    // Ins (Create) - yes.
    // F2 (Edit) - maybe not if editing text? But F2 is usually "Edit current item".
    // Delete - definitely NOT if in input.
    
    const isInputFocused = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName || '')
    
    switch (event.key) {
      case 'Insert':
        if (options.onCreate && !isInputFocused) {
          event.preventDefault()
          options.onCreate()
        }
        break
      case 'F9':
        if (options.onCopy) {
          event.preventDefault()
          options.onCopy()
        }
        break
      case 'F2':
        if (options.onEdit && !isInputFocused) {
          event.preventDefault()
          options.onEdit()
        }
        break
      case 'Delete':
        if (options.onDelete && !isInputFocused) {
          // We don't prevent default here usually, but if we handle it, we might want to.
          // But Delete in a list might scroll? No.
          options.onDelete()
        }
        break
      case 'F5':
        if (options.onRefresh) {
          event.preventDefault()
          options.onRefresh()
        }
        break
      case 'F8':
        if (options.onPrint) {
          event.preventDefault()
          options.onPrint()
        }
        break
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
}
