/**
 * Table Part Settings Service for Web Client
 * 
 * Manages user settings for table parts including panel configuration,
 * keyboard shortcuts, column settings, and persistence.
 */

import type { 
  TablePartSettingsData, 
  PanelSettings, 
  ShortcutSettings,
  TablePartConfiguration 
} from '../types/table-parts'

export interface UserTablePartSettings {
  id?: string
  userId: number
  documentType: string
  tablePartId: string
  settingsData: TablePartSettingsData
  createdAt?: string
  updatedAt?: string
}

export interface SettingsExportData {
  exportVersion: string
  exportDate: string
  userId: number
  settings: UserTablePartSettings[]
}

export interface SettingsMigrationResult {
  success: boolean
  migratedCount: number
  skippedCount: number
  errorCount: number
  errors: string[]
}

export interface SettingsValidationResult {
  isValid: boolean
  errors: string[]
}

const CURRENT_SETTINGS_VERSION = '1.0'
const SETTINGS_STORAGE_KEY = 'table_part_settings'

export class TablePartSettingsService {
  private baseUrl: string
  private userId: number | null = null

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl
  }

  setUserId(userId: number) {
    this.userId = userId
  }

  /**
   * Get user settings for a specific table part
   */
  async getUserSettings(
    userId: number,
    documentType: string,
    tablePartId: string
  ): Promise<TablePartSettingsData | null> {
    try {
      const response = await fetch(
        `${this.baseUrl}/table-part-settings/${userId}/${documentType}/${tablePartId}`
      )

      if (response.status === 404) {
        return null // No settings found
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Migrate settings if needed
      const migrated = this.migrateSettingsIfNeeded(data.settingsData)
      
      return migrated
    } catch (error) {
      console.error('Error loading user settings:', error)
      
      // Fallback to local storage
      return this.getLocalSettings(documentType, tablePartId)
    }
  }

  /**
   * Save user settings for a table part
   */
  async saveUserSettings(
    userId: number,
    documentType: string,
    tablePartId: string,
    settings: TablePartSettingsData
  ): Promise<boolean> {
    try {
      // Add version information
      const settingsWithVersion = {
        ...settings,
        version: CURRENT_SETTINGS_VERSION,
        updatedAt: new Date().toISOString()
      }

      const response = await fetch(
        `${this.baseUrl}/table-part-settings/${userId}/${documentType}/${tablePartId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ settingsData: settingsWithVersion })
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Also save to local storage as backup
      this.saveLocalSettings(documentType, tablePartId, settingsWithVersion)

      return true
    } catch (error) {
      console.error('Error saving user settings:', error)
      
      // Fallback to local storage
      this.saveLocalSettings(documentType, tablePartId, settings)
      return false
    }
  }

  /**
   * Get default settings for a table part
   */
  getDefaultSettings(documentType: string, tablePartId: string): TablePartSettingsData {
    const defaultVisibleCommands = this.getDefaultVisibleCommands(documentType, tablePartId)

    return {
      columnWidths: {},
      columnOrder: [],
      hiddenColumns: [],
      panelSettings: {
        visibleCommands: defaultVisibleCommands,
        hiddenCommands: [],
        buttonSize: 'medium',
        showTooltips: true,
        compactMode: false
      },
      shortcuts: {
        enabled: true,
        customMappings: {}
      },
      sortColumn: null,
      sortDirection: 'asc'
    }
  }

  /**
   * Reset user settings to defaults
   */
  async resetUserSettings(
    userId: number,
    documentType: string,
    tablePartId: string
  ): Promise<boolean> {
    try {
      const response = await fetch(
        `${this.baseUrl}/table-part-settings/${userId}/${documentType}/${tablePartId}`,
        {
          method: 'DELETE'
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Also remove from local storage
      this.removeLocalSettings(documentType, tablePartId)

      return true
    } catch (error) {
      console.error('Error resetting user settings:', error)
      
      // Fallback to local storage
      this.removeLocalSettings(documentType, tablePartId)
      return false
    }
  }

  /**
   * Get all user settings
   */
  async getAllUserSettings(userId: number): Promise<UserTablePartSettings[]> {
    try {
      const response = await fetch(`${this.baseUrl}/table-part-settings/${userId}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data.settings || []
    } catch (error) {
      console.error('Error loading all user settings:', error)
      return []
    }
  }

  /**
   * Export user settings
   */
  async exportUserSettings(
    userId: number,
    documentType?: string,
    tablePartId?: string
  ): Promise<SettingsExportData> {
    try {
      let url = `${this.baseUrl}/table-part-settings/${userId}/export`
      const params = new URLSearchParams()
      
      if (documentType) params.append('documentType', documentType)
      if (tablePartId) params.append('tablePartId', tablePartId)
      
      if (params.toString()) {
        url += `?${params.toString()}`
      }

      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error exporting user settings:', error)
      throw error
    }
  }

  /**
   * Import user settings
   */
  async importUserSettings(
    userId: number,
    importData: SettingsExportData,
    overwriteExisting: boolean = false
  ): Promise<SettingsMigrationResult> {
    try {
      const response = await fetch(`${this.baseUrl}/table-part-settings/${userId}/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          importData,
          overwriteExisting
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error importing user settings:', error)
      return {
        success: false,
        migratedCount: 0,
        skippedCount: 0,
        errorCount: 1,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      }
    }
  }

  /**
   * Validate settings data
   */
  validateSettingsData(settings: TablePartSettingsData): SettingsValidationResult {
    const errors: string[] = []

    // Validate required top-level properties
    if (!settings.panelSettings) {
      errors.push('Missing panelSettings')
    }

    if (!settings.shortcuts) {
      errors.push('Missing shortcuts')
    }

    // Validate panel settings
    if (settings.panelSettings) {
      if (!Array.isArray(settings.panelSettings.visibleCommands)) {
        errors.push('panelSettings.visibleCommands must be an array')
      }

      if (settings.panelSettings.buttonSize && 
          !['small', 'medium', 'large'].includes(settings.panelSettings.buttonSize)) {
        errors.push('panelSettings.buttonSize must be small, medium, or large')
      }

      if (typeof settings.panelSettings.showTooltips !== 'boolean') {
        errors.push('panelSettings.showTooltips must be a boolean')
      }
    }

    // Validate shortcuts
    if (settings.shortcuts) {
      if (typeof settings.shortcuts.enabled !== 'boolean') {
        errors.push('shortcuts.enabled must be a boolean')
      }

      if (settings.shortcuts.customMappings && 
          typeof settings.shortcuts.customMappings !== 'object') {
        errors.push('shortcuts.customMappings must be an object')
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    }
  }

  /**
   * Migrate settings to current version if needed
   */
  private migrateSettingsIfNeeded(settings: any): TablePartSettingsData {
    const currentVersion = settings.version || '0.9'

    if (currentVersion === CURRENT_SETTINGS_VERSION) {
      return settings
    }

    // Apply migrations
    let migrated = { ...settings }

    if (currentVersion === '0.9') {
      migrated = this.migrate_0_9_to_1_0(migrated)
    }

    // Add version and migration timestamp
    migrated.version = CURRENT_SETTINGS_VERSION
    migrated.migratedAt = new Date().toISOString()

    return migrated
  }

  /**
   * Migrate from version 0.9 to 1.0
   */
  private migrate_0_9_to_1_0(settings: any): TablePartSettingsData {
    const migrated: any = { ...settings }

    // Ensure panel settings structure
    if (!migrated.panelSettings) {
      migrated.panelSettings = {}
    }

    const panelSettings = migrated.panelSettings

    // Add missing panel settings with defaults
    if (!panelSettings.visibleCommands) {
      panelSettings.visibleCommands = ['add_row', 'delete_row', 'move_up', 'move_down']
    }

    if (!panelSettings.hiddenCommands) {
      panelSettings.hiddenCommands = []
    }

    if (!panelSettings.buttonSize) {
      panelSettings.buttonSize = 'medium'
    }

    if (panelSettings.showTooltips === undefined) {
      panelSettings.showTooltips = true
    }

    if (panelSettings.compactMode === undefined) {
      panelSettings.compactMode = false
    }

    // Ensure shortcuts structure
    if (!migrated.shortcuts) {
      migrated.shortcuts = {}
    }

    const shortcuts = migrated.shortcuts

    if (shortcuts.enabled === undefined) {
      shortcuts.enabled = true
    }

    if (!shortcuts.customMappings) {
      shortcuts.customMappings = {}
    }

    // Ensure other required fields
    if (!migrated.columnWidths) {
      migrated.columnWidths = {}
    }

    if (!migrated.columnOrder) {
      migrated.columnOrder = []
    }

    if (!migrated.hiddenColumns) {
      migrated.hiddenColumns = []
    }

    if (!migrated.sortColumn) {
      migrated.sortColumn = null
    }

    if (!migrated.sortDirection) {
      migrated.sortDirection = 'asc'
    }

    return migrated as TablePartSettingsData
  }

  /**
   * Get default visible commands based on document type
   */
  private getDefaultVisibleCommands(documentType: string, tablePartId: string): string[] {
    const defaultCommands = ['add_row', 'delete_row', 'move_up', 'move_down']

    // Add document-specific commands
    if (['estimate', 'daily_report'].includes(documentType)) {
      defaultCommands.push('import_data', 'export_data')
    }

    return defaultCommands
  }

  /**
   * Local storage fallback methods
   */
  private getLocalStorageKey(documentType: string, tablePartId: string): string {
    return `${SETTINGS_STORAGE_KEY}_${documentType}_${tablePartId}`
  }

  private getLocalSettings(documentType: string, tablePartId: string): TablePartSettingsData | null {
    try {
      const key = this.getLocalStorageKey(documentType, tablePartId)
      const stored = localStorage.getItem(key)
      
      if (!stored) {
        return null
      }

      const settings = JSON.parse(stored)
      return this.migrateSettingsIfNeeded(settings)
    } catch (error) {
      console.error('Error loading local settings:', error)
      return null
    }
  }

  private saveLocalSettings(
    documentType: string, 
    tablePartId: string, 
    settings: TablePartSettingsData
  ): void {
    try {
      const key = this.getLocalStorageKey(documentType, tablePartId)
      localStorage.setItem(key, JSON.stringify(settings))
    } catch (error) {
      console.error('Error saving local settings:', error)
    }
  }

  private removeLocalSettings(documentType: string, tablePartId: string): void {
    try {
      const key = this.getLocalStorageKey(documentType, tablePartId)
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Error removing local settings:', error)
    }
  }
}

// Create singleton instance
export const tablePartSettingsService = new TablePartSettingsService()

// Composable for Vue components
export function useTablePartSettings() {
  return {
    settingsService: tablePartSettingsService,
    
    async loadSettings(
      userId: number,
      documentType: string,
      tablePartId: string
    ): Promise<TablePartSettingsData> {
      const settings = await tablePartSettingsService.getUserSettings(
        userId,
        documentType,
        tablePartId
      )
      
      return settings || tablePartSettingsService.getDefaultSettings(documentType, tablePartId)
    },

    async saveSettings(
      userId: number,
      documentType: string,
      tablePartId: string,
      settings: TablePartSettingsData
    ): Promise<boolean> {
      return await tablePartSettingsService.saveUserSettings(
        userId,
        documentType,
        tablePartId,
        settings
      )
    },

    async resetSettings(
      userId: number,
      documentType: string,
      tablePartId: string
    ): Promise<boolean> {
      return await tablePartSettingsService.resetUserSettings(
        userId,
        documentType,
        tablePartId
      )
    },

    getDefaultSettings(documentType: string, tablePartId: string): TablePartSettingsData {
      return tablePartSettingsService.getDefaultSettings(documentType, tablePartId)
    },

    validateSettings(settings: TablePartSettingsData): SettingsValidationResult {
      return tablePartSettingsService.validateSettingsData(settings)
    }
  }
}