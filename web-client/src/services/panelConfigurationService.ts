/**
 * Panel Configuration Service for Web Client.
 * 
 * This service handles persistence and retrieval of panel configurations,
 * applying settings to all table parts of the same document type, and
 * managing settings migration and defaults.
 * 
 * Requirements: 9.5
 */

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface TablePartCommand {
  id: string
  name: string
  icon: string
  tooltip: string
  shortcut?: string
  enabled: boolean
  visible: boolean
  formMethod?: string
  position: number
  requiresSelection: boolean
}

export interface PanelSettings {
  visibleCommands: string[]
  hiddenCommands: string[]
  buttonSize: 'small' | 'medium' | 'large'
  showTooltips: boolean
  compactMode: boolean
}

export interface TablePartSettingsData {
  columnWidths: Record<string, number>
  columnOrder: string[]
  hiddenColumns: string[]
  panelSettings: PanelSettings
  shortcuts: {
    enabled: boolean
    customMappings: Record<string, string>
  }
  sortColumn?: string
  sortDirection: 'asc' | 'desc'
}

export interface PanelConfigurationSummary {
  totalConfigurations: number
  documentTypes: Record<string, {
    tableParts: string[]
    lastModified: string
  }>
  lastModified?: string
}

// ============================================================================
// Panel Configuration Service
// ============================================================================

