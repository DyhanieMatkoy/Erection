<template>
  <div class="bg-white shadow rounded-lg p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-medium text-gray-900">Строки сметы</h3>
      <button
        v-if="!disabled"
        @click="handleAddLine"
        class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
      >
        <svg class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Добавить строку
      </button>
    </div>

    <!-- Desktop table -->
    <div class="hidden md:block overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-12">#</th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Работа</th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-24">
              Кол-во
            </th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-20">
              Ед.
            </th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-32">
              Цена
            </th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-32">
              Сумма
            </th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-32">
              Труд.
            </th>
            <th v-if="!disabled" class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase w-24">
              Действия
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="(line, index) in lines" :key="index" :class="{ 'bg-gray-50': line.is_group }">
            <td class="px-3 py-2 text-sm text-gray-900">{{ index + 1 }}</td>
            <td class="px-3 py-2">
              <div 
                v-if="!disabled"
                class="relative cursor-pointer"
                @click="openWorkSelector(index)"
              >
                <div class="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-white flex items-center justify-between hover:border-blue-500">
                  <span class="truncate">{{ line.work_name || 'Выберите работу' }}</span>
                  <span class="text-gray-400 text-xs ml-2">▼</span>
                </div>
              </div>
              <span v-else class="text-sm text-gray-900">{{ line.work_name }}</span>
            </td>
            <td class="px-3 py-2">
              <input
                v-if="!disabled && !line.is_group"
                v-model.number="line.quantity"
                type="number"
                step="0.01"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                @input="handleLineChange(index)"
              />
              <span v-else class="text-sm text-gray-900">{{ line.quantity }}</span>
            </td>
            <td class="px-3 py-2 text-sm text-gray-500">{{ line.unit }}</td>
            <td class="px-3 py-2">
              <input
                v-if="!disabled && !line.is_group"
                v-model.number="line.price"
                type="number"
                step="0.01"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                @input="handleLineChange(index)"
              />
              <span v-else class="text-sm text-gray-900">{{ formatNumber(line.price) }}</span>
            </td>
            <td class="px-3 py-2 text-sm font-medium text-gray-900">
              {{ formatNumber(line.sum) }}
            </td>
            <td class="px-3 py-2">
              <input
                v-if="!disabled && !line.is_group"
                v-model.number="line.labor"
                type="number"
                step="0.01"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
              />
              <span v-else class="text-sm text-gray-900">{{ formatNumber(line.labor) }}</span>
            </td>
            <td v-if="!disabled" class="px-3 py-2 text-right">
              <button
                @click="handleRemoveLine(index)"
                class="text-red-600 hover:text-red-900 text-sm"
              >
                Удалить
              </button>
            </td>
          </tr>
          <tr v-if="lines.length === 0">
            <td :colspan="disabled ? 7 : 8" class="px-3 py-8 text-center text-sm text-gray-500">
              Нет строк
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile cards -->
    <div class="md:hidden space-y-4">
      <div
        v-for="(line, index) in lines"
        :key="index"
        class="border border-gray-200 rounded-lg p-4 space-y-3"
      >
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-500">Строка {{ index + 1 }}</span>
          <button
            v-if="!disabled"
            @click="handleRemoveLine(index)"
            class="text-red-600 hover:text-red-900 text-sm"
          >
            Удалить
          </button>
        </div>

        <div class="space-y-2">
          <div>
            <label class="block text-xs font-medium text-gray-500">Работа</label>
            <div 
              v-if="!disabled"
              class="relative cursor-pointer mt-1"
              @click="openWorkSelector(index)"
            >
              <div class="w-full px-2 py-2 text-sm border border-gray-300 rounded bg-white flex items-center justify-between">
                <span class="truncate">{{ line.work_name || 'Выберите работу' }}</span>
                <span class="text-gray-400">▼</span>
              </div>
            </div>
            <span v-else class="text-sm text-gray-900">{{ line.work_name }}</span>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500">Количество</label>
              <input
                v-if="!disabled && !line.is_group"
                v-model.number="line.quantity"
                type="number"
                step="0.01"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                @input="handleLineChange(index)"
              />
              <span v-else class="text-sm text-gray-900">{{ line.quantity }}</span>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500">Ед. изм.</label>
              <span class="text-sm text-gray-900">{{ line.unit }}</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500">Цена</label>
              <input
                v-if="!disabled && !line.is_group"
                v-model.number="line.price"
                type="number"
                step="0.01"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                @input="handleLineChange(index)"
              />
              <span v-else class="text-sm text-gray-900">{{ formatNumber(line.price) }}</span>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500">Сумма</label>
              <span class="text-sm font-medium text-gray-900">{{ formatNumber(line.sum) }}</span>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-500">Трудоемкость</label>
            <input
              v-if="!disabled && !line.is_group"
              v-model.number="line.labor"
              type="number"
              step="0.01"
              class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
            />
            <span v-else class="text-sm text-gray-900">{{ formatNumber(line.labor) }}</span>
          </div>
        </div>
      </div>

      <div v-if="lines.length === 0" class="text-center py-8 text-sm text-gray-500">
        Нет строк
      </div>
    </div>
    
    <!-- Work Selector Dialog -->
    <WorkListForm
      :is-open="showWorkSelector"
      title="Выберите работу"
      :current-work-id="activeLineIndex !== null ? lines[activeLineIndex]?.work_id : null"
      @close="closeWorkSelector"
      @select="handleWorkSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { EstimateLine, Work, Unit } from '@/types/models'
