<template>
  <div class="keyboard-shortcuts-demo">
    <div class="demo-header">
      <h2>Table Part Keyboard Shortcuts Demo</h2>
      <p class="instructions">
        Try these keyboard shortcuts:
      </p>
      <ul class="shortcut-list">
        <li><kbd>Insert</kbd> - Add new row</li>
        <li><kbd>Delete</kbd> - Delete selected rows</li>
        <li><kbd>Ctrl+C</kbd> - Copy selected rows</li>
        <li><kbd>Ctrl+V</kbd> - Paste rows</li>
        <li><kbd>Ctrl+Shift+↑/↓</kbd> - Move rows</li>
        <li><kbd>F4</kbd> - Open reference selector</li>
        <li><kbd>Ctrl++</kbd> / <kbd>Ctrl+-</kbd> - Add/Delete rows (alternative)</li>
      </ul>
    </div>

    <div class="demo-content">
      <div class="table-container" ref="tableContainer">
        <table class="demo-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Value</th>
              <th>Description</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in tableData"
              :key="row.id"
              :class="{ 'row-selected': selectedRows.includes(index) }"
              @click="handleRowClick(index, $event)"
            >
              <td>
                <input
                  v-if="editingRow === index && editingColumn === 'name'"
                  v-model="editingValue"
                  @blur="saveEdit"
                  @keyup.enter="saveEdit"
                  @keyup.esc="cancelEdit"
                  ref="editInput"
                />
                <span v-else @dblclick="startEdit(index, 'name')">{{ row.name }}</span>
              </td>
              <td>
                <input
                  v-if="editingRow === index && editingColumn === 'value'"
                  v-model="editingValue"
                  type="number"
                  @blur="saveEdit"
                  @keyup.enter="saveEdit"
                  @keyup.esc="cancelEdit"
                  ref="editInput"
                />
                <span v-else @dblclick="startEdit(index, 'value')">{{ row.value }}</span>
              </td>
              <td>
                <input
                  v-if="editingRow === index && editingColumn === 'description'"
                  v-model="editingValue"
                  @blur="saveEdit"
                  @keyup.enter="saveEdit"
                  @keyup.esc="cancelEdit"
                  ref="editInput"
                />
                <span v-else @dblclick="startEdit(index, 'description')">{{ row.description }}</span>
              </td>
              <td>
                <button @click="deleteRow(index)" class="btn btn-sm btn-danger">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="controls">
        <button @click="clearLog" class="btn btn-secondary">Clear Log</button>
        <button @click="showHelp" class="btn btn-info">Show Help</button>
        <button @click="toggleHierarchical" class="btn btn-outline-secondary">
          {{ isHierarchical ? 'Disable' : 'Enable' }} Hierarchical Mode
        </button>
      </div>

      <div class="log-area">
        <h4>Action Log:</h4>
        <div class="log-content" ref="logContent">
          <div v-for="(entry, index) in logEntries" :key="index" class="log-entry">
            • {{ entry }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import {
  TablePartKeyboardHandler,
  ShortcutAction,
  ShortcutContext,
  createKeyboardHandler,
  createTableContext,
  isElementEditing
} from '../services/tablePartKeyboardHandler'

// Reactive data
const tableData = ref([
  { id: 1, name: 'Item 1', value: 100, description: 'First item' },
  { id: 2, name: 'Item 2', value: 200, description: 'Second item' },
  { id: 3, name: 'Item 3', value: 300, description: 'Third item' },
  { id: 4, name: 'Item 4', value: 400, description: 'Fourth item' },
  { id: 5, name: 'Item 5', value: 500, description: 'Fifth item' }
])

const selectedRows = ref<number[]>([])
const logEntries = ref<string[]>([])
const isHierarchical = ref(false)

// Editing state
const editingRow = ref<number | null>(null)
const editingColumn = ref<string | null>(null)
const editingValue = ref<any>(null)

// Copied data for paste functionality
const copiedData = ref<any[]>([])

// Refs
const tableContainer = ref<HTMLElement>()
const logContent = ref<HTMLElement>()
const editInput = ref<HTMLInputElement>()

// Keyboard handler
let keyboardHandler: TablePartKeyboardHandler | null = null

// Methods
function setupKeyboardHandler() {
  if (!tableContainer.value) return

  keyboardHandler = createKeyboardHandler()
  
  // Register action handlers
  keyboardHandler.registerActionHandler(ShortcutAction.ADD_ROW, handleAddRow)
  keyboardHandler.registerActionHandler(ShortcutAction.DELETE_ROW, handleDeleteRow)
  keyboardHandler.registerActionHandler(ShortcutAction.COPY_ROWS, handleCopyRows)
  keyboardHandler.registerActionHandler(ShortcutAction.PASTE_ROWS, handlePasteRows)
  keyboardHandler.registerActionHandler(ShortcutAction.MOVE_ROW_UP, handleMoveRowUp)
  keyboardHandler.registerActionHandler(ShortcutAction.MOVE_ROW_DOWN, handleMoveRowDown)
  keyboardHandler.registerActionHandler(ShortcutAction.OPEN_REFERENCE_SELECTOR, handleOpenReferenceSelector)
  
  // Hierarchical shortcuts
  keyboardHandler.registerActionHandler(ShortcutAction.EXPAND_NODE, handleExpandNode)
  keyboardHandler.registerActionHandler(ShortcutAction.COLLAPSE_NODE, handleCollapseNode)
  keyboardHandler.registerActionHandler(ShortcutAction.GO_TO_FIRST, handleGoToFirst)
  keyboardHandler.registerActionHandler(ShortcutAction.GO_TO_LAST, handleGoToLast)
  
  // Attach to container
  keyboardHandler.attachTo(tableContainer.value)
  
  // Update initial context
  updateKeyboardContext()
  
  log('Demo initialized. Try using keyboard shortcuts!')
}

function updateKeyboardContext() {
  if (!keyboardHandler || !tableContainer.value) return

  const context = createTableContext(
    tableContainer.value,
    selectedRows.value,
    selectedRows.value[0],
    isHierarchical.value,
    isElementEditing(tableContainer.value)
  )

  keyboardHandler.updateContext(context)
}

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
  
  updateKeyboardContext()
}

