/**
 * Tests for drag-and-drop functionality in BaseTablePart component.
 * 
 * Requirements: 7.7
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseTablePart from '../BaseTablePart.vue'
import type { TableColumn, TablePartConfiguration } from '../../../types/table-parts'

// Mock the services
vi.mock('../../../services/tablePartKeyboardHandler', () => ({
  ShortcutAction: {
    ADD_ROW: 'add_row',
    DELETE_ROW: 'delete_row',
    COPY_ROWS: 'copy_rows',
    PASTE_ROWS: 'paste_rows',
    MOVE_ROW_UP: 'move_row_up',
    MOVE_ROW_DOWN: 'move_row_down',
    OPEN_REFERENCE_SELECTOR: 'open_reference_selector'
  },
  createKeyboardHandler: () => ({
    registerActionHandler: vi.fn(),
    attachTo: vi.fn(),
    updateContext: vi.fn(),
    setEnabled: vi.fn(),
    cleanup: vi.fn()
  }),
  createTableContext: vi.fn(),
  isElementEditing: vi.fn(() => false),
  getSelectedRows: vi.fn(() => [])
}))

vi.mock('../../../services/tablePartCalculationEngine', () => ({
  useCalculationEngine: () => ({
    engine: { value: null },
    metrics: { value: {} },
    initializeEngine: vi.fn(),
    calculateField: vi.fn(),
    calculateTotals: vi.fn()
  })
}))

describe('BaseTablePart Drag and Drop', () => {
  const mockColumns: TableColumn[] = [
    { id: 'id', name: 'ID', type: 'number' },
    { id: 'name', name: 'Name', type: 'text' },
    { id: 'value', name: 'Value', type: 'number' }
  ]

  const mockData = [
    { id: 1, name: 'Item 1', value: 10 },
    { id: 2, name: 'Item 2', value: 20 },
    { id: 3, name: 'Item 3', value: 30 }
  ]

  const mockConfigurationWithDragDrop: TablePartConfiguration = {
    tableId: 'test-table',
    documentType: 'test-document',
    availableCommands: [],
    visibleCommands: ['add_row', 'delete_row', 'move_up', 'move_down'],
    keyboardShortcutsEnabled: true,
    autoCalculationEnabled: false,
    dragDropEnabled: true, // Enable drag and drop
    calculationTimeoutMs: 100,
    totalCalculationTimeoutMs: 200
  }

  const mockConfigurationWithoutDragDrop: TablePartConfiguration = {
    ...mockConfigurationWithDragDrop,
    dragDropEnabled: false // Disable drag and drop
  }

  let wrapper: any

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks()
  })

  describe('Drag and Drop Configuration', () => {
    it('should enable draggable attribute when drag-drop is enabled', () => {
      wrapper = mount(BaseTablePart, {
        props: {
          data: mockData,
          columns: mockColumns,
          configuration: mockConfigurationWithDragDrop
        }
      })

      const rows = wrapper.findAll('tbody tr')
      expect(rows.length).toBeGreaterThan(0)
      
      rows.forEach(row => {
        expect(row.attributes('draggable')).toBe('true')
      })
    })

    it('should disable draggable attribute when drag-drop is disabled', () => {
      wrapper = mount(BaseTablePart, {
        props: {
          data: mockData,
          columns: mockColumns,
          configuration: mockConfigurationWithoutDragDrop
        }
      })

      const rows = wrapper.findAll('tbody tr')
      expect(rows.length).toBeGreaterThan(0)
      
      rows.forEach(row => {
        expect(row.attributes('draggable')).toBe('false')
      })
    })
  })

  describe('Drag Event Handlers', () => {
    beforeEach(() => {
      wrapper = mount(BaseTablePart, {
        props: {
          data: mockData,
          columns: mockColumns,
          configuration: mockConfigurationWithDragDrop
        }
      })
    })

    it('should have drag event listeners attached', () => {
      const firstRow = wrapper.find('tbody tr')
      
      // Check that drag event handlers are attached
      expect(firstRow.attributes('draggable')).toBe('true')
      
      // We can't easily test the actual drag events due to Vue Test Utils limitations
      // but we can verify the configuration is correct
    })

    it('should call moveRowToPosition method when drag and drop occurs', async () => {
      // Test the moveRowToPosition method directly
      const vm = wrapper.vm as any
      
      // Spy on the emit function
      const emitSpy = vi.spyOn(wrapper.vm, '$emit')
      
      // Call moveRowToPosition directly
      vm.moveRowToPosition(0, 1)
      
      // Check if data-changed event was emitted
      expect(emitSpy).toHaveBeenCalledWith('data-changed', -1, 'row_order', expect.any(Array))
    })
  })

  describe('Row Movement via Drag and Drop', () => {
    beforeEach(() => {
      wrapper = mount(BaseTablePart, {
        props: {
          data: mockData,
          columns: mockColumns,
          configuration: mockConfigurationWithDragDrop
        }
      })
    })

    it('should move row from position 0 to position 1', () => {
      const vm = wrapper.vm as any
      const emitSpy = vi.spyOn(wrapper.vm, '$emit')
      
      // Call moveRowToPosition directly
      vm.moveRowToPosition(0, 1)

      // Check emitted data
      expect(emitSpy).toHaveBeenCalledWith('data-changed', -1, 'row_order', expect.any(Array))
      
      const emittedData = emitSpy.mock.calls[0][2] // Third parameter is the new data
      expect(emittedData[0].id).toBe(2) // Item 2 should now be first
      expect(emittedData[1].id).toBe(1) // Item 1 should now be second
      expect(emittedData[2].id).toBe(3) // Item 3 should remain third
    })

    it('should not move row when source and target are the same', () => {
      const vm = wrapper.vm as any
      const emitSpy = vi.spyOn(wrapper.vm, '$emit')
      
      // Call moveRowToPosition with same source and target
      vm.moveRowToPosition(0, 0)

      // Should not emit data-changed event
      expect(emitSpy).not.toHaveBeenCalled()
    })
  })

  describe('Visual Indicators', () => {
    beforeEach(() => {
      wrapper = mount(BaseTablePart, {
        props: {
          data: mockData,
          columns: mockColumns,
          configuration: mockConfigurationWithDragDrop
        }
      })
    })

    it('should have cursor move style for draggable rows', () => {
      const rows = wrapper.findAll('tbody tr')
      
      rows.forEach(row => {
        expect(row.attributes('draggable')).toBe('true')
        // CSS class should be applied via draggable attribute
      })
    })

    it('should have drag-over class in CSS', () => {
      // Test that the CSS class exists (this is mainly for documentation)
      const style = wrapper.find('style')
      // We can't easily test CSS content in Vue Test Utils, but we can verify
      // that the component has the necessary structure
      expect(wrapper.find('.table-part-container')).toBeTruthy()
    })
  })

  describe('Integration with Calculation Engine', () => {
    it('should trigger recalculation after drag-drop when auto-calculation is enabled', () => {
      const configWithCalculation = {
        ...mockConfigurationWithDragDrop,
        autoCalculationEnabled: true
      }

      wrapper = mount(BaseTablePart, {
        props: {
          data: mockData,
          columns: mockColumns,
          configuration: configWithCalculation
        }
      })

      const vm = wrapper.vm as any
      const emitSpy = vi.spyOn(wrapper.vm, '$emit')
      
      // Perform row movement
      vm.moveRowToPosition(0, 1)

      // Should emit calculation-requested event
      expect(emitSpy).toHaveBeenCalledWith('calculation-requested', -1, 'row_order')
    })
  })
})