<template>
  <div class="table-part-container">
    <!-- Row Control Panel -->
    <div class="row-control-panel">
      <div class="panel-buttons">
        <button
          v-for="command in visibleCommands"
          :key="command.id"
          :class="['btn', 'btn-sm', getButtonClass(command)]"
          :disabled="!isCommandEnabled(command)"
          :title="command.tooltip"
          @click="executeCommand(command.id)"
        >
          <span class="icon">{{ command.icon }}</span>
          {{ command.name }}
        </button>
        
        <!-- More menu for hidden commands -->
        <div v-if="hiddenCommands.length > 0" class="dropdown">
          <button
            class="btn btn-sm btn-secondary dropdown-toggle"
            @click="showMoreMenu = !showMoreMenu"
          >
            Еще
          </button>
          <div v-if="showMoreMenu" class="dropdown-menu">
            <button
              v-for="command in hiddenCommands"
              :key="command.id"
              :class="['dropdown-item', { disabled: !isCommandEnabled(command) }]"
              :disabled="!isCommandEnabled(command)"
              @click="executeCommand(command.id); showMoreMenu = false"
            >
              <span class="icon">{{ command.icon }}</span>
              {{ command.name }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- Customization button -->
      <button
        class="btn btn-sm btn-outline-secondary"
        @click="showCustomizeDialog = true"
        title="Настроить панель"
      >
        ⚙️
      </button>
    </div>

    <!-- Table Container -->
    <div class="table-container">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.id"
              :style="{ width: column.width }"
              :class="{ sortable: column.sortable }"
              @click="column.sortable && handleSort(column.id)"
            >
              {{ column.name }}
              <span v-if="column.sortable && sortColumn === column.id" class="sort-indicator">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="actions-column">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in displayedData"
            :key="getRowKey(row, index)"
            :class="{ 
              'row-selected': isRowSelected(index),
              'row-editing': editingRowIndex === index,
              'drag-over': dragOverRow === index
            }"
            :draggable="configuration.dragDropEnabled"
            @click="handleRowClick(index, $event)"
            @dragstart="handleDragStart(index, $event)"
            @dragover="handleDragOver(index, $event)"
            @dragleave="handleDragLeave(index, $event)"
            @drop="handleDrop(index, $event)"
            @dragend="handleDragEnd($event)"
          >
            <td
              v-for="column in columns"
              :key="column.id"
              :class="getCellClass(column, row)"
              @dblclick="handleCellDoubleClick(index, column.id)"
            >
              <!-- Editable cell -->
              <input
                v-if="editingRowIndex === index && editingColumnId === column.id"
                v-model="editingValue"
                :type="getInputType(column)"
                :step="getInputStep(column)"
                class="cell-input"
                @blur="saveEdit"
                @keyup.enter="saveEdit"
                @keyup.esc="cancelEdit"
                ref="cellInput"
              />
              
              <!-- Reference field with compact buttons -->
              <CompactReferenceField
                v-else-if="column.type === 'reference'"
                :model-value="getReferenceValue(row, column)"
                :reference-type="column.referenceType || 'unknown'"
                :allow-edit="true"
                :related-fields="column.relatedFields || []"
                @update:model-value="updateReferenceValue(row, column, $event)"
                @open-reference="openReference(row, column, $event)"
                @select-reference="selectReference(row, column, $event)"
                @fill-related-fields="fillRelatedFields(row, $event)"
              />
              
              <!-- Regular cell -->
              <span v-else>{{ formatCellValue(row, column) }}</span>
            </td>
            
            <!-- Actions column -->
            <td class="actions-column">
              <button
                v-if="editingRowIndex !== index"
                class="btn btn-xs btn-secondary"
                @click="startEdit(index, columns[0].id)"
                title="Редактировать"
              >
                ✎
              </button>
              <button
                class="btn btn-xs btn-danger"
                @click="deleteRow(index)"
                title="Удалить строку"
              >
                🗑
              </button>
            </td>
          </tr>
          
          <!-- Empty state -->
          <tr v-if="displayedData.length === 0">
            <td :colspan="columns.length + 1" class="empty-state">
              {{ emptyMessage }}
            </td>
          </tr>
        </tbody>
        
        <!-- Totals footer -->
        <tfoot v-if="showTotals && displayedData.length > 0">
          <tr class="totals-row">
            <td
              v-for="column in columns"
              :key="column.id"
              :class="{ 'text-right': column.type === 'number' || column.type === 'currency' }"
            >
              <strong v-if="column.showTotal">{{ formatTotal(column) }}</strong>
            </td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Customization Dialog -->
    <div v-if="showCustomizeDialog" class="modal-overlay" @click.self="showCustomizeDialog = false">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>Настройка панели управления</h3>
          <button @click="showCustomizeDialog = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <p>Выберите команды для отображения на панели:</p>
          <div class="command-list">
            <label
              v-for="command in allCommands"
              :key="command.id"
              class="command-item"
            >
              <input
                type="checkbox"
                :checked="configuration.visibleCommands.includes(command.id)"
                @change="toggleCommandVisibility(command.id, $event.target.checked)"
              />
              <span class="icon">{{ command.icon }}</span>
              {{ command.name }}
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showCustomizeDialog = false" class="btn btn-secondary">Отмена</button>
          <button @click="saveCustomization" class="btn btn-primary">Сохранить</button>
        </div>
      </div>
    </div>

    <!-- Performance Monitor -->
    <CalculationPerformanceMonitor
      v-if="showPerformanceMonitor"
      ref="performanceMonitor"
      :metrics="calculationMetrics"
      @status-changed="onPerformanceStatusChanged"
      @threshold-exceeded="onThresholdExceeded"
    />
  </div>
