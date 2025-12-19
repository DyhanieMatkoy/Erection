/**
 * TypeScript interfaces and types for document table parts
 */

// ============================================================================
// Core Table Part Types
// ============================================================================

export interface TableColumn {
  id: string
  name: string
  type: 'text' | 'number' | 'currency' | 'date' | 'reference' | 'boolean'
  width?: string
  sortable?: boolean
  editable?: boolean
  showTotal?: boolean
  referenceType?: string
  required?: boolean
  validation?: ColumnValidation
}

export interface ColumnValidation {
  min?: number
  max?: number
  pattern?: string
  customValidator?: (value: any) => boolean | string
}

export interface TablePartCommand {
  id: string
  name: string
  icon: string
  tooltip: string
  shortcut?: string
  enabled?: boolean
  visible?: boolean
  formMethod?: string
  position?: number
  requiresSelection?: boolean
}

export interface TablePartConfiguration {
  tableId: string
  documentType: string
  availableCommands: TablePartCommand[]
  visibleCommands: string[]
  keyboardShortcutsEnabled: boolean
  autoCalculationEnabled: boolean
  dragDropEnabled: boolean
  calculationTimeoutMs: number
  totalCalculationTimeoutMs: number
  showRowNumbers?: boolean
  allowMultiSelect?: boolean
  showTotals?: boolean
}

// ============================================================================
// Command Types
// ============================================================================

export enum CommandType {
  ADD_ROW = 'add_row',
  DELETE_ROW = 'delete_row',
  MOVE_UP = 'move_up',
  MOVE_DOWN = 'move_down',
  IMPORT_DATA = 'import_data',
  EXPORT_DATA = 'export_data',
  PRINT_DATA = 'print_data',
  COPY_ROWS = 'copy_rows',
  PASTE_ROWS = 'paste_rows',
  DUPLICATE_ROW = 'duplicate_row',
  CLEAR_SELECTION = 'clear_selection'
}

export interface CommandContext {
  selectedRows: number[]
  tableData: any[]
  commandId: string
  currentRow?: number
  currentColumn?: string
  additionalData?: Record<string, any>
}

export interface CommandResult {
  success: boolean
  message?: string
  data?: any
  affectedRows?: number[]
}

// ============================================================================
// User Settings Types
// ============================================================================

export interface TablePartUserSettings {
  id?: string
  userId: number
  documentType: string
  tablePartId: string
  settingsData: TablePartSettingsData
  createdAt?: string
  updatedAt?: string
}

export interface TablePartSettingsData {
  columnWidths: Record<string, number>
  columnOrder: string[]
  hiddenColumns: string[]
  panelSettings: PanelSettings
  shortcuts: ShortcutSettings
  sortSettings?: SortSettings
  filterSettings?: FilterSettings
}

export interface PanelSettings {
  visibleCommands: string[]
  hiddenCommands: string[]
  buttonSize: 'small' | 'medium' | 'large'
  showTooltips: boolean
  compactMode: boolean
}

export interface ShortcutSettings {
  enabled: boolean
  customMappings: Record<string, string>
}

export interface SortSettings {
  column?: string
  direction?: 'asc' | 'desc'
  multiSort?: Array<{ column: string; direction: 'asc' | 'desc' }>
}

export interface FilterSettings {
  activeFilters: Record<string, any>
  quickFilters: string[]
}

// ============================================================================
// Reference Field Types
// ============================================================================

export interface ReferenceFieldConfig {
  referenceType: string
  currentValue?: ReferenceValue
  relatedFields: string[]
  compactButtons: boolean
  allowCreate?: boolean
  allowEdit?: boolean
  searchEnabled?: boolean
  hierarchical?: boolean
}

export interface ReferenceValue {
  id: number
  code?: string
  name: string
  description?: string
  additionalData?: Record<string, any>
}

export interface ReferenceFieldState {
  isOpen: boolean
  isLoading: boolean
  searchQuery: string
  selectedValue?: ReferenceValue
  availableValues: ReferenceValue[]
  error?: string
}

// ============================================================================
// Calculation Engine Types
// ============================================================================

export interface CalculationRule {
  id: string
  name: string
  sourceColumns: string[]
  targetColumn: string
  formula: string | CalculationFunction
  triggerOnChange: boolean
  dependencies?: string[]
}

export type CalculationFunction = (row: any, allData: any[]) => number | string | boolean

export interface CalculationResult {
  success: boolean
  value?: any
  error?: string
  executionTime?: number
}

export interface TotalCalculation {
  column: string
  type: 'sum' | 'average' | 'count' | 'min' | 'max' | 'custom'
  customFunction?: (values: any[]) => any
  formatFunction?: (value: any) => string
}

// ============================================================================
// Import/Export Types
// ============================================================================