async function startEdit(rowIndex: number, columnId: string) {
  editingRow.value = rowIndex
  editingColumn.value = columnId
  editingValue.value = tableData.value[rowIndex][columnId as keyof typeof tableData.value[0]]
  
  await nextTick()
  editInput.value?.focus()
  editInput.value?.select()
  
  updateKeyboardContext()
}

function saveEdit() {
  if (editingRow.value !== null && editingColumn.value !== null) {
    const row = tableData.value[editingRow.value]
    ;(row as any)[editingColumn.value] = editingValue.value
    log(`Updated ${editingColumn.value} in row ${editingRow.value} to: ${editingValue.value}`)
  }
  
  cancelEdit()
}

function cancelEdit() {
  editingRow.value = null
  editingColumn.value = null
  editingValue.value = null
  updateKeyboardContext()
}

// Keyboard action handlers
function handleAddRow() {
  const newId = Math.max(...tableData.value.map(r => r.id)) + 1
  const newRow = {
    id: newId,
    name: `New Item ${newId}`,
    value: 0,
    description: 'New item description'
  }
  
  tableData.value.push(newRow)
  log(`Added new row: ${newRow.name}`)
}

function handleDeleteRow() {
  if (selectedRows.value.length === 0) {
    log('No rows selected for deletion')
    return
  }
  
  // Sort in reverse order to delete from bottom up
  const rowsToDelete = [...selectedRows.value].sort((a, b) => b - a)
  
  for (const rowIndex of rowsToDelete) {
    tableData.value.splice(rowIndex, 1)
  }
  
  selectedRows.value = []
  log(`Deleted ${rowsToDelete.length} row(s)`)
  updateKeyboardContext()
}

function handleCopyRows() {
  if (selectedRows.value.length === 0) {
    log('No rows selected for copying')
    return
  }
  
  copiedData.value = selectedRows.value.map(index => ({ ...tableData.value[index] }))
  log(`Copied ${selectedRows.value.length} row(s)`)
}

function handlePasteRows() {
  if (copiedData.value.length === 0) {
    log('No data to paste')
    return
  }
  
  const insertIndex = selectedRows.value[0] || tableData.value.length
  
  for (let i = 0; i < copiedData.value.length; i++) {
    const newRow = { ...copiedData.value[i] }
    newRow.id = Math.max(...tableData.value.map(r => r.id)) + 1 + i
    newRow.name = `${newRow.name} (Copy)`
    
    tableData.value.splice(insertIndex + i, 0, newRow)
  }
  
  log(`Pasted ${copiedData.value.length} row(s) at position ${insertIndex}`)
}

function handleMoveRowUp() {
  if (selectedRows.value.length === 0) {
    log('No rows selected for moving')
    return
  }
  
  if (selectedRows.value.includes(0)) {
    log('Cannot move up: first row is selected')
    return
  }
  
  const sortedRows = [...selectedRows.value].sort((a, b) => a - b)
  
  for (const rowIndex of sortedRows) {
    const row = tableData.value[rowIndex]
    tableData.value.splice(rowIndex, 1)
    tableData.value.splice(rowIndex - 1, 0, row)
  }
  
  // Update selection
  selectedRows.value = sortedRows.map(index => index - 1)
  log(`Moved row(s) up: ${sortedRows}`)
  updateKeyboardContext()
}

