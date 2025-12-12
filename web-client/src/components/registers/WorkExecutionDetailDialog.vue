<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 overflow-y-auto"
    @click.self="handleClose"
  >
    <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
      <div class="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" @click="handleClose"></div>

      <div
        class="inline-block w-full max-w-5xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white rounded-lg shadow-xl"
      >
        <!-- Header -->
        <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900">
              Детализация выполнения работ
            </h3>
            <button
              @click="handleClose"
              class="text-gray-400 hover:text-gray-500"
            >
              <span class="sr-only">Закрыть</span>
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p class="mt-1 text-sm text-gray-600">
            Период: {{ formatDate(periodStart) }} - {{ formatDate(periodEnd) }}
          </p>
        </div>

        <!-- Content -->
        <div class="px-6 py-4 max-h-[70vh] overflow-y-auto">
          <div v-if="loading" class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="mt-2 text-sm text-gray-600">Загрузка...</p>
          </div>

          <div v-else-if="movements.length > 0">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Тип документа
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Номер/Дата
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Дата движения
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Приход кол-во
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Расход кол-во
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Приход сумма
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Расход сумма
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr
                  v-for="movement in movements"
                  :key="movement.id"
                  class="hover:bg-gray-50 cursor-pointer"
                  @dblclick="handleOpenDocument(movement)"
                >
                  <td class="px-4 py-3 text-sm text-gray-900">
                    {{ movement.recorder_type === 'estimate' ? 'Смета' : 'Ежедневный отчет' }}
                  </td>
                  <td class="px-4 py-3 text-sm text-blue-600 hover:text-blue-800">
                    {{ movement.estimate_number || formatDate(movement.period) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-900">
                    {{ formatDate(movement.period) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.quantity_income) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.quantity_expense) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.sum_income) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.sum_expense) }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p class="mt-4 text-sm text-gray-500 italic">
              Дважды кликните на строку, чтобы открыть документ
            </p>
          </div>

          <div v-else class="text-center py-8 text-gray-500">
            Нет данных
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
          <button
            @click="handleClose"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as registersApi from '@/api/registers'
import type { WorkExecutionDetailMovement } from '@/api/registers'

interface Props {
  isOpen: boolean
  periodStart: string
  periodEnd: string
  filters: {
    object_id?: number | null
    estimate_id?: number | null
    work_id?: number | null
  }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const loading = ref(false)
const movements = ref<WorkExecutionDetailMovement[]>([])

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

async function loadData() {
  if (!props.isOpen) return

  loading.value = true
  try {
    const baseParams: Partial<registersApi.WorkExecutionParams> = {
      period_from: props.periodStart,
      period_to: props.periodEnd,
    }

    if (props.filters.object_id) baseParams.object_id = props.filters.object_id
    if (props.filters.estimate_id) baseParams.estimate_id = props.filters.estimate_id
    if (props.filters.work_id) baseParams.work_id = props.filters.work_id

    // Load all movements with pagination
    const allMovements = []
    let page = 1
    let hasMore = true
    
    while (hasMore) {
      const params: registersApi.WorkExecutionParams = {
        ...baseParams,
        page,
        page_size: 100,
      } as registersApi.WorkExecutionParams
      
      const response = await registersApi.getWorkExecutionMovements(params)
      allMovements.push(...response.data)
      hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
      page++
    }
    
    movements.value = allMovements
  } catch (error) {
    console.error('Failed to load work execution movements:', error)
  } finally {
    loading.value = false
  }
}

function handleClose() {
  emit('close')
}

function handleOpenDocument(movement: WorkExecutionDetailMovement) {
  if (movement.recorder_type === 'estimate') {
    router.push(`/documents/estimates/${movement.recorder_id}`)
  } else if (movement.recorder_type === 'daily_report') {
    router.push(`/documents/daily-reports/${movement.recorder_id}`)
  }
  handleClose()
}

watch(() => props.isOpen, (newValue) => {
  if (newValue) {
    loadData()
  }
})
</script>