</template>

<script setup lang="ts" generic="T">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { 
  TablePartKeyboardHandler, 
  ShortcutAction, 
  ShortcutContext,
  createKeyboardHandler,
  createTableContext,
  isElementEditing,
  getSelectedRows
} from '../../services/tablePartKeyboardHandler'
import { 
  useCalculationEngine,
  type CalculationResult,
  type TotalResult
} from '../../services/tablePartCalculationEngine'
import CompactReferenceField from './CompactReferenceField.vue'
import CalculationPerformanceMonitor from './CalculationPerformanceMonitor.vue'
import type { ReferenceValue } from '../../types/table-parts'

// Types
export interface TableColumn {
  id: string
  name: string
  type: 'text' | 'number' | 'currency' | 'date' | 'reference'
  width?: string
  sortable?: boolean
  editable?: boolean
  showTotal?: boolean
  referenceType?: string
  relatedFields?: string[]
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
}

interface Props<T> {
  data: T[]
  columns: TableColumn[]
  configuration: TablePartConfiguration
  emptyMessage?: string
  showTotals?: boolean
  getRowKey?: (row: T, index: number) => string | number
  formatCellValue?: (row: T, column: TableColumn) => string
  isRowSelected?: (index: number) => boolean
}

interface Emits<T> {
  (e: 'row-selection-changed', selectedRows: number[]): void
  (e: 'data-changed', row: number, column: string, value: any): void
  (e: 'command-executed', commandId: string, context: any): void
  (e: 'calculation-requested', row: number, column: string): void
  (e: 'total-calculation-requested'): void
  (e: 'totals-calculated', totals: Record<string, TotalResult>): void
  (e: 'calculation-completed', row: number, column: string, result: CalculationResult): void
  (e: 'calculation-error', errorType: string, message: string): void
  (e: 'performance-alert', metricName: string, value: number): void
  (e: 'reference-open', row: T, column: TableColumn): void
  (e: 'reference-select', row: T, column: TableColumn): void
  (e: 'configuration-changed', config: TablePartConfiguration): void
}

