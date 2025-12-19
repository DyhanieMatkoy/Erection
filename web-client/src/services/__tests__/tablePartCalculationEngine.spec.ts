/**
 * Tests for the table part calculation engine (TypeScript/Vue version)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  TablePartCalculationEngine,
  CalculationType,
  createCalculationEngine,
  createQuantityPriceRule,
  createSumTotalRule,
  useCalculationEngine
} from '../tablePartCalculationEngine'

describe('TablePartCalculationEngine', () => {
  let engine: TablePartCalculationEngine

  beforeEach(() => {
    engine = createCalculationEngine()
  })

  describe('Basic Calculations', () => {
    it('should calculate quantity × price correctly', async () => {
      // Arrange
      const rowData = {
        quantity: 10,
        price: 25.50,
        sum: 0
      }

      // Act
      const result = await engine.calculateField(rowData, 'quantity')

      // Assert
      expect(result.success).toBe(true)
      expect(result.value).toBe(255)
      expect(rowData.sum).toBe(255)
      expect(result.executionTimeMs).toBeGreaterThanOrEqual(0)
    })

    it('should calculate when price changes', async () => {
      // Arrange
      const rowData = {
        quantity: 5,
        price: 12.75,
        sum: 0
      }

      // Act
      const result = await engine.calculateField(rowData, 'price')

      // Assert
      expect(result.success).toBe(true)
      expect(result.value).toBe(63.75)
      expect(rowData.sum).toBe(63.75)
    })

    it('should handle missing values by returning zero', async () => {
      // Arrange
      const rowData = {
        quantity: null,
        price: 10.00,
        sum: 0
      }

      // Act
      const result = await engine.calculateField(rowData, 'quantity')

      // Assert
      expect(result.success).toBe(true)
      expect(result.value).toBe(0)
      expect(rowData.sum).toBe(0)
    })

    it('should handle invalid numeric values', async () => {
      // Arrange
      const rowData = {
        quantity: 'invalid',
        price: 10.00,
        sum: 0
      }

      // Act
      const result = await engine.calculateField(rowData, 'quantity')

      // Assert
      expect(result.success).toBe(false)
      expect(result.error).toContain('Invalid numeric value')
    })

    it('should handle empty string values', async () => {
      // Arrange
      const rowData = {
        quantity: '',
        price: 10.00,
        sum: 0
      }

      // Act
      const result = await engine.calculateField(rowData, 'quantity')

      // Assert
      expect(result.success).toBe(true)
      expect(result.value).toBe(0)
      expect(rowData.sum).toBe(0)
    })
  })

  describe('Total Calculations', () => {
    it('should calculate document totals correctly', async () => {
      // Arrange
      const allData = [
        { quantity: 10, price: 5.00, sum: 50.00 },
        { quantity: 20, price: 3.50, sum: 70.00 },
        { quantity: 5, price: 8.00, sum: 40.00 }
      ]

      // Act
      const totals = await engine.calculateTotals(allData)

      // Assert
      expect(totals.sum).toBeDefined()
      expect(totals.sum.value).toBe(160.00)
      expect(totals.sum.formatted).toBe('160.00')

      expect(totals.quantity).toBeDefined()
      expect(totals.quantity.value).toBe(35.000)
      expect(totals.quantity.formatted).toBe('35.000')
    })

    it('should handle empty data for totals', async () => {
      // Arrange
      const allData: Record<string, any>[] = []

      // Act
      const totals = await engine.calculateTotals(allData)

      // Assert
      expect(totals.sum).toBeDefined()
      expect(totals.sum.value).toBe(0)
      expect(totals.quantity.value).toBe(0)
    })

    it('should skip invalid values in totals', async () => {
      // Arrange
      const allData = [
        { quantity: 10, price: 5.00, sum: 50.00 },
        { quantity: 'invalid', price: 3.50, sum: 'invalid' },
        { quantity: 5, price: 8.00, sum: 40.00 }
      ]

      // Act
      const totals = await engine.calculateTotals(allData)

      // Assert
      expect(totals.sum.value).toBe(90.00) // Only valid values: 50 + 40
      expect(totals.quantity.value).toBe(15.000) // Only valid values: 10 + 5
    })
  })

  describe('Custom Calculation Rules', () => {
    it('should support custom calculation functions', async () => {
      // Arrange
      const customRule = {
        id: 'discount_calculation',
        name: '10% Discount',
        sourceColumns: ['sum'],
        targetColumn: 'discounted_sum',
        calculationType: CalculationType.CUSTOM,
        customFunction: (rowData: Record<string, any>) => {
          const sum = parseFloat(rowData.sum) || 0
          return sum * 0.9
        },
        triggerOnChange: true,
        precision: 2,
        enabled: true
      }

      engine.addCalculationRule(customRule)

      const rowData = {
        quantity: 10,
        price: 5.00,
        sum: 50.00,
        discounted_sum: 0
      }

      // Act
      const result = await engine.calculateField(rowData, 'sum')

      // Assert
      expect(result.success).toBe(true)
      expect(rowData.discounted_sum).toBe(45.00)
    })

    it('should handle custom function errors', async () => {
      // Arrange
      const customRule = {
        id: 'error_calculation',
        name: 'Error Calculation',
        sourceColumns: ['sum'],
        targetColumn: 'error_result',
        calculationType: CalculationType.CUSTOM,
        customFunction: () => {
          throw new Error('Custom calculation error')
        },
        triggerOnChange: true,
        precision: 2,
        enabled: true
      }

      engine.addCalculationRule(customRule)

      const rowData = {
        sum: 50.00,
        error_result: 0
      }

      // Act
      const result = await engine.calculateField(rowData, 'sum')

      // Assert
      expect(result.success).toBe(false)
      expect(result.error).toContain('Custom calculation error')
    })
  })

  describe('Performance Monitoring', () => {
    it('should track performance metrics', async () => {
      // Arrange
      const rowData = { quantity: 10, price: 5.00, sum: 0 }

      // Act
      await engine.calculateField(rowData, 'quantity')
      const metrics = engine.getPerformanceMetrics()

      // Assert
      expect(metrics.individualCalculationTimeMs).toBeGreaterThanOrEqual(0)
      expect(metrics.lastCalculationTimestamp).toBeDefined()
    })

    it('should track calculation history', async () => {
      // Arrange
      const rowData = { quantity: 10, price: 5.00, sum: 0 }

      // Act
      await engine.calculateField(rowData, 'quantity')
      await engine.calculateField(rowData, 'price')

      const metrics = engine.getPerformanceMetrics()

      // Assert
      expect(metrics.calculationsPerSecond).toBeGreaterThanOrEqual(0)
    })

    it('should alert on performance thresholds', async () => {
      // Arrange
      engine.setPerformanceThresholds(1, 2) // Very low thresholds

      let alertReceived = false
      engine.setEventCallbacks({
        onPerformanceAlert: () => {
          alertReceived = true
        }
      })

      // Mock slow performance
      vi.spyOn(performance, 'now')
        .mockReturnValueOnce(0)
        .mockReturnValueOnce(5) // 5ms execution time

      const rowData = { quantity: 10, price: 5.00, sum: 0 }

      // Act
      await engine.calculateField(rowData, 'quantity')

      // Assert
      expect(alertReceived).toBe(true)
    })

    it('should reset performance metrics', () => {
      // Act
      engine.resetPerformanceMetrics()
      const metrics = engine.getPerformanceMetrics()

      // Assert
      expect(metrics.individualCalculationTimeMs).toBe(0)
      expect(metrics.totalCalculationTimeMs).toBe(0)
      expect(metrics.calculationsPerSecond).toBe(0)
      expect(metrics.errorCount).toBe(0)
    })
  })

  describe('Rule Management', () => {
    it('should add and remove calculation rules', () => {
      // Arrange
      const rule = createQuantityPriceRule('qty', 'unit_price', 'total')

      // Act
      engine.addCalculationRule(rule)
      engine.removeCalculationRule(rule.id)

      // Assert - should not trigger calculation after removal
      const rowData = { qty: 10, unit_price: 5.00, total: 0 }
      // This would normally trigger calculation, but rule is removed
    })

    it('should add and remove total rules', () => {
      // Arrange
      const rule = createSumTotalRule('amount', 3)

      // Act
      engine.addTotalRule('test_total', rule)
      engine.removeTotalRule('test_total')

      // Assert - rule should be removed
    })

    it('should validate calculation rules', () => {
      // Arrange
      const invalidRule = {
        id: 'invalid_rule',
        name: 'Invalid Rule',
        sourceColumns: [], // No source columns
        targetColumn: '', // No target column
        calculationType: CalculationType.MULTIPLY,
        triggerOnChange: true,
        precision: 2,
        enabled: true
      }

      engine.addCalculationRule(invalidRule)

      // Act
      const issues = engine.validateCalculationRules()

      // Assert
      expect(issues.length).toBeGreaterThan(0)
      expect(issues.some(issue => issue.includes('No source columns'))).toBe(true)
      expect(issues.some(issue => issue.includes('No target column'))).toBe(true)
    })
  })

  describe('Event Callbacks', () => {
    it('should call calculation completed callback', async () => {
      // Arrange
      let callbackCalled = false
      let callbackResult: any = null

      engine.setEventCallbacks({
        onCalculationCompleted: (row, column, result) => {
          callbackCalled = true
          callbackResult = result
        }
      })

      const rowData = { quantity: 10, price: 5.00, sum: 0 }

      // Act
      await engine.calculateField(rowData, 'quantity')

      // Assert
      expect(callbackCalled).toBe(true)
      expect(callbackResult).toBeDefined()
      expect(callbackResult.success).toBe(true)
    })

    it('should call total calculation completed callback', async () => {
      // Arrange
      let callbackCalled = false
      let callbackTotals: any = null

      engine.setEventCallbacks({
        onTotalCalculationCompleted: (totals) => {
          callbackCalled = true
          callbackTotals = totals
        }
      })

      const allData = [{ quantity: 10, price: 5.00, sum: 50.00 }]

      // Act
      await engine.calculateTotals(allData)

      // Assert
      expect(callbackCalled).toBe(true)
      expect(callbackTotals).toBeDefined()
      expect(callbackTotals.sum).toBeDefined()
    })

    it('should call error callback on calculation errors', async () => {
      // Arrange
      let errorCalled = false
      let errorMessage = ''

      engine.setEventCallbacks({
        onCalculationError: (errorType, message) => {
          errorCalled = true
          errorMessage = message
        }
      })

      const rowData = { quantity: 'invalid', price: 5.00, sum: 0 }

      // Act
      await engine.calculateField(rowData, 'quantity')

      // Assert
      expect(errorCalled).toBe(true)
      expect(errorMessage).toContain('Invalid numeric value')
    })
  })
})

describe('Factory Functions', () => {
  it('should create quantity price rule correctly', () => {
    // Act
    const rule = createQuantityPriceRule('qty', 'unit_price', 'total', 3)

    // Assert
    expect(rule.id).toBe('qty_unit_price_total')
    expect(rule.sourceColumns).toEqual(['qty', 'unit_price'])
    expect(rule.targetColumn).toBe('total')
    expect(rule.calculationType).toBe(CalculationType.MULTIPLY)
    expect(rule.precision).toBe(3)
  })

  it('should create sum total rule correctly', () => {
    // Act
    const rule = createSumTotalRule('amount', 3)

    // Assert
    expect(rule.column).toBe('amount')
    expect(rule.calculationType).toBe(CalculationType.SUM)
    expect(rule.precision).toBe(3)
  })

  it('should create calculation engine with default rules', () => {
    // Act
    const engine = createCalculationEngine()

    // Assert
    expect(engine).toBeInstanceOf(TablePartCalculationEngine)
    // Should have default rules
    const issues = engine.validateCalculationRules()
    expect(issues.length).toBe(0) // No validation issues with default rules
  })
})

describe('Vue Composable', () => {
  it('should initialize calculation engine', () => {
    // Act
    const { engine, metrics, initializeEngine } = useCalculationEngine()

    initializeEngine()

    // Assert
    expect(engine.value).toBeInstanceOf(TablePartCalculationEngine)
    expect(metrics.value).toBeDefined()
  })

  it('should provide reactive metrics', async () => {
    // Arrange
    const { engine, metrics, initializeEngine, calculateField } = useCalculationEngine()
    initializeEngine()

    const rowData = { quantity: 10, price: 5.00, sum: 0 }

    // Act
    await calculateField(rowData, 'quantity')

    // Assert
    expect(metrics.value.individualCalculationTimeMs).toBeGreaterThanOrEqual(0)
  })

  it('should handle calculation errors in composable', async () => {
    // Arrange
    const { initializeEngine, calculateField } = useCalculationEngine()
    initializeEngine()

    const rowData = { quantity: 'invalid', price: 5.00, sum: 0 }

    // Act & Assert
    await expect(calculateField(rowData, 'quantity')).rejects.toThrow()
  })
})