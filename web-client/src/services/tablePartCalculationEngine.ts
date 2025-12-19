/**
 * Automatic calculation engine for document table parts.
 * 
 * Provides real-time calculation capabilities including:
 * - Individual field calculations (< 100ms target)
 * - Document total calculations (< 200ms target)
 * - Performance monitoring and error handling
 */

import { ref, reactive } from 'vue'

// ============================================================================
// Types and Interfaces
// ============================================================================

export enum CalculationType {
  MULTIPLY = 'multiply',
  SUM = 'sum',
  AVERAGE = 'average',
  COUNT = 'count',
  MIN = 'min',
  MAX = 'max',
  CUSTOM = 'custom'
}

export interface CalculationRule {
  id: string
  name: string
  sourceColumns: string[]
  targetColumn: string
  calculationType: CalculationType
  formula?: string
  customFunction?: (rowData: Record<string, any>, allData?: Record<string, any>[]) => number | string | boolean
  triggerOnChange: boolean
  dependencies?: string[]
  precision: number
  enabled: boolean
}

export interface CalculationResult {
  success: boolean
  value?: number | string | boolean
  error?: string
  executionTimeMs: number
  ruleId?: string
}

export interface TotalCalculationRule {
  column: string
  calculationType: CalculationType
  customFunction?: (values: number[]) => number
  formatFunction?: (value: number) => string
  precision: number
  enabled: boolean
}

export interface PerformanceMetrics {
  individualCalculationTimeMs: number
  totalCalculationTimeMs: number
  calculationsPerSecond: number
  memoryUsageMb: number
  errorCount: number
  lastCalculationTimestamp?: number
}

export interface TotalResult {
  value: number
  formatted: string
  ruleId: string
}

// ============================================================================
// Calculation Engine Class
// ============================================================================

export class TablePartCalculationEngine {
  private individualTimeoutMs = 100
  private totalTimeoutMs = 200
  private performanceMonitoringEnabled = true
  
  private calculationRules = new Map<string, CalculationRule>()
  private totalRules = new Map<string, TotalCalculationRule>()
  
  private metrics = reactive<PerformanceMetrics>({
    individualCalculationTimeMs: 0,
    totalCalculationTimeMs: 0,
    calculationsPerSecond: 0,
    memoryUsageMb: 0,
    errorCount: 0
  })
  
  private calculationHistory: number[] = []
  private readonly maxHistorySize = 100
  
  private errorRecoveryEnabled = true
  private maxRetryAttempts = 3
  
  // Event callbacks
  private onCalculationCompleted?: (row: number, column: string, result: CalculationResult) => void
  private onTotalCalculationCompleted?: (totals: Record<string, TotalResult>) => void
  private onCalculationError?: (errorType: string, message: string) => void
  private onPerformanceAlert?: (metricName: string, value: number) => void
  
  constructor() {
    this.setupStandardRules()
  }
  
  // ============================================================================
  // Public API
  // ============================================================================
  
  /**
   * Add a calculation rule to the engine
   */
  addCalculationRule(rule: CalculationRule): void {
    this.calculationRules.set(rule.id, rule)
    console.debug(`Added calculation rule: ${rule.id}`)
  }
  
  /**
   * Remove a calculation rule from the engine
   */
  removeCalculationRule(ruleId: string): void {
    if (this.calculationRules.delete(ruleId)) {
      console.debug(`Removed calculation rule: ${ruleId}`)
    }
  }
  
  /**
   * Add a total calculation rule
   */
  addTotalRule(ruleId: string, rule: TotalCalculationRule): void {
    this.totalRules.set(ruleId, rule)
    console.debug(`Added total rule: ${ruleId}`)
  }
  
  /**
   * Remove a total calculation rule
   */
  removeTotalRule(ruleId: string): void {
    if (this.totalRules.delete(ruleId)) {
      console.debug(`Removed total rule: ${ruleId}`)
    }
  }
  
