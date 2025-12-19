/**
 * Input validation service for table parts.
 * 
 * This module provides comprehensive validation for table part fields,
 * including calculation fields, reference fields, and data integrity checks.
 * 
 * Requirements: 13.2 - Add input validation
 */

import { ref, reactive } from 'vue'
import { TablePartErrorHandler, ErrorCategory } from './tablePartErrorHandler'

// ============================================================================
// Types and Interfaces
// ============================================================================

export enum ValidationType {
  REQUIRED = 'required',
  DATA_TYPE = 'data_type',
  RANGE = 'range',
  LENGTH = 'length',
  PATTERN = 'pattern',
  CUSTOM = 'custom',
  REFERENCE = 'reference',
  CALCULATION = 'calculation',
  UNIQUE = 'unique',
  DEPENDENCY = 'dependency'
}

export enum ValidationSeverity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

export interface ValidationRule {
  id: string
  fieldName: string
  validationType: ValidationType
  severity: ValidationSeverity
  message?: string
  parameters: Record<string, any>
  customValidator?: (value: any, rowData: Record<string, any>) => boolean
  enabled: boolean
  dependsOn: string[]
}

export interface ValidationResult {
  fieldName: string
  ruleId: string
  isValid: boolean
  severity: ValidationSeverity
  message: string
  suggestedValue?: any
  additionalInfo: Record<string, any>
}

export interface ValidationContext {
  rowData: Record<string, any>
  allData: Record<string, any>[]
  fieldDefinitions: Record<string, Record<string, any>>
  currentRowIndex?: number
  operation: string
}

export interface ValidationCallbacks {
  onValidationCompleted?: (fieldName: string, results: ValidationResult[]) => void
  onValidationFailed?: (fieldName: string, result: ValidationResult) => void
  onValidationWarning?: (fieldName: string, result: ValidationResult) => void
}

// ============================================================================
// Validation Service Class
// ============================================================================

export class TablePartValidationService {
  private validationRules: Map<string, ValidationRule[]> = new Map()
  private fieldDefinitions: Map<string, Record<string, any>> = new Map()
  private errorHandler?: TablePartErrorHandler
  private callbacks: ValidationCallbacks = {}
  
  constructor(errorHandler?: TablePartErrorHandler, callbacks?: ValidationCallbacks) {
    this.errorHandler = errorHandler
    this.callbacks = callbacks || {}
    this.setupStandardRules()
  }
  
  /**
   * Add field definition for validation
   */
  addFieldDefinition(fieldName: string, definition: Record<string, any>): void {
    this.fieldDefinitions.set(fieldName, definition)
    this.generateRulesFromDefinition(fieldName, definition)
  }
  
  /**
   * Add a validation rule for a field
   */
  addValidationRule(rule: ValidationRule): void {
    if (!this.validationRules.has(rule.fieldName)) {
      this.validationRules.set(rule.fieldName, [])
    }
    this.validationRules.get(rule.fieldName)!.push(rule)
  }
  
  /**
   * Remove a validation rule
   */
  removeValidationRule(fieldName: string, ruleId: string): void {
    const rules = this.validationRules.get(fieldName)
    if (rules) {
      const filteredRules = rules.filter(rule => rule.id !== ruleId)
      this.validationRules.set(fieldName, filteredRules)
    }
  }
  
  /**
   * Validate a single field value
   */
  async validateField(
    fieldName: string,
    value: any,
    context: ValidationContext
  ): Promise<ValidationResult[]> {
    const results: ValidationResult[] = []
    
    // Get validation rules for the field
    const rules = this.validationRules.get(fieldName) || []
    
    for (const rule of rules) {
      if (!rule.enabled) {
        continue
      }
      
      // Check dependencies
      if (rule.dependsOn.length > 0 && !this.checkDependencies(rule.dependsOn, context)) {
        continue
      }
      
      try {
        const result = await this.executeValidationRule(rule, value, context)
        if (result) {
          results.push(result)
          
          // Emit callbacks based on severity
          if (result.severity === ValidationSeverity.ERROR) {
            this.callbacks.onValidationFailed?.(fieldName, result)
          } else if (result.severity === ValidationSeverity.WARNING) {
            this.callbacks.onValidationWarning?.(fieldName, result)
          }
        }
      } catch (error) {
        if (this.errorHandler) {
          await this.errorHandler.handleValidationError(
            error as Error,
            fieldName,
            value,
            rule.id
          )
        }
        
        // Create error result
        const errorResult: ValidationResult = {
          fieldName,
          ruleId: rule.id,
          isValid: false,
          severity: ValidationSeverity.ERROR,
          message: `Ошибка валидации: ${error instanceof Error ? error.message : String(error)}`,
          additionalInfo: {}
        }
        results.push(errorResult)
      }
    }
    
    // Emit completion callback
    this.callbacks.onValidationCompleted?.(fieldName, results)
    
    return results
  }
  
