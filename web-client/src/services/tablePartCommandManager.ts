/**
 * Table Part Command Manager Service for Web Client.
 * 
 * This module provides command management functionality for table parts,
 * bridging panel buttons with form methods and handling command discovery,
 * registration, and execution.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 */

// ============================================================================
// Types and Interfaces
// ============================================================================

export enum CommandAvailability {
  ALWAYS = 'always',
  REQUIRES_SELECTION = 'requires_selection',
  REQUIRES_ROWS = 'requires_rows',
  REQUIRES_EDIT_MODE = 'requires_edit_mode',
  CUSTOM = 'custom'
}

export interface FormCommand {
  id: string
  name: string
  methodName: string
  formInstance: any
  availability: CommandAvailability
  parameters: any[]
  enabled: boolean
  customAvailabilityCheck?: () => boolean
}

export interface CommandContext {
  selectedRows: number[]
  tableData: any[]
  currentRow?: number
  currentColumn?: string
  additionalData: Record<string, any>
}

export interface CommandResult {
  success: boolean
  message?: string
  data?: any
  affectedRows: number[]
  refreshRequired: boolean
}

export interface ICommandDiscovery {
  discoverCommands(formInstance: any): FormCommand[]
}

// ============================================================================
// Command Discovery Strategies
// ============================================================================

export class AttributeBasedDiscovery implements ICommandDiscovery {
  /**
   * Discovers commands by looking for methods with tableCommand metadata.
   * 
   * Methods should be decorated with @tableCommand decorator.
   */
  discoverCommands(formInstance: any): FormCommand[] {
    const commands: FormCommand[] = []
    
    // Check if form instance has command metadata
    if (formInstance._tableCommands) {
      for (const [methodName, config] of Object.entries(formInstance._tableCommands)) {
        const command: FormCommand = {
          id: (config as any).id || methodName,
          name: (config as any).name || this.formatMethodName(methodName),
          methodName,
          formInstance,
          availability: (config as any).availability || CommandAvailability.ALWAYS,
          parameters: (config as any).parameters || [],
          enabled: (config as any).enabled !== false,
          customAvailabilityCheck: (config as any).customAvailabilityCheck
        }
        commands.push(command)
      }
    }
    
    // Also check the prototype for decorated methods
    const prototype = Object.getPrototypeOf(formInstance)
    if (prototype && prototype._tableCommands) {
      for (const [methodName, config] of Object.entries(prototype._tableCommands)) {
        // Skip if already found in instance
        if (formInstance._tableCommands && formInstance._tableCommands[methodName]) {
          continue
        }
        
        const command: FormCommand = {
          id: (config as any).id || methodName,
          name: (config as any).name || this.formatMethodName(methodName),
          methodName,
          formInstance,
          availability: (config as any).availability || CommandAvailability.ALWAYS,
          parameters: (config as any).parameters || [],
          enabled: (config as any).enabled !== false,
          customAvailabilityCheck: (config as any).customAvailabilityCheck
        }
        commands.push(command)
      }
    }
    
    return commands
  }
  
  private formatMethodName(methodName: string): string {
    return methodName.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())
  }
}

export class NamingConventionDiscovery implements ICommandDiscovery {
  /**
   * Discovers commands based on method naming conventions.
   */
  
  private readonly COMMAND_PATTERNS: Record<string, string[]> = {
    add_row: ['addRow', 'addTableRow', 'insertRow', 'createRow'],
    delete_row: ['deleteRow', 'removeRow', 'deleteSelected', 'removeSelected'],
    move_up: ['moveUp', 'moveRowUp', 'rowUp'],
    move_down: ['moveDown', 'moveRowDown', 'rowDown'],
    import_data: ['importData', 'importRows', 'loadData'],
    export_data: ['exportData', 'exportRows', 'saveData'],
    print_data: ['printData', 'printTable', 'printRows']
  }
  
  discoverCommands(formInstance: any): FormCommand[] {
    const commands: FormCommand[] = []
    
    for (const [commandId, patterns] of Object.entries(this.COMMAND_PATTERNS)) {
      for (const pattern of patterns) {
        if (typeof formInstance[pattern] === 'function') {
          const command: FormCommand = {
            id: commandId,
            name: this.getDefaultName(commandId),
            methodName: pattern,
            formInstance,
            availability: this.getDefaultAvailability(commandId),
            parameters: [],
            enabled: true
          }
          commands.push(command)
          break // Use first matching pattern
        }
      }
    }
    
    return commands
  }
  