  /**
   * Calculate a single field value based on calculation rules
   */
  async calculateField(
    rowData: Record<string, any>,
    column: string,
    allData?: Record<string, any>[]
  ): Promise<CalculationResult> {
    const startTime = performance.now()
    
    try {
      // Find applicable calculation rules
      const applicableRules = this.findApplicableRules(column)
      
      if (applicableRules.length === 0) {
        return {
          success: true,
          executionTimeMs: performance.now() - startTime
        }
      }
      
      // Execute calculations for each applicable rule
      const results: CalculationResult[] = []
      for (const rule of applicableRules) {
        if (!rule.enabled) continue
        
        const result = await this.executeCalculationRule(rule, rowData, allData)
        if (result.success && result.value !== undefined) {
          // Update row data with calculated value
          rowData[rule.targetColumn] = result.value
          results.push(result)
        } else if (!result.success) {
          console.warn(`Calculation failed for rule ${rule.id}: ${result.error}`)
          this.onCalculationError?.('calculation_error', result.error || 'Unknown error')
        }
      }
      
      const executionTime = performance.now() - startTime
      
      // Update performance metrics
      this.updatePerformanceMetrics(executionTime, false)
      
      // Check performance thresholds
      if (executionTime > this.individualTimeoutMs) {
        this.onPerformanceAlert?.('individual_calculation_timeout', executionTime)
        console.warn(`Individual calculation exceeded timeout: ${executionTime.toFixed(2)}ms`)
      }
      
      // Return the primary result
      let primaryResult: CalculationResult
      
      if (results.length > 0) {
        // Return first successful calculation
        primaryResult = results[0]
      } else if (applicableRules.length > 0) {
        // If we had applicable rules but no successful results, 
        // execute the first rule again to get the error
        const firstRule = applicableRules[0]
        primaryResult = await this.executeCalculationRule(firstRule, rowData, allData)
      } else {
        // No applicable rules, return success
        primaryResult = {
          success: true,
          executionTimeMs: 0
        }
      }
      
      primaryResult.executionTimeMs = executionTime
      
      // Emit completion event
      this.onCalculationCompleted?.(0, column, primaryResult) // Row index would be passed from caller
      
      return primaryResult
      
    } catch (error) {
      const executionTime = performance.now() - startTime
      const errorMsg = `Calculation engine error: ${error instanceof Error ? error.message : String(error)}`
      console.error(errorMsg, error)
      
      this.metrics.errorCount++
      
      return {
        success: false,
        error: errorMsg,
        executionTimeMs: executionTime
      }
    }
  }
  
  /**
   * Calculate document totals based on all table data
   */
  async calculateTotals(allData: Record<string, any>[]): Promise<Record<string, TotalResult>> {
    const startTime = performance.now()
    const totals: Record<string, TotalResult> = {}
    
    try {
      for (const [ruleId, rule] of this.totalRules) {
        if (!rule.enabled) continue
        
        try {
          const totalValue = this.calculateTotalForRule(rule, allData)
          if (totalValue !== null) {
            // Apply formatting if specified
            const formatted = rule.formatFunction 
              ? rule.formatFunction(totalValue)
              : this.formatDecimal(totalValue, rule.precision)
            
            totals[rule.column] = {
              value: totalValue,
              formatted,
              ruleId
            }
          }
        } catch (error) {
          const errorMsg = `Total calculation failed for ${ruleId}: ${error instanceof Error ? error.message : String(error)}`
          console.error(errorMsg)
          this.onCalculationError?.('total_calculation_error', errorMsg)
          this.metrics.errorCount++
        }
      }
      
      const executionTime = performance.now() - startTime
      
      // Update performance metrics
      this.updatePerformanceMetrics(executionTime, true)
      
      // Check performance thresholds
      if (executionTime > this.totalTimeoutMs) {
        this.onPerformanceAlert?.('total_calculation_timeout', executionTime)
        console.warn(`Total calculation exceeded timeout: ${executionTime.toFixed(2)}ms`)
      }
      
      // Emit completion event
      this.onTotalCalculationCompleted?.(totals)
      
      return totals
      
    } catch (error) {
      const executionTime = performance.now() - startTime
      const errorMsg = `Total calculation engine error: ${error instanceof Error ? error.message : String(error)}`
      console.error(errorMsg, error)
      this.onCalculationError?.('total_calculation_error', errorMsg)
      this.metrics.errorCount++
      return {}
    }
  }
  
  /**
   * Get current performance metrics
   */
  getPerformanceMetrics(): PerformanceMetrics {
    return { ...this.metrics }
  }
  
