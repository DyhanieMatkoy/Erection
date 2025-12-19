/**
 * Comprehensive error handling service for table parts.
 * 
 * This module provides centralized error handling, recovery mechanisms,
 * and user-friendly error reporting for table part operations.
 * 
 * Requirements: 13.1 - Implement comprehensive error handling
 */

import { ref, reactive } from 'vue'

// ============================================================================
// Types and Interfaces
// ============================================================================

export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export enum ErrorCategory {
  COMMAND_EXECUTION = 'command_execution',
  CALCULATION = 'calculation',
  IMPORT_EXPORT = 'import_export',
  VALIDATION = 'validation',
  REFERENCE_SELECTION = 'reference_selection',
  DATA_ACCESS = 'data_access',
  UI_INTERACTION = 'ui_interaction',
  NETWORK = 'network',
  PERMISSION = 'permission',
  CONFIGURATION = 'configuration'
}

export interface ErrorContext {
  operation: string
  component: string
  userAction?: string
  dataContext: Record<string, any>
  stackTrace?: string
  timestamp: Date
}

export interface ErrorInfo {
  id: string
  category: ErrorCategory
  severity: ErrorSeverity
  message: string
  userMessage: string
  technicalDetails?: string
  context?: ErrorContext
  recoverySuggestions: string[]
  canRetry: boolean
  retryCount: number
  maxRetries: number
  timestamp: Date
}

export interface RecoveryAction {
  id: string
  name: string
  description: string
  action: () => Promise<boolean> | boolean
  automatic: boolean
  priority: number
}

export interface ErrorHandlerCallbacks {
  onErrorOccurred?: (error: ErrorInfo) => void
  onErrorRecovered?: (errorId: string, recoveryMethod: string) => void
  onCriticalError?: (error: ErrorInfo) => void
  onShowUserMessage?: (error: ErrorInfo) => void
}

// ============================================================================
// Error Handler Class
// ============================================================================

export class TablePartErrorHandler {
  private errorHistory: ErrorInfo[] = []
  private recoveryActions: Map<string, RecoveryAction[]> = new Map()
  private errorPatterns: Map<string, Partial<ErrorInfo>> = new Map()
  private readonly maxHistorySize = 100
  private autoRecoveryEnabled = true
  private callbacks: ErrorHandlerCallbacks = {}
  
  constructor(callbacks?: ErrorHandlerCallbacks) {
    this.callbacks = callbacks || {}
    this.setupStandardErrorPatterns()
    this.setupStandardRecoveryActions()
  }
  
  /**
   * Handle an error with comprehensive processing
   */
  async handleError(
    error: Error,
    category: ErrorCategory,
    operation: string,
    component: string,
    userAction?: string,
    dataContext?: Record<string, any>,
    showToUser = true
  ): Promise<ErrorInfo> {
    // Create error context
    const context: ErrorContext = {
      operation,
      component,
      userAction,
      dataContext: dataContext || {},
      stackTrace: error.stack,
      timestamp: new Date()
    }
    
    // Determine error severity
    const severity = this.determineSeverity(error, category)
    
    // Generate error ID
    const errorId = this.generateErrorId(error, category, operation)
    
    // Create user-friendly message
    const userMessage = this.createUserMessage(error, category, operation)
    
    // Get recovery suggestions
    const recoverySuggestions = this.getRecoverySuggestions(error, category)
    
    // Create error info
    const errorInfo: ErrorInfo = {
      id: errorId,
      category,
      severity,
      message: error.message,
      userMessage,
      technicalDetails: error.stack,
      context,
      recoverySuggestions,
      canRetry: this.canRetry(error, category),
      retryCount: 0,
      maxRetries: 3,
      timestamp: new Date()
    }
    
    // Log the error
    this.logError(errorInfo)
    
    // Add to history
    this.addToHistory(errorInfo)
    
    // Emit callbacks
    this.callbacks.onErrorOccurred?.(errorInfo)
    if (severity === ErrorSeverity.CRITICAL) {
      this.callbacks.onCriticalError?.(errorInfo)
    }
    
    // Attempt automatic recovery if enabled
    if (this.autoRecoveryEnabled && errorInfo.canRetry) {
      const recoveryAttempted = await this.attemptAutomaticRecovery(errorInfo)
      if (recoveryAttempted) {
        return errorInfo
      }
    }
    
    // Show to user if requested
    if (showToUser) {
      this.showErrorToUser(errorInfo)
    }
    
    return errorInfo
  }
  
