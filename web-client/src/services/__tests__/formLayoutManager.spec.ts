/**
 * Tests for Form Layout Manager
 *
 * Tests the form layout manager functionality including field analysis,
 * two-column layout creation, and responsive behavior.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { FormLayoutManager, FieldType, type FormField } from '../formLayoutManager'

describe('FormLayoutManager', () => {
  let layoutManager: FormLayoutManager

  beforeEach(() => {
    layoutManager = new FormLayoutManager()
  })

  const createTestFields = (count: number = 6): FormField[] => {
    const fields: FormField[] = []

    // Short fields
    for (let i = 0; i < Math.min(count, 4); i++) {
      fields.push({
        name: `short_${i}`,
        label: `Short Field ${i}`,
        fieldType: FieldType.SHORT_TEXT,
        maxLength: 50
      })
    }

    // Add long fields if needed
    if (count > 4) {
      for (let i = 0; i < count - 4; i++) {
        fields.push({
          name: `long_${i}`,
          label: `Long Field ${i}`,
          fieldType: FieldType.LONG_TEXT,
          isMultiline: true
        })
      }
    }

    return fields
  }

  describe('field classification', () => {
    it('should classify short text fields correctly', () => {
      const field: FormField = {
        name: 'test',
        label: 'Test',
        fieldType: FieldType.SHORT_TEXT,
        maxLength: 50
      }

      expect(layoutManager.isShortField(field)).toBe(true)
      expect(layoutManager.isLongStringField(field)).toBe(false)
    })

    it('should classify long text fields correctly', () => {
      const field: FormField = {
        name: 'test',
        label: 'Test',
        fieldType: FieldType.LONG_TEXT,
        isMultiline: true
      }

      expect(layoutManager.isShortField(field)).toBe(false)
      expect(layoutManager.isLongStringField(field)).toBe(true)
    })

    it('should classify fields with long maxLength as long fields', () => {
      const field: FormField = {
        name: 'test',
        label: 'Test',
        fieldType: FieldType.SHORT_TEXT,
        maxLength: 150
      }

      expect(layoutManager.isShortField(field)).toBe(false)
      expect(layoutManager.isLongStringField(field)).toBe(true)
    })

    it('should classify multiline fields as long fields', () => {
      const field: FormField = {
        name: 'test',
        label: 'Test',
        fieldType: FieldType.SHORT_TEXT,
        isMultiline: true
      }

      expect(layoutManager.isShortField(field)).toBe(false)
      expect(layoutManager.isLongStringField(field)).toBe(true)
    })
  })

  describe('field analysis', () => {
    it('should recommend single column for few fields', () => {
      const fields = createTestFields(4)
      const analysis = layoutManager.analyzeFields(fields)

      expect(analysis.totalFields).toBe(4)
      expect(analysis.shortFields).toHaveLength(4)
      expect(analysis.longStringFields).toHaveLength(0)
      expect(analysis.recommendedLayout).toBe('single_column')
    })

    it('should recommend two columns for many fields', () => {
      const fields = createTestFields(8)
      const analysis = layoutManager.analyzeFields(fields)

      expect(analysis.totalFields).toBe(8)
      expect(analysis.shortFields).toHaveLength(4) // First 4 are short
      expect(analysis.longStringFields).toHaveLength(4) // Last 4 are long
      expect(analysis.recommendedLayout).toBe('two_column')
    })

    it('should handle mixed field types correctly', () => {
      const fields: FormField[] = [
        {
          name: 'name',
          label: 'Name',
          fieldType: FieldType.SHORT_TEXT,
          maxLength: 50
        },
        {
          name: 'email',
          label: 'Email',
          fieldType: FieldType.SHORT_TEXT,
          maxLength: 100
        },
        {
          name: 'description',
          label: 'Description',
          fieldType: FieldType.LONG_TEXT,
          isMultiline: true
        },
        {
          name: 'age',
          label: 'Age',
          fieldType: FieldType.NUMERIC
        },
        {
          name: 'birthdate',
          label: 'Birth Date',
          fieldType: FieldType.DATE
        },
        {
          name: 'active',
          label: 'Active',
          fieldType: FieldType.BOOLEAN
        }
      ]

      const analysis = layoutManager.analyzeFields(fields)

      expect(analysis.totalFields).toBe(6)
      expect(analysis.shortFields).toHaveLength(5) // All except description
      expect(analysis.longStringFields).toHaveLength(1) // Only description
      expect(analysis.recommendedLayout).toBe('two_column')
    })
  })

  describe('two-column layout creation', () => {
    it('should create balanced two-column layout', () => {
      const fields = createTestFields(8)
      const config = layoutManager.createTwoColumnLayout(fields)

      expect(config.leftColumn).toHaveLength(2) // Half of short fields
      expect(config.rightColumn).toHaveLength(2) // Half of short fields
      expect(config.fullWidthFields).toHaveLength(4) // All long fields
      expect(config.columnRatio).toBeGreaterThan(0)
      expect(config.columnRatio).toBeLessThan(1)
    })

    it('should handle odd number of short fields', () => {
      const fields: FormField[] = [
        ...createTestFields(4), // 4 short fields
        {
          name: 'extra',
          label: 'Extra',
          fieldType: FieldType.SHORT_TEXT
        }
      ]

      const config = layoutManager.createTwoColumnLayout(fields)

      expect(config.leftColumn.length + config.rightColumn.length).toBe(5)
      expect(config.leftColumn).toHaveLength(2) // Floor of 5/2
      expect(config.rightColumn).toHaveLength(3) // Remainder
    })

    it('should put all long fields in full width', () => {
      const fields: FormField[] = [
        {
          name: 'short1',
          label: 'Short 1',
          fieldType: FieldType.SHORT_TEXT
        },
        {
          name: 'short2',
          label: 'Short 2',
          fieldType: FieldType.SHORT_TEXT
        },
        {
          name: 'long1',
          label: 'Long 1',
          fieldType: FieldType.LONG_TEXT,
          isMultiline: true
        },
        {
          name: 'long2',
          label: 'Long 2',
          fieldType: FieldType.LONG_TEXT,
          maxLength: 200
        }
      ]

      const config = layoutManager.createTwoColumnLayout(fields)

      expect(config.fullWidthFields).toHaveLength(2)
      expect(config.fullWidthFields.map(f => f.name)).toEqual(['long1', 'long2'])
      expect(config.leftColumn.length + config.rightColumn.length).toBe(2)
    })
  })

  describe('long string field handling', () => {
    it('should identify all long string fields', () => {
      const fields = createTestFields(6)
      const longFields = layoutManager.handleLongStringFields(fields)

      expect(longFields).toHaveLength(2) // Last 2 fields are long
      longFields.forEach(field => {
        expect(layoutManager.isLongStringField(field)).toBe(true)
      })
    })

    it('should return empty array when no long fields', () => {
      const fields = createTestFields(4) // Only short fields
      const longFields = layoutManager.handleLongStringFields(fields)

      expect(longFields).toHaveLength(0)
    })
  })

  describe('field type detection', () => {
    it('should detect field types from input types', () => {
      expect(layoutManager.getFieldTypeFromInputType('text')).toBe(FieldType.SHORT_TEXT)
      expect(layoutManager.getFieldTypeFromInputType('textarea')).toBe(FieldType.LONG_TEXT)
      expect(layoutManager.getFieldTypeFromInputType('number')).toBe(FieldType.NUMERIC)
      expect(layoutManager.getFieldTypeFromInputType('date')).toBe(FieldType.DATE)
      expect(layoutManager.getFieldTypeFromInputType('datetime-local')).toBe(FieldType.DATE)
      expect(layoutManager.getFieldTypeFromInputType('checkbox')).toBe(FieldType.BOOLEAN)
      expect(layoutManager.getFieldTypeFromInputType('select')).toBe(FieldType.REFERENCE)
    })

    it('should default to short text for unknown types', () => {
      expect(layoutManager.getFieldTypeFromInputType('unknown')).toBe(FieldType.SHORT_TEXT)
      expect(layoutManager.getFieldTypeFromInputType('')).toBe(FieldType.SHORT_TEXT)
    })
  })

  describe('field creation helper', () => {
    it('should create field with correct properties', () => {
      const field = layoutManager.createField('test', 'Test Field', 'text', {
        maxLength: 100,
        isRequired: true
      })

      expect(field.name).toBe('test')
      expect(field.label).toBe('Test Field')
      expect(field.fieldType).toBe(FieldType.SHORT_TEXT)
      expect(field.maxLength).toBe(100)
      expect(field.isRequired).toBe(true)
    })

    it('should create field with default options', () => {
      const field = layoutManager.createField('test', 'Test Field')

      expect(field.name).toBe('test')
      expect(field.label).toBe('Test Field')
      expect(field.fieldType).toBe(FieldType.SHORT_TEXT)
      expect(field.maxLength).toBeUndefined()
      expect(field.isRequired).toBeUndefined()
    })

    it('should detect field type from input type', () => {
      const numericField = layoutManager.createField('age', 'Age', 'number')
      expect(numericField.fieldType).toBe(FieldType.NUMERIC)

      const dateField = layoutManager.createField('birth', 'Birth Date', 'date')
      expect(dateField.fieldType).toBe(FieldType.DATE)

      const textareaField = layoutManager.createField('desc', 'Description', 'textarea')
      expect(textareaField.fieldType).toBe(FieldType.LONG_TEXT)
    })
  })

  describe('minimum fields configuration', () => {
    it('should respect custom minimum fields for two columns', () => {
      const customManager = new FormLayoutManager(4) // Require 4 fields instead of 6
      const fields = createTestFields(5) // 4 short + 1 long

      const analysis = customManager.analyzeFields(fields)
      expect(analysis.recommendedLayout).toBe('two_column')
    })

    it('should use default minimum when not specified', () => {
      const defaultManager = new FormLayoutManager()
      const fields = createTestFields(5) // 4 short + 1 long

      const analysis = defaultManager.analyzeFields(fields)
      expect(analysis.recommendedLayout).toBe('single_column') // Less than 6 short fields
    })
  })
})