  /**
   * Reset performance metrics
   */
  resetPerformanceMetrics(): void {
    Object.assign(this.metrics, {
      individualCalculationTimeMs: 0,
      totalCalculationTimeMs: 0,
      calculationsPerSecond: 0,
      memoryUsageMb: 0,
      errorCount: 0,
      lastCalculationTimestamp: undefined
    })
    this.calculationHistory.length = 0
  }
  
  /**
   * Set performance thresholds for calculations
   */
  setPerformanceThresholds(individualTimeoutMs: number, totalTimeoutMs: number): void {
    this.individualTimeoutMs = individualTimeoutMs
    this.totalTimeoutMs = totalTimeoutMs
  }
  
  /**
   * Enable or disable performance monitoring
   */
  enablePerformanceMonitoring(enabled: boolean): void {
    this.performanceMonitoringEnabled = enabled
  }
  
  /**
   * Set event callbacks
   */
  setEventCallbacks(callbacks: {
    onCalculationCompleted?: (row: number, column: string, result: CalculationResult) => void
    onTotalCalculationCompleted?: (totals: Record<string, TotalResult>) => void
    onCalculationError?: (errorType: string, message: string) => void
    onPerformanceAlert?: (metricName: string, value: number) => void
  }): void {
    this.onCalculationCompleted = callbacks.onCalculationCompleted
    this.onTotalCalculationCompleted = callbacks.onTotalCalculationCompleted
    this.onCalculationError = callbacks.onCalculationError
    this.onPerformanceAlert = callbacks.onPerformanceAlert
  }
  
  /**
   * Validate all calculation rules and return list of issues
   */
  validateCalculationRules(): string[] {
    const issues: string[] = []
    
    for (const [ruleId, rule] of this.calculationRules) {
      if (!rule.sourceColumns || rule.sourceColumns.length === 0) {
        issues.push(`Rule ${ruleId}: No source columns specified`)
      }
      
      if (!rule.targetColumn) {
        issues.push(`Rule ${ruleId}: No target column specified`)
      }
      
      if (rule.calculationType === CalculationType.CUSTOM && !rule.customFunction) {
        issues.push(`Rule ${ruleId}: Custom calculation type requires customFunction`)
      }
      
      if (rule.calculationType === CalculationType.MULTIPLY && rule.sourceColumns.length < 2) {
        issues.push(`Rule ${ruleId}: Multiply calculation requires at least 2 source columns`)
      }
    }
    
    return issues
  }
  
  // ============================================================================
  // Private Methods
  // ============================================================================
  
  private setupStandardRules(): void {
    // Quantity × Price = Sum calculation
    const quantityPriceRule: CalculationRule = {
      id: 'quantity_price_sum',
      name: 'Quantity × Price Sum',
      sourceColumns: ['quantity', 'price'],
      targetColumn: 'sum',
      calculationType: CalculationType.MULTIPLY,
      triggerOnChange: true,
      precision: 2,
      enabled: true
    }
    this.addCalculationRule(quantityPriceRule)
    
    // Standard total calculations
    const sumTotal: TotalCalculationRule = {
      column: 'sum',
      calculationType: CalculationType.SUM,
      precision: 2,
      enabled: true
    }
    this.addTotalRule('sum_total', sumTotal)
    
    const quantityTotal: TotalCalculationRule = {
      column: 'quantity',
      calculationType: CalculationType.SUM,
      precision: 3,
      enabled: true
    }
    this.addTotalRule('quantity_total', quantityTotal)
  }
  
  private findApplicableRules(changedColumn: string): CalculationRule[] {
    const applicableRules: CalculationRule[] = []
    
    for (const rule of this.calculationRules.values()) {
      if (!rule.triggerOnChange) continue
      
      // Check if the changed column is a source column for this rule
      if (rule.sourceColumns.includes(changedColumn)) {
        applicableRules.push(rule)
      }
      
      // Check dependencies
      if (rule.dependencies && rule.dependencies.includes(changedColumn)) {
        applicableRules.push(rule)
      }
    }
    
    return applicableRules
  }
  
