<template>
  <div class="space-y-2">
    <label v-if="label" class="block text-sm font-medium text-gray-700">
      {{ label }}
    </label>
    <div class="grid grid-cols-2 gap-2">
      <div>
        <label class="block text-xs text-gray-500 mb-1">С</label>
        <input
          :value="from"
          type="date"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          @input="handleFromChange"
        />
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">По</label>
        <input
          :value="to"
          type="date"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          @input="handleToChange"
        />
      </div>
    </div>
    
    <!-- Quick periods -->
    <div v-if="showQuickPeriods" class="flex flex-wrap gap-1">
      <button
        v-for="period in quickPeriods"
        :key="period.key"
        type="button"
        @click="selectQuickPeriod(period.key)"
        class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 text-gray-700"
      >
        {{ period.label }}
      </button>
    </div>
    
    <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  from?: string | null
  to?: string | null
  label?: string
  showQuickPeriods?: boolean
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  from: null,
  to: null,
  label: '',
  showQuickPeriods: true,
  error: ''
})

const emit = defineEmits<{
  'update:from': [value: string | null]
  'update:to': [value: string | null]
}>()

const quickPeriods = [
  { key: 'today', label: 'Сегодня' },
  { key: 'yesterday', label: 'Вчера' },
  { key: 'week', label: 'Неделя' },
  { key: 'month', label: 'Месяц' },
  { key: 'year', label: 'Год' },
  { key: 'last-month', label: 'Прошлый месяц' },
]

function handleFromChange(event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('update:from', value || null)
}

function handleToChange(event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('update:to', value || null)
}

function selectQuickPeriod(key: string) {
  const today = new Date()
  let from: Date
  let to: Date = today
  
  switch (key) {
    case 'today':
      from = today
      to = today
      break
    case 'yesterday':
      from = new Date(today)
      from.setDate(from.getDate() - 1)
      to = from
      break
    case 'week':
      from = new Date(today)
      from.setDate(from.getDate() - today.getDay() + 1) // Monday
      break
    case 'month':
      from = new Date(today.getFullYear(), today.getMonth(), 1)
      break
    case 'year':
      from = new Date(today.getFullYear(), 0, 1)
      break
    case 'last-month':
      from = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      to = new Date(today.getFullYear(), today.getMonth(), 0)
      break
    default:
      return
  }
  
  emit('update:from', formatDate(from))
  emit('update:to', formatDate(to))
}

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
</script>
