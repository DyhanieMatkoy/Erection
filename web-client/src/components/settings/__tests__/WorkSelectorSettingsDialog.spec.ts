import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkSelectorSettingsDialog from '../WorkSelectorSettingsDialog.vue'
import { useWorkSelectorSettings } from '@/composables/useWorkSelectorSettings'

// Mock the composable
vi.mock('@/composables/useWorkSelectorSettings', () => ({
  useWorkSelectorSettings: vi.fn()
}))

// Mock Modal component
vi.mock('@/components/common/Modal.vue', () => ({
  default: {
    name: 'Modal',
    template: '<div><slot /></div>',
    props: ['isOpen'],
    emits: ['close']
  }
}))

describe('WorkSelectorSettingsDialog', () => {
  const mockComposable = {
    loading: { value: false },
    error: { value: null },
    isModalMode: { value: true },
    hierarchyMode: { value: 'tree' },
    showHierarchyControls: { value: true },
    autoExpandGroups: { value: true },
    loadSettings: vi.fn(),
    saveSettings: vi.fn(),
    setHierarchyMode: vi.fn(),
    toggleHierarchyControls: vi.fn(),
    toggleAutoExpandGroups: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useWorkSelectorSettings).mockReturnValue(mockComposable)
  })

  it('should render correctly when open', () => {
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    expect(wrapper.find('h3').text()).toBe('Настройки селектора работ')
    expect(wrapper.find('input[type="radio"][checked]').exists()).toBe(true)
  })

  it('should load settings on mount', () => {
    mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    expect(mockComposable.loadSettings).toHaveBeenCalled()
  })

  it('should handle modal mode change', async () => {
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    // Find the "В окне" radio button and click it
    const windowModeRadio = wrapper.find('input[type="radio"]:not([checked])')
    await windowModeRadio.trigger('change')

    expect(mockComposable.saveSettings).toHaveBeenCalledWith({ open_modal: false })
  })

  it('should handle hierarchy mode change', async () => {
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    // Find flat mode radio button
    const flatModeRadio = wrapper.findAll('input[type="radio"]').find(radio => 
      radio.element.nextElementSibling?.textContent?.includes('Плоский список')
    )
    
    if (flatModeRadio) {
      await flatModeRadio.trigger('change')
      expect(mockComposable.setHierarchyMode).toHaveBeenCalledWith('flat')
    }
  })

  it('should handle hierarchy controls toggle', async () => {
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    // Find the hierarchy controls checkbox
    const hierarchyControlsCheckbox = wrapper.find('input[type="checkbox"]')
    await hierarchyControlsCheckbox.trigger('change')

    expect(mockComposable.toggleHierarchyControls).toHaveBeenCalled()
  })

  it('should handle auto expand toggle', async () => {
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    // Find the auto expand checkbox (second checkbox)
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    if (checkboxes.length > 1) {
      await checkboxes[1].trigger('change')
      expect(mockComposable.toggleAutoExpandGroups).toHaveBeenCalled()
    }
  })

  it('should emit close event when close button is clicked', async () => {
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    const closeButton = wrapper.find('button:last-child')
    await closeButton.trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('should disable controls when loading', () => {
    mockComposable.loading.value = true
    
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    const radioButtons = wrapper.findAll('input[type="radio"]')
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    const closeButton = wrapper.find('button:last-child')

    radioButtons.forEach(radio => {
      expect(radio.attributes('disabled')).toBeDefined()
    })

    checkboxes.forEach(checkbox => {
      expect(checkbox.attributes('disabled')).toBeDefined()
    })

    expect(closeButton.attributes('disabled')).toBeDefined()
  })

  it('should display error message when error occurs', () => {
    mockComposable.error.value = 'Test error message'
    
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    const errorDiv = wrapper.find('.text-red-600')
    expect(errorDiv.exists()).toBe(true)
    expect(errorDiv.text()).toBe('Test error message')
  })

  it('should reflect current settings in UI', () => {
    // Set specific settings
    mockComposable.isModalMode.value = false
    mockComposable.hierarchyMode.value = 'flat'
    mockComposable.showHierarchyControls.value = false
    mockComposable.autoExpandGroups.value = false
    
    const wrapper = mount(WorkSelectorSettingsDialog, {
      props: {
        isOpen: true
      }
    })

    // Check that the "В окне" radio is selected (not modal)
    const radioButtons = wrapper.findAll('input[type="radio"]')
    const windowModeRadio = radioButtons.find(radio => 
      radio.element.nextElementSibling?.textContent?.includes('В окне')
    )
    expect(windowModeRadio?.element.checked).toBe(true)

    // Check that flat hierarchy mode is selected
    const flatModeRadio = radioButtons.find(radio => 
      radio.element.nextElementSibling?.textContent?.includes('Плоский список')
    )
    expect(flatModeRadio?.element.checked).toBe(true)
  })
})