  private async executeCalculationRule(
    rule: CalculationRule,
    rowData: Record<string, any>,
    allData?: Record<string, any>[]
  ): Promise<CalculationResult> {
    try {
      switch (rule.calculationType) {
        case CalculationType.MULTIPLY:
          return this.calculateMultiply(rule, rowData)
        case CalculationType.CUSTOM:
          if (rule.customFunction) {
            return this.calculateCustom(rule, rowData, allData)
          }
          return {
            success: false,
            error: 'Custom function not provided',
            executionTimeMs: 0,
            ruleId: rule.id
          }
        default:
          return {
            success: false,
            error: `Unsupported calculation type: ${rule.calculationType}`,
            executionTimeMs: 0,
            ruleId: rule.id
          }
      }
    } catch (error) {
      return {
        success: false,
        error: `Calculation execution error: ${error instanceof Error ? error.message : String(error)}`,
        executionTimeMs: 0,
        ruleId: rule.id
      }
    }
  }
  
  private calculateMultiply(rule: CalculationRule, rowData: Record<string, any>): CalculationResult {
    try {
      if (rule.sourceColumns.length < 2) {
        return {
          success: false,
          error: 'Multiply calculation requires at least 2 source columns',
          executionTimeMs: 0,
          ruleId: rule.id
        }
      }
      
      let result = 1
      for (const column of rule.sourceColumns) {
        const value = rowData[column]
        if (value === null || value === undefined || value === '') {
          // Return 0 if any value is missing
          return {
            success: true,
            value: 0,
            executionTimeMs: 0,
            ruleId: rule.id
          }
        }
        
        const numericValue = parseFloat(String(value))
        if (isNaN(numericValue)) {
          return {
            success: false,
            error: `Invalid numeric value in column ${column}: ${value}`,
            executionTimeMs: 0,
            ruleId: rule.id
          }
        }
        
        result *= numericValue
      }
      
      // Round to specified precision
      const roundedResult = Math.round(result * Math.pow(10, rule.precision)) / Math.pow(10, rule.precision)
      
      return {
        success: true,
        value: roundedResult,
        executionTimeMs: 0,
        ruleId: rule.id
      }
    } catch (error) {
      return {
        success: false,
        error: `Multiply calculation error: ${error instanceof Error ? error.message : String(error)}`,
        executionTimeMs: 0,
        ruleId: rule.id
      }
    }
  }
  
  private calculateCustom(
    rule: CalculationRule,
    rowData: Record<string, any>,
    allData?: Record<string, any>[]
  ): CalculationResult {
    try {
      if (!rule.customFunction) {
        return {
          success: false,
          error: 'Custom function not provided',
          executionTimeMs: 0,
          ruleId: rule.id
        }
      }
      
      const result = rule.customFunction(rowData, allData)
      
      return {
        success: true,
        value: result,
        executionTimeMs: 0,
        ruleId: rule.id
      }
    } catch (error) {
      return {
        success: false,
        error: `Custom calculation error: ${error instanceof Error ? error.message : String(error)}`,
        executionTimeMs: 0,
        ruleId: rule.id
      }
    }
  }
  
  private calculateTotalForRule(rule: TotalCalculationRule, allData: Record<string, any>[]): number | null {
    if (!allData || allData.length === 0) {
      return 0
    }
    
    const values: number[] = []
    for (const row of allData) {
      const value = row[rule.column]
      if (value !== null && value !== undefined && value !== '') {
        const numericValue = parseFloat(String(value))
        if (!isNaN(numericValue)) {
          values.push(numericValue)
        }
      }
    }
    
    if (values.length === 0) {
      return 0
    }
    
    switch (rule.calculationType) {
      case CalculationType.SUM:
        return values.reduce((sum, val) => sum + val, 0)
      case CalculationType.AVERAGE:
        return values.reduce((sum, val) => sum + val, 0) / values.length
      case CalculationType.COUNT:
        return values.length
      case CalculationType.MIN:
        return Math.min(...values)
      case CalculationType.MAX:
        return Math.max(...values)
      case CalculationType.CUSTOM:
        if (rule.customFunction) {
          return rule.customFunction(values)
        }
        return null
      default:
        return null
    }
  }
  
  private formatDecimal(value: number, precision: number): string {
    return value.toFixed(precision)
  }
  
