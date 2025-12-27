import { type Component, ref, reactive } from 'vue'

export interface ModalConfig {
  id: string
  component: Component
  props?: Record<string, unknown>
  zIndex?: number
  modal?: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closable?: boolean
  closeOnBackdrop?: boolean
  fullscreen?: boolean
}

export interface ActiveModal extends ModalConfig {
  zIndex: number
  isOpen: boolean
}

class ModalService {
  private modals = reactive(new Map<string, ActiveModal>())
  private baseZIndex = 1000
  private modalStack = ref<string[]>([])

  /**
   * Show a modal dialog with proper z-index management
   */
  show(config: ModalConfig): void {
    const zIndex = config.zIndex || this.getNextZIndex()
    
    const activeModal: ActiveModal = {
      ...config,
      zIndex,
      modal: config.modal !== false, // Default to true (modal)
      isOpen: true,
      closable: config.closable !== false, // Default to true
      closeOnBackdrop: config.closeOnBackdrop !== false, // Default to true
      size: config.size || 'md'
    }

    this.modals.set(config.id, activeModal)
    
    // Add to stack for proper ordering
    if (!this.modalStack.value.includes(config.id)) {
      this.modalStack.value.push(config.id)
    }

    // Focus trapping for modal dialogs
    if (activeModal.modal) {
      this.trapFocus(config.id)
    }
  }

  /**
   * Close a modal dialog and clean up
   */
  close(id: string): void {
    const modal = this.modals.get(id)
    if (!modal) return

    // Remove from stack
    const stackIndex = this.modalStack.value.indexOf(id)
    if (stackIndex > -1) {
      this.modalStack.value.splice(stackIndex, 1)
    }

    // Remove from modals map
    this.modals.delete(id)

    // Restore focus to previous modal if any
    if (this.modalStack.value.length > 0) {
      const topModalId = this.modalStack.value[this.modalStack.value.length - 1]
      if (topModalId) {
        this.trapFocus(topModalId)
      }
    } else {
      this.releaseFocus()
    }
  }

  /**
   * Get the current top z-index
   */
  getTopZIndex(): number {
    let maxZIndex = this.baseZIndex
    for (const modal of this.modals.values()) {
      if (modal.zIndex > maxZIndex) {
        maxZIndex = modal.zIndex
      }
    }
    return maxZIndex
  }

  /**
   * Get the next available z-index
   */
  private getNextZIndex(): number {
    return this.getTopZIndex() + 10
  }

  /**
   * Get all active modals
   */
  getModals(): Map<string, ActiveModal> {
    return this.modals
  }

  /**
   * Get a specific modal by id
   */
  getModal(id: string): ActiveModal | undefined {
    return this.modals.get(id)
  }

  /**
   * Check if a modal is open
   */
  isOpen(id: string): boolean {
    const modal = this.modals.get(id)
    return modal?.isOpen || false
  }

  /**
   * Get the modal stack order
   */
  getModalStack(): string[] {
    return [...this.modalStack.value]
  }

  /**
   * Close all modals
   */
  closeAll(): void {
    const modalIds = [...this.modals.keys()]
    modalIds.forEach(id => this.close(id))
  }

  /**
   * Close the top modal
   */
  closeTop(): void {
    if (this.modalStack.value.length > 0) {
      const topModalId = this.modalStack.value[this.modalStack.value.length - 1]
      if (topModalId) {
        this.close(topModalId)
      }
    }
  }

  /**
   * Trap focus within the specified modal
   */
  private trapFocus(modalId: string): void {
    // Focus trapping implementation
    const modal = this.modals.get(modalId)
    if (!modal || !modal.modal) return

    // Find the modal element in DOM
    setTimeout(() => {
      const modalElement = document.querySelector(`[data-modal-id="${modalId}"]`)
      if (modalElement) {
        const focusableElements = modalElement.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        
        if (focusableElements.length > 0) {
          (focusableElements[0] as HTMLElement).focus()
        }
      }
    }, 100)
  }

  /**
   * Release focus trapping
   */
  private releaseFocus(): void {
    // Implementation to restore focus to the element that was focused before modal opened
    // This could be enhanced to remember the previously focused element
  }

  /**
   * Handle escape key for closing modals
   */
  handleEscape(): void {
    if (this.modalStack.value.length > 0) {
      const topModalId = this.modalStack.value[this.modalStack.value.length - 1]
      if (topModalId) {
        const topModal = this.modals.get(topModalId)
        
        if (topModal?.closable) {
          this.close(topModalId)
        }
      }
    }
  }
}

// Create singleton instance
export const modalService = new ModalService()

// Global escape key handler
document.addEventListener('keydown', (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    modalService.handleEscape()
  }
})

export default modalService