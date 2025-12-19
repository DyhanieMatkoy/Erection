/**
 * Table Part Keyboard Shortcut Handler for Web Client.
 * 
 * This module provides comprehensive keyboard shortcut handling for table parts,
 * implementing standard table shortcuts and ensuring consistent behavior across
 * all table part instances.
 * 
 * Requirements: 3.1, 3.2, 7.3, 7.4
 */

// ============================================================================
// Types and Interfaces
// ============================================================================

export enum ShortcutAction {
  // Row management
  ADD_ROW = 'add_row',
  DELETE_ROW = 'delete_row',
  COPY_ROWS = 'copy_rows',
  PASTE_ROWS = 'paste_rows',
  
  // Row movement
  MOVE_ROW_UP = 'move_row_up',
  MOVE_ROW_DOWN = 'move_row_down',
  
  // Reference field
  OPEN_REFERENCE_SELECTOR = 'open_reference_selector',
  
  // Navigation (for hierarchical lists)
  EXPAND_NODE = 'expand_node',
  COLLAPSE_NODE = 'collapse_node',
  EXPAND_ALL_CHILDREN = 'expand_all_children',
  COLLAPSE_ALL_CHILDREN = 'collapse_all_children',
  GO_TO_FIRST = 'go_to_first',
  GO_TO_LAST = 'go_to_last',
  GO_TO_ROOT = 'go_to_root',
  GO_TO_LAST_IN_HIERARCHY = 'go_to_last_in_hierarchy',
  PAGE_UP = 'page_up',
  PAGE_DOWN = 'page_down'
}

export interface ShortcutMapping {
  keySequence: string
  action: ShortcutAction
  description: string
  enabled: boolean
  context: 'table' | 'hierarchical' | 'all'
  requiresSelection: boolean
  customHandler?: (context: ShortcutContext) => void | Promise<void>
}

export interface ShortcutContext {
  element: HTMLElement
  selectedRows: number[]
  currentRow?: number
  currentColumn?: string
  isHierarchical: boolean
  isEditing: boolean
  additionalData: Record<string, unknown>
}

export type ShortcutHandler = (context: ShortcutContext) => void | Promise<void>

export interface KeyboardEventInfo {
  key: string
  code: string
  ctrlKey: boolean
  shiftKey: boolean
  altKey: boolean
  metaKey: boolean
}

// ============================================================================
// Keyboard Handler Class
// ============================================================================

export class TablePartKeyboardHandler {
  /**
   * Keyboard shortcut handler for table parts.
   * 
   * Provides comprehensive keyboard shortcut handling including:
   * - Standard table shortcuts (Insert, Delete, F4, Ctrl+C/V, Ctrl+±)
   * - Row movement shortcuts (Ctrl+Shift+Up/Down)
   * - Hierarchical navigation shortcuts (Ctrl+→/←, Home/End, etc.)
   * - Consistent behavior across all table parts
   * 
   * Requirements: 3.1, 3.2, 7.3, 7.4
   */
  
  private element: HTMLElement | null = null
  private actionHandlers: Map<ShortcutAction, ShortcutHandler> = new Map()
  private enabled = true
  private currentContext: ShortcutContext | null = null
  private eventListener: ((event: KeyboardEvent) => void) | null = null
  
  // Standard shortcut mappings
  private standardMappings: ShortcutMapping[]
  
  constructor() {
    this.standardMappings = this.createStandardMappings()
  }
  
