/**
 * Form Layout Manager
 *
 * Manages form field layout with intelligent two-column arrangement based on field types and counts.
 * Implements requirements 12.1-12.4 for document table parts.
 */

export enum FieldType {
  SHORT_TEXT = 'short_text',
  LONG_TEXT = 'long_text',
  NUMERIC = 'numeric',
  DATE = 'date',
  BOOLEAN = 'boolean',
  REFERENCE = 'reference',
  CALCULATED = 'calculated'
}

export interface FormField {
  name: string
  label: string
  fieldType: FieldType
  maxLength?: number
  isMultiline?: boolean
  isRequired?: boolean
  component?: any
  props?: Record<string, any>
}

export interface LayoutAnalysis {
  totalFields: number
  longStringFields: FormField[]
  shortFields: FormField[]
  recommendedLayout: 'single_column' | 'two_column'
}

export interface LayoutConfiguration {
  leftColumn: FormField[]
  rightColumn: FormField[]
  fullWidthFields: FormField[]
  columnRatio: number
}

export class FormLayoutManager {
  private minFieldsForTwoColumns: number

  constructor(minFieldsForTwoColumns: number = 6) {
    this.minFieldsForTwoColumns = minFieldsForTwoColumns
  }

  /**
   * Check if field should span full width
   */
  isLongStringField(field: FormField): boolean {
    if (field.fieldType === FieldType.LONG_TEXT) {
      return true
    }
    if (field.isMultiline) {
      return true
    }
    if (field.maxLength && field.maxLength > 100) {
      return true
    }
    return false
  }

  /**
   * Check if field is suitable for column layout
   */
  isShortField(field: FormField): boolean {
    return !this.isLongStringField(field)
  }

  /**
   * Analyze fields to determine optimal layout strategy
   */
  analyzeFields(fields: FormField[]): LayoutAnalysis {
    const analysis: LayoutAnalysis = {
      totalFields: fields.length,
      longStringFields: [],
      shortFields: [],
      recommendedLayout: 'single_column'
    }

    // Classify fields
    for (const field of fields) {
      if (this.isLongStringField(field)) {
        analysis.longStringFields.push(field)
      } else {
        analysis.shortFields.push(field)
      }
    }

    // Determine recommended layout
    // Use two-column if we have enough total fields and enough short fields
    if (analysis.totalFields >= this.minFieldsForTwoColumns && analysis.shortFields.length >= 4) {
      analysis.recommendedLayout = 'two_column'
    }

    return analysis
  }

  /**
   * Create two-column layout configuration
   */
  createTwoColumnLayout(fields: FormField[]): LayoutConfiguration {
    const config: LayoutConfiguration = {
      leftColumn: [],
      rightColumn: [],
      fullWidthFields: [],
      columnRatio: 0.5
    }

    // Separate long and short fields
    const shortFields = fields.filter((f) => this.isShortField(f))
    const longFields = fields.filter((f) => !this.isShortField(f))

    // Long fields go to full width
    config.fullWidthFields = longFields

    // Distribute short fields between columns
    const midPoint = Math.floor(shortFields.length / 2)

    config.leftColumn = shortFields.slice(0, midPoint)
    config.rightColumn = shortFields.slice(midPoint)

    // Adjust ratio if columns are unbalanced
    if (config.leftColumn.length > 0 && config.rightColumn.length > 0) {
      const ratio = config.leftColumn.length / (config.leftColumn.length + config.rightColumn.length)
      config.columnRatio = ratio
    }

    return config
  }

  /**
   * Identify long string fields for full-width layout
   */
  handleLongStringFields(fields: FormField[]): FormField[] {
    return fields.filter((f) => this.isLongStringField(f))
  }

  /**
   * Get field type from HTML input type
   */
  getFieldTypeFromInputType(inputType: string): FieldType {
    switch (inputType) {
      case 'textarea':
        return FieldType.LONG_TEXT
      case 'number':
        return FieldType.NUMERIC
      case 'date':
      case 'datetime-local':
        return FieldType.DATE
      case 'checkbox':
        return FieldType.BOOLEAN
      case 'select':
        return FieldType.REFERENCE
      default:
        return FieldType.SHORT_TEXT
    }
  }

  /**
   * Create field configuration from simple definition
   */
  createField(
    name: string,
    label: string,
    inputType: string = 'text',
    options: Partial<FormField> = {}
  ): FormField {
    return {
      name,
      label,
      fieldType: this.getFieldTypeFromInputType(inputType),
      ...options
    }
  }
}

/**
 * Helper function to create form layout manager instance
 */
export function createFormLayoutManager(minFieldsForTwoColumns: number = 6): FormLayoutManager {
  return new FormLayoutManager(minFieldsForTwoColumns)
}
