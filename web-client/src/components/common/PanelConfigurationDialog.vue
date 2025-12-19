<template>
  <div v-if="isVisible" class="modal-overlay" @click.self="closeDialog">
    <div class="modal-dialog">
      <div class="modal-header">
        <h3 class="modal-title">Настройка панели команд</h3>
        <button class="close-button" @click="closeDialog" title="Закрыть">
          ✕
        </button>
      </div>
      
      <div class="modal-body">
        <div class="configuration-layout">
          <!-- Left side - Command tree -->
          <div class="command-tree-section">
            <div class="section-header">
              <h4>Доступные команды:</h4>
              <p class="instructions">
                Отметьте команды, которые должны быть видны на панели.
                Неотмеченные команды будут доступны в меню "Еще".
              </p>
            </div>
            
            <div class="command-list">
              <div
                v-for="command in availableCommandsList"
                :key="command.id"
                class="command-item"
                :class="{ disabled: !command.enabled }"
              >
                <label class="command-checkbox">
                  <input
                    type="checkbox"
                    :checked="isCommandVisible(command.id)"
                    :disabled="!command.enabled"
                    @change="toggleCommandVisibility(command.id, $event.target.checked)"
                  />
                  <span class="checkmark"></span>
                  <span class="command-info">
                    <span class="command-icon">{{ command.icon }}</span>
                    <span class="command-name">{{ command.name }}</span>
                  </span>
                </label>
                <span class="command-tooltip" :title="command.tooltip">ℹ️</span>
              </div>
            </div>
            
            <!-- Options -->
            <div class="options-section">
              <h5>Настройки</h5>
              <label class="option-checkbox">
                <input
                  type="checkbox"
                  v-model="localConfig.showTooltips"
                  @change="updatePreview"
                />
                <span class="checkmark"></span>
                <span>Показывать подсказки</span>
              </label>
              
              <label class="option-checkbox">
                <input
                  type="checkbox"
                  v-model="localConfig.compactMode"
                  @change="updatePreview"
                />
                <span class="checkmark"></span>
                <span>Компактный режим</span>
              </label>
            </div>
          </div>
          
          <!-- Right side - Preview -->
          <div class="preview-section">
            <div class="section-header">
              <h4>Предварительный просмотр:</h4>
            </div>
            
            <div class="preview-area">
              <div v-if="visibleCommands.length > 0" class="preview-group">
                <h6>Видимые кнопки:</h6>
                <div class="preview-buttons">
                  <span
                    v-for="commandId in visibleCommands"
                    :key="commandId"
                    class="preview-button"
                    :class="getPreviewButtonClass(commandId)"
                  >
                    <span class="icon">{{ getCommandIcon(commandId) }}</span>
                    <span v-if="!localConfig.compactMode" class="text">
                      {{ getCommandName(commandId) }}
                    </span>
                  </span>
                </div>
              </div>
              
              <div v-if="hiddenCommands.length > 0" class="preview-group">
                <h6>Меню "Еще":</h6>
                <div class="preview-more-menu">
                  <span class="preview-more-button">Еще ▼</span>
                  <div class="preview-dropdown">
                    <div
                      v-for="commandId in hiddenCommands"
                      :key="commandId"
                      class="preview-dropdown-item"
                    >
                      <span class="icon">{{ getCommandIcon(commandId) }}</span>
                      <span class="text">{{ getCommandName(commandId) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="visibleCommands.length === 0 && hiddenCommands.length === 0" class="no-commands">
                Нет доступных команд
              </div>
            </div>
            
            <!-- Statistics -->
            <div class="statistics">
              <span>Всего команд: {{ totalCommands }}</span>
              <span>Видимых: {{ visibleCommands.length }}</span>
              <span>Скрытых: {{ hiddenCommands.length }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="showPreview">
          Предварительный просмотр
        </button>
        <button class="btn btn-warning" @click="resetConfiguration">
          Сброс
        </button>
        <button class="btn btn-secondary" @click="closeDialog">
          Отмена
        </button>
        <button class="btn btn-primary" @click="saveConfiguration">
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

// ============================================================================
// Types and Interfaces
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

interface Props {
  isVisible?: boolean
  currentConfig?: PanelConfiguration
  availableCommands?: Record<string, CommandTreeNode>
}

interface Emits {
  (e: 'close'): void
  (e: 'save', config: PanelConfiguration): void
  (e: 'preview', visibleCommands: string[]): void
  (e: 'configuration-changed', config: PanelConfiguration): void
}

// ============================================================================
// Props and Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  isVisible: false,
  currentConfig: () => ({
    visibleCommands: [
      'add_row',
      'delete_row',
      'move_up',
      'move_down',
      'import_data',
      'export_data',
      'print_data'
    ],
    showTooltips: true,
    compactMode: false
  }),
  availableCommands: () => ({})
})

const emit = defineEmits<Emits>()

// ============================================================================
// Local State
// ============================================================================

const localConfig = ref<PanelConfiguration>({
  visibleCommands: [],
  showTooltips: true,
  compactMode: false
})

// ============================================================================
// Default Commands
// ============================================================================

function getDefaultCommands(): Record<string, CommandTreeNode> {
  return {
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
}

// ============================================================================
// Computed Properties
// ============================================================================

const availableCommandsList = computed(() => {
  const commands = Object.keys(props.availableCommands).length > 0 
    ? props.availableCommands 
    : getDefaultCommands()
  return Object.values(commands)
    .sort((a, b) => a.name.localeCompare(b.name))
})

const visibleCommands = computed(() => {
  return localConfig.value.visibleCommands.filter(
    id => props.availableCommands[id]?.enabled !== false
  )
})

const hiddenCommands = computed(() => {
  return Object.keys(props.availableCommands).filter(
    id => !localConfig.value.visibleCommands.includes(id) &&
          props.availableCommands[id]?.enabled !== false
  )
})

const totalCommands = computed(() => {
  return Object.values(props.availableCommands).filter(
    cmd => cmd.enabled !== false
  ).length
})

// ============================================================================
// Methods
// ============================================================================

function isCommandVisible(commandId: string): boolean {
  return localConfig.value.visibleCommands.includes(commandId)
}

function toggleCommandVisibility(commandId: string, visible: boolean) {
  if (visible) {
    if (!localConfig.value.visibleCommands.includes(commandId)) {
      localConfig.value.visibleCommands.push(commandId)
    }
  } else {
    const index = localConfig.value.visibleCommands.indexOf(commandId)
    if (index > -1) {
      localConfig.value.visibleCommands.splice(index, 1)
    }
  }
  
  updatePreview()
}

function getCommandIcon(commandId: string): string {
  return props.availableCommands[commandId]?.icon || '❓'
}

function getCommandName(commandId: string): string {
  return props.availableCommands[commandId]?.name || commandId
}

function getPreviewButtonClass(commandId: string): string {
  switch (commandId) {
    case 'add_row':
      return 'btn-primary'
    case 'delete_row':
      return 'btn-danger'
    default:
      return 'btn-secondary'
  }
}

function updatePreview() {
  emit('preview', visibleCommands.value)
  emit('configuration-changed', { ...localConfig.value })
}

function showPreview() {
  emit('preview', visibleCommands.value)
}

function resetConfiguration() {
  if (confirm('Вы уверены, что хотите сбросить настройки панели к значениям по умолчанию?')) {
    localConfig.value = {
      visibleCommands: Object.keys(props.availableCommands),
      showTooltips: true,
      compactMode: false
    }
    updatePreview()
  }
}

function saveConfiguration() {
  // Validate configuration
  if (localConfig.value.visibleCommands.length === 0) {
    const confirmed = confirm(
      'Вы не выбрали ни одной видимой команды. Все команды будут доступны только в меню "Еще". Продолжить?'
    )
    
    if (!confirmed) {
      return
    }
  }
  
  emit('save', { ...localConfig.value })
  closeDialog()
}

function closeDialog() {
  emit('close')
}

function loadConfiguration() {
  localConfig.value = {
    visibleCommands: [...props.currentConfig.visibleCommands],
    showTooltips: props.currentConfig.showTooltips,
    compactMode: props.currentConfig.compactMode
  }
  updatePreview()
}

// ============================================================================
// Watchers
// ============================================================================

watch(
  () => props.currentConfig,
  () => {
    loadConfiguration()
  },
  { deep: true, immediate: true }
)

watch(
  () => props.isVisible,
  (visible) => {
    if (visible) {
      loadConfiguration()
    }
  }
)

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadConfiguration()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #dee2e6;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-button:hover {
  background-color: #f8f9fa;
  color: #000;
}

.modal-body {
  flex: 1;
  overflow: hidden;
  padding: 1.5rem;
}

.configuration-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  height: 100%;
}