  /**
   * Create standard keyboard shortcut mappings.
   * 
   * Requirements: 3.1, 3.2, 7.3, 7.4
   */
  private createStandardMappings(): ShortcutMapping[] {
    return [
      // Row management shortcuts
      {
        keySequence: 'Insert',
        action: ShortcutAction.ADD_ROW,
        description: 'Добавить новую строку',
        enabled: true,
        context: 'all',
        requiresSelection: false
      },
      {
        keySequence: 'Delete',
        action: ShortcutAction.DELETE_ROW,
        description: 'Удалить выбранные строки',
        enabled: true,
        context: 'all',
        requiresSelection: true
      },
      {
        keySequence: 'Ctrl+C',
        action: ShortcutAction.COPY_ROWS,
        description: 'Копировать выбранные строки',
        enabled: true,
        context: 'all',
        requiresSelection: true
      },
      {
        keySequence: 'Ctrl+V',
        action: ShortcutAction.PASTE_ROWS,
        description: 'Вставить скопированные строки',
        enabled: true,
        context: 'all',
        requiresSelection: false
      },
      {
        keySequence: 'Ctrl+=',
        action: ShortcutAction.ADD_ROW,
        description: 'Добавить новую строку (альтернатива)',
        enabled: true,
        context: 'all',
        requiresSelection: false
      },
      {
        keySequence: 'Ctrl+-',
        action: ShortcutAction.DELETE_ROW,
        description: 'Удалить выбранные строки (альтернатива)',
        enabled: true,
        context: 'all',
        requiresSelection: true
      },
      
      // Row movement shortcuts
      {
        keySequence: 'Ctrl+Shift+ArrowUp',
        action: ShortcutAction.MOVE_ROW_UP,
        description: 'Переместить строки вверх',
        enabled: true,
        context: 'all',
        requiresSelection: true
      },
      {
        keySequence: 'Ctrl+Shift+ArrowDown',
        action: ShortcutAction.MOVE_ROW_DOWN,
        description: 'Переместить строки вниз',
        enabled: true,
        context: 'all',
        requiresSelection: true
      },
      
      // Reference field shortcut
      {
        keySequence: 'F4',
        action: ShortcutAction.OPEN_REFERENCE_SELECTOR,
        description: 'Открыть форму выбора для поля справочника',
        enabled: true,
        context: 'all',
        requiresSelection: false
      },
      
      // Hierarchical navigation shortcuts
      {
        keySequence: 'Ctrl+ArrowRight',
        action: ShortcutAction.EXPAND_NODE,
        description: 'Развернуть узел',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'Ctrl+ArrowLeft',
        action: ShortcutAction.COLLAPSE_NODE,
        description: 'Свернуть узел',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'Ctrl+Shift+ArrowRight',
        action: ShortcutAction.EXPAND_ALL_CHILDREN,
        description: 'Развернуть все дочерние узлы',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'Ctrl+Shift+ArrowLeft',
        action: ShortcutAction.COLLAPSE_ALL_CHILDREN,
        description: 'Свернуть все дочерние узлы',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'Home',
        action: ShortcutAction.GO_TO_FIRST,
        description: 'Перейти к первому элементу',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'End',
        action: ShortcutAction.GO_TO_LAST,
        description: 'Перейти к последнему элементу',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'Ctrl+Home',
        action: ShortcutAction.GO_TO_ROOT,
        description: 'Перейти к корневому элементу',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'Ctrl+End',
        action: ShortcutAction.GO_TO_LAST_IN_HIERARCHY,
        description: 'Перейти к последнему элементу в иерархии',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'PageUp',
        action: ShortcutAction.PAGE_UP,
        description: 'Прокрутить на страницу вверх',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      },
      {
        keySequence: 'PageDown',
        action: ShortcutAction.PAGE_DOWN,
        description: 'Прокрутить на страницу вниз',
        enabled: true,
        context: 'hierarchical',
        requiresSelection: false
      }
    ]
  }
  
  /**
   * Attach keyboard handler to an HTML element.
   */
  attachTo(element: HTMLElement): void {
    this.detach() // Remove previous listener if any
    
    this.element = element
    this.eventListener = (event: KeyboardEvent) => this.handleKeyboardEvent(event)
    
    // Add event listener with capture to ensure we get the event first
    element.addEventListener('keydown', this.eventListener, { capture: true })
    
    console.log('Keyboard handler attached to element')
  }
  
  /**
   * Detach keyboard handler from current element.
   */
  detach(): void {
    if (this.element && this.eventListener) {
      this.element.removeEventListener('keydown', this.eventListener, { capture: true })
      this.element = null
      this.eventListener = null
      console.log('Keyboard handler detached')
    }
  }
  
  /**
   * Handle keyboard events.
   */
  private handleKeyboardEvent(event: KeyboardEvent): void {
    if (!this.enabled) {
      return
    }
    
    const eventInfo = this.extractKeyboardEventInfo(event)
    const keySequence = this.buildKeySequence(eventInfo)
    
    // Find matching shortcut mapping
    const mapping = this.findMatchingMapping(keySequence)
    if (!mapping) {
      return
    }
    
    // Get current context
    const context = this.currentContext || this.createDefaultContext()
    
    // Check if shortcut is applicable
    if (!this.isShortcutApplicable(mapping, context)) {
      const reason = this.getBlockReason(mapping, context)
      console.debug(`Shortcut ${mapping.action} blocked: ${reason}`)
      return
    }
    
    // Prevent default behavior
    event.preventDefault()
    event.stopPropagation()
    
    // Execute shortcut
    this.executeShortcut(mapping, context)
  }
  
  /**
   * Extract keyboard event information.
   */
  private extractKeyboardEventInfo(event: KeyboardEvent): KeyboardEventInfo {
    return {
      key: event.key,
      code: event.code,
      ctrlKey: event.ctrlKey,
      shiftKey: event.shiftKey,
      altKey: event.altKey,
      metaKey: event.metaKey
    }
  }
  
