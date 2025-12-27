import { describe, it, expect, beforeEach, vi } from 'vitest'
import { modalService, type ModalConfig } from '../modalService'
import { defineComponent } from 'vue'

// Mock component for testing
const TestComponent = defineComponent({
  name: 'TestComponent',
  template: '<div>Test Component</div>'
})

describe('ModalService', () => {
  beforeEach(() => {
    // Clear all modals before each test
    modalService.closeAll()
  })

  it('should show a modal with proper z-index', () => {
    const config: ModalConfig = {
      id: 'test-modal',
      component: TestComponent,
      title: 'Test Modal'
    }

    modalService.show(config)

    const modal = modalService.getModal('test-modal')
    expect(modal).toBeDefined()
    expect(modal?.id).toBe('test-modal')
    expect(modal?.zIndex).toBeGreaterThanOrEqual(1000)
    expect(modal?.isOpen).toBe(true)
  })

  it('should close a modal and remove it from stack', () => {
    const config: ModalConfig = {
      id: 'test-modal',
      component: TestComponent
    }

    modalService.show(config)
    expect(modalService.isOpen('test-modal')).toBe(true)

    modalService.close('test-modal')
    expect(modalService.isOpen('test-modal')).toBe(false)
    expect(modalService.getModal('test-modal')).toBeUndefined()
  })

  it('should manage z-index properly for stacked modals', () => {
    const config1: ModalConfig = {
      id: 'modal-1',
      component: TestComponent
    }
    const config2: ModalConfig = {
      id: 'modal-2',
      component: TestComponent
    }

    modalService.show(config1)
    modalService.show(config2)

    const modal1 = modalService.getModal('modal-1')
    const modal2 = modalService.getModal('modal-2')

    expect(modal2?.zIndex).toBeGreaterThan(modal1?.zIndex || 0)
  })

  it('should maintain proper modal stack order', () => {
    const config1: ModalConfig = {
      id: 'modal-1',
      component: TestComponent
    }
    const config2: ModalConfig = {
      id: 'modal-2',
      component: TestComponent
    }
    const config3: ModalConfig = {
      id: 'modal-3',
      component: TestComponent
    }

    modalService.show(config1)
    modalService.show(config2)
    modalService.show(config3)

    const stack = modalService.getModalStack()
    expect(stack).toEqual(['modal-1', 'modal-2', 'modal-3'])
  })

  it('should close top modal correctly', () => {
    const config1: ModalConfig = {
      id: 'modal-1',
      component: TestComponent
    }
    const config2: ModalConfig = {
      id: 'modal-2',
      component: TestComponent
    }

    modalService.show(config1)
    modalService.show(config2)

    modalService.closeTop()

    expect(modalService.isOpen('modal-1')).toBe(true)
    expect(modalService.isOpen('modal-2')).toBe(false)
  })

  it('should close all modals', () => {
    const config1: ModalConfig = {
      id: 'modal-1',
      component: TestComponent
    }
    const config2: ModalConfig = {
      id: 'modal-2',
      component: TestComponent
    }

    modalService.show(config1)
    modalService.show(config2)

    modalService.closeAll()

    expect(modalService.isOpen('modal-1')).toBe(false)
    expect(modalService.isOpen('modal-2')).toBe(false)
    expect(modalService.getModalStack()).toHaveLength(0)
  })

  it('should handle non-modal dialogs correctly', () => {
    const config: ModalConfig = {
      id: 'non-modal',
      component: TestComponent,
      modal: false
    }

    modalService.show(config)

    const modal = modalService.getModal('non-modal')
    expect(modal?.modal).toBe(false)
  })

  it('should get correct top z-index', () => {
    const initialZIndex = modalService.getTopZIndex()
    expect(initialZIndex).toBe(1000) // Base z-index

    const config: ModalConfig = {
      id: 'test-modal',
      component: TestComponent
    }

    modalService.show(config)
    const newTopZIndex = modalService.getTopZIndex()
    expect(newTopZIndex).toBeGreaterThan(initialZIndex)
  })

  it('should handle custom z-index', () => {
    const config: ModalConfig = {
      id: 'custom-z-modal',
      component: TestComponent,
      zIndex: 2000
    }

    modalService.show(config)

    const modal = modalService.getModal('custom-z-modal')
    expect(modal?.zIndex).toBe(2000)
  })

  it('should handle modal configuration defaults', () => {
    const config: ModalConfig = {
      id: 'default-modal',
      component: TestComponent
    }

    modalService.show(config)

    const modal = modalService.getModal('default-modal')
    expect(modal?.modal).toBe(true) // Default to modal
    expect(modal?.closable).toBe(true) // Default to closable
    expect(modal?.closeOnBackdrop).toBe(true) // Default to close on backdrop
    expect(modal?.size).toBe('md') // Default size
  })
})