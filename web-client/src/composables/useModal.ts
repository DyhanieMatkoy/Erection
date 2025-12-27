import { ref, computed, onUnmounted } from 'vue'
import { modalService, type ModalConfig, type ActiveModal } from '@/services/modalService'

export function useModal() {
  const modals = computed(() => modalService.getModals())
  const modalStack = computed(() => modalService.getModalStack())

  /**
   * Show a modal dialog
   */
  const showModal = (config: ModalConfig) => {
    modalService.show(config)
  }

  /**
   * Close a modal dialog
   */
  const closeModal = (id: string) => {
    modalService.close(id)
  }

  /**
   * Check if a modal is open
   */
  const isModalOpen = (id: string) => {
    return modalService.isOpen(id)
  }

  /**
   * Get a specific modal
   */
  const getModal = (id: string): ActiveModal | undefined => {
    return modalService.getModal(id)
  }

  /**
   * Close all modals
   */
  const closeAllModals = () => {
    modalService.closeAll()
  }

  /**
   * Close the top modal
   */
  const closeTopModal = () => {
    modalService.closeTop()
  }

  /**
   * Get the current top z-index
   */
  const getTopZIndex = () => {
    return modalService.getTopZIndex()
  }

  return {
    modals,
    modalStack,
    showModal,
    closeModal,
    isModalOpen,
    getModal,
    closeAllModals,
    closeTopModal,
    getTopZIndex
  }
}

/**
 * Composable for managing a single modal instance
 */
export function useSingleModal(id: string) {
  const isOpen = ref(false)
  
  const open = (config: Omit<ModalConfig, 'id'>) => {
    modalService.show({ ...config, id })
    isOpen.value = true
  }

  const close = () => {
    modalService.close(id)
    isOpen.value = false
  }

  const toggle = (config?: Omit<ModalConfig, 'id'>) => {
    if (isOpen.value) {
      close()
    } else if (config) {
      open(config)
    }
  }

  // Clean up on unmount
  onUnmounted(() => {
    if (isOpen.value) {
      close()
    }
  })

  return {
    isOpen: computed(() => modalService.isOpen(id)),
    open,
    close,
    toggle
  }
}