<template>
  <div class="panel-preview">
    <div class="preview-label">Предварительный просмотр панели:</div>
    
    <div class="preview-panel" :class="panelClasses">
      <!-- Visible command buttons -->
      <button
        v-for="command in visibleCommands"
        :key="command.id"
        :class="['preview-button', getButtonClass(command)]"
        :title="panelSettings.showTooltips ? command.tooltip : ''"
        disabled
      >
        <span class="button-icon">{{ command.icon }}</span>
        <span v-if="!panelSettings.compactMode" class="button-text">{{ command.name }}</span>
      </button>
      
      <!-- More menu for hidden commands -->
      <div v-if="hiddenCommands.length > 0" class="more-menu-preview">
        <button 
          class="preview-button more-button"
          :title="moreMenuTooltip"
          disabled
        >
          Еще
        </button>
      </div>
      
      <!-- Customization button -->
      <button class="preview-button customize-button" title="Настроить панель" disabled>
        ⚙️
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// ============================================================================
// Types and Interfaces
// ============================================================================

interface TablePartCommand {
  id: string
  name: string
  icon: string
  tooltip: string
  shortcut?: string
  enabled: boolean
  visible: boolean
  formMethod?: string
  position: number
  requiresSelection: boolean
}

interface PanelSettings {
  visibleCommands: string[]
  hiddenCommands: string[]
  buttonSize: 'small' | 'medium' | 'large'
  showTooltips: boolean
  compactMode: boolean
}

interface Props {
  commands: TablePartCommand[]
  visibleCommandIds: string[]
  panelSettings: PanelSettings
}

// ============================================================================
// Props
// ============================================================================

const props = defineProps<Props>()

// ============================================================================
// Computed Properties
// ============================================================================

const visibleCommands = computed(() => {
  return props.commands
    .filter(cmd => props.visibleCommandIds.includes(cmd.id))
    .sort((a, b) => a.position - b.position)
})

const hiddenCommands = computed(() => {
  return props.commands
    .filter(cmd => !props.visibleCommandIds.includes(cmd.id))
    .sort((a, b) => a.position - b.position)
})

const panelClasses = computed(() => {
  return {
    [`size-${props.panelSettings.buttonSize}`]: true,
    'compact-mode': props.panelSettings.compactMode
  }
})

const moreMenuTooltip = computed(() => {
  if (!props.panelSettings.showTooltips) return ''
  
  const hiddenNames = hiddenCommands.value.map(cmd => cmd.name).join(', ')
  return `Скрытые команды: ${hiddenNames}`
})

// ============================================================================
// Methods
// ============================================================================

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
</script>

<style scoped>
.panel-preview {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
  min-height: 80px;
}

.preview-label {
  font-size: 0.9rem;
  color: #495057;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.preview-panel {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding: 0.5rem;
  background-color: white;
  border: 1px solid #e9ecef;
  border-radius: 3px;
  min-height: 40px;
}

.preview-button {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  border: none;
  border-radius: 0.25rem;
  cursor: not-allowed;
  transition: all 0.2s ease;
  white-space: nowrap;
  text-decoration: none;
  font-weight: 400;
  line-height: 1.5;
  text-align: center;
  vertical-align: middle;
  user-select: none;
  opacity: 0.8;
}

.preview-button:disabled {
  pointer-events: none;
}

.button-icon {
  font-size: 1rem;
  line-height: 1;
}

.button-text {
  font-size: 0.875rem;
}

/* Button variants */
.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.more-button {
  background-color: #6c757d;
  color: white;
}

.customize-button {
  background-color: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
  margin-left: auto;
}

/* Size variants */
.size-small .preview-button {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.size-small .button-icon {
  font-size: 0.875rem;
}

.size-small .button-text {
  font-size: 0.75rem;
}

.size-medium .preview-button {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.size-large .preview-button {
  padding: 0.5rem 1rem;
  font-size: 1rem;
}

.size-large .button-icon {
  font-size: 1.125rem;
}

.size-large .button-text {
  font-size: 1rem;
}

/* Compact mode */
.compact-mode .preview-button {
  padding: 0.25rem;
  min-width: 2rem;
  justify-content: center;
}

.compact-mode .button-text {
  display: none;
}

.compact-mode .button-icon {
  margin: 0;
}

/* More menu preview */
.more-menu-preview {
  position: relative;
}

/* Responsive design */
@media (max-width: 768px) {
  .preview-panel {
    gap: 0.25rem;
  }
  
  .preview-button {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
  }
  
  .button-text {
    display: none;
  }
  
  .preview-button {
    min-width: 2rem;
    justify-content: center;
  }
}

/* Animation for preview updates */
.preview-panel {
  transition: all 0.3s ease;
}

.preview-button {
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 0.8;
    transform: scale(1);
  }
}

/* Empty state */
.preview-panel:empty::after {
  content: 'Нет видимых команд';
  color: #6c757d;
  font-style: italic;
  font-size: 0.875rem;
}
</style>