const props = withDefaults(defineProps<Props<T>>(), {
  emptyMessage: 'Нет данных для отображения',
  showTotals: false,
  getRowKey: (row: any, index: number) => index,
  formatCellValue: (row: any, column: TableColumn) => row[column.id] || '',
  isRowSelected: () => false
})

const emit = defineEmits<Emits<T>>()

// Local state
const showMoreMenu = ref(false)
const showCustomizeDialog = ref(false)
const editingRowIndex = ref<number | null>(null)
const editingColumnId = ref<string | null>(null)
const editingValue = ref<any>(null)
const selectedRows = ref<number[]>([])
const sortColumn = ref<string | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')
const cellInput = ref<HTMLInputElement | null>(null)

// Drag and drop state
const draggedRowIndex = ref<number | null>(null)
const dragOverRow = ref<number | null>(null)
const isDragging = ref(false)

// Calculation engine
const { engine: calculationEngine, metrics: calculationMetrics, initializeEngine, calculateField, calculateTotals } = useCalculationEngine()

// Performance monitoring
const performanceMonitor = ref<InstanceType<typeof CalculationPerformanceMonitor> | null>(null)
const showPerformanceMonitor = ref(false)

// Calculation timers
let calculationTimer: number | null = null
let totalCalculationTimer: number | null = null

// Keyboard handler
let keyboardHandler: TablePartKeyboardHandler | null = null

// Standard commands
const standardCommands: TablePartCommand[] = [
  {
    id: 'add_row',
    name: 'Добавить',
    icon: '➕',
    tooltip: 'Добавить новую строку (Insert)',
    shortcut: 'Insert'
  },
  {
    id: 'delete_row',
    name: 'Удалить',
    icon: '🗑',
    tooltip: 'Удалить выбранные строки (Delete)',
    shortcut: 'Delete'
  },
  {
    id: 'move_up',
    name: 'Выше',
    icon: '↑',
    tooltip: 'Переместить строки выше (Ctrl+Shift+Up)',
    shortcut: 'Ctrl+Shift+Up'
  },
  {
    id: 'move_down',
    name: 'Ниже',
    icon: '↓',
    tooltip: 'Переместить строки ниже (Ctrl+Shift+Down)',
    shortcut: 'Ctrl+Shift+Down'
  },
  {
    id: 'import_data',
    name: 'Импорт',
    icon: '📥',
    tooltip: 'Импортировать данные из файла'
  },
  {
    id: 'export_data',
    name: 'Экспорт',
    icon: '📤',
    tooltip: 'Экспортировать данные в файл'
  },
  {
    id: 'print_data',
    name: 'Печать',
    icon: '🖨',
    tooltip: 'Печать табличной части'
  }
]

// Computed properties
const allCommands = computed(() => {
  return [...standardCommands, ...props.configuration.availableCommands]
})

const visibleCommands = computed(() => {
  return allCommands.value.filter(cmd => 
    props.configuration.visibleCommands.includes(cmd.id)
  )
})

const hiddenCommands = computed(() => {
  return allCommands.value.filter(cmd => 
    !props.configuration.visibleCommands.includes(cmd.id)
  )
})

const displayedData = computed(() => {
  let data = [...props.data]
  
  // Apply sorting
  if (sortColumn.value) {
    data.sort((a, b) => {
      const aVal = a[sortColumn.value as keyof T]
      const bVal = b[sortColumn.value as keyof T]
      
      if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1
      return 0
    })
  }
  
  return data
})

// Methods
function handleRowClick(index: number, event: MouseEvent) {
  if (event.ctrlKey) {
    // Multi-select with Ctrl
    const idx = selectedRows.value.indexOf(index)
    if (idx > -1) {
      selectedRows.value.splice(idx, 1)
    } else {
      selectedRows.value.push(index)
    }
  } else if (event.shiftKey && selectedRows.value.length > 0) {
    // Range select with Shift
    const lastSelected = selectedRows.value[selectedRows.value.length - 1]
    const start = Math.min(lastSelected, index)
    const end = Math.max(lastSelected, index)
    selectedRows.value = Array.from({ length: end - start + 1 }, (_, i) => start + i)
  } else {
    // Single select
    selectedRows.value = [index]
  }
  
  emit('row-selection-changed', selectedRows.value)
  updateKeyboardContext()
}

