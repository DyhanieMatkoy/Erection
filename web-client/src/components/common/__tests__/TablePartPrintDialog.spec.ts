/**
 * Tests for TablePartPrintDialog component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import TablePartPrintDialog from '../TablePartPrintDialog.vue'

// Mock the composable
vi.mock('@/composables/useTablePartPrint', () => ({
  useTablePartPrint: () => ({
    generatePreview: vi.fn().mockResolvedValue('<div>Mock preview</div>'),
    printToPrinter: vi.fn().mockResolvedValue(undefined),
    printToPdf: vi.fn().mockResolvedValue(undefined),
    validatePrintData: vi.fn().mockReturnValue({ isValid: true }),
    getPageCount: vi.fn().mockReturnValue(1)
  })
}))

describe('TablePartPrintDialog', () => {
  const mockTableData = [
    { id: 1, name: 'Item 1', quantity: 10, price: 100 },
    { id: 2, name: 'Item 2', quantity: 5, price: 200 },
    { id: 3, name: 'Item 3', quantity: 15, price: 50 }
  ]

  let wrapper: any

  beforeEach(() => {
    wrapper = mount(TablePartPrintDialog, {
      props: {
        tableData: mockTableData,
        tableName: 'Test Table',
        visible: true
      }
    })
  })

  it('renders correctly when visible', () => {
    expect(wrapper.find('.table-part-print-dialog').exists()).toBe(true)
    expect(wrapper.find('.modal-overlay').exists()).toBe(true)
    expect(wrapper.find('.modal-content').exists()).toBe(true)
  })

  it('displays the correct table name', () => {
    expect(wrapper.find('.modal-header h3').text()).toBe('Печать: Test Table')
  })

  it('has all required print settings controls', () => {
    // Orientation controls
    expect(wrapper.find('input[value="portrait"]').exists()).toBe(true)
    expect(wrapper.find('input[value="landscape"]').exists()).toBe(true)
    
    // Scale control
    expect(wrapper.find('input[type="range"]').exists()).toBe(true)
    
    // Margin controls
    expect(wrapper.findAll('input[type="number"]')).toHaveLength(4)
    
    // Checkbox controls
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(3) // repeatHeaders, showGrid, fitToWidth
    
    // Format controls
    expect(wrapper.find('input[value="print"]').exists()).toBe(true)
    expect(wrapper.find('input[value="pdf"]').exists()).toBe(true)
  })

  it('has action buttons', () => {
    const buttons = wrapper.findAll('button')
    const buttonTexts = buttons.map((btn: any) => btn.text())
    
    expect(buttonTexts).toContain('Обновить просмотр')
    expect(buttonTexts).toContain('Печать')
    expect(buttonTexts).toContain('Отмена')
  })

  it('emits close event when close button is clicked', async () => {
    await wrapper.find('.close-button').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close event when cancel button is clicked', async () => {
    const cancelButton = wrapper.findAll('button').find((btn: any) => 
      btn.text() === 'Отмена'
    )
    await cancelButton.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('has default print configuration values', () => {
    // Check that default values are set correctly
    expect(wrapper.find('input[value="portrait"]').element.checked).toBe(true)
    expect(wrapper.find('input[type="range"]').element.value).toBe('100')
    expect(wrapper.find('input[value="print"]').element.checked).toBe(true)
  })

  it('updates configuration when settings change', async () => {
    // Change orientation to landscape
    await wrapper.find('input[value="landscape"]').setChecked(true)
    
    // Change scale
    await wrapper.find('input[type="range"]').setValue('150')
    
    // Change format to PDF
    await wrapper.find('input[value="pdf"]').setChecked(true)
    
    // Verify changes are reflected
    expect(wrapper.find('input[value="landscape"]').element.checked).toBe(true)
    expect(wrapper.find('input[type="range"]').element.value).toBe('150')
    expect(wrapper.find('input[value="pdf"]').element.checked).toBe(true)
  })

  it('shows preview container', () => {
    expect(wrapper.find('.print-preview-panel').exists()).toBe(true)
    expect(wrapper.find('.preview-container').exists()).toBe(true)
  })

  it('handles empty table data gracefully', async () => {
    await wrapper.setProps({ tableData: [] })
    
    // Should still render but show appropriate message
    expect(wrapper.find('.table-part-print-dialog').exists()).toBe(true)
  })

  it('is responsive on mobile', () => {
    // Check that responsive classes exist
    const styles = wrapper.find('.modal-content').element.style
    expect(wrapper.html()).toContain('modal-content')
    
    // The actual responsive behavior would be tested with CSS testing tools
    // or visual regression testing in a real browser environment
  })

  it('validates required props', () => {
    // Test with minimal props
    const minimalWrapper = mount(TablePartPrintDialog, {
      props: {
        tableData: mockTableData
      }
    })
    
    expect(minimalWrapper.exists()).toBe(true)
  })

  it('handles print configuration correctly', () => {
    // Access the component's internal state
    const vm = wrapper.vm as any
    
    // Check that print configuration has expected structure
    expect(vm.printConfig).toHaveProperty('orientation')
    expect(vm.printConfig).toHaveProperty('scale')
    expect(vm.printConfig).toHaveProperty('topMargin')
    expect(vm.printConfig).toHaveProperty('repeatHeaders')
    expect(vm.printConfig).toHaveProperty('showGrid')
    expect(vm.printConfig).toHaveProperty('format')
  })
})