  /**
   * Handle command execution errors
   */
  async handleCommandError(
    error: Error,
    commandId: string,
    context: Record<string, any>,
    showToUser = true
  ): Promise<ErrorInfo> {
    return this.handleError(
      error,
      ErrorCategory.COMMAND_EXECUTION,
      `execute_command_${commandId}`,
      'command_manager',
      `Execute command: ${commandId}`,
      context,
      showToUser
    )
  }
  
  /**
   * Handle calculation errors
   */
  async handleCalculationError(
    error: Error,
    ruleId: string,
    rowData: Record<string, any>,
    showToUser = true
  ): Promise<ErrorInfo> {
    return this.handleError(
      error,
      ErrorCategory.CALCULATION,
      `calculate_${ruleId}`,
      'calculation_engine',
      'Field calculation',
      { ruleId, rowData },
      showToUser
    )
  }
  
  /**
   * Handle import/export errors
   */
  async handleImportError(
    error: Error,
    filePath: string,
    rowNumber?: number,
    showToUser = true
  ): Promise<ErrorInfo> {
    const context: Record<string, any> = { filePath }
    if (rowNumber !== undefined) {
      context.rowNumber = rowNumber
    }
    
    return this.handleError(
      error,
      ErrorCategory.IMPORT_EXPORT,
      'import_data',
      'import_service',
      `Import from ${filePath}`,
      context,
      showToUser
    )
  }
  
  /**
   * Handle validation errors
   */
  async handleValidationError(
    error: Error,
    fieldName: string,
    fieldValue: any,
    validationRule: string,
    showToUser = true
  ): Promise<ErrorInfo> {
    return this.handleError(
      error,
      ErrorCategory.VALIDATION,
      `validate_${fieldName}`,
      'validation_service',
      `Input validation for ${fieldName}`,
      { fieldName, fieldValue, validationRule },
      showToUser
    )
  }
  
  /**
   * Retry a failed operation
   */
  async retryOperation(errorId: string): Promise<boolean> {
    const errorInfo = this.findErrorById(errorId)
    if (!errorInfo || !errorInfo.canRetry) {
      return false
    }
    
    if (errorInfo.retryCount >= errorInfo.maxRetries) {
      console.warn(`Maximum retries exceeded for error ${errorId}`)
      return false
    }
    
    errorInfo.retryCount++
    
    // Attempt recovery actions
    const recoveryActions = this.recoveryActions.get(errorInfo.category) || []
    for (const action of recoveryActions) {
      try {
        const result = await action.action()
        if (result) {
          console.log(`Recovery successful for error ${errorId} using ${action.name}`)
          this.callbacks.onErrorRecovered?.(errorId, action.name)
          return true
        }
      } catch (e) {
        console.warn(`Recovery action ${action.name} failed:`, e)
      }
    }
    
    return false
  }
  
  /**
   * Get error history, optionally filtered by category
   */
  getErrorHistory(category?: ErrorCategory): ErrorInfo[] {
    if (category) {
      return this.errorHistory.filter(error => error.category === category)
    }
    return [...this.errorHistory]
  }
  
  /**
   * Clear error history
   */
  clearErrorHistory(): void {
    this.errorHistory.length = 0
  }
  
  /**
   * Add a recovery action for a specific error category
   */
  addRecoveryAction(category: ErrorCategory, action: RecoveryAction): void {
    if (!this.recoveryActions.has(category)) {
      this.recoveryActions.set(category, [])
    }
    this.recoveryActions.get(category)!.push(action)
  }
  
  /**
   * Enable or disable automatic recovery attempts
   */
  enableAutoRecovery(enabled: boolean): void {
    this.autoRecoveryEnabled = enabled
  }
  
  /**
   * Set event callbacks
   */
  setCallbacks(callbacks: ErrorHandlerCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }
  
  // ============================================================================
  // Private Methods
  // ============================================================================
  
