import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWorkSelectorSettings } from '../useWorkSelectorSettings'
import { useAuth } from '../useAuth'

// Mock the auth composable
vi.mock('../useAuth', () => ({
  useAuth: vi.fn()
}))

// Mock the settings service
vi.mock('@/services/workSelectorSettingsService', () => ({
  workSelectorSettingsService: {
    getUserSettings: vi.fn(),
    saveUserSettings: vi.fn()
  }
}))

describe('useWorkSelectorSettings', () => {
  const mockUser = { id: 1, username: 'testuser' }
  
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock useAuth to return a test user
    vi.mocked(useAuth).mockReturnValue({
      user: { value: mockUser },
      isAuthenticated: { value: true },
      login: vi.fn(),
      logout: vi.fn(),
      isAdmin: { value: false },
      canModifyHierarchy: { value: true },
      canCreateGeneralEstimate: { value: true },
      canCreatePlanEstimate: { value: true }
    } as any)
  })

  it('should initialize with default settings', () => {
    const { settings, isModalMode, hierarchyMode, showHierarchyControls, autoExpandGroups } = useWorkSelectorSettings()

    expect(settings.value).toEqual({
      open_modal: true,
      default_hierarchy_mode: 'tree',
      show_hierarchy_controls: true,
      auto_expand_groups: true
    })

    expect(isModalMode.value).toBe(true)
    expect(hierarchyMode.value).toBe('tree')
    expect(showHierarchyControls.value).toBe(true)
    expect(autoExpandGroups.value).toBe(true)
  })

  it('should load settings from service', async () => {
    const { workSelectorSettingsService } = await import('@/services/workSelectorSettingsService')
    const mockSettings = {
      open_modal: false,
      default_hierarchy_mode: 'flat' as const,
      show_hierarchy_controls: false,
      auto_expand_groups: false
    }

    vi.mocked(workSelectorSettingsService.getUserSettings).mockResolvedValue(mockSettings)

    const { loadSettings, settings } = useWorkSelectorSettings()
    await loadSettings()

    expect(workSelectorSettingsService.getUserSettings).toHaveBeenCalledWith(1)
    expect(settings.value).toEqual(mockSettings)
  })

  it('should save settings to service', async () => {
    const { workSelectorSettingsService } = await import('@/services/workSelectorSettingsService')
    vi.mocked(workSelectorSettingsService.saveUserSettings).mockResolvedValue(true)

    const { saveSettings } = useWorkSelectorSettings()
    const newSettings = { open_modal: false }
    
    const result = await saveSettings(newSettings)

    expect(result).toBe(true)
    expect(workSelectorSettingsService.saveUserSettings).toHaveBeenCalledWith(
      1,
      expect.objectContaining(newSettings)
    )
  })

  it('should toggle modal mode', async () => {
    const { workSelectorSettingsService } = await import('@/services/workSelectorSettingsService')
    vi.mocked(workSelectorSettingsService.saveUserSettings).mockResolvedValue(true)

    const { toggleModalMode, settings } = useWorkSelectorSettings()
    
    // Initial state is modal mode = true
    expect(settings.value.open_modal).toBe(true)
    
    const result = await toggleModalMode()
    
    expect(result).toBe(true)
    expect(workSelectorSettingsService.saveUserSettings).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ open_modal: false })
    )
    
    // After successful save, settings should be updated
    expect(settings.value.open_modal).toBe(false)
  })

  it('should set hierarchy mode', async () => {
    const { workSelectorSettingsService } = await import('@/services/workSelectorSettingsService')
    vi.mocked(workSelectorSettingsService.saveUserSettings).mockResolvedValue(true)

    const { setHierarchyMode } = useWorkSelectorSettings()
    
    await setHierarchyMode('breadcrumb')
    
    expect(workSelectorSettingsService.saveUserSettings).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ default_hierarchy_mode: 'breadcrumb' })
    )
  })

  it('should handle service errors gracefully', async () => {
    const { workSelectorSettingsService } = await import('@/services/workSelectorSettingsService')
    vi.mocked(workSelectorSettingsService.getUserSettings).mockRejectedValue(new Error('Service error'))

    const { loadSettings, error } = useWorkSelectorSettings()
    await loadSettings()

    expect(error.value).toBe('Service error')
  })

  it('should not make API calls when user is not authenticated', async () => {
    // Mock no user
    vi.mocked(useAuth).mockReturnValue({
      user: { value: null },
      isAuthenticated: { value: false }
    } as any)

    const { workSelectorSettingsService } = await import('@/services/workSelectorSettingsService')
    const { loadSettings, saveSettings } = useWorkSelectorSettings()

    await loadSettings()
    const result = await saveSettings({ open_modal: false })

    expect(workSelectorSettingsService.getUserSettings).not.toHaveBeenCalled()
    expect(workSelectorSettingsService.saveUserSettings).not.toHaveBeenCalled()
    expect(result).toBe(false)
  })
})