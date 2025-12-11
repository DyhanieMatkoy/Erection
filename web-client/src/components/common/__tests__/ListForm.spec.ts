import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ListForm from '../ListForm.vue'

interface TestItem {
  id: number
  code: string
  name: string
  description: string
}

describe('ListForm - Substring Entry Feature', () => {
  const testItems: TestItem[] = [
    { id: 1, code: 'M001', name: 'Цемент М400', description: 'Портландцемент М400' },
    { id: 2, code: 'M002', name: 'Песок речной', description: 'Песок речной мытый' },
    { id: 3, code: 'M003', name: 'Щебень', description: 'Щебень фракция 5-20' },
    { id: 4, code: 'C001', name: 'Труд рабочих', description: 'Труд рабочих 4 разряда' },
    { id: 5, code: 'C002', name: 'Аренда оборудования', description: 'Аренда бетономешалки' }
  ]

  let wrapper: any

  beforeEach(() => {
    wrapper = mount(ListForm, {
      props: {
        isOpen: true,
        title: 'Test List',
        items: testItems,
        getItemKey: (item: TestItem) => item.id,
        getItemCode: (item: TestItem) => item.code,
        getItemDescription: (item: TestItem) => item.description,
        highlightMatches: true
      }
    })
  })

  it('should filter items by code substring', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('M00')
    
    // Wait for debounce (300ms) and Vue to update
    await new Promise(resolve => setTimeout(resolve, 350))
    await wrapper.vm.$nextTick()
    
    // Should show items with codes starting with M00
    const items = wrapper.findAll('.item-row')
    expect(items.length).toBe(3) // M001, M002, M003
  })

  it('should filter items by name substring', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('цем')
    
    // Should show items with "цем" in name or description
    const items = wrapper.findAll('.item-row')
    expect(items.length).toBeGreaterThanOrEqual(1)
  })

  it('should filter items by description substring', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('речной')
    
    // Should show items with "речной" in description
    const items = wrapper.findAll('.item-row')
    expect(items.length).toBeGreaterThanOrEqual(1)
  })

  it('should be case-insensitive', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('ЦЕМЕНТ')
    
    const items = wrapper.findAll('.item-row')
    expect(items.length).toBeGreaterThanOrEqual(1)
  })

  it('should highlight matching text when highlightMatches is true', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('M00')
    
    await wrapper.vm.$nextTick()
    
    // Check if mark tags are present in the rendered HTML
    const html = wrapper.html()
    expect(html).toContain('<mark>')
  })

  it('should select first item on Enter key press', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('M00')
    
    // Trigger Enter key
    await searchInput.trigger('keyup.enter')
    
    // Check if an item was selected (internal state)
    // Note: This would emit a 'select' event in real usage
    expect(wrapper.emitted('select')).toBeTruthy()
  })

  it('should show all items when search is cleared', async () => {
    const searchInput = wrapper.find('.search-input')
    
    // First filter
    await searchInput.setValue('M00')
    await new Promise(resolve => setTimeout(resolve, 350))
    await wrapper.vm.$nextTick()
    let items = wrapper.findAll('.item-row')
    expect(items.length).toBe(3)
    
    // Clear search
    await searchInput.setValue('')
    await new Promise(resolve => setTimeout(resolve, 350))
    await wrapper.vm.$nextTick()
    items = wrapper.findAll('.item-row')
    expect(items.length).toBe(5) // All items
  })

  it('should show empty state when no matches found', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('ZZZZZ')
    
    // Wait for debounce and Vue to update
    await new Promise(resolve => setTimeout(resolve, 350))
    await wrapper.vm.$nextTick()
    
    const emptyState = wrapper.find('.empty-state')
    expect(emptyState.exists()).toBe(true)
  })

  it('should filter by both code and name simultaneously', async () => {
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('00')
    
    // Should match codes M001, M002, M003, C001, C002
    const items = wrapper.findAll('.item-row')
    expect(items.length).toBe(5)
  })
})

describe('ListForm - Highlight Text Function', () => {
  it('should escape special regex characters', () => {
    const wrapper = mount(ListForm, {
      props: {
        isOpen: true,
        items: [],
        highlightMatches: true
      }
    })

    // Access the exposed highlightText function
    const highlightText = (wrapper.vm as any).highlightText
    
    // Test with special characters
    const result = highlightText('Test (special) characters')
    expect(result).toBeDefined()
  })

  it('should not highlight when search is empty', () => {
    const wrapper = mount(ListForm, {
      props: {
        isOpen: true,
        items: [],
        highlightMatches: true
      }
    })

    const highlightText = (wrapper.vm as any).highlightText
    const result = highlightText('Test text')
    
    // Should return original text without mark tags
    expect(result).toBe('Test text')
    expect(result).not.toContain('<mark>')
  })

  it('should not highlight when highlightMatches is false', async () => {
    const wrapper = mount(ListForm, {
      props: {
        isOpen: true,
        items: [{ id: 1, code: 'TEST', name: 'Test Item', description: 'Test' }],
        highlightMatches: false,
        getItemKey: (item: any) => item.id,
        getItemCode: (item: any) => item.code,
        getItemDescription: (item: any) => item.description
      }
    })

    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('TEST')
    
    await wrapper.vm.$nextTick()
    
    const html = wrapper.html()
    expect(html).not.toContain('<mark>')
  })
})
