/**
 * Tests for Responsive Layout Adapter
 *
 * Tests the responsive layout adapter functionality including window size handling,
 * breakpoint detection, and layout adaptation.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ResponsiveLayoutAdapter, type WindowSize } from '../responsiveLayoutAdapter'
import { FieldType, type FormField } from '../formLayoutManager'

// Mock window object
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024
})

Object.defineProperty(window, 'innerHeight', {
  writable: true,
  configurable: true,
  value: 768
})

// Mock addEventListener and removeEventListener
const mockAddEventListener = vi.fn()
const mockRemoveEventListener = vi.fn()
Object.defineProperty(window, 'addEventListener', {
  value: mockAddEventListener
})
Object.defineProperty(window, 'removeEventListener', {
  value: mockRemoveEventListener
})

describe('ResponsiveLayoutAdapter', () => {
  let adapter: ResponsiveLayoutAdapter

  beforeEach(() => {
    vi.clearAllMocks()
    adapter = new ResponsiveLayoutAdapter()
  })

  const createTestFields = (count: number): FormField[] => {
    const fields: FormField[] = []

    for (let i = 0; i < count; i++) {
      fields.push({
        name: `field_${i}`,
        label: `Field ${i}`,
        fieldType: i < 4 ? FieldType.SHORT_TEXT : FieldType.LONG_TEXT,
        maxLength: i < 4 ? 50 : undefined,
        isMultiline: i >= 4
      })
    }

    return fields
  }

  describe('initialization', () => {
    it('should set up resize listener on creation', () => {
      expect(mockAddEventListener).toHaveBeenCalledWith('resize', expect.any(Function))
    })

    it('should initialize with default values', () => {
      expect(adapter.windowSize.value).toEqual({ width: 1024, height: 768 })
      expect(adapter.layoutType.value).toBe('single_column')
      expect(adapter.breakpoint.value).toBe('desktop')
    })
  })

  describe('window size handling', () => {
    it('should update window size when handleWindowResize is called', () => {
      const newSize: WindowSize = { width: 800, height: 600 }
      adapter.handleWindowResize(newSize)

      expect(adapter.windowSize.value).toEqual(newSize)
    })

    it('should update breakpoint based on window size', () => {
      // Mobile
      adapter.handleWindowResize({ width: 400, height: 300 })
      expect(adapter.breakpoint.value).toBe('mobile')

      // Tablet
      adapter.handleWindowResize({ width: 700, height: 500 })
      expect(adapter.breakpoint.value).toBe('tablet')

      // Desktop
      adapter.handleWindowResize({ width: 1100, height: 700 })
      expect(adapter.breakpoint.value).toBe('desktop')

      // Wide
      adapter.handleWindowResize({ width: 1500, height: 900 })
      expect(adapter.breakpoint.value).toBe('wide')
    })
  })

  describe('layout type determination', () => {
    it('should use two columns for wide window with many fields', () => {
      const fields = createTestFields(8)
      adapter.setFields(fields)

      const windowSize: WindowSize = { width: 1000, height: 600 }
      const shouldUseTwoColumns = adapter.shouldUseTwoColumns(windowSize, 6)

      expect(shouldUseTwoColumns).toBe(true)
    })

    it('should use single column for narrow window', () => {
      const fields = createTestFields(8)
      adapter.setFields(fields)

      const windowSize: WindowSize = { width: 600, height: 400 }
      const shouldUseTwoColumns = adapter.shouldUseTwoColumns(windowSize, 6)

      expect(shouldUseTwoColumns).toBe(false)
    })

    it('should use single column for few fields', () => {
      const fields = createTestFields(4)
      adapter.setFields(fields)

      const windowSize: WindowSize = { width: 1000, height: 600 }
      const shouldUseTwoColumns = adapter.shouldUseTwoColumns(windowSize, 4)

      expect(shouldUseTwoColumns).toBe(false)
    })
  })

  describe('breakpoint detection', () => {
    it('should detect mobile breakpoint', () => {
      adapter.handleWindowResize({ width: 400, height: 300 })
      expect(adapter.getCurrentBreakpoint()).toBe('mobile')
    })

    it('should detect tablet breakpoint', () => {
      adapter.handleWindowResize({ width: 700, height: 500 })
      expect(adapter.getCurrentBreakpoint()).toBe('tablet')
    })

    it('should detect desktop breakpoint', () => {
      adapter.handleWindowResize({ width: 1100, height: 700 })
      expect(adapter.getCurrentBreakpoint()).toBe('desktop')
    })

    it('should detect wide breakpoint', () => {
      adapter.handleWindowResize({ width: 1500, height: 900 })
      expect(adapter.getCurrentBreakpoint()).toBe('wide')
    })
  })

  describe('column ratio calculation', () => {
    it('should return equal columns for small screens', () => {
      const windowSize: WindowSize = { width: 600, height: 400 }
      const ratio = adapter.getColumnRatio(windowSize)
      expect(ratio).toBe(0.5)
    })

    it('should favor right column on medium screens', () => {
      const windowSize: WindowSize = { width: 900, height: 600 }
      const ratio = adapter.getColumnRatio(windowSize)
      expect(ratio).toBe(0.45)
    })

    it('should give more space to right column on large screens', () => {
      const windowSize: WindowSize = { width: 1200, height: 800 }
      const ratio = adapter.getColumnRatio(windowSize)
      expect(ratio).toBe(0.4)
    })
  })

  describe('layout adaptation', () => {
    it('should adapt layout configuration to window size', () => {
      const initialConfig = {
        leftColumn: createTestFields(2),
        rightColumn: createTestFields(2),
        fullWidthFields: createTestFields(1),
        columnRatio: 0.5
      }

      const windowSize: WindowSize = { width: 1200, height: 800 }
      const adaptedConfig = adapter.adaptToWindowSize(initialConfig, windowSize)

      expect(adaptedConfig.columnRatio).toBe(0.4) // Large screen ratio
      expect(adaptedConfig.fullWidthFields).toEqual(initialConfig.fullWidthFields)
    })

    it('should redistribute fields based on new ratio', () => {
      const allShortFields = createTestFields(6).slice(0, 4) // Only short fields
      const initialConfig = {
        leftColumn: allShortFields.slice(0, 2),
        rightColumn: allShortFields.slice(2, 4),
        fullWidthFields: [],
        columnRatio: 0.5
      }

      const windowSize: WindowSize = { width: 1200, height: 800 }
      const adaptedConfig = adapter.adaptToWindowSize(initialConfig, windowSize)

      // With ratio 0.4, should have floor(4 * 0.4) = 1 field in left column
      expect(adaptedConfig.leftColumn).toHaveLength(1)
      expect(adaptedConfig.rightColumn).toHaveLength(3)
    })
  })

  describe('single column forcing', () => {
    it('should force single column for narrow windows', () => {
      adapter.handleWindowResize({ width: 600, height: 400 })
      expect(adapter.shouldForceSingleColumn()).toBe(true)
    })

    it('should not force single column for wide windows', () => {
      adapter.handleWindowResize({ width: 1000, height: 600 })
      expect(adapter.shouldForceSingleColumn()).toBe(false)
    })
  })

  describe('field width calculation', () => {
    it('should return wider fields on mobile', () => {
      adapter.handleWindowResize({ width: 400, height: 300 })
      const width = adapter.getFieldWidthForBreakpoint('short')
      expect(width).toBeGreaterThan(0.3) // Base ratio * 1.2, capped at 1.0
    })

    it('should return base ratio on tablet', () => {
      adapter.handleWindowResize({ width: 700, height: 500 })
      const width = adapter.getFieldWidthForBreakpoint('short')
      expect(width).toBe(0.3) // Base ratio for 'short'
    })

    it('should return narrower fields on desktop', () => {
      adapter.handleWindowResize({ width: 1200, height: 800 })
      const width = adapter.getFieldWidthForBreakpoint('short')
      expect(width).toBe(0.27) // Base ratio * 0.9
    })

    it('should handle unknown field types', () => {
      adapter.handleWindowResize({ width: 1000, height: 600 })
      const width = adapter.getFieldWidthForBreakpoint('unknown')
      expect(width).toBe(0.45) // Default 0.5 * 0.9
    })
  })

  describe('field management', () => {
    it('should set fields correctly', () => {
      const fields = createTestFields(4)
      adapter.setFields(fields)

      expect(adapter['fields']).toEqual(fields)
    })

    it('should handle empty fields array', () => {
      adapter.setFields([])
      expect(adapter['fields']).toEqual([])
    })
  })

  describe('debouncing', () => {
    it('should debounce resize events', (done) => {
      const fields = createTestFields(8)
      adapter.setFields(fields)

      // Trigger multiple resize events quickly
      adapter.handleWindowResize({ width: 800, height: 600 })
      adapter.handleWindowResize({ width: 900, height: 600 })
      adapter.handleWindowResize({ width: 1000, height: 600 })

      // Layout type should not change immediately
      expect(adapter.layoutType.value).toBe('single_column')

      // Wait for debounce timeout
      setTimeout(() => {
        expect(adapter.layoutType.value).toBe('two_column')
        done()
      }, 200)
    })
  })
})