export interface ImportConfiguration {
  supportedFormats: ImportFormat[]
  columnMapping: Record<string, string>
  validationRules: ValidationRule[]
  previewRows: number
  skipEmptyRows: boolean
  headerRow: boolean
}

export interface ImportFormat {
  id: string
  name: string
  extensions: string[]
  mimeTypes: string[]
  parser: string
}

export interface ValidationRule {
  column: string
  type: 'required' | 'numeric' | 'date' | 'email' | 'custom'
  message: string
  customValidator?: (value: any) => boolean
}

export interface ImportResult {
  success: boolean
  totalRows: number
  successfulRows: number
  failedRows: ImportErrorRow[]
  warnings: string[]
  data?: any[]
}

export interface ImportErrorRow {
  rowNumber: number
  errors: string[]
  data: Record<string, any>
}

export interface ExportConfiguration {
  format: 'excel' | 'csv' | 'pdf'
  includeHeaders: boolean
  selectedRowsOnly: boolean
  columnSelection: string[]
  formatting: ExportFormatting
}

export interface ExportFormatting {
  dateFormat: string
  numberFormat: string
  currencyFormat: string
  booleanFormat: { true: string; false: string }
}

// ============================================================================
// Form Layout Types
// ============================================================================

export interface FormLayoutConfiguration {
  layoutType: 'single-column' | 'two-column' | 'auto'
  fieldDistribution: FieldDistribution
  responsiveBreakpoints: ResponsiveBreakpoints
  fieldSpacing: number
  grouping: FieldGrouping[]
}

export interface FieldDistribution {
  leftColumn: string[]
  rightColumn: string[]
  fullWidth: string[]
}

export interface ResponsiveBreakpoints {
  mobile: number
  tablet: number
  desktop: number
}

export interface FieldGrouping {
  id: string
  name: string
  fields: string[]
  collapsible: boolean
  collapsed: boolean
}

// ============================================================================
// Event Types
// ============================================================================

export interface TablePartEvent {
  type: string
  timestamp: Date
  source: 'user' | 'system' | 'external'
  data: any
}

export interface RowSelectionEvent extends TablePartEvent {
  type: 'row-selection-changed'
  data: {
    selectedRows: number[]
    previousSelection: number[]
  }
}

export interface DataChangeEvent extends TablePartEvent {
  type: 'data-changed'
  data: {
    row: number
    column: string
    oldValue: any
    newValue: any
  }
}

export interface CommandExecutionEvent extends TablePartEvent {
  type: 'command-executed'
  data: {
    commandId: string
    context: CommandContext
    result: CommandResult
  }
}

export interface CalculationEvent extends TablePartEvent {
  type: 'calculation-completed'
  data: {
    row?: number
    column?: string
    result: CalculationResult
    isTotal: boolean
  }
}

// ============================================================================
// Performance Monitoring Types
// ============================================================================

export interface PerformanceMetrics {
  renderTime: number
  calculationTime: number
  dataLoadTime: number
  memoryUsage?: number
  interactionLatency: number
}

export interface PerformanceThresholds {
  maxRenderTime: number
  maxCalculationTime: number
  maxDataLoadTime: number
  maxInteractionLatency: number
}

// ============================================================================
// Error Handling Types
// ============================================================================

export interface TablePartError {
  id: string
  type: 'validation' | 'calculation' | 'command' | 'import' | 'export' | 'system'
  message: string
  details?: string
  timestamp: Date
  recoverable: boolean
  suggestedActions?: string[]
}

export interface ErrorRecoveryAction {
  id: string
  name: string
  description: string
  handler: () => Promise<void>
}

// ============================================================================
// Utility Types
// ============================================================================

export type TablePartEventHandler<T = any> = (event: T) => void | Promise<void>

export type TablePartValidator<T = any> = (value: T) => boolean | string

export type TablePartFormatter<T = any> = (value: T) => string

export type TablePartParser<T = any> = (value: string) => T

// ============================================================================
// Factory Functions
// ============================================================================

export interface TablePartFactory {
  createConfiguration(documentType: string, tableId: string): TablePartConfiguration
  createCommand(type: CommandType, overrides?: Partial<TablePartCommand>): TablePartCommand
  createColumn(id: string, name: string, type: TableColumn['type'], options?: Partial<TableColumn>): TableColumn
}

// ============================================================================
// Plugin System Types
// ============================================================================

export interface TablePartPlugin {
  id: string
  name: string
  version: string
  description: string
  commands?: TablePartCommand[]
  columns?: TableColumn[]
  calculationRules?: CalculationRule[]
  eventHandlers?: Record<string, TablePartEventHandler>
  initialize?: (tablePartInstance: any) => void
  destroy?: () => void
}

export interface PluginRegistry {
  register(plugin: TablePartPlugin): void
  unregister(pluginId: string): void
  getPlugin(pluginId: string): TablePartPlugin | undefined
  getAllPlugins(): TablePartPlugin[]
  isPluginActive(pluginId: string): boolean
}