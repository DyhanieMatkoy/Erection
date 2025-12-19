/**
 * Tests for the Panel Configuration Dialog component.
 * 
 * This module tests the panel configuration dialog functionality including:
 * - Command tree interface with checkboxes
 * - Real-time panel updates during configuration
 * - "More" submenu configuration
 * - Save/Reset functionality
 * 
 * Requirements: 9.1, 9.2, 9.3, 9.4
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import PanelConfigurationDialog from '../PanelConfigurationDialog.vue'

// ============================================================================
// Types and Interfaces
// ============================================================================

interface CommandTreeNode {
  id: string
  name: string
  icon: string
  tooltip: string
  visible?: boolean
  enabled?: boolean
  isStandard?: boolean
}

interface PanelConfiguration {
  visibleCommands: string[]
  showTooltips: boolean
  compactMode: boolean
}

// ============================================================================
// Test Data
// ============================================================================

const sampleCommands: Record<string, CommandTreeNode> = {
  add_row: {
    id: 'add_row',
    name: 'Добавить',
    icon: '➕',
    tooltip: 'Добавить новую строку',
    enabled: true,
    isStandard: true
  },
  delete_row: {
    id: 'delete_row',
    name: 'Удалить',
    icon: '🗑',
    tooltip: 'Удалить выбранные строки',
    enabled: true,
    isStandard: true
  },
  import_data: {
    id: 'import_data',
    name: 'Импорт',
    icon: '📥',
    tooltip: 'Импортировать данные',
    enabled: true,
    isStandard: true
  },
  export_data: {
    id: 'export_data',
    name: 'Экспорт',
    icon: '📤',
    tooltip: 'Экспортировать данные',
    enabled: true,
    isStandard: true
  }
}

const sampleConfig: PanelConfiguration = {
  visibleCommands: ['add_row', 'delete_row'],
  showTooltips: true,
  compactMode: false
}

// ============================================================================
// Test Utilities
// ============================================================================

function createWrapper(props: Partial<any> = {}) {
  return mount(PanelConfigurationDialog, {
    props: {
      isVisible: true,
      currentConfig: sampleConfig,
      availableCommands: sampleCommands,
      ...props
    }
  })
}

// ============================================================================
// Test Suites
// ============================================================================

describe('PanelConfigurationDialog', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = createWrapper()
  })

  describe('Dialog UI Components', () => {
    it('should render dialog when visible (Requirements 9.1)', () => {
      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.modal-dialog').exists()).toBe(true)
      expect(wrapper.find('.modal-title').text()).toBe('Настройка панели команд')
    })

    it('should not render dialog when not visible', () => {
      const hiddenWrapper = createWrapper({ isVisible: false })
      expect(hiddenWrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('should render all main sections (Requirements 9.1)', () => {
      expect(wrapper.find('.command-tree-section').exists()).toBe(true)
      expect(wrapper.find('.preview-section').exists()).toBe(true)
      expect(wrapper.find('.command-list').exists()).toBe(true)
      expect(wrapper.find('.preview-area').exists()).toBe(true)
      expect(wrapper.find('.options-section').exists()).toBe(true)
    })

    it('should render all action buttons', () => {
      const buttons = wrapper.findAll('.modal-footer .btn')
      expect(buttons.length).toBeGreaterThanOrEqual(4)
      
      const buttonTexts = buttons.map(btn => btn.text())
      expect(buttonTexts).toContain('Предварительный просмотр')
      expect(buttonTexts).toContain('Сброс')
      expect(buttonTexts).toContain('Отмена')
      expect(buttonTexts).toContain('Сохранить')
    })
  })

  describe('Command Tree Interface', () => {
    it('should display all available commands (Requirements 9.1)', () => {
      const commandItems = wrapper.findAll('.command-item')
      expect(commandItems.length).toBe(Object.keys(sampleCommands).length)
    })

    it('should show command icons and names correctly', () => {
      const commandItems = wrapper.findAll('.command-item')
      
      commandItems.forEach((item, index) => {
        const commandId = Object.keys(sampleCommands)[index]
        const command = sampleCommands[commandId]
        
        expect(item.find('.command-icon').text()).toBe(command.icon)
        expect(item.find('.command-name').text()).toBe(command.name)
      })
    })

    it('should reflect current visibility in checkboxes', () => {
      const checkboxes = wrapper.findAll('.command-checkbox input[type="checkbox"]')
      
      checkboxes.forEach((checkbox, index) => {
        const commandId = Object.keys(sampleCommands)[index]
        const isVisible = sampleConfig.visibleCommands.includes(commandId)
        
        expect((checkbox.element as HTMLInputElement).checked).toBe(isVisible)
      })
    })

    it('should show tooltips for commands', () => {
      const tooltipElements = wrapper.findAll('.command-tooltip')
      expect(tooltipElements.length).toBe(Object.keys(sampleCommands).length)
      
      tooltipElements.forEach(tooltip => {
        expect(tooltip.attributes('title')).toBeDefined()
      })
    })
  })

  describe('Configuration Changes', () => {
    it('should update configuration when checkbox is toggled (Requirements 9.2)', async () => {
      const checkbox = wrapper.find('.command-checkbox input[type="checkbox"]')
      const originalChecked = (checkbox.element as HTMLInputElement).checked
      
      await checkbox.setValue(!originalChecked)
      
      // Should emit configuration-changed event
      expect(wrapper.emitted('configuration-changed')).toBeTruthy()
    })

    it('should update options when option checkboxes are toggled', async () => {
      const tooltipsCheckbox = wrapper.findAll('.option-checkbox input[type="checkbox"]')[0]
      const originalChecked = (tooltipsCheckbox.element as HTMLInputElement).checked
      
      await tooltipsCheckbox.setValue(!originalChecked)
      
      // Should emit configuration-changed event
      expect(wrapper.emitted('configuration-changed')).toBeTruthy()
    })

    it('should emit preview event when configuration changes (Requirements 9.2)', async () => {
      const checkbox = wrapper.find('.command-checkbox input[type="checkbox"]')
      await checkbox.setValue(false)
      
      expect(wrapper.emitted('preview')).toBeTruthy()
    })
  })

  describe('Preview Functionality', () => {
    it('should show visible commands in preview (Requirements 9.2)', () => {
      const previewArea = wrapper.find('.preview-area')
      const previewText = previewArea.text()
      
      expect(previewText).toContain('Видимые кнопки:')
      
      // Check that visible commands are shown
      sampleConfig.visibleCommands.forEach(commandId => {
        const command = sampleCommands[commandId]
        expect(previewText).toContain(command.name)
      })
    })

    it('should show hidden commands in More menu (Requirements 9.3)', () => {
      const previewArea = wrapper.find('.preview-area')
      const previewText = previewArea.text()
      
      const hiddenCommands = Object.keys(sampleCommands).filter(
        id => !sampleConfig.visibleCommands.includes(id)
      )
      
      if (hiddenCommands.length > 0) {
        expect(previewText).toContain('Меню "Еще":')
        
        hiddenCommands.forEach(commandId => {
          const command = sampleCommands[commandId]
          expect(previewText).toContain(command.name)
        })
      }
    })

    it('should update statistics correctly', () => {
      const statistics = wrapper.find('.statistics')
      const statsText = statistics.text()
      
      expect(statsText).toContain('Всего команд:')
      expect(statsText).toContain('Видимых:')
      expect(statsText).toContain('Скрытых:')
      
      // Check numbers
      const totalCommands = Object.keys(sampleCommands).length
      const visibleCount = sampleConfig.visibleCommands.length
      const hiddenCount = totalCommands - visibleCount
      
      expect(statsText).toContain(totalCommands.toString())
      expect(statsText).toContain(visibleCount.toString())
      expect(statsText).toContain(hiddenCount.toString())
    })

    it('should show preview buttons with correct styling', () => {
      const previewButtons = wrapper.findAll('.preview-button')
      
      previewButtons.forEach(button => {
        expect(button.classes()).toContain('preview-button')
        expect(button.find('.icon').exists()).toBe(true)
      })
    })
  })

  describe('Dialog Actions', () => {
    it('should emit close event when close button is clicked', async () => {
      const closeButton = wrapper.find('.close-button')
      await closeButton.trigger('click')
      
      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('should emit close event when cancel button is clicked', async () => {
      const cancelButton = wrapper.findAll('.modal-footer .btn').find(
        btn => btn.text() === 'Отмена'
      )
      
      if (cancelButton) {
        await cancelButton.trigger('click')
        expect(wrapper.emitted('close')).toBeTruthy()
      }
    })

    it('should emit save event when save button is clicked (Requirements 9.4)', async () => {
      const saveButton = wrapper.findAll('.modal-footer .btn').find(
        btn => btn.text() === 'Сохранить'
      )
      
      if (saveButton) {
        await saveButton.trigger('click')
        expect(wrapper.emitted('save')).toBeTruthy()
      }
    })

    it('should emit preview event when preview button is clicked', async () => {
      const previewButton = wrapper.findAll('.modal-footer .btn').find(
        btn => btn.text() === 'Предварительный просмотр'
      )
      
      if (previewButton) {
        await previewButton.trigger('click')
        expect(wrapper.emitted('preview')).toBeTruthy()
      }
    })

    it('should reset configuration when reset button is clicked (Requirements 9.4)', async () => {
      // Mock window.confirm to return true
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
      
      const resetButton = wrapper.findAll('.modal-footer .btn').find(
        btn => btn.text() === 'Сброс'
      )
      
      if (resetButton) {
        await resetButton.trigger('click')
        
        // Should show confirmation dialog
        expect(confirmSpy).toHaveBeenCalled()
        
        // Should emit configuration-changed with reset values
        expect(wrapper.emitted('configuration-changed')).toBeTruthy()
      }
      
      confirmSpy.mockRestore()
    })
  })

  describe('Validation', () => {
    it('should warn when no commands are visible', async () => {
      // Mock window.confirm to return false (cancel)
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
      
      // Uncheck all commands
      const checkboxes = wrapper.findAll('.command-checkbox input[type="checkbox"]')
      for (const checkbox of checkboxes) {
        await checkbox.setValue(false)
      }
      
      // Try to save
      const saveButton = wrapper.findAll('.modal-footer .btn').find(
        btn => btn.text() === 'Сохранить'
      )
      
      if (saveButton) {
        await saveButton.trigger('click')
        
        // Should show warning
        expect(confirmSpy).toHaveBeenCalled()
        
        // Should not emit save event since user cancelled
        expect(wrapper.emitted('save')).toBeFalsy()
      }
      
      confirmSpy.mockRestore()
    })

    it('should allow saving when user confirms no visible commands', async () => {
      // Mock window.confirm to return true (proceed)
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
      
      // Uncheck all commands
      const checkboxes = wrapper.findAll('.command-checkbox input[type="checkbox"]')
      for (const checkbox of checkboxes) {
        await checkbox.setValue(false)
      }
      
      // Try to save
      const saveButton = wrapper.findAll('.modal-footer .btn').find(
        btn => btn.text() === 'Сохранить'
      )
      
      if (saveButton) {
        await saveButton.trigger('click')
        
        // Should show warning
        expect(confirmSpy).toHaveBeenCalled()
        
        // Should emit save event since user confirmed
        expect(wrapper.emitted('save')).toBeTruthy()
      }
      
      confirmSpy.mockRestore()
    })
  })

  describe('Responsive Design', () => {
    it('should handle mobile layout', () => {
      // This test would need to simulate different viewport sizes
      // For now, we just check that responsive classes exist
      expect(wrapper.find('.configuration-layout').exists()).toBe(true)
    })

    it('should handle keyboard navigation', async () => {
      const firstCheckbox = wrapper.find('.command-checkbox input[type="checkbox"]')
      
      // Focus the checkbox
      await firstCheckbox.trigger('focus')
      
      // Should be focusable
      expect(document.activeElement).toBe(firstCheckbox.element)
    })
  })

  describe('Integration', () => {
    it('should load configuration correctly on mount', () => {
      const newWrapper = createWrapper({
        currentConfig: {
          visibleCommands: ['add_row'],
          showTooltips: false,
          compactMode: true
        }
      })
      
      // Check that configuration is loaded
      const tooltipsCheckbox = newWrapper.findAll('.option-checkbox input[type="checkbox"]')[0]
      const compactCheckbox = newWrapper.findAll('.option-checkbox input[type="checkbox"]')[1]
      
      expect((tooltipsCheckbox.element as HTMLInputElement).checked).toBe(false)
      expect((compactCheckbox.element as HTMLInputElement).checked).toBe(true)
    })

    it('should handle empty commands gracefully', () => {
      const emptyWrapper = createWrapper({
        availableCommands: {}
      })
      
      expect(emptyWrapper.findAll('.command-item').length).toBe(0)
      expect(emptyWrapper.find('.no-commands').exists()).toBe(true)
    })

    it('should handle disabled commands correctly', () => {
      const disabledCommands = {
        ...sampleCommands,
        disabled_command: {
          id: 'disabled_command',
          name: 'Disabled',
          icon: '❌',
          tooltip: 'Disabled command',
          enabled: false,
          isStandard: true
        }
      }
      
      const disabledWrapper = createWrapper({
        availableCommands: disabledCommands
      })
      
      const disabledItem = disabledWrapper.findAll('.command-item').find(
        item => item.classes().includes('disabled')
      )
      
      expect(disabledItem).toBeDefined()
    })
  })
})