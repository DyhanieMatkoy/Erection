/**
 * Composable for managing work selector settings
 */

import { ref, computed } from 'vue'
import { workSelectorSettingsService, type WorkSelectorSettings } from '@/services/workSelectorSettingsService'
import { useAuth } from './useAuth'

export function useWorkSelectorSettings() {
  const { user } = useAuth()

  const settings = ref<WorkSelectorSettings>({
    open_modal: true,
    default_hierarchy_mode: 'tree',
    show_hierarchy_controls: true,
    auto_expand_groups: true
  })

  const loading = ref(false)
  const error = ref<string | null>(null)

  const isModalMode = computed(() => settings.value.open_modal)
  const hierarchyMode = computed(() => settings.value.default_hierarchy_mode)
  const showHierarchyControls = computed(() => settings.value.show_hierarchy_controls)
  const autoExpandGroups = computed(() => settings.value.auto_expand_groups)

  /**
   * Load settings from server
   */
  async function loadSettings() {
    if (!user.value?.id) return

    loading.value = true
    error.value = null

    try {
      const userSettings = await workSelectorSettingsService.getUserSettings(user.value.id)
      settings.value = userSettings
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load settings'
      console.error('Error loading work selector settings:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Save settings to server
   */
  async function saveSettings(newSettings: Partial<WorkSelectorSettings>) {
    if (!user.value?.id) return false

    loading.value = true
    error.value = null

    try {
      const updatedSettings = { ...settings.value, ...newSettings }
      const success = await workSelectorSettingsService.saveUserSettings(
        user.value.id,
        updatedSettings
      )

      if (success) {
        settings.value = updatedSettings
        return true
      } else {
        error.value = 'Failed to save settings'
        return false
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to save settings'
      console.error('Error saving work selector settings:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Toggle modal mode
   */
  async function toggleModalMode() {
    return await saveSettings({ open_modal: !settings.value.open_modal })
  }

  /**
   * Set hierarchy mode
   */
  async function setHierarchyMode(mode: 'flat' | 'tree' | 'breadcrumb') {
    return await saveSettings({ default_hierarchy_mode: mode })
  }

  /**
   * Toggle hierarchy controls visibility
   */
  async function toggleHierarchyControls() {
    return await saveSettings({ show_hierarchy_controls: !settings.value.show_hierarchy_controls })
  }

  /**
   * Toggle auto expand groups
   */
  async function toggleAutoExpandGroups() {
    return await saveSettings({ auto_expand_groups: !settings.value.auto_expand_groups })
  }

  return {
    // State
    settings: computed(() => settings.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),

    // Computed properties
    isModalMode,
    hierarchyMode,
    showHierarchyControls,
    autoExpandGroups,

    // Methods
    loadSettings,
    saveSettings,
    toggleModalMode,
    setHierarchyMode,
    toggleHierarchyControls,
    toggleAutoExpandGroups
  }
}