function handleCellDoubleClick(rowIndex: number, columnId: string) {
  const column = props.columns.find(col => col.id === columnId)
  if (column?.editable) {
    startEdit(rowIndex, columnId)
  }
}

async function startEdit(rowIndex: number, columnId: string) {
  editingRowIndex.value = rowIndex
  editingColumnId.value = columnId
  editingValue.value = props.data[rowIndex][columnId as keyof T]
  
  await nextTick()
  cellInput.value?.focus()
  cellInput.value?.select()
}

function saveEdit() {
  if (editingRowIndex.value !== null && editingColumnId.value !== null) {
    emit('data-changed', editingRowIndex.value, editingColumnId.value, editingValue.value)
    
    // Schedule calculation if enabled
    if (props.configuration.autoCalculationEnabled) {
      scheduleCalculation(editingRowIndex.value, editingColumnId.value)
    }
  }
  
  cancelEdit()
}

function cancelEdit() {
  editingRowIndex.value = null
  editingColumnId.value = null
  editingValue.value = null
}

async function scheduleCalculation(row: number, column: string) {
  if (calculationTimer) {
    clearTimeout(calculationTimer)
  }
  
  calculationTimer = setTimeout(async () => {
    // Perform calculation using the engine
    const rowData = { ...props.data[row] }
    
    try {
      const result = await calculateField(rowData, column, props.data)
      
      if (result.success && result.value !== undefined) {
        // Update the row data with calculated value
        emit('data-changed', row, column, result.value)
      }
      
      emit('calculation-requested', row, column)
      
      // Schedule total calculation
      if (totalCalculationTimer) {
        clearTimeout(totalCalculationTimer)
      }
      
      totalCalculationTimer = setTimeout(async () => {
        try {
          const totals = await calculateTotals(props.data)
          emit('total-calculation-requested')
          
          // Emit totals for parent component to handle
          if (Object.keys(totals).length > 0) {
            emit('totals-calculated', totals)
          }
        } catch (error) {
          console.error('Total calculation error:', error)
        }
      }, props.configuration.totalCalculationTimeoutMs)
      
    } catch (error) {
      console.error('Field calculation error:', error)
      emit('calculation-requested', row, column)
    }
  }, props.configuration.calculationTimeoutMs)
}

function handleSort(columnId: string) {
  if (sortColumn.value === columnId) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = columnId
    sortDirection.value = 'asc'
  }
}

function executeCommand(commandId: string) {
  const context = {
    selectedRows: selectedRows.value,
    tableData: props.data,
    commandId
  }
  
  // Handle built-in commands
  switch (commandId) {
    case 'move_up':
      moveRowsUp()
      break
    case 'move_down':
      moveRowsDown()
      break
    default:
      // Emit for external handling
      emit('command-executed', commandId, context)
      break
  }
}

function moveRowsUp() {
  if (selectedRows.value.length === 0) {
    return
  }
  
  // Sort selected rows to maintain order
  const sortedRows = [...selectedRows.value].sort((a, b) => a - b)
  
  // Check if we can move up (first selected row must not be at index 0)
  if (sortedRows[0] <= 0) {
    return
  }
  
  // Create a copy of the data array
  const newData = [...props.data]
  
  // Move each selected row up by one position
  for (const rowIndex of sortedRows) {
    // Swap rows
    const temp = newData[rowIndex]
    newData[rowIndex] = newData[rowIndex - 1]
    newData[rowIndex - 1] = temp
  }
  
  // Update selection to follow moved rows
  const newSelection = sortedRows.map(row => row - 1)
  selectedRows.value = newSelection
  
  // Emit data change
  emit('data-changed', -1, 'row_order', newData)
  
  // Trigger recalculation if enabled
  if (props.configuration.autoCalculationEnabled) {
    scheduleCalculation(-1, 'row_order')
  }
}