export class PanelConfigurationService {
  private baseUrl: string
  
  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl
  }
  
  /**
   * Save panel configuration for a document type.
   * 
   * Requirements: 9.5
   */
  async savePanelConfiguration(
    userId: number,
    documentType: string,
    commands: TablePartCommand[],
    panelSettings: PanelSettings,
    applyToAllTableParts: boolean = true
  ): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/panel-configuration`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          document_type: documentType,
          commands: commands.map(cmd => ({
            id: cmd.id,
            name: cmd.name,
            icon: cmd.icon,
            tooltip: cmd.tooltip,
            shortcut: cmd.shortcut,
            enabled: cmd.enabled,
            visible: cmd.visible,
            form_method: cmd.formMethod,
            position: cmd.position,
            requires_selection: cmd.requiresSelection
          })),
          panel_settings: {
            visible_commands: panelSettings.visibleCommands,
            hidden_commands: panelSettings.hiddenCommands,
            button_size: panelSettings.buttonSize,
            show_tooltips: panelSettings.showTooltips,
            compact_mode: panelSettings.compactMode
          },
          apply_to_all_table_parts: applyToAllTableParts
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      return result.success
      
    } catch (error) {
      console.error('Error saving panel configuration:', error)
      return false
    }
  }
  
  /**
   * Load panel configuration for a document type and table part.
   * 
   * Requirements: 9.5
   */
  async loadPanelConfiguration(
    userId: number,
    documentType: string,
    tablePartId?: string
  ): Promise<{ commands: TablePartCommand[], panelSettings: PanelSettings }> {
    try {
      const params = new URLSearchParams({
        user_id: userId.toString(),
        document_type: documentType
      })
      
      if (tablePartId) {
        params.append('table_part_id', tablePartId)
      }
      
      const response = await fetch(`${this.baseUrl}/panel-configuration?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      // Convert API response to client format
      const commands: TablePartCommand[] = result.commands.map((cmd: any) => ({
        id: cmd.id,
        name: cmd.name,
        icon: cmd.icon,
        tooltip: cmd.tooltip,
        shortcut: cmd.shortcut,
        enabled: cmd.enabled,
        visible: cmd.visible,
        formMethod: cmd.form_method,
        position: cmd.position,
        requiresSelection: cmd.requires_selection
      }))
      
      const panelSettings: PanelSettings = {
        visibleCommands: result.panel_settings.visible_commands,
        hiddenCommands: result.panel_settings.hidden_commands,
        buttonSize: result.panel_settings.button_size,
        showTooltips: result.panel_settings.show_tooltips,
        compactMode: result.panel_settings.compact_mode
      }
      
      return { commands, panelSettings }
      
    } catch (error) {
      console.error('Error loading panel configuration:', error)
      // Return defaults on error
      return this.getDefaultConfiguration(documentType)
    }
  }
  
  /**
   * Reset panel configuration to defaults.
   * 
   * Requirements: 9.5
   */
  async resetPanelConfiguration(
    userId: number,
    documentType: string,
    applyToAllTableParts: boolean = true
  ): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/panel-configuration/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          document_type: documentType,
          apply_to_all_table_parts: applyToAllTableParts
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      return result.success
      
    } catch (error) {
      console.error('Error resetting panel configuration:', error)
      return false
    }
  }
  
  /**
   * Get panel configuration summary for a user.
   */
  async getPanelConfigurationSummary(userId: number): Promise<PanelConfigurationSummary> {
    try {
      const response = await fetch(`${this.baseUrl}/panel-configuration/summary?user_id=${userId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      return {
        totalConfigurations: result.total_configurations,
        documentTypes: result.document_types,
        lastModified: result.last_modified
      }
      
    } catch (error) {
      console.error('Error getting panel configuration summary:', error)
      return {
        totalConfigurations: 0,
        documentTypes: {},
        lastModified: undefined
      }
    }
  }
  
  /**
   * Get default configuration for a document type.
   */
  getDefaultConfiguration(documentType: string): { commands: TablePartCommand[], panelSettings: PanelSettings } {
    const defaultCommands = this.createDefaultCommands()
    const defaultVisible = defaultCommands.slice(0, 4).map(cmd => cmd.id)
    
    const panelSettings: PanelSettings = {
      visibleCommands: defaultVisible,
      hiddenCommands: defaultCommands.slice(4).map(cmd => cmd.id),
      buttonSize: 'medium',
      showTooltips: true,
      compactMode: false
    }
    
    return { commands: defaultCommands, panelSettings }
  }
  
  /**
   * Create default commands.
   */
  private createDefaultCommands(): TablePartCommand[] {
    return [
      {
        id: 'add_row',
        name: 'Добавить',
        icon: '➕',
        tooltip: 'Добавить новую строку (Insert)',
        shortcut: 'Insert',
        enabled: true,
        visible: true,
        position: 1,
        requiresSelection: false
      },
      {
        id: 'delete_row',
        name: 'Удалить',
        icon: '🗑',
        tooltip: 'Удалить выбранные строки (Delete)',
        shortcut: 'Delete',
        enabled: true,
        visible: true,
        position: 2,
        requiresSelection: true
      },
      {
        id: 'move_up',
        name: 'Выше',
        icon: '↑',
        tooltip: 'Переместить строки выше (Ctrl+Shift+Up)',
        shortcut: 'Ctrl+Shift+Up',
        enabled: true,
        visible: true,
        position: 3,
        requiresSelection: true
      },
      {
        id: 'move_down',
        name: 'Ниже',
        icon: '↓',
        tooltip: 'Переместить строки ниже (Ctrl+Shift+Down)',
        shortcut: 'Ctrl+Shift+Down',
        enabled: true,
        visible: true,
        position: 4,
        requiresSelection: true
      },
      {
        id: 'import_data',
        name: 'Импорт',
        icon: '📥',
        tooltip: 'Импортировать данные из файла',
        enabled: true,
        visible: false,
        position: 5,
        requiresSelection: false
      },
      {
        id: 'export_data',
        name: 'Экспорт',
        icon: '📤',
        tooltip: 'Экспортировать данные в файл',
        enabled: true,
        visible: false,
        position: 6,
        requiresSelection: false
      },
      {
        id: 'print_data',
        name: 'Печать',
        icon: '🖨',
        tooltip: 'Печать табличной части',
        enabled: true,
        visible: false,
        position: 7,
        requiresSelection: false
      }
    ]
  }
  
  /**
   * Save configuration to local storage as fallback.
   */
  saveToLocalStorage(
    userId: number,
    documentType: string,
    commands: TablePartCommand[],
    panelSettings: PanelSettings
  ): void {
    try {
      const key = `panel_config_${userId}_${documentType}`
      const config = {
        commands,
        panelSettings,
        timestamp: new Date().toISOString()
      }
      
      localStorage.setItem(key, JSON.stringify(config))
      
    } catch (error) {
      console.error('Error saving to local storage:', error)
    }
  }
  
  /**
   * Load configuration from local storage as fallback.
   */
  loadFromLocalStorage(
    userId: number,
    documentType: string
  ): { commands: TablePartCommand[], panelSettings: PanelSettings } | null {
    try {
      const key = `panel_config_${userId}_${documentType}`
      const stored = localStorage.getItem(key)
      
      if (stored) {
        const config = JSON.parse(stored)
        return {
          commands: config.commands,
          panelSettings: config.panelSettings
        }
      }
      
      return null
      
    } catch (error) {
      console.error('Error loading from local storage:', error)
      return null
    }
  }
  
  /**
   * Clear all local storage configurations for a user.
   */
  clearLocalStorage(userId: number): void {
    try {
      const keys = Object.keys(localStorage)
      const userKeys = keys.filter(key => key.startsWith(`panel_config_${userId}_`))
      
      userKeys.forEach(key => {
        localStorage.removeItem(key)
      })
      
    } catch (error) {
      console.error('Error clearing local storage:', error)
    }
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a panel configuration service instance.
 */
export function createPanelConfigurationService(baseUrl?: string): PanelConfigurationService {
  return new PanelConfigurationService(baseUrl)
}

/**
 * Get table part IDs for a document type.
 */
export function getTablePartIdsForDocumentType(documentType: string): string[] {
  const documentTableParts: Record<string, string[]> = {
    estimate: ['lines', 'materials', 'equipment'],
    daily_report: ['works', 'materials', 'equipment', 'personnel'],
    timesheet: ['entries'],
    work_composition: ['cost_items', 'materials'],
    counterparty: ['contacts', 'addresses'],
    object: ['estimates', 'reports']
  }
  
  return documentTableParts[documentType] || ['main']
}

/**
 * Get main table part ID for a document type.
 */
export function getMainTablePartId(documentType: string): string {
  const mainTableParts: Record<string, string> = {
    estimate: 'lines',
    daily_report: 'works',
    timesheet: 'entries',
    work_composition: 'cost_items',
    counterparty: 'contacts',
    object: 'estimates'
  }
  
  return mainTableParts[documentType] || 'main'
}