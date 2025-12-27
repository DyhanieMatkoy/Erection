/**
 * Work Selector Settings Service
 * 
 * Manages user settings for work selector dialog behavior
 */

export interface WorkSelectorSettings {
  open_modal: boolean
  default_hierarchy_mode: 'flat' | 'tree' | 'breadcrumb'
  show_hierarchy_controls: boolean
  auto_expand_groups: boolean
}

export class WorkSelectorSettingsService {
  private baseUrl = '/api/work-selector-settings'

  /**
   * Get work selector settings for a user
   */
  async getUserSettings(userId: number): Promise<WorkSelectorSettings> {
    try {
      const response = await fetch(`${this.baseUrl}/${userId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      return data.settings
    } catch (error) {
      console.error('Error loading work selector settings:', error)
      
      // Return defaults if API fails
      return {
        open_modal: true,
        default_hierarchy_mode: 'tree',
        show_hierarchy_controls: true,
        auto_expand_groups: true
      }
    }
  }

  /**
   * Save work selector settings for a user
   */
  async saveUserSettings(
    userId: number,
    settings: WorkSelectorSettings
  ): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return true
    } catch (error) {
      console.error('Error saving work selector settings:', error)
      return false
    }
  }
}

// Export singleton instance
export const workSelectorSettingsService = new WorkSelectorSettingsService()