function moveRowsDown() {
  if (selectedRows.value.length === 0) {
    return
  }
  
  // Sort selected rows in reverse order to maintain order when moving down
  const sortedRows = [...selectedRows.value].sort((a, b) => b - a)
  
  // Check if we can move down (last selected row must not be at last index)
  if (sortedRows[0] >= props.data.length - 1) {
    return
  }
  
  // Create a copy of the data array
  const newData = [...props.data]
  
  // Move each selected row down by one position
  for (const rowIndex of sortedRows) {
    // Swap rows
    const temp = newData[rowIndex]
    newData[rowIndex] = newData[rowIndex + 1]
    newData[rowIndex + 1] = temp
  }
  
  // Update selection to follow moved rows
  const newSelection = [...selectedRows.value].sort((a, b) => a - b).map(row => row + 1)
  selectedRows.value = newSelection
  
  // Emit data change
  emit('data-changed', -1, 'row_order', newData)
  
  // Trigger recalculation if enabled
  if (props.configuration.autoCalculationEnabled) {
    scheduleCalculation(-1, 'row_order')
  }
}

function isCommandEnabled(command: TablePartCommand): boolean {
  const hasSelection = selectedRows.value.length > 0
  const hasRows = props.data.length > 0
  
  switch (command.id) {
    case 'delete_row':
    case 'move_up':
    case 'move_down':
      return hasSelection
    case 'export_data':
      return hasRows
    default:
      return true
  }
}

function getButtonClass(command: TablePartCommand): string {
  switch (command.id) {
    case 'add_row':
      return 'btn-primary'
    case 'delete_row':
      return 'btn-danger'
    default:
      return 'btn-secondary'
  }
}

function getCellClass(column: TableColumn, row: T): string {
  const classes = []
  
  if (column.type === 'number' || column.type === 'currency') {
    classes.push('text-right')
  }
  
  if (column.editable) {
    classes.push('editable-cell')
  }
  
  return classes.join(' ')
}

function getInputType(column: TableColumn): string {
  switch (column.type) {
    case 'number':
    case 'currency':
      return 'number'
    case 'date':
      return 'date'
    default:
      return 'text'
  }
}

function getInputStep(column: TableColumn): string | undefined {
  if (column.type === 'currency') {
    return '0.01'
  } else if (column.type === 'number') {
    return '0.001'
  }
  return undefined
}

function deleteRow(index: number) {
  selectedRows.value = [index]
  executeCommand('delete_row')
}

function getReferenceValue(row: T, column: TableColumn): ReferenceValue | null {
  const id = row[column.id as keyof T] as number
  const nameField = `${column.id}_name`
  const codeField = `${column.id}_code`
  
  if (!id || id <= 0) return null
  
  return {
    id,
    name: (row[nameField as keyof T] as string) || `${column.referenceType} ${id}`,
    code: (row[codeField as keyof T] as string) || undefined
  }
}

function updateReferenceValue(row: T, column: TableColumn, value: ReferenceValue | null) {
  if (value) {
    // Update the row data
    (row as any)[column.id] = value.id
    const nameField = `${column.id}_name`
    const codeField = `${column.id}_code`
    
    if (nameField in row) {
      (row as any)[nameField] = value.name
    }
    if (codeField in row && value.code) {
      (row as any)[codeField] = value.code
    }
  } else {
    // Clear the reference
    (row as any)[column.id] = null
    const nameField = `${column.id}_name`
    const codeField = `${column.id}_code`
    
    if (nameField in row) {
      (row as any)[nameField] = ''
    }
    if (codeField in row) {
      (row as any)[codeField] = ''
    }
  }
  
  emit('cell-changed', row, column.id, value)
}

function openReference(row: T, column: TableColumn, value: ReferenceValue) {
  emit('reference-open', row, column, value)
}

function selectReference(row: T, column: TableColumn, referenceType: string) {
  emit('reference-select', row, column, referenceType)
}

