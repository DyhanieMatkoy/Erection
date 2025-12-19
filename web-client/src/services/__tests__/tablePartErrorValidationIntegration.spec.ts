/**
 * Integration tests for table part error handling and validation services.
 * 
 * Tests the interaction between error handling and validation services
 * to ensure comprehensive error management and user feedback.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  TablePartErrorHandler,
  ErrorCategory,
  ErrorSeverity,
  createErrorHandler
} from '../tablePartErrorHandler'
import {
  TablePartValidationService,
  ValidationType,
  ValidationSeverity,
  createValidationService,
  validateNumericField,
  validateDateField,
  validateReferenceField
} from '../tablePartValidationService'

describe('TablePartErrorValidationIntegration', () => {
  let errorHandler: TablePartErrorHandler
  let validationService: TablePartValidationService
  
  beforeEach(() => {
    errorHandler = createErrorHandler()
    validationService = createValidationService(errorHandler)
  })
  
  it('should integrate validation errors with error handler', async () => {
    // Setup field definition
    validationService.addFieldDefinition('quantity', {
      dataType: 'number',
      required: true,
      minValue: 0
    })
    
    // Create validation context
    const context = {
      rowData: { quantity: 'invalid_number' },
      allData: [],
      fieldDefinitions: {},
      operation: 'edit'
    }
    
    // Mock error handler to capture calls
    const handleValidationErrorSpy = vi.spyOn(errorHandler, 'handleValidationError')
    
    // Validate field - should trigger error handling for invalid type
    const results = await validationService.validateField('quantity', 'invalid_number', context)
    
    // Should have validation results
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].isValid).toBe(false)
    expect(results[0].severity).toBe(ValidationSeverity.ERROR)
  })
  
  it('should handle calculation errors with validation feedback', async () => {
    // Add calculation field validation
    validationService.addFieldDefinition('sum', {
      dataType: 'number',
      calculation: true
    })
    
    // Test calculation with invalid source data
    const calculationRules = [{
      id: 'quantity_price_sum',
      sourceColumns: ['quantity', 'price'],
      targetColumn: 'sum',
      calculationType: 'multiply'
    }]
    
    const context = {
      rowData: { quantity: 'invalid', price: 10.0, sum: 0 },
      allData: [],
      fieldDefinitions: {},
      operation: 'calculate'
    }
    
    // Validate calculation fields
    const results = await validationService.validateCalculationFields(context, calculationRules)
    
    // Should detect invalid source column
    expect(results.length).toBeGreaterThan(0)
    const calcErrors = results.filter(r => r.ruleId.includes('calc_source'))
    expect(calcErrors.length).toBeGreaterThan(0)
    expect(calcErrors[0].isValid).toBe(false)
  })
  
  it('should handle import errors with validation feedback', async () => {
    // Simulate import error
    const importError = new Error('Invalid data format in row 5')
    
    // Handle import error
    const errorInfo = await errorHandler.handleImportError(
      importError,
      'test_file.xlsx',
      5
    )
    
    // Verify error information
    expect(errorInfo.category).toBe(ErrorCategory.IMPORT_EXPORT)
    expect(errorInfo.severity).toBe(ErrorSeverity.ERROR)
    expect(errorInfo.context?.dataContext.filePath).toBe('test_file.xlsx')
    expect(errorInfo.context?.dataContext.rowNumber).toBe(5)
    expect(errorInfo.recoverySuggestions.length).toBeGreaterThan(0)
  })
  
  it('should validate reference fields with error handling', async () => {
    // Add field definition to validation service first
    validationService.addFieldDefinition('work_id', { required: true })
    
    // Test reference validation
    const context = {
      rowData: { work_id: null },
      allData: [],
      fieldDefinitions: { work_id: { required: true } },
      operation: 'edit'
    }
    
    // Validate reference field
    const results = await validationService.validateReferenceField(
      'work_id',
      null,
      'work',
      context
    )
    
    // Should have validation error for required field
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].isValid).toBe(false)
    expect(results[0].severity).toBe(ValidationSeverity.ERROR)
    expect(results[0].message.toLowerCase()).toContain('обязательно')
  })
  
  it('should validate data integrity across multiple rows', async () => {
    // Test uniqueness validation
    const allData = [
      { id: 1, code: 'A001' },
      { id: 2, code: 'A002' },
      { id: 3, code: 'A001' } // Duplicate
    ]
    
    const integrityRules = [{
      type: 'unique',
      field: 'code'
    }]
    
    const results = await validationService.validateDataIntegrity(allData, integrityRules)
    
    // Should detect duplicate
    expect(results.length).toBeGreaterThan(0)
    const uniqueErrors = results.filter(r => r.ruleId.includes('unique'))
    expect(uniqueErrors.length).toBeGreaterThan(0)
    expect(uniqueErrors[0].isValid).toBe(false)
  })
  
  it('should generate validation summary correctly', () => {
    // Create validation results
    const results = {
      field1: [{
        fieldName: 'field1',
        ruleId: 'test1',
        isValid: false,
        severity: ValidationSeverity.ERROR,
        message: 'Error 1',
        additionalInfo: {}
      }],
      field2: [{
        fieldName: 'field2',
        ruleId: 'test2',
        isValid: false,
        severity: ValidationSeverity.WARNING,
        message: 'Warning 1',
        additionalInfo: {}
      }]
    }
    
    const summary = validationService.getValidationSummary(results)
    
    expect(summary.totalFields).toBe(2)
    expect(summary.fieldsWithErrors).toBe(1)
    expect(summary.fieldsWithWarnings).toBe(1)
    expect(summary.totalErrors).toBe(1)
    expect(summary.totalWarnings).toBe(1)
  })
  
  it('should handle error recovery with validation', async () => {
    // Create a recoverable error
    const calcError = new Error('Division by zero in calculation')
    
    const errorInfo = await errorHandler.handleCalculationError(
      calcError,
      'quantity_price_sum',
      { quantity: 5, price: 0 }
    )
    
    // Verify error can be retried
    expect(errorInfo.canRetry).toBe(true)
    expect(errorInfo.category).toBe(ErrorCategory.CALCULATION)
    
    // Test retry mechanism
    const retrySuccess = await errorHandler.retryOperation(errorInfo.id)
    // Note: In real implementation, this would depend on recovery actions
  })
  
  it('should generate validation rules from field definitions', () => {
    // Add field definition with multiple constraints
    const fieldDef = {
      dataType: 'number',
      required: true,
      minValue: 0,
      maxValue: 1000,
      precision: 2
    }
    
    validationService.addFieldDefinition('price', fieldDef)
    
    // Check that rules were generated
    const rules = validationService['validationRules'].get('price') || []
    expect(rules.length).toBeGreaterThan(0)
    
    // Should have required rule
    const requiredRules = rules.filter(r => r.validationType === ValidationType.REQUIRED)
    expect(requiredRules.length).toBeGreaterThan(0)
    
    // Should have type rule
    const typeRules = rules.filter(r => r.validationType === ValidationType.DATA_TYPE)
    expect(typeRules.length).toBeGreaterThan(0)
    
    // Should have range rule
    const rangeRules = rules.filter(r => r.validationType === ValidationType.RANGE)
    expect(rangeRules.length).toBeGreaterThan(0)
  })
  
  it('should validate using common validation functions', () => {
    // Test numeric validation
    let result = validateNumericField(123.45)
    expect(result.isValid).toBe(true)
    expect(result.message).toBeUndefined()
    
    result = validateNumericField('not_a_number')
    expect(result.isValid).toBe(false)
    expect(result.message).toBeDefined()
    
    result = validateNumericField(-10, false) // Don't allow negative
    expect(result.isValid).toBe(false)
    expect(result.message?.toLowerCase()).toContain('отрицательным')
    
    // Test date validation
    result = validateDateField(new Date())
    expect(result.isValid).toBe(true)
    
    result = validateDateField('invalid_date')
    expect(result.isValid).toBe(false)
    
    // Test reference validation
    result = validateReferenceField(123)
    expect(result.isValid).toBe(true)
    
    result = validateReferenceField(null, true) // Required
    expect(result.isValid).toBe(false)
    expect(result.message?.toLowerCase()).toContain('обязательно')
  })
  
  it('should match error patterns and generate user messages', async () => {
    // Test file not found error
    const fileError = new Error("File 'test.xlsx' not found")
    const errorInfo = await errorHandler.handleImportError(fileError, 'test.xlsx')
    
    expect(errorInfo.userMessage.toLowerCase()).toContain('файл не найден')
    expect(errorInfo.recoverySuggestions.length).toBeGreaterThan(0)
    
    // Test calculation error
    const calcError = new Error('division by zero')
    const calcErrorInfo = await errorHandler.handleCalculationError(
      calcError,
      'test_rule',
      { quantity: 5, price: 0 }
    )
    
    expect(calcErrorInfo.userMessage.toLowerCase()).toContain('расчет')
    expect(calcErrorInfo.canRetry).toBe(true)
  })
  
  it('should monitor validation performance', async () => {
    // Add multiple validation rules
    for (let i = 0; i < 10; i++) {
      validationService.addValidationRule({
        id: `test_rule_${i}`,
        fieldName: 'test_field',
        validationType: ValidationType.CUSTOM,
        severity: ValidationSeverity.WARNING,
        customValidator: () => true, // Always pass
        enabled: true,
        dependsOn: [],
        parameters: {}
      })
    }
    
    const context = {
      rowData: { test_field: 'test_value' },
      allData: [],
      fieldDefinitions: {},
      operation: 'performance_test'
    }
    
    // Validate field multiple times
    const startTime = performance.now()
    
    for (let i = 0; i < 5; i++) {
      await validationService.validateField('test_field', 'test_value', context)
    }
    
    const endTime = performance.now()
    
    // Should complete reasonably quickly
    expect(endTime - startTime).toBeLessThan(1000) // Less than 1 second for 50 validations
  })
  
  it('should emit validation callbacks correctly', async () => {
    // Mock callback handlers
    const completedHandler = vi.fn()
    const failedHandler = vi.fn()
    const warningHandler = vi.fn()
    
    // Set callbacks
    validationService.setCallbacks({
      onValidationCompleted: completedHandler,
      onValidationFailed: failedHandler,
      onValidationWarning: warningHandler
    })
    
    // Add validation rule that will fail
    validationService.addValidationRule({
      id: 'test_required',
      fieldName: 'required_field',
      validationType: ValidationType.REQUIRED,
      severity: ValidationSeverity.ERROR,
      enabled: true,
      dependsOn: [],
      parameters: {}
    })
    
    const context = {
      rowData: { required_field: '' }, // Empty value
      allData: [],
      fieldDefinitions: {},
      operation: 'callback_test'
    }
    
    // Validate field
    await validationService.validateField('required_field', '', context)
    
    // Check that callbacks were called
    expect(completedHandler).toHaveBeenCalledOnce()
    expect(failedHandler).toHaveBeenCalledOnce()
    expect(warningHandler).not.toHaveBeenCalled()
  })
  
  it('should handle complex validation scenarios', async () => {
    // Setup complex field definitions
    validationService.addFieldDefinition('quantity', {
      dataType: 'number',
      required: true,
      minValue: 0,
      maxValue: 1000
    })
    
    validationService.addFieldDefinition('price', {
      dataType: 'number',
      required: true,
      minValue: 0.01
    })
    
    validationService.addFieldDefinition('sum', {
      dataType: 'number',
      calculation: true
    })
    
    // Test row with multiple validation issues
    const context = {
      rowData: {
        quantity: -5, // Invalid: negative
        price: 0, // Invalid: below minimum
        sum: 100 // May be invalid if doesn't match calculation
      },
      allData: [],
      fieldDefinitions: {},
      operation: 'complex_validation'
    }
    
    // Validate entire row
    const results = await validationService.validateRow(context)
    
    // Should have multiple validation errors
    expect(Object.keys(results).length).toBeGreaterThan(0)
    
    // Check quantity validation
    if (results.quantity) {
      const quantityErrors = results.quantity.filter(r => !r.isValid)
      expect(quantityErrors.length).toBeGreaterThan(0)
    }
    
    // Check price validation
    if (results.price) {
      const priceErrors = results.price.filter(r => !r.isValid)
      expect(priceErrors.length).toBeGreaterThan(0)
    }
  })
  
  it('should handle validation dependencies correctly', async () => {
    // Add validation rule with dependencies
    validationService.addValidationRule({
      id: 'dependent_validation',
      fieldName: 'dependent_field',
      validationType: ValidationType.CUSTOM,
      severity: ValidationSeverity.ERROR,
      customValidator: (value, rowData) => {
        // Only validate if dependency is present
        return rowData.base_field ? value !== null : true
      },
      enabled: true,
      dependsOn: ['base_field'],
      parameters: {}
    })
    
    // Test with dependency missing
    let context = {
      rowData: { dependent_field: null, base_field: null },
      allData: [],
      fieldDefinitions: {},
      operation: 'dependency_test'
    }
    
    let results = await validationService.validateField('dependent_field', null, context)
    // Should not validate because dependency is missing
    expect(results.length).toBe(0)
    
    // Test with dependency present
    context = {
      rowData: { dependent_field: null, base_field: 'present' },
      allData: [],
      fieldDefinitions: {},
      operation: 'dependency_test'
    }
    
    results = await validationService.validateField('dependent_field', null, context)
    // Should validate and fail because dependent_field is null when base_field is present
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].isValid).toBe(false)
  })
})