  /**
   * Validate all fields in a row
   */
  async validateRow(context: ValidationContext): Promise<Record<string, ValidationResult[]>> {
    const allResults: Record<string, ValidationResult[]> = {}
    
    for (const [fieldName, value] of Object.entries(context.rowData)) {
      const results = await this.validateField(fieldName, value, context)
      if (results.length > 0) {
        allResults[fieldName] = results
      }
    }
    
    return allResults
  }
  
  /**
   * Validate calculation field values and dependencies
   */
  async validateCalculationFields(
    context: ValidationContext,
    calculationRules: Array<Record<string, any>>
  ): Promise<ValidationResult[]> {
    const results: ValidationResult[] = []
    
    for (const rule of calculationRules) {
      const sourceColumns = rule.sourceColumns || []
      const targetColumn = rule.targetColumn
      
      if (!targetColumn) {
        continue
      }
      
      // Validate source columns have valid numeric values
      for (const sourceCol of sourceColumns) {
        const value = context.rowData[sourceCol]
        
        if (value !== null && value !== undefined && value !== '') {
          if (isNaN(Number(value))) {
            const result: ValidationResult = {
              fieldName: sourceCol,
              ruleId: `calc_source_${rule.id || 'unknown'}`,
              isValid: false,
              severity: ValidationSeverity.ERROR,
              message: `Поле '${sourceCol}' должно содержать числовое значение для расчета`,
              additionalInfo: {}
            }
            results.push(result)
          }
        }
      }
      
      // Validate target column is not manually edited if auto-calculated
      if (rule.autoCalculate !== false) {
        const targetValue = context.rowData[targetColumn]
        if (targetValue !== null && targetValue !== undefined) {
          // Check if value matches expected calculation
          const expectedValue = this.calculateExpectedValue(rule, context.rowData)
          if (expectedValue !== null && Math.abs(Number(targetValue) - expectedValue) > 0.01) {
            const result: ValidationResult = {
              fieldName: targetColumn,
              ruleId: `calc_target_${rule.id || 'unknown'}`,
              isValid: false,
              severity: ValidationSeverity.WARNING,
              message: `Значение поля '${targetColumn}' не соответствует расчету`,
              suggestedValue: expectedValue,
              additionalInfo: {}
            }
            results.push(result)
          }
        }
      }
    }
    
    return results
  }
  