function fillRelatedFields(row: T, data: { referenceValue: ReferenceValue, relatedFields: string[] }) {
  emit('fill-related-fields', row, data.referenceValue, data.relatedFields)
}

function formatTotal(column: TableColumn): string {
  if (!column.showTotal) return ''
  
  const total = props.data.reduce((sum, row) => {
    const value = parseFloat(row[column.id as keyof T] as string) || 0
    return sum + value
  }, 0)
  
  if (column.type === 'currency') {
    return total.toFixed(2)
  } else if (column.type === 'number') {
    return total.toFixed(3)
  }
  
  return total.toString()
}

function toggleCommandVisibility(commandId: string, visible: boolean) {
  const newVisibleCommands = [...props.configuration.visibleCommands]
  
  if (visible && !newVisibleCommands.includes(commandId)) {
    newVisibleCommands.push(commandId)
  } else if (!visible) {
    const index = newVisibleCommands.indexOf(commandId)
    if (index > -1) {
      newVisibleCommands.splice(index, 1)
    }
  }
  
  const newConfig = {
    ...props.configuration,
    visibleCommands: newVisibleCommands
  }
  
  emit('configuration-changed', newConfig)
}

function saveCustomization() {
  showCustomizeDialog.value = false
  // Configuration is already updated through toggleCommandVisibility
}

// Keyboard shortcuts setup
function setupKeyboardHandler() {
  if (!keyboardHandler) {
    keyboardHandler = createKeyboardHandler()
    
    // Register action handlers
    keyboardHandler.registerActionHandler(ShortcutAction.ADD_ROW, () => executeCommand('add_row'))
    keyboardHandler.registerActionHandler(ShortcutAction.DELETE_ROW, () => executeCommand('delete_row'))
    keyboardHandler.registerActionHandler(ShortcutAction.COPY_ROWS, () => executeCommand('copy_rows'))
    keyboardHandler.registerActionHandler(ShortcutAction.PASTE_ROWS, () => executeCommand('paste_rows'))
    keyboardHandler.registerActionHandler(ShortcutAction.MOVE_ROW_UP, () => executeCommand('move_up'))
    keyboardHandler.registerActionHandler(ShortcutAction.MOVE_ROW_DOWN, () => executeCommand('move_down'))
    keyboardHandler.registerActionHandler(ShortcutAction.OPEN_REFERENCE_SELECTOR, () => executeCommand('open_reference_selector'))
    
    // Attach to container element
    const container = document.querySelector('.table-part-container') as HTMLElement
    if (container) {
      keyboardHandler.attachTo(container)
    }
  }
  
  // Update keyboard handler state
  keyboardHandler.setEnabled(props.configuration.keyboardShortcutsEnabled)
  updateKeyboardContext()
}

function updateKeyboardContext() {
  if (!keyboardHandler) return
  
  const container = document.querySelector('.table-part-container') as HTMLElement
  if (!container) return
  
  const context = createTableContext(
    container,
    selectedRows.value,
    selectedRows.value[0],
    false, // isHierarchical - override in hierarchical components
    isElementEditing(container)
  )
  
  keyboardHandler.updateContext(context)
}

// Lifecycle
onMounted(() => {
  // Initialize calculation engine
  initializeEngine()
  
  // Set up calculation engine event callbacks
  if (calculationEngine.value) {
    calculationEngine.value.setEventCallbacks({
      onCalculationCompleted: (row, column, result) => {
        emit('calculation-completed', row, column, result)
        
        // Update performance monitor
        if (performanceMonitor.value) {
          performanceMonitor.value.addCalculationResult(result)
          performanceMonitor.value.updateMetrics(calculationMetrics.value)
          performanceMonitor.value.showCalculationActivity()
        }
      },
      onTotalCalculationCompleted: (totals) => {
        emit('totals-calculated', totals)
        
        // Update performance monitor
        if (performanceMonitor.value) {
          performanceMonitor.value.updateMetrics(calculationMetrics.value)
        }
      },
      onCalculationError: (errorType, message) => {
        emit('calculation-error', errorType, message)
        
        // Show error indicator
        if (performanceMonitor.value) {
          performanceMonitor.value.showErrorActivity()
        }
      },
      onPerformanceAlert: (metricName, value) => {
        emit('performance-alert', metricName, value)
        
        // Show performance monitor on alerts
        showPerformanceMonitor.value = true
      }
    })
    
    // Set performance thresholds from configuration
    calculationEngine.value.setPerformanceThresholds(
      props.configuration.calculationTimeoutMs,
      props.configuration.totalCalculationTimeoutMs
    )
  }
  
  setupKeyboardHandler()
})