  /**
   * Build key sequence string from keyboard event.
   */
  private buildKeySequence(eventInfo: KeyboardEventInfo): string {
    const parts: string[] = []
    
    if (eventInfo.ctrlKey || eventInfo.metaKey) {
      parts.push('Ctrl')
    }
    if (eventInfo.shiftKey) {
      parts.push('Shift')
    }
    if (eventInfo.altKey) {
      parts.push('Alt')
    }
    
    // Normalize key names
    let key = eventInfo.key
    if (key === 'ArrowUp') key = 'ArrowUp'
    else if (key === 'ArrowDown') key = 'ArrowDown'
    else if (key === 'ArrowLeft') key = 'ArrowLeft'
    else if (key === 'ArrowRight') key = 'ArrowRight'
    else if (key === ' ') key = 'Space'
    else if (key === '+') key = '='
    
    parts.push(key)
    
    return parts.join('+')
  }
  
  /**
   * Find matching shortcut mapping for key sequence.
   */
  private findMatchingMapping(keySequence: string): ShortcutMapping | null {
    return this.standardMappings.find(mapping => 
      mapping.enabled && mapping.keySequence === keySequence
    ) || null
  }
  
  /**
   * Check if shortcut is applicable in current context.
   */
  private isShortcutApplicable(mapping: ShortcutMapping, context: ShortcutContext): boolean {
    // Check if editing (some shortcuts should be disabled while editing)
    if (context.isEditing && [
      ShortcutAction.DELETE_ROW,
      ShortcutAction.MOVE_ROW_UP,
      ShortcutAction.MOVE_ROW_DOWN
    ].includes(mapping.action)) {
      return false
    }
    
    // Check context type
    if (mapping.context === 'hierarchical' && !context.isHierarchical) {
      return false
    }
    
    // Check selection requirement
    if (mapping.requiresSelection && context.selectedRows.length === 0) {
      return false
    }
    
    return true
  }
  
  /**
   * Get reason why shortcut was blocked.
   */
  private getBlockReason(mapping: ShortcutMapping, context: ShortcutContext): string {
    if (context.isEditing) {
      return 'editing in progress'
    }
    if (mapping.context === 'hierarchical' && !context.isHierarchical) {
      return 'not in hierarchical context'
    }
    if (mapping.requiresSelection && context.selectedRows.length === 0) {
      return 'no rows selected'
    }
    return 'unknown reason'
  }
  
  /**
   * Execute a shortcut.
   */
  private async executeShortcut(mapping: ShortcutMapping, context: ShortcutContext): Promise<void> {
    try {
      // Try custom handler first
      if (mapping.customHandler) {
        await mapping.customHandler(context)
        return
      }
      
      // Try registered action handler
      const handler = this.actionHandlers.get(mapping.action)
      if (handler) {
        await handler(context)
        return
      }
      
      // Emit event for external handling
      this.emitShortcutEvent(mapping.action, context)
      
      console.debug(`Shortcut executed: ${mapping.action}`)
    } catch (error) {
      console.error(`Shortcut execution failed for ${mapping.action}:`, error)
    }
  }
  
  /**
   * Emit shortcut event for external handling.
   */
  private emitShortcutEvent(action: ShortcutAction, context: ShortcutContext): void {
    const event = new CustomEvent('table-part-shortcut', {
      detail: { action, context },
      bubbles: true,
      cancelable: true
    })
    
    if (this.element) {
      this.element.dispatchEvent(event)
    }
  }
  
  /**
   * Create default context when none is provided.
   */
  private createDefaultContext(): ShortcutContext {
    return {
      element: this.element || document.body,
      selectedRows: [],
      isHierarchical: false,
      isEditing: false,
      additionalData: {}
    }
  }
  
  // ============================================================================
  // Public Interface Methods
  // ============================================================================
  
  /**
   * Register a handler for a specific shortcut action.
   */
  registerActionHandler(action: ShortcutAction, handler: ShortcutHandler): void {
    this.actionHandlers.set(action, handler)
    console.debug(`Registered action handler for ${action}`)
  }
  
  /**
   * Unregister a handler for a specific shortcut action.
   */
  unregisterActionHandler(action: ShortcutAction): void {
    if (this.actionHandlers.has(action)) {
      this.actionHandlers.delete(action)
      console.debug(`Unregistered action handler for ${action}`)
    }
  }
  
  /**
   * Update current shortcut context.
   */
  updateContext(context: ShortcutContext): void {
    this.currentContext = context
  }
  
  /**
   * Enable or disable all keyboard shortcuts.
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled
    console.log(`Keyboard shortcuts ${enabled ? 'enabled' : 'disabled'}`)
  }
  
  /**
   * Enable or disable a specific shortcut.
   */
  enableShortcut(action: ShortcutAction, enabled = true): void {
    const mapping = this.standardMappings.find(m => m.action === action)
    if (mapping) {
      mapping.enabled = enabled
      console.debug(`Shortcut ${action} ${enabled ? 'enabled' : 'disabled'}`)
    }
  }
  