  /**
   * Validate reference field value
   */
  async validateReferenceField(
    fieldName: string,
    referenceId: any,
    referenceType: string,
    context: ValidationContext
  ): Promise<ValidationResult[]> {
    const results: ValidationResult[] = []
    
    if (referenceId === null || referenceId === undefined || referenceId === '') {
      // Check if field is required
      const fieldDef = this.fieldDefinitions.get(fieldName) || {}
      if (fieldDef.required) {
        const result: ValidationResult = {
          fieldName,
          ruleId: `ref_required_${fieldName}`,
          isValid: false,
          severity: ValidationSeverity.ERROR,
          message: `Поле '${fieldName}' обязательно для заполнения`,
          additionalInfo: {}
        }
        results.push(result)
      }
      return results
    }
    
    // Validate reference exists and is accessible
    try {
      // Basic format validation
      if (typeof referenceId !== 'number' && typeof referenceId !== 'string') {
        const result: ValidationResult = {
          fieldName,
          ruleId: `ref_format_${fieldName}`,
          isValid: false,
          severity: ValidationSeverity.ERROR,
          message: `Некорректный формат ссылки в поле '${fieldName}'`,
          additionalInfo: {}
        }
        results.push(result)
      } else if (String(referenceId).trim() === '') {
        const result: ValidationResult = {
          fieldName,
          ruleId: `ref_empty_${fieldName}`,
          isValid: false,
          severity: ValidationSeverity.ERROR,
          message: `Пустая ссылка в поле '${fieldName}'`,
          additionalInfo: {}
        }
        results.push(result)
      }
      
      // Additional reference-specific validation could be added here
      // e.g., checking if the referenced object exists, is active, etc.
      
    } catch (error) {
      if (this.errorHandler) {
        await this.errorHandler.handleValidationError(
          error as Error,
          fieldName,
          referenceId,
          `reference_${referenceType}`
        )
      }
      
      const result: ValidationResult = {
        fieldName,
        ruleId: `ref_error_${fieldName}`,
        isValid: false,
        severity: ValidationSeverity.ERROR,
        message: `Ошибка проверки ссылки в поле '${fieldName}'`,
        additionalInfo: {}
      }
      results.push(result)
    }
    
    return results
  }
  
  /**
   * Validate data integrity across all rows
   */
  async validateDataIntegrity(
    allData: Array<Record<string, any>>,
    integrityRules: Array<Record<string, any>>
  ): Promise<ValidationResult[]> {
    const results: ValidationResult[] = []
    
    for (const rule of integrityRules) {
      const ruleType = rule.type
      
      if (ruleType === 'unique') {
        results.push(...this.validateUniqueness(allData, rule))
      } else if (ruleType === 'sum_constraint') {
        results.push(...this.validateSumConstraint(allData, rule))
      } else if (ruleType === 'dependency') {
        results.push(...this.validateDependencies(allData, rule))
      }
    }
    
    return results
  }
  
  /**
   * Get summary of validation results
   */
  getValidationSummary(results: Record<string, ValidationResult[]>): Record<string, number> {
    const summary = {
      totalFields: Object.keys(results).length,
      fieldsWithErrors: 0,
      fieldsWithWarnings: 0,
      totalErrors: 0,
      totalWarnings: 0,
      totalInfo: 0
    }
    
    for (const fieldResults of Object.values(results)) {
      let hasError = false
      let hasWarning = false
      
      for (const result of fieldResults) {
        if (result.severity === ValidationSeverity.ERROR) {
          summary.totalErrors++
          hasError = true
        } else if (result.severity === ValidationSeverity.WARNING) {
          summary.totalWarnings++
          hasWarning = true
        } else if (result.severity === ValidationSeverity.INFO) {
          summary.totalInfo++
        }
      }
      
      if (hasError) {
        summary.fieldsWithErrors++
      } else if (hasWarning) {
        summary.fieldsWithWarnings++
      }
    }
    
    return summary
  }
  
  /**
   * Set validation callbacks
   */
  setCallbacks(callbacks: ValidationCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }
  
  // ============================================================================
  // Private Methods
  // ============================================================================
  
  private setupStandardRules(): void {
    // Standard numeric field validation
    this.addValidationRule({
      id: 'numeric_format',
      fieldName: '*', // Applies to all numeric fields
      validationType: ValidationType.DATA_TYPE,
      severity: ValidationSeverity.ERROR,
      message: 'Поле должно содержать числовое значение',
      parameters: { dataType: 'numeric' },
      enabled: true,
      dependsOn: []
    })
    
    // Standard date field validation
    this.addValidationRule({
      id: 'date_format',
      fieldName: '*', // Applies to all date fields
      validationType: ValidationType.DATA_TYPE,
      severity: ValidationSeverity.ERROR,
      message: 'Поле должно содержать корректную дату',
      parameters: { dataType: 'date' },
      enabled: true,
      dependsOn: []
    })
  }
  