function onPerformanceStatusChanged(status: string) {
  console.log(`Performance status changed to: ${status}`)
  
  // Show performance monitor for warning/critical status
  if (status === 'warning' || status === 'critical') {
    showPerformanceMonitor.value = true
  }
}

function onThresholdExceeded(metricName: string, value: number) {
  console.warn(`Performance threshold exceeded - ${metricName}: ${value}`)
  
  // Show performance monitor
  showPerformanceMonitor.value = true
}

function togglePerformanceMonitor() {
  showPerformanceMonitor.value = !showPerformanceMonitor.value
}

// Drag and drop handlers
function handleDragStart(rowIndex: number, event: DragEvent) {
  if (!props.configuration.dragDropEnabled) {
    event.preventDefault()
    return
  }
  
  draggedRowIndex.value = rowIndex
  isDragging.value = true
  
  // Set drag data
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', rowIndex.toString())
    
    // Add visual feedback
    const target = event.target as HTMLElement
    target.style.opacity = '0.5'
  }
}

function handleDragOver(rowIndex: number, event: DragEvent) {
  if (!props.configuration.dragDropEnabled || !isDragging.value) {
    return
  }
  
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
  
  // Update drop zone highlighting
  dragOverRow.value = rowIndex
}

function handleDragLeave(rowIndex: number, event: DragEvent) {
  if (!props.configuration.dragDropEnabled) {
    return
  }
  
  // Clear drop zone highlighting if leaving the row
  const relatedTarget = event.relatedTarget as HTMLElement
  const currentTarget = event.currentTarget as HTMLElement
  
  if (!currentTarget.contains(relatedTarget)) {
    if (dragOverRow.value === rowIndex) {
      dragOverRow.value = null
    }
  }
}

function handleDrop(targetRowIndex: number, event: DragEvent) {
  if (!props.configuration.dragDropEnabled || draggedRowIndex.value === null) {
    return
  }
  
  event.preventDefault()
  
  const sourceRowIndex = draggedRowIndex.value
  
  if (sourceRowIndex !== targetRowIndex) {
    // Perform the row move
    moveRowToPosition(sourceRowIndex, targetRowIndex)
  }
  
  // Clean up drag state
  draggedRowIndex.value = null
  dragOverRow.value = null
  isDragging.value = false
}

function handleDragEnd(event: DragEvent) {
  // Clean up visual feedback
  const target = event.target as HTMLElement
  target.style.opacity = ''
  
  // Clean up drag state
  draggedRowIndex.value = null
  dragOverRow.value = null
  isDragging.value = false
}

function moveRowToPosition(sourceIndex: number, targetIndex: number) {
  if (sourceIndex === targetIndex) {
    return
  }
  
  // Create a copy of the data array
  const newData = [...props.data]
  
  // Remove the source row
  const [movedRow] = newData.splice(sourceIndex, 1)
  
  // Insert at target position
  newData.splice(targetIndex, 0, movedRow)
  
  // Update selection to follow moved row
  if (selectedRows.value.includes(sourceIndex)) {
    const newSelection = selectedRows.value.map(row => {
      if (row === sourceIndex) {
        return targetIndex
      } else if (sourceIndex < targetIndex) {
        // Moving down: rows between source and target shift up
        return row > sourceIndex && row <= targetIndex ? row - 1 : row
      } else {
        // Moving up: rows between target and source shift down
        return row >= targetIndex && row < sourceIndex ? row + 1 : row
      }
    })
    selectedRows.value = newSelection
  }
  
  // Emit data change
  emit('data-changed', -1, 'row_order', newData)
  
  // Trigger recalculation if enabled
  if (props.configuration.autoCalculationEnabled) {
    scheduleCalculation(-1, 'row_order')
  }
}

