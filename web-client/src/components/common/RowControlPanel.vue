<template>
  <div class="row-control-panel">
    <!-- Main button group -->
    <div class="button-group">
      <button
        v-for="command in visibleCommandButtons"
        :key="command.id"
        :class="['btn', 'btn-sm', getButtonClass(command)]"
        :disabled="!isCommandEnabled(command)"
        :title="command.tooltip"
        @click="executeCommand(command.id)"
      >
        <span class="icon">{{ command.icon }}</span>
        <span class="text">{{ command.name }}</span>
      </button>
      
      <!-- More menu for hidden commands -->
      <div v-if="hiddenCommandButtons.length > 0" class="dropdown">
        <button
          class="btn btn-sm btn-secondary dropdown-toggle"
          :class="{ active: showMoreMenu }"
          @click="showMoreMenu = !showMoreMenu"
          title="Дополнительные команды"
        >
          Еще
        </button>
        <div v-if="showMoreMenu" class="dropdown-menu" @click.stop>
          <button
            v-for="command in hiddenCommandButtons"
            :key="command.id"
            :class="['dropdown-item', { disabled: !isCommandEnabled(command) }]"
            :disabled="!isCommandEnabled(command)"
            :title="command.tooltip"
            @click="executeCommand(command.id); showMoreMenu = false"
          >
            <span class="icon">{{ command.icon }}</span>
            <span class="text">{{ command.name }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Customization button -->
    <button
      class="btn btn-sm btn-outline-secondary customize-btn"
      @click="showConfigurationDialog"
      title="Настроить панель"
    >
      ⚙️
    </button>
    
    <!-- Panel Configuration Dialog -->
    <PanelConfigurationDialog
      :is-visible="showConfigDialog"
      :available-commands="availableCommands"
      :current-visible-commands="props.visibleCommands"
      :current-panel-settings="currentPanelSettings"
      @close="showConfigDialog = false"
      @save="onConfigurationSaved"
      @configuration-changed="onConfigurationChanged"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { 
  TablePartCommandManager, 
  CommandContext, 
  createCommandContext,
  createCommandManager 
} from '../../services/tablePartCommandManager'
import PanelConfigurationDialog from './PanelConfigurationDialog.vue'

// ============================================================================
// Types and Interfaces
// ============================================================================

interface PanelButton {
  id: string
  name: string
  icon: string
  tooltip: string
  enabled?: boolean
  visible?: boolean
  requiresSelection?: boolean
}

interface Props {
  visibleCommands?: string[]
  hasSelection?: boolean
  hasRows?: boolean
  isFirstRowSelected?: boolean
  isLastRowSelected?: boolean
  selectedRows?: number[]
  tableData?: any[]
  formInstance?: any
  commandManager?: TablePartCommandManager
}

interface PanelSettings {
  visibleCommands: string[]
  hiddenCommands: string[]
  buttonSize: 'small' | 'medium' | 'large'
  showTooltips: boolean
  compactMode: boolean
}

interface PanelConfiguration {
  visibleCommands: string[]
  showTooltips: boolean
  compactMode: boolean
}

interface Emits {
  (e: 'command-triggered', commandId: string): void
  (e: 'customize-requested'): void
  (e: 'command-executed', commandId: string, result: unknown): void
  (e: 'configuration-changed', config: PanelConfiguration): void
}

// ============================================================================
// Props and Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  visibleCommands: () => [
    'add_row',
    'delete_row', 
    'move_up',
    'move_down',
    'import_data',
    'export_data',
    'print_data'
  ],
  hasSelection: false,
  hasRows: false,
  isFirstRowSelected: false,
  isLastRowSelected: false,
  selectedRows: () => [],
  tableData: () => []
})

const emit = defineEmits<Emits>()

// ============================================================================
// Local State
// ============================================================================

const showMoreMenu = ref(false)
const showConfigDialog = ref(false)
const commandManager = ref<TablePartCommandManager>(props.commandManager || createCommandManager())
const formCommandStates = ref<Record<string, boolean>>({})

// Configuration state
const availableCommands = ref<PanelButton[]>([])
const currentPanelSettings = ref<PanelSettings>({
  visibleCommands: props.visibleCommands,
  hiddenCommands: [],
  buttonSize: 'medium',
  showTooltips: true,
  compactMode: false
})

// ============================================================================
// Standard Button Definitions
// ============================================================================