  private setupStandardErrorPatterns(): void {
    // Command execution patterns
    this.errorPatterns.set('method_not_found', {
      category: ErrorCategory.COMMAND_EXECUTION,
      severity: ErrorSeverity.ERROR,
      userMessage: 'Команда недоступна в текущем контексте',
      recoverySuggestions: [
        'Проверьте, что форма поддерживает данную операцию',
        'Обновите форму и попробуйте снова'
      ]
    })
    
    // Calculation patterns
    this.errorPatterns.set('division_by_zero', {
      category: ErrorCategory.CALCULATION,
      severity: ErrorSeverity.WARNING,
      userMessage: 'Деление на ноль в расчете',
      recoverySuggestions: [
        'Проверьте значения в полях расчета',
        'Убедитесь, что делитель не равен нулю'
      ],
      canRetry: true
    })
    
    // Import/Export patterns
    this.errorPatterns.set('file_not_found', {
      category: ErrorCategory.IMPORT_EXPORT,
      severity: ErrorSeverity.ERROR,
      userMessage: 'Файл не найден',
      recoverySuggestions: [
        'Проверьте путь к файлу',
        'Убедитесь, что файл существует и доступен для чтения'
      ]
    })
    
    // Validation patterns
    this.errorPatterns.set('invalid_format', {
      category: ErrorCategory.VALIDATION,
      severity: ErrorSeverity.WARNING,
      userMessage: 'Неверный формат данных',
      recoverySuggestions: [
        'Проверьте формат введенных данных',
        'Используйте правильный формат для данного поля'
      ],
      canRetry: true
    })
  }
  
  private setupStandardRecoveryActions(): void {
    // Command execution recovery
    this.addRecoveryAction(ErrorCategory.COMMAND_EXECUTION, {
      id: 'refresh_form',
      name: 'Обновить форму',
      description: 'Обновить состояние формы и команд',
      action: () => true, // Placeholder - would be implemented by caller
      automatic: false,
      priority: 1
    })
    
    // Calculation recovery
    this.addRecoveryAction(ErrorCategory.CALCULATION, {
      id: 'reset_calculation',
      name: 'Сбросить расчет',
      description: 'Сбросить значения расчетных полей',
      action: () => true, // Placeholder
      automatic: true,
      priority: 2
    })
    
    // Import/Export recovery
    this.addRecoveryAction(ErrorCategory.IMPORT_EXPORT, {
      id: 'retry_file_operation',
      name: 'Повторить операцию с файлом',
      description: 'Повторить чтение/запись файла',
      action: () => true, // Placeholder
      automatic: true,
      priority: 1
    })
  }
  
  private determineSeverity(error: Error, category: ErrorCategory): ErrorSeverity {
    // Critical errors
    if (error.name === 'OutOfMemoryError' || error.message.includes('out of memory')) {
      return ErrorSeverity.CRITICAL
    }
    
    // Category-specific severity
    switch (category) {
      case ErrorCategory.DATA_ACCESS:
        return ErrorSeverity.ERROR
      case ErrorCategory.VALIDATION:
        return ErrorSeverity.WARNING
      case ErrorCategory.CALCULATION:
        return ErrorSeverity.WARNING
      case ErrorCategory.COMMAND_EXECUTION:
        return ErrorSeverity.ERROR
      case ErrorCategory.IMPORT_EXPORT:
        return ErrorSeverity.ERROR
      default:
        break
    }
    
    // Default based on error type
    if (error instanceof TypeError || error instanceof RangeError) {
      return ErrorSeverity.WARNING
    } else if (error.message.includes('network') || error.message.includes('fetch')) {
      return ErrorSeverity.ERROR
    } else {
      return ErrorSeverity.ERROR
    }
  }
  