  private generateRulesFromDefinition(fieldName: string, definition: Record<string, any>): void {
    // Required field rule
    if (definition.required) {
      this.addValidationRule({
        id: `required_${fieldName}`,
        fieldName,
        validationType: ValidationType.REQUIRED,
        severity: ValidationSeverity.ERROR,
        message: `Поле '${fieldName}' обязательно для заполнения`,
        parameters: {},
        enabled: true,
        dependsOn: []
      })
    }
    
    // Data type rule
    const dataType = definition.dataType
    if (dataType) {
      this.addValidationRule({
        id: `type_${fieldName}`,
        fieldName,
        validationType: ValidationType.DATA_TYPE,
        severity: ValidationSeverity.ERROR,
        message: `Поле '${fieldName}' должно быть типа ${dataType}`,
        parameters: { dataType },
        enabled: true,
        dependsOn: []
      })
    }
    
    // Range validation for numeric fields
    if (['int', 'float', 'number'].includes(dataType)) {
      const minValue = definition.minValue
      const maxValue = definition.maxValue
      
      if (minValue !== undefined || maxValue !== undefined) {
        this.addValidationRule({
          id: `range_${fieldName}`,
          fieldName,
          validationType: ValidationType.RANGE,
          severity: ValidationSeverity.ERROR,
          message: `Значение поля '${fieldName}' вне допустимого диапазона`,
          parameters: { minValue, maxValue },
          enabled: true,
          dependsOn: []
        })
      }
    }
    
    // Length validation for string fields
    if (dataType === 'string') {
      const maxLength = definition.maxLength
      if (maxLength) {
        this.addValidationRule({
          id: `length_${fieldName}`,
          fieldName,
          validationType: ValidationType.LENGTH,
          severity: ValidationSeverity.ERROR,
          message: `Длина поля '${fieldName}' не должна превышать ${maxLength} символов`,
          parameters: { maxLength },
          enabled: true,
          dependsOn: []
        })
      }
    }
    
    // Pattern validation
    const pattern = definition.pattern
    if (pattern) {
      this.addValidationRule({
        id: `pattern_${fieldName}`,
        fieldName,
        validationType: ValidationType.PATTERN,
        severity: ValidationSeverity.ERROR,
        message: `Поле '${fieldName}' не соответствует требуемому формату`,
        parameters: { pattern },
        enabled: true,
        dependsOn: []
      })
    }
  }
  
  private async executeValidationRule(
    rule: ValidationRule,
    value: any,
    context: ValidationContext
  ): Promise<ValidationResult | null> {
    switch (rule.validationType) {
      case ValidationType.REQUIRED:
        return this.validateRequired(rule, value, context)
      case ValidationType.DATA_TYPE:
        return this.validateDataType(rule, value, context)
      case ValidationType.RANGE:
        return this.validateRange(rule, value, context)
      case ValidationType.LENGTH:
        return this.validateLength(rule, value, context)
      case ValidationType.PATTERN:
        return this.validatePattern(rule, value, context)
      case ValidationType.CUSTOM:
        return this.validateCustom(rule, value, context)
      default:
        return null
    }
  }
  