const standardButtons: Record<string, PanelButton> = {
  add_row: {
    id: 'add_row',
    name: 'Добавить',
    icon: '➕',
    tooltip: 'Добавить новую строку (Insert)',
    requiresSelection: false
  },
  delete_row: {
    id: 'delete_row',
    name: 'Удалить',
    icon: '🗑',
    tooltip: 'Удалить выбранные строки (Delete)',
    requiresSelection: true
  },
  move_up: {
    id: 'move_up',
    name: 'Выше',
    icon: '↑',
    tooltip: 'Переместить строки выше (Ctrl+Shift+Up)',
    requiresSelection: true
  },
  move_down: {
    id: 'move_down',
    name: 'Ниже',
    icon: '↓',
    tooltip: 'Переместить строки ниже (Ctrl+Shift+Down)',
    requiresSelection: true
  },
  import_data: {
    id: 'import_data',
    name: 'Импорт',
    icon: '📥',
    tooltip: 'Импортировать данные из файла',
    requiresSelection: false
  },
  export_data: {
    id: 'export_data',
    name: 'Экспорт',
    icon: '📤',
    tooltip: 'Экспортировать данные в файл',
    requiresSelection: false
  },
  print_data: {
    id: 'print_data',
    name: 'Печать',
    icon: '🖨',
    tooltip: 'Печать табличной части',
    requiresSelection: false
  }
}

// ============================================================================
// Computed Properties
// ============================================================================

const visibleCommandButtons = computed(() => {
  return props.visibleCommands
    .map(id => standardButtons[id])
    .filter(Boolean)
})

const hiddenCommandButtons = computed(() => {
  const hiddenIds = Object.keys(standardButtons).filter(
    id => !props.visibleCommands.includes(id)
  )
  return hiddenIds
    .map(id => standardButtons[id])
    .filter(Boolean)
})

// ============================================================================
// Methods
// ============================================================================

async function executeCommand(commandId: string) {
  // Create command context
  const context = createCommandContext(
    props.selectedRows || [],
    props.tableData || [],
    {}
  )
  
  // Try to execute through command manager first
  if (commandManager.value.getRegisteredCommands()[commandId]) {
    try {
      const result = await commandManager.value.executeCommand(commandId, context)
      emit('command-executed', commandId, result)
      
      if (result.success) {
        // Also emit the standard signal for backward compatibility
        emit('command-triggered', commandId)
        return
      }
    } catch (error) {
      console.error('Command execution failed:', error)
    }
  }
  
  // Fall back to standard command triggering
  emit('command-triggered', commandId)
}

function isCommandEnabled(command: PanelButton): boolean {
  // Check form command state first
  if (formCommandStates.value[command.id] !== undefined) {
    return formCommandStates.value[command.id]
  }
  
  // Check basic requirements
  if (command.requiresSelection && !props.hasSelection) {
    return false
  }
  
  // Specific command logic
  switch (command.id) {
    case 'delete_row':
      return props.hasSelection
    
    case 'move_up':
      return props.hasSelection && !props.isFirstRowSelected
    
    case 'move_down':
      return props.hasSelection && !props.isLastRowSelected
    
    case 'export_data':
      return props.hasRows
    
    default:
      return true
  }
}

function getButtonClass(command: PanelButton): string {
  switch (command.id) {
    case 'add_row':
      return 'btn-primary'
    case 'delete_row':
      return 'btn-danger'
    default:
      return 'btn-secondary'
  }
}

// ============================================================================
// Event Handlers
// ============================================================================

function handleClickOutside(event: Event) {
  const target = event.target as Element
  if (!target.closest('.dropdown')) {
    showMoreMenu.value = false
  }
}

// ============================================================================
// Panel Configuration Methods
// ============================================================================



// ============================================================================
// Form Integration Methods
// ============================================================================

function registerFormInstance(formInstance: unknown) {
  /**
   * Register a form instance for command discovery and integration.
   * Requirements: 2.1, 2.2
   */
  const discoveredCommands = commandManager.value.discoverAndRegisterCommands(formInstance)
  updateFormCommandStates()
  return discoveredCommands
}

function updateFormCommandStates() {
  /**
   * Update command states based on registered form commands.
   * Requirements: 2.5
   */
  const context = createCommandContext(
    props.selectedRows || [],
    props.tableData || [],
    {}
  )
  
  formCommandStates.value = commandManager.value.updateCommandStates(context)
}