  private getDefaultAvailability(commandId: string): CommandAvailability {
    if (['delete_row', 'move_up', 'move_down'].includes(commandId)) {
      return CommandAvailability.REQUIRES_SELECTION
    } else if (['export_data'].includes(commandId)) {
      return CommandAvailability.REQUIRES_ROWS
    } else {
      return CommandAvailability.ALWAYS
    }
  }
  
  private getDefaultName(commandId: string): string {
    const names: Record<string, string> = {
      add_row: 'Добавить строку',
      delete_row: 'Удалить строки',
      move_up: 'Переместить выше',
      move_down: 'Переместить ниже',
      import_data: 'Импорт данных',
      export_data: 'Экспорт данных',
      print_data: 'Печать данных'
    }
    return names[commandId] || commandId.replace(/_/g, ' ')
  }
}

// ============================================================================
// Command Manager
// ============================================================================

export class TablePartCommandManager {
  /**
   * Command manager for table parts.
   * 
   * Provides functionality to:
   * - Discover commands from form instances
   * - Register and manage form commands
   * - Execute commands with proper context
   * - Handle command availability and state updates
   * 
   * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
   */
  
  private registeredCommands: Map<string, FormCommand> = new Map()
  private discoveryStrategies: ICommandDiscovery[]
  private commandStateCache: Map<string, boolean> = new Map()
  private lastContext?: CommandContext
  
  constructor(discoveryStrategies?: ICommandDiscovery[]) {
    this.discoveryStrategies = discoveryStrategies || [
      new AttributeBasedDiscovery(),
      new NamingConventionDiscovery()
    ]
  }
  
  /**
   * Discover and register commands from a form instance.
   * 
   * Requirements: 2.1, 2.2
   */
  discoverAndRegisterCommands(formInstance: any): FormCommand[] {
    const discoveredCommands: FormCommand[] = []
    
    for (const strategy of this.discoveryStrategies) {
      try {
        const commands = strategy.discoverCommands(formInstance)
        discoveredCommands.push(...commands)
        console.log(`Discovered ${commands.length} commands using ${strategy.constructor.name}`)
      } catch (error) {
        console.warn(`Command discovery failed with ${strategy.constructor.name}:`, error)
      }
    }
    
    // Register discovered commands
    for (const command of discoveredCommands) {
      this.registerCommand(command)
    }
    
    console.log(`Total registered commands: ${this.registeredCommands.size}`)
    return discoveredCommands
  }
  
  /**
   * Register a form command.
   * 
   * Requirements: 2.2
   */
  registerCommand(command: FormCommand): void {
    this.registeredCommands.set(command.id, command)
    console.debug(`Registered command: ${command.id} -> ${command.methodName}`)
  }
  
  /**
   * Unregister a form command.
   */
  unregisterCommand(commandId: string): void {
    if (this.registeredCommands.has(commandId)) {
      this.registeredCommands.delete(commandId)
      console.debug(`Unregistered command: ${commandId}`)
    }
  }
  
  /**
   * Execute a registered command.
   * 
   * Requirements: 2.3, 2.4
   */
  async executeCommand(commandId: string, context: CommandContext): Promise<CommandResult> {
    const command = this.registeredCommands.get(commandId)
    
    if (!command) {
      return {
        success: false,
        message: `Command '${commandId}' not found`,
        affectedRows: [],
        refreshRequired: false
      }
    }
    
    // Check availability
    if (!this.isCommandAvailable(command, context)) {
      return {
        success: false,
        message: `Command '${commandId}' is not available in current context`,
        affectedRows: [],
        refreshRequired: false
      }
    }
    
    try {
      // Get the method from form instance
      const method = command.formInstance[command.methodName]
      
      if (typeof method !== 'function') {
        throw new Error(`Method '${command.methodName}' is not a function`)
      }
      
      // Prepare method arguments
      const args = this.prepareMethodArguments(method, command, context)
      
      // Execute the method
      const result = await method.apply(command.formInstance, args)
      
      // Handle different return types
      if (this.isCommandResult(result)) {
        return result
      } else if (typeof result === 'boolean') {
        return {
          success: result,
          message: result ? 'Command executed' : 'Command failed',
          affectedRows: [],
          refreshRequired: false
        }
      } else {
        return {
          success: true,
          message: 'Command executed successfully',
          data: result,
          affectedRows: [],
          refreshRequired: false
        }
      }
    } catch (error) {
      console.error(`Command execution failed for '${commandId}':`, error)
      return {
        success: false,
        message: `Command execution failed: ${error instanceof Error ? error.message : String(error)}`,
        affectedRows: [],
        refreshRequired: false
      }
    }
  }
  