  private validateRequired(
    rule: ValidationRule,
    value: any,
    context: ValidationContext
  ): ValidationResult | null {
    if (value === null || value === undefined || value === '' || 
        (typeof value === 'string' && value.trim() === '')) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: rule.message || `Поле '${rule.fieldName}' обязательно для заполнения`,
        additionalInfo: {}
      }
    }
    return null
  }
  
  private validateDataType(
    rule: ValidationRule,
    value: any,
    context: ValidationContext
  ): ValidationResult | null {
    if (value === null || value === undefined || value === '') {
      return null // Empty values are handled by required validation
    }
    
    const dataType = rule.parameters.dataType
    
    try {
      if (dataType === 'int' || dataType === 'integer') {
        const num = Number(value)
        if (isNaN(num) || !Number.isInteger(num)) {
          throw new Error('Not an integer')
        }
      } else if (dataType === 'float' || dataType === 'number' || dataType === 'numeric') {
        const num = Number(value)
        if (isNaN(num)) {
          throw new Error('Not a number')
        }
      } else if (dataType === 'date') {
        if (typeof value === 'string') {
          const date = new Date(value)
          if (isNaN(date.getTime())) {
            throw new Error('Invalid date')
          }
        } else if (!(value instanceof Date)) {
          throw new Error('Invalid date type')
        }
      } else if (dataType === 'boolean') {
        if (typeof value !== 'boolean' && 
            !['true', 'false', '1', '0'].includes(String(value).toLowerCase())) {
          throw new Error('Invalid boolean value')
        }
      }
    } catch (error) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: rule.message || `Поле '${rule.fieldName}' должно быть типа ${dataType}`,
        additionalInfo: {}
      }
    }
    
    return null
  }
  
  private validateRange(
    rule: ValidationRule,
    value: any,
    context: ValidationContext
  ): ValidationResult | null {
    if (value === null || value === undefined || value === '') {
      return null
    }
    
    const numericValue = Number(value)
    if (isNaN(numericValue)) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: `Поле '${rule.fieldName}' должно содержать числовое значение`,
        additionalInfo: {}
      }
    }
    
    const minValue = rule.parameters.minValue
    const maxValue = rule.parameters.maxValue
    
    if (minValue !== undefined && numericValue < minValue) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: `Значение поля '${rule.fieldName}' должно быть не менее ${minValue}`,
        additionalInfo: {}
      }
    }
    
    if (maxValue !== undefined && numericValue > maxValue) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: `Значение поля '${rule.fieldName}' должно быть не более ${maxValue}`,
        additionalInfo: {}
      }
    }
    
    return null
  }
  
  private validateLength(
    rule: ValidationRule,
    value: any,
    context: ValidationContext
  ): ValidationResult | null {
    if (value === null || value === undefined) {
      return null
    }
    
    const strValue = String(value)
    const maxLength = rule.parameters.maxLength
    const minLength = rule.parameters.minLength || 0
    
    if (strValue.length < minLength) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: `Длина поля '${rule.fieldName}' должна быть не менее ${minLength} символов`,
        additionalInfo: {}
      }
    }
    
    if (maxLength && strValue.length > maxLength) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: `Длина поля '${rule.fieldName}' не должна превышать ${maxLength} символов`,
        additionalInfo: {}
      }
    }
    
    return null
  }
  
  private validatePattern(
    rule: ValidationRule,
    value: any,
    context: ValidationContext
  ): ValidationResult | null {
    if (value === null || value === undefined || value === '') {
      return null
    }
    
    const pattern = rule.parameters.pattern
    if (!pattern) {
      return null
    }
    
    const strValue = String(value)
    const regex = new RegExp(pattern)
    
    if (!regex.test(strValue)) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: rule.severity,
        message: rule.message || `Поле '${rule.fieldName}' не соответствует требуемому формату`,
        additionalInfo: {}
      }
    }
    
    return null
  }
  
  private validateCustom(
    rule: ValidationRule,
    value: any,
    context: ValidationContext
  ): ValidationResult | null {
    if (!rule.customValidator) {
      return null
    }
    
    try {
      const isValid = rule.customValidator(value, context.rowData)
      if (!isValid) {
        return {
          fieldName: rule.fieldName,
          ruleId: rule.id,
          isValid: false,
          severity: rule.severity,
          message: rule.message || `Поле '${rule.fieldName}' не прошло проверку`,
          additionalInfo: {}
        }
      }
    } catch (error) {
      return {
        fieldName: rule.fieldName,
        ruleId: rule.id,
        isValid: false,
        severity: ValidationSeverity.ERROR,
        message: `Ошибка при выполнении проверки: ${error instanceof Error ? error.message : String(error)}`,
        additionalInfo: {}
      }
    }
    
    return null
  }
  
  private checkDependencies(dependsOn: string[], context: ValidationContext): boolean {
    for (const depField of dependsOn) {
      const value = context.rowData[depField]
      if (value === null || value === undefined || value === '') {
        return false
      }
    }
    return true
  }
  
  private calculateExpectedValue(rule: Record<string, any>, rowData: Record<string, any>): number | null {
    const calculationType = rule.calculationType || 'multiply'
    const sourceColumns = rule.sourceColumns || []
    
    if (calculationType === 'multiply' && sourceColumns.length >= 2) {
      try {
        let result = 1
        for (const col of sourceColumns) {
          const value = rowData[col]
          if (value === null || value === undefined || value === '') {
            return null
          }
          result *= Number(value)
        }
        return result
      } catch (error) {
        return null
      }
    }
    
    return null
  }
  
  private validateUniqueness(
    allData: Array<Record<string, any>>,
    rule: Record<string, any>
  ): ValidationResult[] {
    const results: ValidationResult[] = []
    const fieldName = rule.field
    
    if (!fieldName) {
      return results
    }
    
    const seenValues: Map<any, number> = new Map()
    
    for (let i = 0; i < allData.length; i++) {
      const row = allData[i]
      const value = row[fieldName]
      
      if (value !== null && value !== undefined && value !== '') {
        if (seenValues.has(value)) {
          const result: ValidationResult = {
            fieldName,
            ruleId: `unique_${fieldName}`,
            isValid: false,
            severity: ValidationSeverity.ERROR,
            message: `Значение '${value}' в поле '${fieldName}' должно быть уникальным`,
            additionalInfo: { duplicateRows: [seenValues.get(value), i] }
          }
          results.push(result)
        } else {
          seenValues.set(value, i)
        }
      }
    }
    
    return results
  }
  
  private validateSumConstraint(
    allData: Array<Record<string, any>>,
    rule: Record<string, any>
  ): ValidationResult[] {
    const results: ValidationResult[] = []
    const fieldName = rule.field
    const maxSum = rule.maxSum
    const minSum = rule.minSum
    
    if (!fieldName) {
      return results
    }
    
    try {
      const total = allData.reduce((sum, row) => {
        const value = row[fieldName]
        return sum + (Number(value) || 0)
      }, 0)
      
      if (maxSum !== undefined && total > maxSum) {
        const result: ValidationResult = {
          fieldName,
          ruleId: `sum_max_${fieldName}`,
          isValid: false,
          severity: ValidationSeverity.ERROR,
          message: `Общая сумма по полю '${fieldName}' (${total}) превышает максимум (${maxSum})`,
          additionalInfo: { currentSum: total, maxSum }
        }
        results.push(result)
      }
      
      if (minSum !== undefined && total < minSum) {
        const result: ValidationResult = {
          fieldName,
          ruleId: `sum_min_${fieldName}`,
          isValid: false,
          severity: ValidationSeverity.WARNING,
          message: `Общая сумма по полю '${fieldName}' (${total}) меньше минимума (${minSum})`,
          additionalInfo: { currentSum: total, minSum }
        }
        results.push(result)
      }
    } catch (error) {
      const result: ValidationResult = {
        fieldName,
        ruleId: `sum_error_${fieldName}`,
        isValid: false,
        severity: ValidationSeverity.ERROR,
        message: `Ошибка при расчете суммы по полю '${fieldName}': ${error instanceof Error ? error.message : String(error)}`,
        additionalInfo: {}
      }
      results.push(result)
    }
    
    return results
  }
  
  private validateDependencies(
    allData: Array<Record<string, any>>,
    rule: Record<string, any>
  ): ValidationResult[] {
    const results: ValidationResult[] = []
    // Implementation would depend on specific dependency rules
    // This is a placeholder for complex dependency validation
    return results
  }
}