// Expose methods for parent components
defineExpose({
  togglePerformanceMonitor,
  showPerformanceMonitor: () => { showPerformanceMonitor.value = true },
  hidePerformanceMonitor: () => { showPerformanceMonitor.value = false },
  getPerformanceMetrics: () => calculationMetrics.value,
  getCalculationEngine: () => calculationEngine.value
})

onUnmounted(() => {
  if (keyboardHandler) {
    keyboardHandler.cleanup()
    keyboardHandler = null
  }
  
  if (calculationTimer) {
    clearTimeout(calculationTimer)
  }
  
  if (totalCalculationTimer) {
    clearTimeout(totalCalculationTimer)
  }
})
</script>

<style scoped>
.table-part-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.row-control-panel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.panel-buttons {
  display: flex;
  gap: 0.25rem;
}

.table-container {
  flex: 1;
  overflow: auto;
}

.table {
  width: 100%;
  margin-bottom: 0;
}

.table th {
  position: sticky;
  top: 0;
  background-color: #f8f9fa;
  border-top: none;
  font-weight: 600;
  white-space: nowrap;
}

.table th.sortable {
  cursor: pointer;
  user-select: none;
}

.table th.sortable:hover {
  background-color: #e9ecef;
}

.sort-indicator {
  margin-left: 0.25rem;
  font-size: 0.8rem;
}

.actions-column {
  width: 100px;
  text-align: center;
}

.row-selected {
  background-color: #e7f3ff !important;
}

.row-editing {
  background-color: #fff3cd !important;
}

.drag-over {
  background-color: #e3f2fd !important;
  border-top: 2px solid #2196f3;
}

tr[draggable="true"] {
  cursor: move;
}

tr[draggable="true"]:hover {
  background-color: #f5f5f5;
}

.dragging {
  opacity: 0.5;
}

.editable-cell {
  cursor: pointer;
}

.editable-cell:hover {
  background-color: #f8f9fa;
}

.cell-input {
  width: 100%;
  border: 1px solid #007bff;
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  font-size: inherit;
}

.cell-input:focus {
  outline: none;
  border-color: #0056b3;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.reference-field {
  position: relative;
  display: flex;
  align-items: center;
}

.reference-text {
  flex: 1;
  padding-right: 60px;
}

.compact-buttons {
  position: absolute;
  right: 4px;
  display: flex;
  gap: 2px;
}

.compact-button {
  width: 24px;
  height: 24px;
  border: 1px solid #999;
  background: #f5f5f5;
  border-radius: 2px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.compact-button:hover {
  background: #e9ecef;
  border-color: #666;
}

.empty-state {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 2rem;
}

.totals-row {
  background-color: #f8f9fa;
  font-weight: 600;
}

.text-right {
  text-align: right;
}

/* Dropdown styles */
.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
  min-width: 160px;
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.5rem 1rem;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
}

.dropdown-item:hover:not(.disabled) {
  background-color: #f8f9fa;
}

.dropdown-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.modal-dialog {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
}

.close-btn:hover {
  color: #000;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid #dee2e6;
}

.command-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.command-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.command-item input[type="checkbox"] {
  margin: 0;
}

.icon {
  font-size: 1rem;
  width: 1.5rem;
  text-align: center;
}

/* Button styles */
.btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c82333;
}

.btn-outline-secondary {
  background-color: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background-color: #6c757d;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.btn-xs {
  padding: 0.125rem 0.25rem;
  font-size: 0.75rem;
}
</style>