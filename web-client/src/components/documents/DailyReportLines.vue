<template>
  <div class="bg-white shadow rounded-lg p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-medium text-gray-900">Строки отчета</h3>
      
      <!-- Deviation display mode toggle -->
      <div class="flex items-center space-x-2">
        <label class="text-sm text-gray-700">Отклонение:</label>
        <select
          v-model="deviationMode"
          class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="units">В единицах</option>
          <option value="percent">В процентах</option>
        </select>
      </div>
    </div>

    <!-- Desktop table -->
    <div class="hidden md:block overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-12">#</th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Работа</th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-32">
              План. труд.
            </th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-32">
              Факт. труд.
            </th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase w-32">
              Отклонение
            </th>
            <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Исполнители
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="(line, index) in lines" :key="index">
            <td class="px-3 py-2 text-sm text-gray-900">{{ index + 1 }}</td>
            <td class="px-3 py-2 text-sm text-gray-900">{{ line.work_name }}</td>
            <td class="px-3 py-2 text-sm text-gray-900">{{ formatNumber(line.planned_labor) }}</td>
            <td class="px-3 py-2">
              <input
                v-if="!disabled"
                v-model.number="line.actual_labor"
                type="number"
                step="0.01"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                @input="handleLineChange(index)"
              />
              <span v-else class="text-sm text-gray-900">{{ formatNumber(line.actual_labor) }}</span>
            </td>
            <td
              class="px-3 py-2 text-sm font-medium"
              :class="getDeviationValue(line) >= 0 ? 'text-green-600' : 'text-red-600'"
            >
              {{ formatDeviation(line) }}
            </td>
            <td class="px-3 py-2">
              <MultiPicker
                v-if="!disabled"
                v-model="line.executors"
                :items="persons"
                display-key="full_name"
                placeholder="Выберите исполнителей"
              />
              <span v-else class="text-sm text-gray-900">
                {{ line.executor_names?.join(', ') || '—' }}
              </span>
            </td>
          </tr>
          <tr v-if="lines.length === 0">
            <td colspan="6" class="px-3 py-8 text-center text-sm text-gray-500">
              Нет строк. Выберите смету для автозаполнения.
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
        </div>

        <div class="space-y-2">
          <div>
            <label class="block text-xs font-medium text-gray-500">Работа</label>
            <span class="text-sm text-gray-900">{{ line.work_name }}</span>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500">План. труд.</label>
              <span class="text-sm text-gray-900">{{ formatNumber(line.planned_labor) }}</span>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500">Факт. труд.</label>
              <input
                v-if="!disabled"
                v-model.number="line.actual_labor"
                type="number"
                step="0.01"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                @input="handleLineChange(index)"
              />
              <span v-else class="text-sm text-gray-900">{{ formatNumber(line.actual_labor) }}</span>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-500">Отклонение</label>
            <span
              class="text-sm font-medium"
              :class="getDeviationValue(line) >= 0 ? 'text-green-600' : 'text-red-600'"
            >
              {{ formatDeviation(line) }}
            </span>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-500">Исполнители</label>
            <MultiPicker
              v-if="!disabled"
              v-model="line.executors"
              :items="persons"
              display-key="full_name"
              placeholder="Выберите исполнителей"
            />
            <span v-else class="text-sm text-gray-900">
              {{ line.executor_names?.join(', ') || '—' }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="lines.length === 0" class="text-center py-8 text-sm text-gray-500">
        Нет строк. Выберите смету для автозаполнения.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DailyReportLine, Person } from '@/types/models'
import MultiPicker from '@/components/common/MultiPicker.vue'

const props = defineProps<{
  modelValue: DailyReportLine[]
  persons: Person[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [lines: DailyReportLine[]]
}>()

// Deviation display mode: 'units' or 'percent'
const deviationMode = ref<'units' | 'percent'>('units')

const lines = computed({
  get: () => props.modelValue || [],
  set: (value) => emit('update:modelValue', value),
})

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function handleLineChange(index: number) {
  // Create a copy of the lines array to trigger reactivity
  const updatedLines = [...lines.value]
  const line = updatedLines[index]
  
  if (!line) return
  
  // Convert to numbers, handling non-numeric values
  const planned = parseFloat(String(line.planned_labor)) || 0
  const actual = parseFloat(String(line.actual_labor)) || 0
  
  // Calculate deviation as percentage (always store as percentage)
  if (planned > 0) {
    line.deviation = ((actual - planned) / planned) * 100
  } else {
    line.deviation = 0
  }
  
  // Emit the updated lines
  emit('update:modelValue', updatedLines)
}

function getDeviationValue(line: DailyReportLine): number {
  const planned = parseFloat(String(line.planned_labor)) || 0
  const actual = parseFloat(String(line.actual_labor)) || 0
  
  if (deviationMode.value === 'units') {
    // Return deviation in units (actual - planned)
    return actual - planned
  } else {
    // Return deviation in percent (stored value)
    return line.deviation
  }
}

function formatDeviation(line: DailyReportLine): string {
  const value = getDeviationValue(line)
  const formatted = formatNumber(Math.abs(value))
  const sign = value >= 0 ? '+' : '-'
  const unit = deviationMode.value === 'percent' ? '%' : ''
  
  return `${sign}${formatted}${unit}`
}
</script>