  private generateErrorId(error: Error, category: ErrorCategory, operation: string): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '_')
    const errorName = error.constructor.name
    return `${category}_${operation}_${errorName}_${timestamp}`
  }
  
  private createUserMessage(error: Error, category: ErrorCategory, operation: string): string {
    const errorName = error.constructor.name.toLowerCase()
    const message = error.message.toLowerCase()
    
    // File-related errors
    if (message.includes('file') && message.includes('not found')) {
      return 'Файл не найден. Проверьте путь к файлу и попробуйте снова.'
    } else if (message.includes('permission') || message.includes('access denied')) {
      return 'Недостаточно прав доступа. Проверьте права на файл или папку.'
    } else if (message.includes('memory') || errorName.includes('memory')) {
      return 'Недостаточно памяти для выполнения операции.'
    }
    
    // Network errors
    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return 'Ошибка сети. Проверьте подключение к интернету и попробуйте снова.'
    }
    
    // Category-specific messages
    switch (category) {
      case ErrorCategory.CALCULATION:
        if (message.includes('division') && message.includes('zero')) {
          return 'Ошибка в расчете: деление на ноль. Проверьте значения в полях.'
        } else if (message.includes('invalid') && message.includes('operation')) {
          return 'Ошибка в расчете: недопустимая операция. Проверьте типы данных.'
        } else {
          return 'Ошибка при выполнении расчета. Проверьте введенные значения.'
        }
      
      case ErrorCategory.COMMAND_EXECUTION:
        if (message.includes('not found') || message.includes('undefined')) {
          return 'Команда недоступна в текущем контексте.'
        } else {
          return 'Ошибка при выполнении команды. Попробуйте еще раз.'
        }
      
      case ErrorCategory.IMPORT_EXPORT:
        if (message.includes('format') || message.includes('parse')) {
          return 'Неподдерживаемый формат файла или ошибка при чтении данных.'
        } else if (message.includes('corrupt') || message.includes('invalid')) {
          return 'Файл поврежден или содержит некорректные данные.'
        } else {
          return 'Ошибка при работе с файлом. Проверьте файл и попробуйте снова.'
        }
      
      case ErrorCategory.VALIDATION:
        return 'Введенные данные не соответствуют требованиям. Проверьте формат и значения.'
      
      case ErrorCategory.NETWORK:
        return 'Ошибка сети. Проверьте подключение и попробуйте снова.'
      
      default:
        return `Произошла ошибка при выполнении операции: ${operation}. Обратитесь к администратору.`
    }
  }
  
  private getRecoverySuggestions(error: Error, category: ErrorCategory): string[] {
    const suggestions: string[] = []
    const message = error.message.toLowerCase()
    
    // Generic suggestions based on error type
    if (message.includes('not found')) {
      suggestions.push('Проверьте путь к файлу', 'Убедитесь, что файл существует')
    } else if (message.includes('permission') || message.includes('access')) {
      suggestions.push('Проверьте права доступа', 'Обратитесь к администратору')
    } else if (error instanceof TypeError || error instanceof RangeError) {
      suggestions.push('Проверьте формат введенных данных', 'Убедитесь в корректности значений')
    }
    
    // Category-specific suggestions
    switch (category) {
      case ErrorCategory.CALCULATION:
        suggestions.push(
          'Проверьте числовые значения в полях',
          'Убедитесь, что все обязательные поля заполнены'
        )
        break
      case ErrorCategory.IMPORT_EXPORT:
        suggestions.push(
          'Проверьте формат файла',
          'Убедитесь, что файл не поврежден'
        )
        break
      case ErrorCategory.COMMAND_EXECUTION:
        suggestions.push(
          'Обновите форму и попробуйте снова',
          'Проверьте, что операция доступна в текущем контексте'
        )
        break
      case ErrorCategory.NETWORK:
        suggestions.push(
          'Проверьте подключение к интернету',
          'Попробуйте повторить операцию через некоторое время'
        )
        break
    }
    
    return suggestions
  }
  
  private canRetry(error: Error, category: ErrorCategory): boolean {
    const message = error.message.toLowerCase()
    
    // Never retry critical system errors
    if (error.name === 'OutOfMemoryError' || message.includes('out of memory')) {
      return false
    }
    
    // Retry transient errors
    if (message.includes('temporarily unavailable') || message.includes('timeout')) {
      return true
    }
    
    // Category-specific retry logic
    switch (category) {
      case ErrorCategory.CALCULATION:
      case ErrorCategory.VALIDATION:
        return true
      case ErrorCategory.IMPORT_EXPORT:
        return !message.includes('not found') && !message.includes('permission')
      case ErrorCategory.COMMAND_EXECUTION:
        return !message.includes('not found') && !message.includes('undefined')
      case ErrorCategory.NETWORK:
        return true
      default:
        return false
    }
  }
  
  private logError(errorInfo: ErrorInfo): void {
    const logMessage = `[${errorInfo.category}] ${errorInfo.message}`
    
    const contextInfo = errorInfo.context 
      ? ` | Operation: ${errorInfo.context.operation} | Component: ${errorInfo.context.component}`
      : ''
    
    const fullMessage = logMessage + contextInfo
    
    switch (errorInfo.severity) {
      case ErrorSeverity.CRITICAL:
        console.error('CRITICAL:', fullMessage, errorInfo.technicalDetails)
        break
      case ErrorSeverity.ERROR:
        console.error('ERROR:', fullMessage)
        break
      case ErrorSeverity.WARNING:
        console.warn('WARNING:', fullMessage)
        break
      default:
        console.info('INFO:', fullMessage)
        break
    }
  }
  
  private addToHistory(errorInfo: ErrorInfo): void {
    this.errorHistory.push(errorInfo)
    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory.shift()
    }
  }
  
  private findErrorById(errorId: string): ErrorInfo | undefined {
    return this.errorHistory.find(error => error.id === errorId)
  }
  
  private async attemptAutomaticRecovery(errorInfo: ErrorInfo): Promise<boolean> {
    const recoveryActions = this.recoveryActions.get(errorInfo.category) || []
    const automaticActions = recoveryActions.filter(action => action.automatic)
    
    // Sort by priority
    automaticActions.sort((a, b) => a.priority - b.priority)
    
    for (const action of automaticActions) {
      try {
        const result = await action.action()
        if (result) {
          console.log(`Automatic recovery successful: ${action.name}`)
          this.callbacks.onErrorRecovered?.(errorInfo.id, action.name)
          return true
        }
      } catch (e) {
        console.warn(`Automatic recovery failed for ${action.name}:`, e)
      }
    }
    
    return false
  }
  
  private showErrorToUser(errorInfo: ErrorInfo): void {
    // Use callback to show error to user (implementation depends on UI framework)
    this.callbacks.onShowUserMessage?.(errorInfo)
  }
}