function handleMoveRowDown() {
  if (selectedRows.value.length === 0) {
    log('No rows selected for moving')
    return
  }
  
  if (selectedRows.value.includes(tableData.value.length - 1)) {
    log('Cannot move down: last row is selected')
    return
  }
  
  const sortedRows = [...selectedRows.value].sort((a, b) => b - a)
  
  for (const rowIndex of sortedRows) {
    const row = tableData.value[rowIndex]
    tableData.value.splice(rowIndex, 1)
    tableData.value.splice(rowIndex + 1, 0, row)
  }
  
  // Update selection
  selectedRows.value = sortedRows.map(index => index + 1)
  log(`Moved row(s) down: ${sortedRows}`)
  updateKeyboardContext()
}

function handleOpenReferenceSelector() {
  const currentRow = selectedRows.value[0]
  if (currentRow !== undefined) {
    log(`Opening reference selector for row ${currentRow}`)
  } else {
    log('Opening reference selector (no specific row)')
  }
}

// Hierarchical navigation handlers
function handleExpandNode() {
  log('Expand node (hierarchical mode)')
}

function handleCollapseNode() {
  log('Collapse node (hierarchical mode)')
}

function handleGoToFirst() {
  selectedRows.value = [0]
  log('Navigate to first item')
  updateKeyboardContext()
}

function handleGoToLast() {
  selectedRows.value = [tableData.value.length - 1]
  log('Navigate to last item')
  updateKeyboardContext()
}

// Utility functions
function deleteRow(index: number) {
  selectedRows.value = [index]
  handleDeleteRow()
}

function log(message: string) {
  logEntries.value.push(message)
  
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
}

function clearLog() {
  logEntries.value = []
  log('Log cleared')
}

function showHelp() {
  if (keyboardHandler) {
    const helpText = keyboardHandler.getShortcutHelpText()
    log('=== Keyboard Shortcuts Help ===')
    for (const line of helpText.split('\n')) {
      if (line.trim()) {
        log(line)
      }
    }
    log('=== End Help ===')
  }
}

function toggleHierarchical() {
  isHierarchical.value = !isHierarchical.value
  updateKeyboardContext()
  log(`Hierarchical mode ${isHierarchical.value ? 'enabled' : 'disabled'}`)
}

// Lifecycle
onMounted(() => {
  setupKeyboardHandler()
})

onUnmounted(() => {
  if (keyboardHandler) {
    keyboardHandler.cleanup()
  }
})
</script>

<style scoped>
.keyboard-shortcuts-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.demo-header {
  margin-bottom: 30px;
}

.demo-header h2 {
  color: #333;
  margin-bottom: 15px;
}

.instructions {
  margin-bottom: 10px;
  color: #666;
}

.shortcut-list {
  list-style: none;
  padding: 0;
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.shortcut-list li {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

kbd {
  background-color: #e9ecef;
  border: 1px solid #adb5bd;
  border-radius: 3px;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2);
  color: #495057;
  display: inline-block;
  font-size: 0.85em;
  font-weight: 700;
  line-height: 1;
  padding: 2px 4px;
  white-space: nowrap;
  margin-right: 8px;
  min-width: 120px;
}

.demo-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.table-container {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.demo-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

.demo-table th,
.demo-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.demo-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.demo-table tr:hover {
  background-color: #f8f9fa;
}

.demo-table tr.row-selected {
  background-color: #e7f3ff !important;
}

.demo-table td input {
  width: 100%;
  border: 1px solid #007bff;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: inherit;
}

.demo-table td input:focus {
  outline: none;
  border-color: #0056b3;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.demo-table td span {
  cursor: pointer;
  display: block;
  padding: 4px 0;
}

.demo-table td span:hover {
  background-color: rgba(0, 123, 255, 0.1);
  border-radius: 2px;
}

.controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn-info:hover {
  background-color: #138496;
}

.btn-outline-secondary {
  background-color: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-outline-secondary:hover {
  background-color: #6c757d;
  color: white;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.log-area {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
}

.log-area h4 {
  margin: 0 0 10px 0;
  color: #495057;
}

.log-content {
  max-height: 200px;
  overflow-y: auto;
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 10px;
}

.log-entry {
  margin-bottom: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #495057;
}

.log-entry:last-child {
  margin-bottom: 0;
}

/* Scrollbar styling */
.log-content::-webkit-scrollbar {
  width: 8px;
}

.log-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.log-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>