  private prepareMethodArguments(method: Function, command: FormCommand, context: CommandContext): any[] {
    const args: any[] = []
    
    // Add predefined parameters
    args.push(...command.parameters)
    
    // For JavaScript/TypeScript, we can't easily inspect method signatures
    // So we'll pass context as the first argument if no predefined parameters
    if (command.parameters.length === 0) {
      args.push(context)
    }
    
    return args
  }
  
  private isCommandResult(obj: any): obj is CommandResult {
    return obj && typeof obj === 'object' && 'success' in obj
  }
  
  /**
   * Update command availability states.
   * 
   * Requirements: 2.5
   */
  updateCommandStates(context: CommandContext): Record<string, boolean> {
    this.lastContext = context
    const states: Record<string, boolean> = {}
    
    for (const [commandId, command] of this.registeredCommands) {
      const isAvailable = this.isCommandAvailable(command, context)
      states[commandId] = isAvailable
      this.commandStateCache.set(commandId, isAvailable)
    }
    
    return states
  }
  
  private isCommandAvailable(command: FormCommand, context: CommandContext): boolean {
    if (!command.enabled) {
      return false
    }
    
    if (command.customAvailabilityCheck) {
      return command.customAvailabilityCheck()
    }
    
    switch (command.availability) {
      case CommandAvailability.ALWAYS:
        return true
      case CommandAvailability.REQUIRES_SELECTION:
        return context.selectedRows.length > 0
      case CommandAvailability.REQUIRES_ROWS:
        return context.tableData.length > 0
      case CommandAvailability.REQUIRES_EDIT_MODE:
        return context.additionalData.editMode === true
      default:
        return true
    }
  }
  
  /**
   * Get cached command availability state.
   */
  getCommandState(commandId: string): boolean {
    return this.commandStateCache.get(commandId) ?? false
  }
  
  /**
   * Get list of currently available commands.
   */
  getAvailableCommands(context?: CommandContext): FormCommand[] {
    const checkContext = context || this.lastContext
    if (!checkContext) {
      return Array.from(this.registeredCommands.values())
    }
    
    const available: FormCommand[] = []
    for (const command of this.registeredCommands.values()) {
      if (this.isCommandAvailable(command, checkContext)) {
        available.push(command)
      }
    }
    
    return available
  }
  
  /**
   * Get all registered commands.
   */
  getRegisteredCommands(): Record<string, FormCommand> {
    const result: Record<string, FormCommand> = {}
    for (const [id, command] of this.registeredCommands) {
      result[id] = command
    }
    return result
  }
  
  /**
   * Clear all registered commands.
   */
  clearCommands(): void {
    this.registeredCommands.clear()
    this.commandStateCache.clear()
    this.lastContext = undefined
  }
}

// ============================================================================
// Decorator for TypeScript/JavaScript
// ============================================================================

export interface TableCommandConfig {
  id?: string
  name?: string
  availability?: CommandAvailability
  parameters?: any[]
  enabled?: boolean
  customAvailabilityCheck?: () => boolean
}

/**
 * Decorator to mark methods as table commands.
 * 
 * Example:
 *   @tableCommand({ id: 'add_row', name: 'Add Row', availability: CommandAvailability.ALWAYS })
 *   addNewRow(context: CommandContext) {
 *     // Implementation
 *   }
 */
export function tableCommand(config: TableCommandConfig = {}) {
  return function (target: any, propertyKey: string | symbol, descriptor: PropertyDescriptor) {
    // Initialize _tableCommands if it doesn't exist on the prototype
    if (!target.constructor.prototype._tableCommands) {
      target.constructor.prototype._tableCommands = {}
    }
    
    // Convert propertyKey to string if it's a symbol
    const methodName = typeof propertyKey === 'string' ? propertyKey : propertyKey.toString()
    
    // Store command configuration on the prototype
    target.constructor.prototype._tableCommands[methodName] = {
      id: config.id || methodName,
      name: config.name || methodName.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()),
      availability: config.availability || CommandAvailability.ALWAYS,
      parameters: config.parameters || [],
      enabled: config.enabled !== false,
      customAvailabilityCheck: config.customAvailabilityCheck
    }
    
    return descriptor
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a command manager with default discovery strategies.
 */
export function createCommandManager(): TablePartCommandManager {
  return new TablePartCommandManager()
}

/**
 * Create a command context from table part state.
 */
export function createCommandContext(
  selectedRows: number[] = [],
  tableData: any[] = [],
  additionalData: Record<string, any> = {}
): CommandContext {
  return {
    selectedRows,
    tableData,
    additionalData
  }
}