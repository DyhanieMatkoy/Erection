<template>
  <Modal :open="open" title="Печать документа" size="sm" @close="$emit('close')">
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Формат печати</label>
        <div class="space-y-2">
          <label class="flex items-center">
            <input
              v-model="selectedFormat"
              type="radio"
              value="pdf"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
            />
            <span class="ml-3 text-sm text-gray-700">PDF (АРСД)</span>
          </label>
          <label class="flex items-center">
            <input
              v-model="selectedFormat"
              type="radio"
              value="excel"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
            />
            <span class="ml-3 text-sm text-gray-700">Excel</span>
          </label>
        </div>
      </div>

      <div v-if="error" class="rounded-md bg-red-50 p-4">
        <p class="text-sm text-red-800">{{ error }}</p>
      </div>
    </div>

    <template #footer>
      <button
        @click="$emit('close')"
        type="button"
        class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
      >
        Отмена
      </button>
      <button
        @click="handleDownload"
        type="button"
        :disabled="loading"
        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
      >
        {{ loading ? 'Загрузка...' : 'Скачать' }}
      </button>
      <button
        v-if="selectedFormat === 'pdf'"
        @click="handleOpen"
        type="button"
        :disabled="loading"
        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
      >
        {{ loading ? 'Загрузка...' : 'Открыть' }}
      </button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Modal from '@/components/common/Modal.vue'

const props = defineProps<{
  open: boolean
  documentType: "estimate" | "daily-report" | "timesheet"
  documentId: number
  documentName: string
}>()

const emit = defineEmits<{
  close: []
  print: [format: 'pdf' | 'excel', action: 'download' | 'open']
}>()

const selectedFormat = ref<'pdf' | 'excel'>('pdf')
const loading = ref(false)
const error = ref('')

function handleDownload() {
  emit('print', selectedFormat.value, 'download')
}

function handleOpen() {
  emit('print', selectedFormat.value, 'open')
}
</script>