// ============================================================================
// Watchers
// ============================================================================

// Watch for changes in selection/data to update command states
watch(
  () => [props.selectedRows, props.tableData, props.hasSelection, props.hasRows],
  () => {
    updateFormCommandStates()
  },
  { deep: true }
)

// Register form instance when it changes
watch(
  () => props.formInstance,
  (newFormInstance) => {
    if (newFormInstance) {
      registerFormInstance(newFormInstance)
    }
  },
  { immediate: true }
)

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  
  // Register form instance if provided
  if (props.formInstance) {
    registerFormInstance(props.formInstance)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// ============================================================================
// Configuration Methods
// ============================================================================

function showConfigurationDialog() {
  /**
   * Show the panel configuration dialog.
   * Requirements: 9.1, 9.2, 9.3, 9.4
   */
  // Initialize available commands from standard buttons
  availableCommands.value = Object.values(standardButtons).map(btn => ({
    ...btn,
    position: Object.keys(standardButtons).indexOf(btn.id) + 1
  }))
  
  // Update current panel settings
  currentPanelSettings.value = {
    visibleCommands: props.visibleCommands,
    hiddenCommands: Object.keys(standardButtons).filter(id => !props.visibleCommands.includes(id)),
    buttonSize: 'medium',
    showTooltips: true,
    compactMode: false
  }
  
  showConfigDialog.value = true
}

function onConfigurationChanged(commands: PanelButton[], visibleCommandIds: string[]) {
  /**
   * Handle real-time configuration changes from dialog.
   * Requirements: 9.2
   */
  // Emit configuration change for real-time preview
  // The parent component can choose to apply changes immediately or wait for save
  emit('customize-requested')
}

function onConfigurationSaved(commands: PanelButton[], panelSettings: PanelSettings) {
  /**
   * Handle final configuration save from dialog.
   * Requirements: 9.4
   */
  // Update current settings
  currentPanelSettings.value = panelSettings
  
  // Emit configuration saved event
  emit('configuration-saved', commands, panelSettings)
  
  // Close dialog
  showConfigDialog.value = false
}

// ============================================================================
// Expose Methods for Parent Components
// ============================================================================

defineExpose({
  registerFormInstance,
  updateFormCommandStates,
  commandManager: commandManager.value
})
</script>

<style scoped>
.row-control-panel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  gap: 0.5rem;
}

.button-group {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  white-space: nowrap;
  text-decoration: none;
  font-weight: 400;
  line-height: 1.5;
  text-align: center;
  vertical-align: middle;
  user-select: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.btn:focus {
  outline: none;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
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

.icon {
  font-size: 1rem;
  line-height: 1;
}

.text {
  font-size: 0.875rem;
}

/* Dropdown styles */
.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-toggle {
  position: relative;
}

.dropdown-toggle::after {
  content: '';
  display: inline-block;
  margin-left: 0.255em;
  vertical-align: 0.255em;
  border-top: 0.3em solid;
  border-right: 0.3em solid transparent;
  border-bottom: 0;
  border-left: 0.3em solid transparent;
}

.dropdown-toggle.active {
  background-color: #545b62;
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
  padding: 0.5rem 0;
  margin: 0.125rem 0 0;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.5rem 1rem;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  color: #212529;
  text-decoration: none;
  font-size: 0.875rem;
  line-height: 1.5;
}

.dropdown-item:hover:not(.disabled) {
  background-color: #f8f9fa;
  color: #16181b;
}

.dropdown-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.dropdown-item .icon {
  margin-right: 0.5rem;
}

.customize-btn {
  flex-shrink: 0;
}

/* Responsive design */
@media (max-width: 768px) {
  .row-control-panel {
    flex-wrap: wrap;
    gap: 0.25rem;
  }
  
  .button-group {
    flex-wrap: wrap;
    gap: 0.125rem;
  }
  
  .btn .text {
    display: none;
  }
  
  .btn {
    padding: 0.25rem;
    min-width: 2rem;
    justify-content: center;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .row-control-panel {
    border-bottom-width: 2px;
  }
  
  .btn {
    border: 1px solid currentColor;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .btn {
    transition: none;
  }
}

/* Focus visible for keyboard navigation */
.btn:focus-visible {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}
</style>