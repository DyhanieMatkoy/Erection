/**
 * Test suite for CompactReferenceField component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import CompactReferenceField from '../CompactReferenceField.vue'
import type { ReferenceValue } from '@/types/table-parts'

// Mock the reference selector service
vi.mock('@/services/referenceSelectorService', () => ({
  referenceSelectorService: {
    getAutoComplete: vi.fn(),
    openSelector: vi.fn(),
    openReference: vi.fn(),
    fillRelatedFields: vi.fn()
  }
}))

describe('CompactReferenceField', () => {
  let wrapper: VueWrapper<any>
  
  const defaultProps = {
    referenceType: 'works',
    placeholder: 'Select work',
    allowEdit: true,
    allowCreate: false,
    relatedFields: [],
    autoComplete: true,
    minSearchLength: 3
  }
  
  beforeEach(() => {
    vi.clearAllMocks()
  })
  
  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })
  
  describe('Component Initialization', () => {
    it('renders with default props', () => {
      wrapper = mount(CompactReferenceField, {
        props: defaultProps
      })
      
      expect(wrapper.find('.compact-reference-field').exists()).toBe(true)
      expect(wrapper.find('.reference-input').exists()).toBe(true)
      expect(wrapper.find('.compact-buttons').exists()).toBe(true)
      expect(wrapper.find('.selector-button').exists()).toBe(true)
    })
    
    it('shows open button when has value and allow edit', async () => {
      const testValue: ReferenceValue = {
        id: 1,
        name: 'Test Work',
        code: 'TW001'
      }
      
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          modelValue: testValue,
          allowEdit: true
        }
      })
      
      await nextTick()
      
      expect(wrapper.find('.open-button').exists()).toBe(true)
      expect(wrapper.find('.open-button').text()).toBe('o')
    })
    
    it('hides open button when no value', () => {
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          modelValue: null
        }
      })
      
      expect(wrapper.find('.open-button').exists()).toBe(false)
    })
    
    it('hides open button when edit not allowed', async () => {
      const testValue: ReferenceValue = {
        id: 1,
        name: 'Test Work',
        code: 'TW001'
      }
      
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          modelValue: testValue,
          allowEdit: false
        }
      })
      
      await nextTick()
      
      expect(wrapper.find('.open-button').exists()).toBe(false)
    })
  })
  
  describe('Value Display', () => {
    it('displays reference name when value is set', async () => {
      const testValue: ReferenceValue = {
        id: 123,
        name: 'Test Reference Item',
        code: 'TRI001'
      }
      
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          modelValue: testValue
        }
      })
      
      await nextTick()
      
      const input = wrapper.find('.reference-input')
      expect(input.element.value).toBe('Test Reference Item')
    })
    
    it('shows placeholder when no value', () => {
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          modelValue: null,
          placeholder: 'Select an item'
        }
      })
      
      const input = wrapper.find('.reference-input')
      expect(input.attributes('placeholder')).toBe('Select an item')
      expect(input.element.value).toBe('')
    })
  })
  
  describe('Keyboard Interactions', () => {
    it('opens selector on F4 key', async () => {
      const { referenceSelectorService } = await import('@/services/referenceSelectorService')
      const mockOpenSelector = vi.mocked(referenceSelectorService.openSelector)
      mockOpenSelector.mockResolvedValue({ selected: false, action: 'cancel' })
      
      wrapper = mount(CompactReferenceField, {
        props: defaultProps
      })
      
      const input = wrapper.find('.reference-input')
      await input.trigger('keydown', { key: 'F4' })
      
      expect(mockOpenSelector).toHaveBeenCalledWith({
        referenceType: 'works',
        currentValue: undefined,
        allowCreate: false,
        allowEdit: true
      })
    })
    
    it('opens selector on Enter key', async () => {
      const { referenceSelectorService } = await import('@/services/referenceSelectorService')
      const mockOpenSelector = vi.mocked(referenceSelectorService.openSelector)
      mockOpenSelector.mockResolvedValue({ selected: false, action: 'cancel' })
      
      wrapper = mount(CompactReferenceField, {
        props: defaultProps
      })
      
      const input = wrapper.find('.reference-input')
      await input.trigger('keydown', { key: 'Enter' })
      
      expect(mockOpenSelector).toHaveBeenCalled()
    })
  })
  
  describe('Button Interactions', () => {
    it('calls openReference when open button is clicked', async () => {
      const { referenceSelectorService } = await import('@/services/referenceSelectorService')
      const mockOpenReference = vi.mocked(referenceSelectorService.openReference)
      mockOpenReference.mockResolvedValue(true)
      
      const testValue: ReferenceValue = {
        id: 456,
        name: 'Test Item',
        code: 'TI001'
      }
      
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          modelValue: testValue,
          allowEdit: true
        }
      })
      
      await nextTick()
      
      const openButton = wrapper.find('.open-button')
      await openButton.trigger('click')
      
      expect(mockOpenReference).toHaveBeenCalledWith('works', 456)
    })
    
    it('calls selectReference when selector button is clicked', async () => {
      const { referenceSelectorService } = await import('@/services/referenceSelectorService')
      const mockOpenSelector = vi.mocked(referenceSelectorService.openSelector)
      mockOpenSelector.mockResolvedValue({ selected: false, action: 'cancel' })
      
      wrapper = mount(CompactReferenceField, {
        props: defaultProps
      })
      
      const selectorButton = wrapper.find('.selector-button')
      await selectorButton.trigger('click')
      
      expect(mockOpenSelector).toHaveBeenCalled()
    })
  })
  
  describe('Value Updates', () => {
    it('emits update:modelValue when value changes', async () => {
      const { referenceSelectorService } = await import('@/services/referenceSelectorService')
      const mockOpenSelector = vi.mocked(referenceSelectorService.openSelector)
      
      const newValue: ReferenceValue = {
        id: 789,
        name: 'New Selected Item',
        code: 'NSI001'
      }
      
      mockOpenSelector.mockResolvedValue({
        selected: true,
        value: newValue,
        action: 'select'
      })
      
      wrapper = mount(CompactReferenceField, {
        props: defaultProps
      })
      
      const selectorButton = wrapper.find('.selector-button')
      await selectorButton.trigger('click')
      
      // Wait for async operations
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))
      
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual([newValue])
    })
    
    it('emits fill-related-fields when related fields are configured', async () => {
      const { referenceSelectorService } = await import('@/services/referenceSelectorService')
      const mockOpenSelector = vi.mocked(referenceSelectorService.openSelector)
      const mockFillRelatedFields = vi.mocked(referenceSelectorService.fillRelatedFields)
      
      const newValue: ReferenceValue = {
        id: 999,
        name: 'Item with Related Fields',
        code: 'IWRF001'
      }
      
      mockOpenSelector.mockResolvedValue({
        selected: true,
        value: newValue,
        action: 'select'
      })
      
      mockFillRelatedFields.mockResolvedValue({
        unit_id: 5,
        unit_name: 'м²',
        price: 150.00
      })
      
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          relatedFields: ['unit', 'price']
        }
      })
      
      const selectorButton = wrapper.find('.selector-button')
      await selectorButton.trigger('click')
      
      // Wait for async operations
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))
      
      expect(mockFillRelatedFields).toHaveBeenCalledWith('works', 999, ['unit', 'price'])
      expect(wrapper.emitted('fill-related-fields')).toBeTruthy()
    })
  })
  
  describe('Disabled State', () => {
    it('disables input and buttons when disabled prop is true', () => {
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          disabled: true
        }
      })
      
      const input = wrapper.find('.reference-input')
      const selectorButton = wrapper.find('.selector-button')
      
      expect(input.attributes('disabled')).toBeDefined()
      expect(selectorButton.attributes('disabled')).toBeDefined()
    })
    
    it('adds disabled class when disabled', () => {
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          disabled: true
        }
      })
      
      expect(wrapper.find('.compact-reference-field').classes()).toContain('disabled')
    })
  })
  
  describe('Auto-completion', () => {
    it('shows autocomplete dropdown when items are available', async () => {
      const { referenceSelectorService } = await import('@/services/referenceSelectorService')
      const mockGetAutoComplete = vi.mocked(referenceSelectorService.getAutoComplete)
      
      const autoCompleteItems: ReferenceValue[] = [
        { id: 1, name: 'Auto Item 1', code: 'AI1' },
        { id: 2, name: 'Auto Item 2', code: 'AI2' }
      ]
      
      mockGetAutoComplete.mockResolvedValue(autoCompleteItems)
      
      wrapper = mount(CompactReferenceField, {
        props: {
          ...defaultProps,
          autoComplete: true
        }
      })
      
      // Simulate search (this would normally be triggered by typing)
      const component = wrapper.vm as unknown
      await component.searchAutoComplete('test query')
      
      await nextTick()
      
      expect(wrapper.find('.autocomplete-dropdown').exists()).toBe(true)
      expect(wrapper.findAll('.autocomplete-item')).toHaveLength(2)
    })
  })
  
  describe('Component Methods', () => {
    it('exposes focus method', () => {
      wrapper = mount(CompactReferenceField, {
        props: defaultProps
      })
      
      expect(typeof wrapper.vm.focus).toBe('function')
    })
  })
})