<template>
  <div class="bg-white shadow rounded-lg p-4 space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="text-base font-medium text-gray-900">Табличная часть</h3>
      <button
        v-if="!disabled"
        @click="handleAddEmployee"
        class="inline-flex items-center px-2 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
      >
        <svg class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        Добавить сотрудника
      </button>
    </div>

    <div class="border border-gray-200 rounded-lg overflow-hidden">
      <!-- Fixed columns wrapper -->
      <div class="flex">
        <!-- Fixed left columns (Employee and Rate) -->
        <div class="flex-shrink-0 border-r border-gray-200">
          <table class="divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  class="px-2 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-40"
                >
                  Сотрудник
                </th>
                <th
                  class="px-2 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20"
                >
                  Ставка
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-if="lines.length === 0">
                <td colspan="2" class="px-2 py-2 text-center text-xs text-gray-500">
                  Нет данных
                </td>
              </tr>
              <tr v-for="(line, index) in lines" :key="index" class="hover:bg-gray-50">
                <td class="px-2 py-1 whitespace-nowrap text-xs text-gray-900">
                  {{ getEmployeeName(line.employee_id) }}
                </td>
                <td class="px-2 py-1 whitespace-nowrap">
                  <input
                    v-model.number="line.hourly_rate"
                    type="number"
                    min="0"
                    step="0.01"
                    :disabled="disabled"
                    class="w-16 rounded border-gray-300 text-xs text-center focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 no-spinner"
                    @input="recalculateLine(index)"
                    @keydown="handleKeyDown"
                  />
                </td>
              </tr>
              <tr v-if="lines.length > 0" class="bg-gray-100 font-bold">
                <td class="px-2 py-1 text-xs text-gray-900">Итого:</td>
                <td class="px-2 py-1"></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Scrollable days columns -->
        <div class="flex-1 overflow-x-auto">
          <table class="divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  v-for="day in daysInMonth"
                  :key="day"
                  :class="[
                    'px-1 py-1.5 text-center text-xs font-medium w-14',
                    isWeekend(day) ? 'bg-red-50 text-red-700' : 'text-gray-500',
                  ]"
                >
                  {{ day }}
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-if="lines.length === 0">
                <td :colspan="daysInMonth" class="px-2 py-2 text-center text-xs text-gray-500">
                  Добавьте сотрудников
                </td>
              </tr>
              <tr v-for="(line, index) in lines" :key="index" class="hover:bg-gray-50">
                <td v-for="day in daysInMonth" :key="day" class="px-1 py-1">
                  <input
                    v-model.number="line.days[day]"
                    type="number"
                    min="0"
                    max="24"
                    step="0.5"
                    :disabled="disabled"
                    :class="[
                      'w-12 rounded border-gray-300 text-xs text-center focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 no-spinner',
                      isWeekend(day) ? 'bg-red-50' : '',
                    ]"
                    @input="recalculateLine(index)"
                    @keydown="handleKeyDown"
                  />
                </td>
              </tr>
              <tr v-if="lines.length > 0" class="bg-gray-100 font-bold">
                <td v-for="day in daysInMonth" :key="day" class="px-1 py-1 text-center text-xs">
                  {{ getDayTotal(day).toFixed(1) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Fixed right columns (Totals and Actions) -->
        <div class="flex-shrink-0 border-l border-gray-200">
          <table class="divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  class="px-2 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-blue-50 w-16"
                >
                  Итого
                </th>
                <th
                  class="px-2 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-blue-50 w-20"
                >
                  Сумма
                </th>
                <th
                  v-if="!disabled"
                  class="px-2 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16"
                >
                  
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-if="lines.length === 0">
                <td :colspan="disabled ? 2 : 3" class="px-2 py-2 text-center text-xs text-gray-500">
                  -
                </td>
              </tr>
              <tr v-for="(line, index) in lines" :key="index" class="hover:bg-gray-50">
                <td class="px-2 py-1 whitespace-nowrap text-xs font-medium text-gray-900 bg-blue-50">
                  {{ line.total_hours.toFixed(1) }}
                </td>
                <td class="px-2 py-1 whitespace-nowrap text-xs font-medium text-gray-900 bg-blue-50">
                  {{ line.total_amount.toFixed(0) }}
                </td>
                <td v-if="!disabled" class="px-2 py-1 whitespace-nowrap text-xs">
                  <button
                    @click="handleRemoveLine(index)"
                    class="text-red-600 hover:text-red-900"
                    title="Удалить"
                  >
                    ✕
                  </button>
                </td>
              </tr>
              <tr v-if="lines.length > 0" class="bg-gray-100 font-bold">
                <td class="px-2 py-1 text-xs bg-blue-100">{{ totalHours.toFixed(1) }}</td>
                <td class="px-2 py-1 text-xs bg-blue-100">{{ totalAmount.toFixed(0) }}</td>
                <td v-if="!disabled"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Employee Picker Dialog -->
    <div
      v-if="showEmployeePicker"
      class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50"
      @click.self="showEmployeePicker = false"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Выбор сотрудника</h3>
        </div>
        <div class="px-6 py-4 overflow-y-auto flex-1">
          <div class="mb-4">
            <input
              v-model="employeeSearch"
              type="text"
              placeholder="Поиск..."
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>
          <div class="space-y-2">
            <button
              v-for="person in filteredPersons"
              :key="person.id"
              @click="selectEmployee(person)"
              class="w-full text-left px-4 py-3 border border-gray-200 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <div class="font-medium text-gray-900">{{ person.full_name }}</div>
              <div v-if="person.position" class="text-sm text-gray-500">{{ person.position }}</div>
            </button>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            @click="showEmployeePicker = false"
            class="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { TimesheetLine, Person } from '@/types/models'

interface Props {
  modelValue: TimesheetLine[]
  persons: Person[]
  monthYear: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: TimesheetLine[]]
}>()

const lines = ref<TimesheetLine[]>([])
const showEmployeePicker = ref(false)
const employeeSearch = ref('')

// Calculate days in month
const daysInMonth = computed(() => {
  if (!props.monthYear) return 31
  const parts = props.monthYear.split('-').map(Number)
  const year = parts[0]
  const month = parts[1]
  if (!year || !month) return 31
  return new Date(year, month, 0).getDate()
})

// Filter persons for picker
const filteredPersons = computed(() => {
  const search = employeeSearch.value.toLowerCase()
  return props.persons.filter(
    (p) =>
      !p.is_deleted &&
      (p.full_name.toLowerCase().includes(search) ||
        (p.position && p.position.toLowerCase().includes(search)))
  )
})

// Calculate totals
const totalHours = computed(() => {
  return lines.value.reduce((sum, line) => sum + line.total_hours, 0)
})

const totalAmount = computed(() => {
  return lines.value.reduce((sum, line) => sum + line.total_amount, 0)
})

// Get employee name
function getEmployeeName(employeeId: number): string {
  const person = props.persons.find((p) => p.id === employeeId)
  return person?.full_name || 'Неизвестно'
}

// Check if day is weekend
function isWeekend(day: number): boolean {
  if (!props.monthYear) return false
  const parts = props.monthYear.split('-').map(Number)
  const year = parts[0]
  const month = parts[1]
  if (!year || !month) return false
  const date = new Date(year, month - 1, day)
  const dayOfWeek = date.getDay()
  return dayOfWeek === 0 || dayOfWeek === 6 // Sunday or Saturday
}

// Get total hours for a specific day
function getDayTotal(day: number): number {
  return lines.value.reduce((sum: number, line) => {
    const hours = line.days[day] || 0
    return sum + (typeof hours === 'number' ? hours : 0)
  }, 0)
}

// Recalculate line totals
function recalculateLine(index: number) {
  const line = lines.value[index]
  if (!line) return
  line.total_hours = Object.values(line.days).reduce((sum: number, hours) => {
    const hoursValue = typeof hours === 'number' ? hours : 0
    return sum + hoursValue
  }, 0)
  line.total_amount = line.total_hours * line.hourly_rate
  emitUpdate()
}

// Add employee
function handleAddEmployee() {
  employeeSearch.value = ''
  showEmployeePicker.value = true
}

// Select employee from picker
function selectEmployee(person: Person) {
  // Check if employee already exists
  if (lines.value.some((line) => line.employee_id === person.id)) {
    alert('Этот сотрудник уже добавлен')
    return
  }

  // Create new line
  const newLine: TimesheetLine = {
    line_number: lines.value.length + 1,
    employee_id: person.id,
    employee_name: person.full_name,
    hourly_rate: 0,
    days: {},
    total_hours: 0,
    total_amount: 0,
  }

  // Initialize all days to 0
  for (let day = 1; day <= daysInMonth.value; day++) {
    newLine.days[day] = 0
  }

  lines.value.push(newLine)
  showEmployeePicker.value = false
  emitUpdate()
}

// Remove line
function handleRemoveLine(index: number) {
  if (confirm('Удалить строку?')) {
    lines.value.splice(index, 1)
    // Renumber lines
    lines.value.forEach((line, i) => {
      line.line_number = i + 1
    })
    emitUpdate()
  }
}

// Emit update
function emitUpdate() {
  emit('update:modelValue', lines.value)
}

// Handle keyboard navigation
function handleKeyDown(event: KeyboardEvent) {
  const input = event.target as HTMLInputElement
  
  if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
    event.preventDefault()
    
    // Find the current cell
    const td = input.closest('td')
    const tr = td?.closest('tr')
    const tbody = tr?.closest('tbody')
    
    if (!td || !tr || !tbody) return
    
    // Get all rows
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(
      (row) => !row.classList.contains('bg-gray-100')
    )
    const currentRowIndex = rows.indexOf(tr)
    
    // Get all inputs in current row
    const rowInputs = Array.from(tr.querySelectorAll('input[type="number"]'))
    const currentInputIndex = rowInputs.indexOf(input)
    
    if (currentInputIndex === -1) return
    
    // Calculate target row
    let targetRowIndex = currentRowIndex
    if (event.key === 'ArrowUp' && currentRowIndex > 0) {
      targetRowIndex = currentRowIndex - 1
    } else if (event.key === 'ArrowDown' && currentRowIndex < rows.length - 1) {
      targetRowIndex = currentRowIndex + 1
    }
    
    // Focus the same input in the target row
    if (targetRowIndex !== currentRowIndex) {
      const targetRow = rows[targetRowIndex]
      if (!targetRow) return
      const targetInputs = Array.from(targetRow.querySelectorAll('input[type="number"]'))
      const targetInput = targetInputs[currentInputIndex] as HTMLInputElement
      
      if (targetInput) {
        targetInput.focus()
        targetInput.select()
      }
    }
  }
}

// Watch for external changes
watch(
  () => props.modelValue,
  (newValue) => {
    lines.value = JSON.parse(JSON.stringify(newValue))
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
/* Hide number input spinner controls */
.no-spinner::-webkit-outer-spin-button,
.no-spinner::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.no-spinner[type='number'] {
  -moz-appearance: textfield;
  appearance: textfield;
}
</style>
