/**
 * Tests for the Row Control Panel Vue component.
 * 
 * This module tests the row control panel functionality including:
 * - Button presence and configuration
 * - State management based on selection
 * - Command triggering
 * - Customization support
 * 
 * Requirements: 1.1, 1.2, 1.3
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import RowControlPanel from '../RowControlPanel.vue'

describe('RowControlPanel', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = mount(RowControlPanel)
  })

  describe('Button Presence and Configuration', () => {
    it('should contain all required buttons as per Requirements 1.2', () => {
      const requiredButtons = [
        'add_row',      // Добавить
        'delete_row',   // Удалить
        'move_up',      // Переместить выше
        'move_down',    // Переместить ниже
        'import_data',  // Импорт
        'export_data',  // Экспорт
        'print_data'    // Печать
      ]

      // Check that all required buttons are present
      requiredButtons.forEach(buttonId => {
        const button = wrapper.find(`[data-command="${buttonId}"]`)
        if (!button.exists()) {
          // Try finding by title attribute containing the expected text
          const buttons = wrapper.findAll('button')
          const found = buttons.some(btn => {
            const onClick = btn.attributes('onclick') || btn.element.getAttribute('data-testid')
            return onClick && onClick.includes(buttonId)
          })
          
          if (!found) {
            // Check if button exists in visible commands
            const component = wrapper.vm as any
            expect(component.visibleCommandButtons.some((cmd: any) => cmd.id === buttonId))
              .toBe(true, `Button ${buttonId} not found in panel`)
          }
        }
      })
    })

    it('should have tooltips for all buttons as per Requirements 1.3', () => {
      const buttons = wrapper.findAll('button')
      
      // Filter out the customize button and dropdown toggle
      const commandButtons = buttons.filter(btn => 
        btn.attributes('title') && 
        !btn.classes().includes('customize-btn') &&
        !btn.classes().includes('dropdown-toggle')
      )

      commandButtons.forEach(button => {
        const title = button.attributes('title')
        expect(title).toBeTruthy()
        expect(title?.trim()).not.toBe('')
      })
    })

    it('should have icons for all buttons', () => {
      const expectedIcons = {
        'add_row': '➕',
        'delete_row': '🗑',
        'move_up': '↑',
        'move_down': '↓',
        'import_data': '📥',
        'export_data': '📤',
        'print_data': '🖨'
      }

      const component = wrapper.vm as any
      component.visibleCommandButtons.forEach((command: any) => {
        const expectedIcon = expectedIcons[command.id as keyof typeof expectedIcons]
        if (expectedIcon) {
          expect(command.icon).toBe(expectedIcon)
        }
      })
    })
  })

  describe('Button State Management', () => {
    it('should disable delete button without selection (Requirements 1.4)', async () => {
      await wrapper.setProps({
        hasSelection: false,
        hasRows: true
      })

      const component = wrapper.vm as any
      const deleteCommand = component.visibleCommandButtons.find((cmd: any) => cmd.id === 'delete_row')
      
      if (deleteCommand) {
        expect(component.isCommandEnabled(deleteCommand)).toBe(false)
      }
    })

    it('should enable delete button with selection', async () => {
      await wrapper.setProps({
        hasSelection: true,
        hasRows: true
      })

      const component = wrapper.vm as any
      const deleteCommand = component.visibleCommandButtons.find((cmd: any) => cmd.id === 'delete_row')
      
      if (deleteCommand) {
        expect(component.isCommandEnabled(deleteCommand)).toBe(true)
      }
    })

    it('should disable move up button for first row (Requirements 1.5)', async () => {
      await wrapper.setProps({
        hasSelection: true,
        hasRows: true,
        isFirstRowSelected: true
      })

      const component = wrapper.vm as any
      const moveUpCommand = component.visibleCommandButtons.find((cmd: any) => cmd.id === 'move_up')
      
      if (moveUpCommand) {
        expect(component.isCommandEnabled(moveUpCommand)).toBe(false)
      }
    })

    it('should disable move down button for last row (Requirements 1.6)', async () => {
      await wrapper.setProps({
        hasSelection: true,
        hasRows: true,
        isLastRowSelected: true
      })

      const component = wrapper.vm as any
      const moveDownCommand = component.visibleCommandButtons.find((cmd: any) => cmd.id === 'move_down')
      
      if (moveDownCommand) {
        expect(component.isCommandEnabled(moveDownCommand)).toBe(false)
      }
    })

    it('should disable export button without rows', async () => {
      await wrapper.setProps({
        hasSelection: false,
        hasRows: false
      })

      const component = wrapper.vm as any
      const exportCommand = component.visibleCommandButtons.find((cmd: any) => cmd.id === 'export_data')
      
      if (exportCommand) {
        expect(component.isCommandEnabled(exportCommand)).toBe(false)
      }
    })

    it('should always enable add button', async () => {
      // Test with no selection and no rows
      await wrapper.setProps({
        hasSelection: false,
        hasRows: false
      })

      const component = wrapper.vm as any
      const addCommand = component.visibleCommandButtons.find((cmd: any) => cmd.id === 'add_row')
      
      if (addCommand) {
        expect(component.isCommandEnabled(addCommand)).toBe(true)
      }

      // Test with selection
      await wrapper.setProps({
        hasSelection: true,
        hasRows: true
      })

      expect(component.isCommandEnabled(addCommand)).toBe(true)
    })
  })

  describe('Command Triggering', () => {
    it('should emit command-triggered event when button is clicked', async () => {
      const component = wrapper.vm as any
      
      // Simulate clicking a command
      component.executeCommand('add_row')
      
      // Check that the event was emitted
      expect(wrapper.emitted('command-triggered')).toBeTruthy()
      expect(wrapper.emitted('command-triggered')?.[0]).toEqual(['add_row'])
    })

    it('should emit customize-requested event', async () => {
      const customizeButton = wrapper.find('.customize-btn')
      expect(customizeButton.exists()).toBe(true)
      
      await customizeButton.trigger('click')
      
      expect(wrapper.emitted('customize-requested')).toBeTruthy()
    })
  })

  describe('Panel Customization', () => {
    it('should show only visible commands', async () => {
      const customCommands = ['add_row', 'delete_row']
      
      await wrapper.setProps({
        visibleCommands: customCommands
      })

      const component = wrapper.vm as any
      expect(component.visibleCommandButtons).toHaveLength(2)
      expect(component.visibleCommandButtons.map((cmd: any) => cmd.id)).toEqual(customCommands)
    })

    it('should show hidden commands in More menu', async () => {
      const visibleCommands = ['add_row', 'delete_row']
      
      await wrapper.setProps({
        visibleCommands: visibleCommands
      })

      const component = wrapper.vm as any
      expect(component.hiddenCommandButtons.length).toBeGreaterThan(0)
      
      // Check that More menu exists
      const moreButton = wrapper.find('.dropdown-toggle')
      expect(moreButton.exists()).toBe(true)
    })

    it('should toggle More menu visibility', async () => {
      const visibleCommands = ['add_row', 'delete_row']
      
      await wrapper.setProps({
        visibleCommands: visibleCommands
      })

      const moreButton = wrapper.find('.dropdown-toggle')
      expect(moreButton.exists()).toBe(true)

      // Initially menu should be hidden
      expect(wrapper.find('.dropdown-menu').exists()).toBe(false)

      // Click to show menu
      await moreButton.trigger('click')
      expect(wrapper.find('.dropdown-menu').exists()).toBe(true)

      // Click again to hide menu
      await moreButton.trigger('click')
      expect(wrapper.find('.dropdown-menu').exists()).toBe(false)
    })
  })

  describe('Button Styling', () => {
    it('should apply correct CSS classes to buttons', () => {
      const component = wrapper.vm as any
      
      // Test add button gets primary class
      const addCommand = { id: 'add_row', name: 'Добавить', icon: '➕', tooltip: 'Add' }
      expect(component.getButtonClass(addCommand)).toBe('btn-primary')
      
      // Test delete button gets danger class
      const deleteCommand = { id: 'delete_row', name: 'Удалить', icon: '🗑', tooltip: 'Delete' }
      expect(component.getButtonClass(deleteCommand)).toBe('btn-danger')
      
      // Test other buttons get secondary class
      const moveCommand = { id: 'move_up', name: 'Выше', icon: '↑', tooltip: 'Move up' }
      expect(component.getButtonClass(moveCommand)).toBe('btn-secondary')
    })
  })

  describe('Integration', () => {
    it('should initialize with default commands', () => {
      const component = wrapper.vm as any
      const expectedDefault = [
        'add_row', 'delete_row', 'move_up', 'move_down',
        'import_data', 'export_data', 'print_data'
      ]
      
      expect(component.visibleCommandButtons.map((cmd: any) => cmd.id)).toEqual(expectedDefault)
    })

    it('should handle empty visible commands gracefully', async () => {
      await wrapper.setProps({
        visibleCommands: []
      })

      const component = wrapper.vm as any
      expect(component.visibleCommandButtons).toHaveLength(0)
      expect(component.hiddenCommandButtons.length).toBeGreaterThan(0)
    })
  })
})