.command-tree-section,
.preview-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-header h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.instructions {
  margin: 0 0 1rem 0;
  color: #6c757d;
  font-size: 0.9rem;
  line-height: 1.4;
}

.command-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 0.5rem;
  margin-bottom: 1rem;
  max-height: 300px;
}

.command-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.25rem;
}

.command-item:hover {
  background-color: #f8f9fa;
}

.command-item.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.command-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
  flex: 1;
}

.command-checkbox input[type="checkbox"] {
  margin-right: 0.5rem;
}

.command-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.command-icon {
  font-size: 1.1rem;
}

.command-name {
  font-size: 0.9rem;
}

.command-tooltip {
  color: #6c757d;
  cursor: help;
  font-size: 0.8rem;
}

.options-section {
  border-top: 1px solid #dee2e6;
  padding-top: 1rem;
}

.options-section h5 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
}

.option-checkbox {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.option-checkbox input[type="checkbox"] {
  margin-right: 0.5rem;
}

.preview-area {
  flex: 1;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
  background-color: #f8f9fa;
  overflow-y: auto;
  margin-bottom: 1rem;
  min-height: 200px;
}

.preview-group {
  margin-bottom: 1.5rem;
}

.preview-group:last-child {
  margin-bottom: 0;
}

.preview-group h6 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #495057;
}