// ============================================================================
// Factory Functions and Utilities
// ============================================================================

/**
 * Create a validation service with default configuration
 */
export function createValidationService(
  errorHandler?: TablePartErrorHandler,
  callbacks?: ValidationCallbacks
): TablePartValidationService {
  return new TablePartValidationService(errorHandler, callbacks)
}

/**
 * Common validation functions
 */
export function validateNumericField(
  value: any,
  allowNegative = true,
  precision = 2
): { isValid: boolean; message?: string } {
  if (value === null || value === undefined || value === '') {
    return { isValid: true }
  }
  
  const numericValue = Number(value)
  
  if (isNaN(numericValue)) {
    return { isValid: false, message: 'Значение должно быть числом' }
  }
  
  if (!allowNegative && numericValue < 0) {
    return { isValid: false, message: 'Значение не может быть отрицательным' }
  }
  
  // Check precision
  const decimalPlaces = (String(numericValue).split('.')[1] || '').length
  if (decimalPlaces > precision) {
    return { isValid: false, message: `Слишком много знаков после запятой (максимум ${precision})` }
  }
  
  return { isValid: true }
}

export function validateDateField(
  value: any,
  allowFuture = true,
  allowPast = true
): { isValid: boolean; message?: string } {
  if (value === null || value === undefined || value === '') {
    return { isValid: true }
  }
  
  let parsedDate: Date
  
  try {
    if (typeof value === 'string') {
      parsedDate = new Date(value)
    } else if (value instanceof Date) {
      parsedDate = value
    } else {
      return { isValid: false, message: 'Неверный формат даты' }
    }
    
    if (isNaN(parsedDate.getTime())) {
      return { isValid: false, message: 'Неверный формат даты' }
    }
    
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    parsedDate.setHours(0, 0, 0, 0)
    
    if (!allowFuture && parsedDate > today) {
      return { isValid: false, message: 'Дата не может быть в будущем' }
    }
    
    if (!allowPast && parsedDate < today) {
      return { isValid: false, message: 'Дата не может быть в прошлом' }
    }
    
    return { isValid: true }
  } catch (error) {
    return { isValid: false, message: 'Неверный формат даты' }
  }
}