// ============================================================================
// Factory Functions and Utilities
// ============================================================================

/**
 * Create an error handler with default configuration
 */
export function createErrorHandler(callbacks?: ErrorHandlerCallbacks): TablePartErrorHandler {
  return new TablePartErrorHandler(callbacks)
}

/**
 * Decorator for automatic error handling in TypeScript methods
 */
export function handleTablePartErrors(
  category: ErrorCategory,
  operation: string,
  component: string,
  showToUser = true
) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value
    
    descriptor.value = async function (...args: any[]) {
      try {
        return await originalMethod.apply(this, args)
      } catch (error) {
        // Get error handler from instance or create new one
        const errorHandler = this.errorHandler || createErrorHandler()
        
        // Handle the error
        await errorHandler.handleError(
          error as Error,
          category,
          operation,
          component,
          propertyKey,
          undefined,
          showToUser
        )
        
        // Re-throw for caller to handle if needed
        throw error
      }
    }
    
    return descriptor
  }
}

// ============================================================================
// Vue Composable
// ============================================================================

/**
 * Vue composable for using the error handler
 */
export function useErrorHandler(callbacks?: ErrorHandlerCallbacks) {
  const errorHandler = ref<TablePartErrorHandler | null>(null)
  const errorHistory = ref<ErrorInfo[]>([])
  const hasErrors = ref(false)
  
  const initializeErrorHandler = () => {
    errorHandler.value = createErrorHandler({
      ...callbacks,
      onErrorOccurred: (error) => {
        errorHistory.value = errorHandler.value?.getErrorHistory() || []
        hasErrors.value = errorHistory.value.length > 0
        callbacks?.onErrorOccurred?.(error)
      },
      onErrorRecovered: (errorId, recoveryMethod) => {
        console.log(`Error ${errorId} recovered using ${recoveryMethod}`)
        callbacks?.onErrorRecovered?.(errorId, recoveryMethod)
      }
    })
  }
  
  const handleError = async (
    error: Error,
    category: ErrorCategory,
    operation: string,
    component: string,
    userAction?: string,
    dataContext?: Record<string, any>,
    showToUser = true
  ) => {
    if (!errorHandler.value) {
      throw new Error('Error handler not initialized')
    }
    
    return errorHandler.value.handleError(
      error,
      category,
      operation,
      component,
      userAction,
      dataContext,
      showToUser
    )
  }
  
  const retryOperation = async (errorId: string) => {
    if (!errorHandler.value) {
      return false
    }
    
    return errorHandler.value.retryOperation(errorId)
  }
  
  const clearErrors = () => {
    errorHandler.value?.clearErrorHistory()
    errorHistory.value = []
    hasErrors.value = false
  }
  
  return {
    errorHandler,
    errorHistory,
    hasErrors,
    initializeErrorHandler,
    handleError,
    retryOperation,
    clearErrors
  }
}