  /**
   * Add a custom keyboard shortcut.
   */
  addCustomShortcut(
    keySequence: string,
    action: ShortcutAction,
    description: string,
    handler?: ShortcutHandler,
    options: Partial<ShortcutMapping> = {}
  ): void {
    const mapping: ShortcutMapping = {
      keySequence,
      action,
      description,
      enabled: true,
      context: 'all',
      requiresSelection: false,
      customHandler: handler,
      ...options
    }
    
    this.standardMappings.push(mapping)
    console.log(`Added custom shortcut: ${keySequence} -> ${action}`)
  }
  
  /**
   * Remove a keyboard shortcut.
   */
  removeShortcut(keySequence: string, action: ShortcutAction): void {
    const index = this.standardMappings.findIndex(
      m => m.keySequence === keySequence && m.action === action
    )
    
    if (index !== -1) {
      this.standardMappings.splice(index, 1)
      console.log(`Removed shortcut: ${keySequence} -> ${action}`)
    }
  }
  
  /**
   * Get list of shortcut mappings, optionally filtered by context.
   */
  getShortcutMappings(contextFilter?: 'table' | 'hierarchical' | 'all'): ShortcutMapping[] {
    if (contextFilter) {
      return this.standardMappings.filter(
        m => m.context === contextFilter || m.context === 'all'
      )
    }
    return [...this.standardMappings]
  }
  
  /**
   * Get formatted help text for all shortcuts.
   */
  getShortcutHelpText(): string {
    const lines = ['Горячие клавиши табличной части:', '']
    
    // Group by category
    const categories = {
      'Управление строками': [
        ShortcutAction.ADD_ROW,
        ShortcutAction.DELETE_ROW,
        ShortcutAction.COPY_ROWS,
        ShortcutAction.PASTE_ROWS
      ],
      'Перемещение строк': [
        ShortcutAction.MOVE_ROW_UP,
        ShortcutAction.MOVE_ROW_DOWN
      ],
      'Справочники': [
        ShortcutAction.OPEN_REFERENCE_SELECTOR
      ],
      'Навигация по иерархии': [
        ShortcutAction.EXPAND_NODE,
        ShortcutAction.COLLAPSE_NODE,
        ShortcutAction.EXPAND_ALL_CHILDREN,
        ShortcutAction.COLLAPSE_ALL_CHILDREN,
        ShortcutAction.GO_TO_FIRST,
        ShortcutAction.GO_TO_LAST,
        ShortcutAction.GO_TO_ROOT,
        ShortcutAction.GO_TO_LAST_IN_HIERARCHY,
        ShortcutAction.PAGE_UP,
        ShortcutAction.PAGE_DOWN
      ]
    }
    
    for (const [category, actions] of Object.entries(categories)) {
      lines.push(`${category}:`)
      for (const mapping of this.standardMappings) {
        if (actions.includes(mapping.action)) {
          lines.push(`  ${mapping.keySequence.padEnd(20)} - ${mapping.description}`)
        }
      }
      lines.push('')
    }
    
    return lines.join('\n')
  }
  
  /**
   * Cleanup resources.
   */
  cleanup(): void {
    this.detach()
    this.actionHandlers.clear()
    console.log('Keyboard handler cleaned up')
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a keyboard handler for a table part element.
 */
export function createKeyboardHandler(): TablePartKeyboardHandler {
  return new TablePartKeyboardHandler()
}

/**
 * Create a shortcut context for table operations.
 */
export function createTableContext(
  element: HTMLElement,
  selectedRows: number[] = [],
  currentRow?: number,
  isHierarchical = false,
  isEditing = false
): ShortcutContext {
  return {
    element,
    selectedRows,
    currentRow,
    isHierarchical,
    isEditing,
    additionalData: {}
  }
}

/**
 * Check if an element is currently being edited.
 */
export function isElementEditing(element: HTMLElement): boolean {
  const activeElement = document.activeElement
  
  if (!activeElement) {
    return false
  }
  
  // Check if active element is an input within the table part
  return element.contains(activeElement) && (
    activeElement.tagName === 'INPUT' ||
    activeElement.tagName === 'TEXTAREA' ||
    activeElement.tagName === 'SELECT' ||
    activeElement.hasAttribute('contenteditable')
  )
}

/**
 * Get selected row indices from a table element.
 */
export function getSelectedRows(tableElement: HTMLElement): number[] {
  const selectedRows: number[] = []
  const rows = tableElement.querySelectorAll('tr.row-selected')
  
  rows.forEach((row, index) => {
    const rowIndex = Array.from(row.parentElement?.children || []).indexOf(row)
    if (rowIndex !== -1) {
      selectedRows.push(rowIndex)
    }
  })
  
  return selectedRows
}