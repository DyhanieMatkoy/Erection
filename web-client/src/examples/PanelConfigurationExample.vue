<template>
  <div class="panel-configuration-example">
    <div class="example-header">
      <h1>Panel Configuration Example</h1>
      <p>This example demonstrates the panel configuration dialog functionality.</p>
    </div>
    
    <div class="example-content">
      <!-- Row Control Panel -->
      <div class="panel-section">
        <h2>Row Control Panel</h2>
        <p>Click the ⚙️ button to customize the panel commands.</p>
        
        <RowControlPanel
          :visible-commands="currentVisibleCommands"
          :has-selection="hasSelection"
          :has-rows="hasRows"
          :is-first-row-selected="isFirstRowSelected"
          :is-last-row-selected="isLastRowSelected"
          :selected-rows="selectedRows"
          :table-data="tableData"
          @command-triggered="onCommandTriggered"
          @configuration-changed="onConfigurationChanged"
        />
      </div>
      
      <!-- Manual Configuration Button -->
      <div class="controls-section">
        <h2>Manual Configuration</h2>
        <button 
          class="btn btn-primary"
          @click="showConfigDialog = true"
        >
          Open Configuration Dialog
        </button>
      </div>
      
      <!-- Current Configuration Display -->
      <div class="config-display">
        <h2>Current Configuration</h2>
        <div class="config-info">
          <div class="config-item">
            <strong>Visible Commands:</strong>
            <ul>
              <li v-for="cmd in currentVisibleCommands" :key="cmd">
                {{ getCommandName(cmd) }} ({{ cmd }})
              </li>
            </ul>
          </div>
          <div class="config-item">
            <strong>Hidden Commands:</strong>
            <ul>
              <li v-for="cmd in hiddenCommands" :key="cmd">
                {{ getCommandName(cmd) }} ({{ cmd }})
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <!-- Example Table Data -->
      <div class="table-section">
        <h2>Example Table Data</h2>
        <p>Use these controls to simulate different table states:</p>
        
        <div class="table-controls">
          <label>
            <input type="checkbox" v-model="hasRows" />
            Has Rows
          </label>
          <label>
            <input type="checkbox" v-model="hasSelection" :disabled="!hasRows" />
            Has Selection
          </label>
          <label>
            <input type="checkbox" v-model="isFirstRowSelected" :disabled="!hasSelection" />
            First Row Selected
          </label>
          <label>
            <input type="checkbox" v-model="isLastRowSelected" :disabled="!hasSelection" />
            Last Row Selected
          </label>
        </div>
        
        <div class="table-data">
          <strong>Table Data:</strong> {{ tableData.length }} rows
          <br>
          <strong>Selected Rows:</strong> {{ selectedRows.join(', ') || 'None' }}
        </div>
      </div>
    </div>
    
    <!-- Panel Configuration Dialog -->
    <PanelConfigurationDialog
      :is-visible="showConfigDialog"
      :current-config="currentConfig"
      :available-commands="availableCommands"
      @close="showConfigDialog = false"
      @save="onConfigurationSaved"
      @preview="onPreviewConfiguration"
      @configuration-changed="onConfigurationPreview"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import RowControlPanel from '../components/common/RowControlPanel.vue'
import PanelConfigurationDialog from '../components/common/PanelConfigurationDialog.vue'

// ============================================================================
// Types
// ============================================================================

interface CommandTreeNode {
  id: string
  name: string
  icon: string
  tooltip: string
  visible?: boolean
  enabled?: boolean
  isStandard?: boolean
}

interface PanelConfiguration {
  visibleCommands: string[]
  showTooltips: boolean
  compactMode: boolean
}

// ============================================================================
// State
// ============================================================================

const showConfigDialog = ref(false)

// Table state simulation
const hasRows = ref(true)
const hasSelection = ref(false)
const isFirstRowSelected = ref(false)
const isLastRowSelected = ref(false)

// Current panel configuration
const currentVisibleCommands = ref([
  'add_row',
  'delete_row',
  'move_up',
  'move_down',
  'import_data',
  'export_data',
  'print_data'
])