.preview-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.preview-button {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  border: 1px solid transparent;
}

.preview-button.btn-primary {
  background-color: #007bff;
  color: white;
}

.preview-button.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.preview-button.btn-danger {
  background-color: #dc3545;
  color: white;
}

.preview-more-menu {
  position: relative;
  display: inline-block;
}

.preview-more-button {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background-color: #6c757d;
  color: white;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.preview-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  min-width: 160px;
  z-index: 10;
}

.preview-dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  font-size: 0.875rem;
  border-bottom: 1px solid #f8f9fa;
}

.preview-dropdown-item:last-child {
  border-bottom: none;
}

.no-commands {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 2rem;
}

.statistics {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #6c757d;
  padding: 0.5rem;
  background-color: #e9ecef;
  border-radius: 4px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #dee2e6;
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

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-warning {
  background-color: #ffc107;
  color: #212529;
}

.btn-warning:hover {
  background-color: #e0a800;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-dialog {
    width: 95%;
    max-height: 95vh;
  }
  
  .configuration-layout {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .modal-footer {
    flex-wrap: wrap;
  }
  
  .btn {
    flex: 1;
    min-width: 0;
  }
}

/* Accessibility improvements */
.command-checkbox:focus-within,
.option-checkbox:focus-within {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

.btn:focus {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

/* Custom checkbox styling */
.checkmark {
  position: relative;
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 0.5rem;
}

input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

input[type="checkbox"] + .checkmark {
  background-color: #fff;
  border: 2px solid #dee2e6;
  border-radius: 3px;
}

input[type="checkbox"]:checked + .checkmark {
  background-color: #007bff;
  border-color: #007bff;
}

input[type="checkbox"]:checked + .checkmark::after {
  content: '✓';
  position: absolute;
  left: 2px;
  top: -2px;
  color: white;
  font-size: 12px;
  font-weight: bold;
}
</style>