<template>
  <div class="example-container">
    <h1>Row Control Panel Example</h1>
    <p class="description">
      This example demonstrates the row control panel with command manager integration.
    </p>
    
    <!-- Row Control Panel -->
    <RowControlPanel
      :visible-commands="visibleCommands"
      :has-selection="hasSelection"
      :has-rows="hasRows"
      :is-first-row-selected="isFirstRowSelected"
      :is-last-row-selected="isLastRowSelected"
      :selected-rows="selectedRows"
      :table-data="tableData"
      :form-instance="formInstance"
      @command-triggered="handleCommand"
      @command-executed="handleCommandExecuted"
      @customize-requested="handleCustomize"
    />
    
    <!-- Table -->
    <div class="table-container">
      <table class="table">
        <thead>
          <tr>
            <th>
              <input 
                type="checkbox" 
                :checked="allSelected"
                @change="toggleAllSelection"
              />
            </th>
            <th>Name</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(row, index) in tableData" 
            :key="index"
            :class="{ selected: selectedRows.includes(index) }"
            @click="toggleRowSelection(index, $event)"
          >
            <td>
              <input 
                type="checkbox" 
                :checked="selectedRows.includes(index)"
                @change="toggleRowSelection(index)"
              />
            </td>
            <td>
              <input 
                v-model="row.name" 
                type="text" 
                class="cell-input"
                @input="calculateTotal(index)"
              />
            </td>
            <td>
              <input 
                v-model.number="row.quantity" 
                type="number" 
                class="cell-input"
                @input="calculateTotal(index)"
              />
            </td>
            <td>
              <input 
                v-model.number="row.price" 
                type="number" 
                step="0.01"
                class="cell-input"
                @input="calculateTotal(index)"
              />
            </td>
            <td class="total-cell">
              {{ formatCurrency(row.total) }}
            </td>
          </tr>
          <tr v-if="tableData.length === 0">
            <td colspan="5" class="empty-message">
              No data available. Click "Add" to create a new row.
            </td>
          </tr>
        </tbody>
        <tfoot v-if="tableData.length > 0">
          <tr class="totals-row">
            <td></td>
            <td><strong>Total:</strong></td>
            <td><strong>{{ totalQuantity }}</strong></td>
            <td></td>
            <td><strong>{{ formatCurrency(grandTotal) }}</strong></td>
          </tr>
        </tfoot>
      </table>
    </div>
    
    <!-- Status Messages -->
    <div v-if="statusMessage" class="status-message" :class="statusType">
      {{ statusMessage }}
    </div>
    
    <!-- Command Log -->
    <div class="command-log">
      <h3>Command Log</h3>
      <div class="log-entries">
        <div 
          v-for="(entry, index) in commandLog" 
          :key="index"
          class="log-entry"
          :class="entry.type"
        >
          <span class="timestamp">{{ entry.timestamp }}</span>
          <span class="command">{{ entry.command }}</span>
          <span class="message">{{ entry.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import RowControlPanel from '../components/common/RowControlPanel.vue'
import { createCommandManager, tableCommand, CommandAvailability, type CommandContext, type CommandResult } from '../services/tablePartCommandManager'

// ============================================================================
// Types
// ============================================================================

interface TableRow {
  name: string
  quantity: number
  price: number
  total: number
}

interface LogEntry {
  timestamp: string
  command: string
  message: string
  type: 'success' | 'error' | 'info'
}

// ============================================================================
// Reactive State
// ============================================================================

const tableData = ref<TableRow[]>([])
const selectedRows = ref<number[]>([])
const visibleCommands = ref<string[]>([
  'add_row',
  'delete_row',
  'move_up',
  'move_down',
  'import_data',
  'export_data',
  'print_data'
])
const statusMessage = ref<string>('')
const statusType = ref<'success' | 'error' | 'info'>('info')
const commandLog = ref<LogEntry[]>([])

// ============================================================================
// Form Instance (Mock)
// ============================================================================

class ExampleFormInstance {
  // Commands discovered by naming convention
  addRow(): boolean {
    const newRow: TableRow = {
      name: `Item ${tableData.value.length + 1}`,
      quantity: 1,
      price: 10.00,
      total: 10.00
    }
    tableData.value.push(newRow)
    logCommand('add_row', 'Added new row', 'success')
    return true
  }

  deleteRow(): boolean {
    if (selectedRows.value.length === 0) {
      logCommand('delete_row', 'No rows selected', 'error')
      return false
    }

    // Remove rows in reverse order to maintain indices
    const rowsToDelete = [...selectedRows.value].sort((a, b) => b - a)
    rowsToDelete.forEach(index => {
      tableData.value.splice(index, 1)
    })
    
    selectedRows.value = []
    logCommand('delete_row', `Deleted ${rowsToDelete.length} rows`, 'success')
    return true
  }

  moveUp(): boolean {
    if (selectedRows.value.length === 0 || selectedRows.value.includes(0)) {
      logCommand('move_up', 'Cannot move up: no selection or first row selected', 'error')
      return false
    }

    logCommand('move_up', 'Moved rows up', 'success')
    return true
  }

  moveDown(): boolean {
    const lastIndex = tableData.value.length - 1
    if (selectedRows.value.length === 0 || selectedRows.value.includes(lastIndex)) {
      logCommand('move_down', 'Cannot move down: no selection or last row selected', 'error')
      return false
    }

    logCommand('move_down', 'Moved rows down', 'success')
    return true
  }

  importData(): boolean {
    // Simulate importing data
    const importedData: TableRow[] = [
      { name: 'Imported Item 1', quantity: 5, price: 15.00, total: 75.00 },
      { name: 'Imported Item 2', quantity: 3, price: 25.00, total: 75.00 }
    ]
    
    tableData.value.push(...importedData)
    logCommand('import_data', `Imported ${importedData.length} rows`, 'success')
    return true
  }

  exportData(): boolean {
    // Simulate exporting data
    const dataToExport = JSON.stringify(tableData.value, null, 2)
    console.log('Exported data:', dataToExport)
    logCommand('export_data', `Exported ${tableData.value.length} rows`, 'success')
    return true
  }

  printData(): boolean {
    // Simulate printing
    window.print()
    logCommand('print_data', 'Sent to printer', 'success')
    return true
  }

  @tableCommand({
    id: 'duplicate_row',
    name: 'Duplicate Row',
    availability: CommandAvailability.REQUIRES_SELECTION
  })
  duplicateSelectedRow(context: CommandContext): CommandResult {
    if (context.selectedRows.length === 0) {
      return {
        success: false,
        message: 'No row selected',
        affectedRows: [],
        refreshRequired: false
      }
    }

    const rowToDuplicate = context.selectedRows[0]
    const originalRow = tableData.value[rowToDuplicate]
    const duplicatedRow = { ...originalRow }
    
    tableData.value.push(duplicatedRow)
    
    logCommand('duplicate_row', `Duplicated row ${rowToDuplicate}`, 'success')
    
    return {
      success: true,
      message: 'Row duplicated successfully',
      affectedRows: [tableData.value.length - 1],
      refreshRequired: true
    }
  }
}

const formInstance = ref(new ExampleFormInstance())

// ============================================================================
// Computed Properties
// ============================================================================

const hasSelection = computed(() => selectedRows.value.length > 0)
const hasRows = computed(() => tableData.value.length > 0)
const isFirstRowSelected = computed(() => selectedRows.value.includes(0))
const isLastRowSelected = computed(() => 
  selectedRows.value.includes(tableData.value.length - 1)
)
const allSelected = computed(() => 
  tableData.value.length > 0 && selectedRows.value.length === tableData.value.length
)

const totalQuantity = computed(() => 
  tableData.value.reduce((sum, row) => sum + (row.quantity || 0), 0)
)

const grandTotal = computed(() => 
  tableData.value.reduce((sum, row) => sum + (row.total || 0), 0)
)

// ============================================================================
// Methods
// ============================================================================

function toggleRowSelection(index: number, event?: Event) {
  if (event && (event as MouseEvent).ctrlKey) {
    // Multi-select with Ctrl
    const idx = selectedRows.value.indexOf(index)
    if (idx > -1) {
      selectedRows.value.splice(idx, 1)
    } else {
      selectedRows.value.push(index)
    }
  } else {
    // Single select
    selectedRows.value = selectedRows.value.includes(index) ? [] : [index]
  }
}

function toggleAllSelection() {
  if (allSelected.value) {
    selectedRows.value = []
  } else {
    selectedRows.value = Array.from({ length: tableData.value.length }, (_, i) => i)
  }
}

function calculateTotal(index: number) {
  const row = tableData.value[index]
  row.total = (row.quantity || 0) * (row.price || 0)
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value || 0)
}

function logCommand(command: string, message: string, type: 'success' | 'error' | 'info') {
  const timestamp = new Date().toLocaleTimeString()
  commandLog.value.unshift({
    timestamp,
    command,
    message,
    type
  })
  
  // Keep only last 10 entries
  if (commandLog.value.length > 10) {
    commandLog.value = commandLog.value.slice(0, 10)
  }
  
  // Show status message
  statusMessage.value = message
  statusType.value = type
  
  // Clear status after 3 seconds
  setTimeout(() => {
    statusMessage.value = ''
  }, 3000)
}

function handleCommand(commandId: string) {
  logCommand(commandId, `Command ${commandId} triggered`, 'info')
}

function handleCommandExecuted(commandId: string, result: any) {
  if (result.success) {
    logCommand(commandId, result.message || 'Command executed successfully', 'success')
  } else {
    logCommand(commandId, result.message || 'Command failed', 'error')
  }
}

function handleCustomize() {
  // Toggle visibility of import/export commands
  const currentCommands = [...visibleCommands.value]
  
  if (currentCommands.includes('import_data')) {
    const index = currentCommands.indexOf('import_data')
    currentCommands.splice(index, 1)
    logCommand('customize', 'Hidden import command', 'info')
  } else {
    currentCommands.push('import_data')
    logCommand('customize', 'Shown import command', 'info')
  }
  
  visibleCommands.value = currentCommands
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  // Add some sample data
  const sampleData: TableRow[] = [
    { name: 'Item 1', quantity: 10, price: 25.50, total: 255.00 },
    { name: 'Item 2', quantity: 5, price: 15.00, total: 75.00 },
    { name: 'Item 3', quantity: 8, price: 30.75, total: 246.00 }
  ]
  
  tableData.value = sampleData
  
  logCommand('init', 'Example initialized with sample data', 'info')
})
</script>