export function validateReferenceField(
  value: any,
  required = false
): { isValid: boolean; message?: string } {
  if (value === null || value === undefined || value === '') {
    if (required) {
      return { isValid: false, message: 'Поле обязательно для заполнения' }
    }
    return { isValid: true }
  }
  
  // Basic validation - in real implementation would check if reference exists
  if (typeof value !== 'number' && typeof value !== 'string') {
    return { isValid: false, message: 'Некорректное значение ссылки' }
  }
  
  if (String(value).trim() === '') {
    return { isValid: false, message: 'Некорректное значение ссылки' }
  }
  
  return { isValid: true }
}

// ============================================================================
// Vue Composable
// ============================================================================

/**
 * Vue composable for using the validation service
 */
export function useValidationService(
  errorHandler?: TablePartErrorHandler,
  callbacks?: ValidationCallbacks
) {
  const validationService = ref<TablePartValidationService | null>(null)
  const validationResults = ref<Record<string, ValidationResult[]>>({})
  const hasValidationErrors = ref(false)
  const validationSummary = ref<Record<string, number>>({})
  
  const initializeValidationService = () => {
    validationService.value = createValidationService(errorHandler, {
      ...callbacks,
      onValidationCompleted: (fieldName, results) => {
        if (results.length > 0) {
          validationResults.value[fieldName] = results
        } else {
          delete validationResults.value[fieldName]
        }
        
        // Update summary
        validationSummary.value = validationService.value?.getValidationSummary(validationResults.value) || {}
        hasValidationErrors.value = validationSummary.value.totalErrors > 0
        
        callbacks?.onValidationCompleted?.(fieldName, results)
      }
    })
  }
  
  const validateField = async (
    fieldName: string,
    value: any,
    context: ValidationContext
  ) => {
    if (!validationService.value) {
      throw new Error('Validation service not initialized')
    }
    
    return validationService.value.validateField(fieldName, value, context)
  }
  
  const validateRow = async (context: ValidationContext) => {
    if (!validationService.value) {
      throw new Error('Validation service not initialized')
    }
    
    const results = await validationService.value.validateRow(context)
    validationResults.value = { ...validationResults.value, ...results }
    
    // Update summary
    validationSummary.value = validationService.value.getValidationSummary(validationResults.value)
    hasValidationErrors.value = validationSummary.value.totalErrors > 0
    
    return results
  }
  
  const clearValidationResults = (fieldName?: string) => {
    if (fieldName) {
      delete validationResults.value[fieldName]
    } else {
      validationResults.value = {}
    }
    
    // Update summary
    if (validationService.value) {
      validationSummary.value = validationService.value.getValidationSummary(validationResults.value)
      hasValidationErrors.value = validationSummary.value.totalErrors > 0
    }
  }
  
  return {
    validationService,
    validationResults,
    hasValidationErrors,
    validationSummary,
    initializeValidationService,
    validateField,
    validateRow,
    clearValidationResults
  }
}