  private updatePerformanceMetrics(executionTimeMs: number, isTotal: boolean): void {
    const currentTime = Date.now()
    
    if (isTotal) {
      this.metrics.totalCalculationTimeMs = executionTimeMs
    } else {
      this.metrics.individualCalculationTimeMs = executionTimeMs
    }
    
    // Update calculation history for rate calculation
    this.calculationHistory.push(currentTime)
    if (this.calculationHistory.length > this.maxHistorySize) {
      this.calculationHistory.shift()
    }
    
    // Calculate calculations per second
    if (this.calculationHistory.length > 1) {
      const timeSpan = currentTime - this.calculationHistory[0]
      if (timeSpan > 0) {
        this.metrics.calculationsPerSecond = (this.calculationHistory.length / timeSpan) * 1000
      }
    }
    
    this.metrics.lastCalculationTimestamp = currentTime
    
    // Estimate memory usage (rough approximation)
    if (this.performanceMonitoringEnabled) {
      this.metrics.memoryUsageMb = this.estimateMemoryUsage()
    }
  }
  
  private estimateMemoryUsage(): number {
    // Rough estimation based on number of rules and history
    const rulesSize = (this.calculationRules.size + this.totalRules.size) * 0.001 // ~1KB per rule
    const historySize = this.calculationHistory.length * 0.000008 // ~8 bytes per timestamp
    return rulesSize + historySize
  }
}

// ============================================================================
// Factory Functions
// ============================================================================

/**
 * Create a calculation engine with standard configuration
 */
export function createCalculationEngine(): TablePartCalculationEngine {
  return new TablePartCalculationEngine()
}

/**
 * Create a standard quantity × price calculation rule
 */
export function createQuantityPriceRule(
  quantityColumn = 'quantity',
  priceColumn = 'price',
  sumColumn = 'sum',
  precision = 2
): CalculationRule {
  return {
    id: `${quantityColumn}_${priceColumn}_${sumColumn}`,
    name: `${quantityColumn} × ${priceColumn} = ${sumColumn}`,
    sourceColumns: [quantityColumn, priceColumn],
    targetColumn: sumColumn,
    calculationType: CalculationType.MULTIPLY,
    triggerOnChange: true,
    precision,
    enabled: true
  }
}

/**
 * Create a standard sum total calculation rule
 */
export function createSumTotalRule(column: string, precision = 2): TotalCalculationRule {
  return {
    column,
    calculationType: CalculationType.SUM,
    precision,
    enabled: true
  }
}

// ============================================================================
// Composable for Vue Components
// ============================================================================

/**
 * Vue composable for using the calculation engine
 */
export function useCalculationEngine() {
  const engine = ref<TablePartCalculationEngine | null>(null)
  const metrics = ref<PerformanceMetrics>({
    individualCalculationTimeMs: 0,
    totalCalculationTimeMs: 0,
    calculationsPerSecond: 0,
    memoryUsageMb: 0,
    errorCount: 0
  })
  
  const initializeEngine = () => {
    engine.value = createCalculationEngine()
    
    // Set up event callbacks to update reactive metrics
    engine.value.setEventCallbacks({
      onCalculationCompleted: () => {
        if (engine.value) {
          metrics.value = engine.value.getPerformanceMetrics()
        }
      },
      onTotalCalculationCompleted: () => {
        if (engine.value) {
          metrics.value = engine.value.getPerformanceMetrics()
        }
      },
      onCalculationError: (errorType, message) => {
        console.error(`Calculation error (${errorType}): ${message}`)
      },
      onPerformanceAlert: (metricName, value) => {
        console.warn(`Performance alert - ${metricName}: ${value}`)
      }
    })
  }
  
  const calculateField = async (
    rowData: Record<string, any>,
    column: string,
    allData?: Record<string, any>[]
  ) => {
    if (!engine.value) {
      throw new Error('Calculation engine not initialized')
    }
    const result = await engine.value.calculateField(rowData, column, allData)
    
    // Throw error if calculation failed
    if (!result.success) {
      throw new Error(result.error || 'Calculation failed')
    }
    
    return result
  }
  
  const calculateTotals = async (allData: Record<string, any>[]) => {
    if (!engine.value) {
      throw new Error('Calculation engine not initialized')
    }
    return engine.value.calculateTotals(allData)
  }
  
  return {
    engine,
    metrics,
    initializeEngine,
    calculateField,
    calculateTotals
  }
}