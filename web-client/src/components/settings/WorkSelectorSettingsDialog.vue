<template>
  <Modal :is-open="isOpen" @close="handleClose">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">
          Настройки селектора работ
        </h3>
      </div>

      <div class="px-6 py-4 space-y-6">
        <!-- Modal Mode Setting -->
        <div class="flex items-center justify-between">
          <div>
            <label class="text-sm font-medium text-gray-700">
              Режим открытия
            </label>
            <p class="text-xs text-gray-500 mt-1">
              Как открывать селектор работ из сметы
            </p>
          </div>
          <div class="flex items-center space-x-3">
            <label class="inline-flex items-center">
              <input
                type="radio"
                :checked="!isModalMode"
                @change="handleModeChange(false)"
                class="form-radio h-4 w-4 text-blue-600"
                :disabled="loading"
              />
              <span class="ml-2 text-sm text-gray-700">В окне</span>
            </label>
            <label class="inline-flex items-center">
              <input
                type="radio"
                :checked="isModalMode"
                @change="handleModeChange(true)"
                class="form-radio h-4 w-4 text-blue-600"
                :disabled="loading"
              />
              <span class="ml-2 text-sm text-gray-700">Модально</span>
            </label>
          </div>
        </div>

        <!-- Hierarchy Mode Setting -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Режим отображения иерархии
          </label>
          <div class="space-y-2">
            <label class="inline-flex items-center">
              <input
                type="radio"
                :checked="hierarchyMode === 'flat'"
                @change="handleHierarchyModeChange('flat')"
                class="form-radio h-4 w-4 text-blue-600"
                :disabled="loading"
              />
              <span class="ml-2 text-sm text-gray-700">Плоский список</span>
            </label>
            <label class="inline-flex items-center">
              <input
                type="radio"
                :checked="hierarchyMode === 'tree'"
                @change="handleHierarchyModeChange('tree')"
                class="form-radio h-4 w-4 text-blue-600"
                :disabled="loading"
              />
              <span class="ml-2 text-sm text-gray-700">Дерево</span>
            </label>
            <label class="inline-flex items-center">
              <input
                type="radio"
                :checked="hierarchyMode === 'breadcrumb'"
                @change="handleHierarchyModeChange('breadcrumb')"
                class="form-radio h-4 w-4 text-blue-600"
                :disabled="loading"
              />
              <span class="ml-2 text-sm text-gray-700">С путями</span>
            </label>
          </div>
        </div>

        <!-- Additional Settings -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm font-medium text-gray-700">
                Показывать элементы управления иерархией
              </label>
              <p class="text-xs text-gray-500 mt-1">
                Кнопки переключения режимов отображения
              </p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="showHierarchyControls"
                @change="handleHierarchyControlsToggle"
                class="sr-only"
                :disabled="loading"
              />
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm font-medium text-gray-700">
                Автоматически разворачивать группы
              </label>
              <p class="text-xs text-gray-500 mt-1">
                Показывать содержимое групп при открытии
              </p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="autoExpandGroups"
                @change="handleAutoExpandToggle"
                class="sr-only"
                :disabled="loading"
              />
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="text-sm text-red-600 bg-red-50 p-3 rounded-md">
          {{ error }}
        </div>
      </div>

      <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
        <button
          @click="handleClose"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          :disabled="loading"
        >
          Закрыть
        </button>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Modal from '@/components/common/Modal.vue'
import { useWorkSelectorSettings } from '@/composables/useWorkSelectorSettings'

interface Props {
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const {
  loading,
  error,
  isModalMode,
  hierarchyMode,
  showHierarchyControls,
  autoExpandGroups,
  loadSettings,
  saveSettings,
  setHierarchyMode,
  toggleHierarchyControls,
  toggleAutoExpandGroups
} = useWorkSelectorSettings()

async function handleModeChange(modal: boolean) {
  await saveSettings({ open_modal: modal })
}

async function handleHierarchyModeChange(mode: 'flat' | 'tree' | 'breadcrumb') {
  await setHierarchyMode(mode)
}

async function handleHierarchyControlsToggle() {
  await toggleHierarchyControls()
}

async function handleAutoExpandToggle() {
  await toggleAutoExpandGroups()
}

function handleClose() {
  emit('close')
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.form-radio {
  color: #3b82f6;
}

.form-radio:focus {
  ring-color: #93c5fd;
  ring-opacity: 0.5;
}

/* Toggle switch styles */
input:checked + div {
  background-color: #3b82f6;
}

input:checked + div:after {
  transform: translateX(100%);
  border-color: white;
}
</style>