// Available commands
const availableCommands: Record<string, CommandTreeNode> = {
  add_row: {
    id: 'add_row',
    name: 'Добавить',
    icon: '➕',
    tooltip: 'Добавить новую строку (Insert)',
    enabled: true,
    isStandard: true
  },
  delete_row: {
    id: 'delete_row',
    name: 'Удалить',
    icon: '🗑',
    tooltip: 'Удалить выбранные строки (Delete)',
    enabled: true,
    isStandard: true
  },
  move_up: {
    id: 'move_up',
    name: 'Переместить выше',
    icon: '↑',
    tooltip: 'Переместить строки выше (Ctrl+Shift+Up)',
    enabled: true,
    isStandard: true
  },
  move_down: {
    id: 'move_down',
    name: 'Переместить ниже',
    icon: '↓',
    tooltip: 'Переместить строки ниже (Ctrl+Shift+Down)',
    enabled: true,
    isStandard: true
  },
  import_data: {
    id: 'import_data',
    name: 'Импорт',
    icon: '📥',
    tooltip: 'Импортировать данные из файла',
    enabled: true,
    isStandard: true
  },
  export_data: {
    id: 'export_data',
    name: 'Экспорт',
    icon: '📤',
    tooltip: 'Экспортировать данные в файл',
    enabled: true,
    isStandard: true
  },
  print_data: {
    id: 'print_data',
    name: 'Печать',
    icon: '🖨',
    tooltip: 'Печать табличной части',
    enabled: true,
    isStandard: true
  }
}

// ============================================================================
// Computed Properties
// ============================================================================

const currentConfig = computed((): PanelConfiguration => ({
  visibleCommands: currentVisibleCommands.value,
  showTooltips: true,
  compactMode: false
}))

const hiddenCommands = computed(() => {
  return Object.keys(availableCommands).filter(
    id => !currentVisibleCommands.value.includes(id)
  )
})

const selectedRows = computed(() => {
  if (!hasSelection.value) return []
  
  const rows = []
  if (isFirstRowSelected.value) rows.push(0)
  if (isLastRowSelected.value && tableData.value.length > 1) {
    rows.push(tableData.value.length - 1)
  }
  
  return rows
})

const tableData = computed(() => {
  if (!hasRows.value) return []
  
  return [
    { id: 1, name: 'Row 1', value: 100 },
    { id: 2, name: 'Row 2', value: 200 },
    { id: 3, name: 'Row 3', value: 300 }
  ]
})

// ============================================================================
// Methods
// ============================================================================

function getCommandName(commandId: string): string {
  return availableCommands[commandId]?.name || commandId
}

function onCommandTriggered(commandId: string) {
  console.log('Command triggered:', commandId)
  
  // Simulate command effects
  switch (commandId) {
    case 'add_row':
      console.log('Adding new row...')
      break
    case 'delete_row':
      console.log('Deleting selected rows...')
      hasSelection.value = false
      break
    case 'move_up':
      console.log('Moving rows up...')
      break
    case 'move_down':
      console.log('Moving rows down...')
      break
    case 'import_data':
      console.log('Opening import dialog...')
      break
    case 'export_data':
      console.log('Opening export dialog...')
      break
    case 'print_data':
      console.log('Opening print dialog...')
      break
    default:
      console.log('Unknown command:', commandId)
  }
}

function onConfigurationChanged(config: PanelConfiguration) {
  console.log('Configuration changed:', config)
  currentVisibleCommands.value = config.visibleCommands
}

function onConfigurationSaved(config: PanelConfiguration) {
  console.log('Configuration saved:', config)
  currentVisibleCommands.value = config.visibleCommands
  showConfigDialog.value = false
}

function onPreviewConfiguration(visibleCommands: string[]) {
  console.log('Preview configuration:', visibleCommands)
  // In a real application, you might show a temporary preview
}

function onConfigurationPreview(config: PanelConfiguration) {
  console.log('Configuration preview:', config)
  // Real-time preview updates
}
</script>

<style scoped>
.panel-configuration-example {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.example-header {
  text-align: center;
  margin-bottom: 2rem;
}

.example-header h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.example-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
}

.example-content {
  display: grid;
  gap: 2rem;
}

.panel-section,
.controls-section,
.config-display,
.table-section {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.panel-section h2,
.controls-section h2,
.config-display h2,
.table-section h2 {
  margin: 0 0 1rem 0;
  color: #495057;
  font-size: 1.25rem;
}

.panel-section p,
.table-section p {
  margin: 0 0 1rem 0;
  color: #6c757d;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.config-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.config-item {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.config-item strong {
  display: block;
  margin-bottom: 0.5rem;
  color: #495057;
}

.config-item ul {
  margin: 0;
  padding-left: 1.5rem;
}

.config-item li {
  margin-bottom: 0.25rem;
  color: #6c757d;
}

.table-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.table-controls label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.table-controls input[type="checkbox"] {
  margin: 0;
}

.table-data {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  font-family: monospace;
  font-size: 0.9rem;
  color: #495057;
}

/* Responsive design */
@media (max-width: 768px) {
  .panel-configuration-example {
    padding: 1rem;
  }
  
  .config-info {
    grid-template-columns: 1fr;
  }
  
  .table-controls {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>