import WorkListForm from '@/components/common/WorkListForm.vue'

const props = defineProps<{
  modelValue: EstimateLine[]
  works: Work[]
  units?: Unit[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [lines: EstimateLine[]]
  'update:totals': [totals: { sum: number; labor: number }]
}>()

const lines = computed({
  get: () => props.modelValue || [],
  set: (value) => emit('update:modelValue', value),
})

const showWorkSelector = ref(false)
const activeLineIndex = ref<number | null>(null)

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function handleAddLine() {
  const newLine: EstimateLine = {
    work_id: null,
    quantity: 0,
    price: 0,
    sum: 0,
    labor: 0,
    parent_id: null,
    is_group: false,
    order_num: lines.value.length,
  }
  lines.value = [...lines.value, newLine]
}

function handleRemoveLine(index: number) {
  lines.value = lines.value.filter((_, i) => i !== index)
  calculateTotals()
}

function openWorkSelector(index: number) {
  activeLineIndex.value = index
  showWorkSelector.value = true
}

function closeWorkSelector() {
  showWorkSelector.value = false
  activeLineIndex.value = null
}

function handleWorkSelect(work: Work) {
  if (activeLineIndex.value === null) return
  
  const index = activeLineIndex.value
  const line = lines.value[index]
  if (line) {
    line.work_id = work.id
    line.work_name = work.name
    // Get unit name - prefer unit_name from API, then try local units lookup, then fallback to unit field
    let unitName = ''
    if (work.unit_name) {
      // API already resolved the unit name via JOIN
      unitName = work.unit_name
    } else if (work.unit_id && props.units) {
      // Try to find in local units cache
      const unit = props.units.find(u => u.id === work.unit_id)
      unitName = unit?.name || ''
    }
    // Legacy unit column removed - only use unit_id foreign key
    if (!unitName) {
      unitName = ''
    }
    line.unit = unitName
    line.price = work.price || 0
    line.labor_rate = work.labor_rate || 0
    
    // Default quantity to 1 if 0
    if (line.quantity === 0) {
      line.quantity = 1
    }
    
    handleLineChange(index)
  }
  closeWorkSelector()
}

function handleLineChange(index: number) {
  const line = lines.value[index]
  if (line) {
      line.sum = line.quantity * line.price
    }
  calculateTotals()
}

function calculateTotals() {
  const totals = lines.value.reduce(
    (acc, line) => {
      if (!line.is_group) {
        acc.sum += line.sum
        acc.labor += line.labor
      }
      return acc
    },
    { sum: 0, labor: 0 }
  )
  emit('update:totals', totals)
}

// Watch for changes and recalculate totals
watch(
  () => lines.value,
  () => {
    calculateTotals()
  },
  { deep: true }
)
</script>