<style scoped>
.example-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.description {
  color: #6c757d;
  margin-bottom: 2rem;
}

.table-container {
  margin: 1rem 0;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  overflow: hidden;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

.table th,
.table td {
  padding: 0.75rem;
  border-bottom: 1px solid #dee2e6;
  text-align: left;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
}

.table tr.selected {
  background-color: #e7f3ff;
}

.table tr:hover {
  background-color: #f8f9fa;
}

.cell-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 0.25rem;
  font-size: inherit;
}

.cell-input:focus {
  outline: 1px solid #007bff;
  background-color: white;
  border-radius: 0.25rem;
}

.total-cell {
  font-weight: 600;
  text-align: right;
}

.totals-row {
  background-color: #f8f9fa;
  font-weight: 600;
}

.totals-row td {
  border-top: 2px solid #dee2e6;
}

.empty-message {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 2rem;
}

.status-message {
  padding: 0.75rem 1rem;
  border-radius: 0.25rem;
  margin: 1rem 0;
  font-weight: 500;
}

.status-message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.status-message.info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.command-log {
  margin-top: 2rem;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  background-color: #f8f9fa;
}

.command-log h3 {
  margin: 0;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  background-color: white;
  font-size: 1.1rem;
}

.log-entries {
  max-height: 200px;
  overflow-y: auto;
  padding: 0.5rem;
}

.log-entry {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  border-radius: 0.25rem;
  margin-bottom: 0.25rem;
  font-family: monospace;
  font-size: 0.875rem;
}

.log-entry.success {
  background-color: #d4edda;
  color: #155724;
}

.log-entry.error {
  background-color: #f8d7da;
  color: #721c24;
}

.log-entry.info {
  background-color: #d1ecf1;
  color: #0c5460;
}

.log-entry .timestamp {
  font-weight: 600;
  min-width: 80px;
}

.log-entry .command {
  font-weight: 600;
  min-width: 120px;
}

.log-entry .message {
  flex: 1;
}

/* Responsive design */
@media (max-width: 768px) {
  .example-container {
    padding: 1rem;
  }
  
  .table th,
  .table td {
    padding: 0.5rem;
    font-size: 0.875rem;
  }
  
  .log-entry {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .log-entry .timestamp,
  .log-entry .command {
    min-width: auto;
  }
}
</style>