<template>
  <div class="table-part-example">
    <h2>Table Part Infrastructure Example</h2>
    
    <div class="example-section">
      <h3>Estimate Lines Table Part</h3>
      <BaseTablePart
        :data="estimateLines"
        :columns="estimateColumns"
        :configuration="estimateConfig"
        :get-row-key="(row, index) => row.id || index"
        :format-cell-value="formatCellValue"
        :is-row-selected="(index) => selectedRows.includes(index)"
        @row-selection-changed="handleRowSelectionChanged"
        @data-changed="handleDataChanged"
        @command-executed="handleCommandExecuted"
        @calculation-requested="handleCalculationRequested"
        @total-calculation-requested="handleTotalCalculationRequested"
        @reference-open="handleReferenceOpen"
        @reference-select="handleReferenceSelect"
        @configuration-changed="handleConfigurationChanged"
      />
    </div>
    
    <div class="example-section">
      <h3>Event Log</h3>
      <div class="event-log">
        <div
          v-for="(event, index) in eventLog"
          :key="index"
          class="event-item"
        >
          <span class="event-time">{{ event.time }}</span>
          <span class="event-type">{{ event.type }}</span>
          <span class="event-data">{{ event.data }}</span>
        </div>
      </div>
    </div>
    
    <div class="example-section">
      <h3>Configuration</h3>
      <div class="config-display">
        <pre>{{ JSON.stringify(estimateConfig, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import BaseTablePart from '@/components/common/BaseTablePart.vue'
import type { TableColumn, TablePartConfiguration, TablePartCommand } from '@/types/table-parts'

// Sample data for estimate lines
const estimateLines = ref([
  {
    id: 1,
    line_number: 1,
    work_id: 101,
    work_name: 'Земляные работы',
    quantity: 100.0,
    unit: 'м³',
    price: 150.00,
    sum: 15000.00,
    labor_rate: 2.5
  },
  {
    id: 2,
    line_number: 2,
    work_id: 102,
    work_name: 'Бетонные работы',
    quantity: 50.0,
    unit: 'м³',
    price: 300.00,
    sum: 15000.00,
    labor_rate: 4.0
  },
  {
    id: 3,
    line_number: 3,
    work_id: 103,
    work_name: 'Монтажные работы',
    quantity: 25.0,
    unit: 'т',
    price: 800.00,
    sum: 20000.00,
    labor_rate: 6.0
  }
])

// Define columns for estimate lines
const estimateColumns: TableColumn[] = [
  {
    id: 'line_number',
    name: '№',
    type: 'number',
    width: '60px',
    editable: false,
    sortable: true
  },
  {
    id: 'work_name',
    name: 'Работа',
    type: 'reference',
    width: '300px',
    editable: true,
    referenceType: 'works'
  },
  {
    id: 'quantity',
    name: 'Количество',
    type: 'number',
    width: '100px',
    editable: true,
    showTotal: true
  },
  {
    id: 'unit',
    name: 'Ед.изм',
    type: 'text',
    width: '80px',
    editable: false
  },
  {
    id: 'price',
    name: 'Цена',
    type: 'currency',
    width: '120px',
    editable: true
  },
  {
    id: 'sum',
    name: 'Сумма',
    type: 'currency',
    width: '120px',
    editable: false,
    showTotal: true
  },
  {
    id: 'labor_rate',
    name: 'Норма труда',
    type: 'number',
    width: '100px',
    editable: true
  }
]

// Create table part configuration
const estimateConfig: TablePartConfiguration = reactive({
  tableId: 'estimate_lines',
  documentType: 'estimate',
  availableCommands: [
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
    }
  ],
  visibleCommands: ['add_row', 'delete_row', 'move_up', 'move_down'],
  keyboardShortcutsEnabled: true,
  autoCalculationEnabled: true,
  dragDropEnabled: true,
  calculationTimeoutMs: 100,
  totalCalculationTimeoutMs: 200
})

// State
const selectedRows = ref<number[]>([])
const eventLog = ref<Array<{ time: string; type: string; data: string }>>([])

// Helper functions
function addEvent(type: string, data: any) {
  const time = new Date().toLocaleTimeString()
  eventLog.value.unshift({
    time,
    type,
    data: typeof data === 'object' ? JSON.stringify(data) : String(data)
  })
  
  // Keep only last 20 events
  if (eventLog.value.length > 20) {
    eventLog.value = eventLog.value.slice(0, 20)
  }
}

function formatCellValue(row: any, column: TableColumn): string {
  const value = row[column.id]
  
  if (value === null || value === undefined) {
    return ''
  }
  
  switch (column.type) {
    case 'currency':
      return typeof value === 'number' ? value.toFixed(2) : String(value)
    case 'number':
      return typeof value === 'number' ? value.toFixed(3) : String(value)
    case 'reference':
      // For reference fields, show the name if available
      if (column.id === 'work_name') {
        return row.work_name || `Work ${row.work_id}`
      }
      return String(value)
    default:
      return String(value)
  }
}

// Event handlers
function handleRowSelectionChanged(newSelectedRows: number[]) {
  selectedRows.value = newSelectedRows
  addEvent('Row Selection Changed', `Selected rows: [${newSelectedRows.join(', ')}]`)
}

function handleDataChanged(row: number, column: string, value: any) {
  // Update the data
  if (estimateLines.value[row]) {
    estimateLines.value[row][column as keyof typeof estimateLines.value[0]] = value
    
    // Trigger calculation if it's quantity or price
    if (column === 'quantity' || column === 'price') {
      const rowData = estimateLines.value[row]
      const newSum = (rowData.quantity || 0) * (rowData.price || 0)
      estimateLines.value[row].sum = newSum
    }
  }
  
  addEvent('Data Changed', `Row ${row}, Column ${column}, Value: ${value}`)
}

function handleCommandExecuted(commandId: string, context: any) {
  addEvent('Command Executed', `Command: ${commandId}`)
  
  switch (commandId) {
    case 'add_row':
      const newRow = {
        id: estimateLines.value.length + 1,
        line_number: estimateLines.value.length + 1,
        work_id: null,
        work_name: '',
        quantity: 0,
        unit: '',
        price: 0,
        sum: 0,
        labor_rate: 0
      }
      estimateLines.value.push(newRow)
      break
      
    case 'delete_row':
      if (context.selectedRows && context.selectedRows.length > 0) {
        // Sort in descending order to avoid index issues
        const sortedRows = [...context.selectedRows].sort((a, b) => b - a)
        for (const rowIndex of sortedRows) {
          estimateLines.value.splice(rowIndex, 1)
        }
        // Renumber lines
        estimateLines.value.forEach((line, index) => {
          line.line_number = index + 1
        })
        selectedRows.value = []
      }
      break
      
    case 'move_up':
      if (context.selectedRows && context.selectedRows.length > 0) {
        const firstSelected = Math.min(...context.selectedRows)
        if (firstSelected > 0) {
          // Move selected rows up
          for (const rowIndex of context.selectedRows.sort()) {
            const temp = estimateLines.value[rowIndex - 1]
            estimateLines.value[rowIndex - 1] = estimateLines.value[rowIndex]
            estimateLines.value[rowIndex] = temp
          }
          // Update selection
          selectedRows.value = context.selectedRows.map((i: number) => i - 1)
        }
      }
      break
      
    case 'move_down':
      if (context.selectedRows && context.selectedRows.length > 0) {
        const lastSelected = Math.max(...context.selectedRows)
        if (lastSelected < estimateLines.value.length - 1) {
          // Move selected rows down
          for (const rowIndex of context.selectedRows.sort().reverse()) {
            const temp = estimateLines.value[rowIndex + 1]
            estimateLines.value[rowIndex + 1] = estimateLines.value[rowIndex]
            estimateLines.value[rowIndex] = temp
          }
          // Update selection
          selectedRows.value = context.selectedRows.map((i: number) => i + 1)
        }
      }
      break
      
    case 'export_data':
      // Simulate export
      const csvData = estimateLines.value.map(row => 
        `${row.line_number},${row.work_name},${row.quantity},${row.unit},${row.price},${row.sum}`
      ).join('\n')
      console.log('Export data:', csvData)
      break
  }
}

function handleCalculationRequested(row: number, column: string) {
  addEvent('Calculation Requested', `Row ${row}, Column ${column}`)
  
  // Perform calculation for sum field
  if (column === 'quantity' || column === 'price') {
    const rowData = estimateLines.value[row]
    if (rowData) {
      const newSum = (rowData.quantity || 0) * (rowData.price || 0)
      rowData.sum = newSum
    }
  }
}

function handleTotalCalculationRequested() {
  addEvent('Total Calculation Requested', 'Calculating totals')
  
  // Calculate totals (this would typically update footer totals)
  const totalQuantity = estimateLines.value.reduce((sum, row) => sum + (row.quantity || 0), 0)
  const totalSum = estimateLines.value.reduce((sum, row) => sum + (row.sum || 0), 0)
  
  console.log('Totals calculated:', { totalQuantity, totalSum })
}

function handleReferenceOpen(row: any, column: TableColumn) {
  addEvent('Reference Open', `Row: ${row.line_number}, Column: ${column.name}`)
  // This would typically open a reference form
  alert(`Opening reference for ${column.name} in row ${row.line_number}`)
}

function handleReferenceSelect(row: any, column: TableColumn) {
  addEvent('Reference Select', `Row: ${row.line_number}, Column: ${column.name}`)
  // This would typically open a selection dialog
  alert(`Selecting reference for ${column.name} in row ${row.line_number}`)
}

function handleConfigurationChanged(newConfig: TablePartConfiguration) {
  addEvent('Configuration Changed', 'Panel configuration updated')
  // Update the configuration
  Object.assign(estimateConfig, newConfig)
}
</script>

<style scoped>
.table-part-example {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.example-section {
  margin-bottom: 2rem;
  border: 1px solid #dee2e6;
  border-radius: 0.5rem;
  padding: 1rem;
}

.example-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #495057;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 0.5rem;
}

.event-log {
  max-height: 300px;
  overflow-y: auto;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 0.5rem;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

.event-item {
  display: flex;
  gap: 1rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid #e9ecef;
}

.event-item:last-child {
  border-bottom: none;
}

.event-time {
  color: #6c757d;
  min-width: 80px;
}

.event-type {
  color: #007bff;
  font-weight: 600;
  min-width: 150px;
}

.event-data {
  color: #495057;
  flex: 1;
  word-break: break-all;
}

.config-display {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 1rem;
  overflow-x: auto;
}

.config-display pre {
  margin: 0;
  font-size: 0.875rem;
  color: #495057;
}
</style>