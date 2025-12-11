<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Регистр выполнения работ</h2>
        <p class="mt-1 text-sm text-gray-600">Просмотр движений по выполнению работ</p>
      </div>

      <!-- Filters -->
      <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Фильтры</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FormField
            v-model="filters.period_from"
            label="Период с"
            type="date"
          />

          <FormField
            v-model="filters.period_to"
            label="Период по"
            type="date"
          />

          <Picker
            v-model="filters.object_id"
            label="Объект"
            :items="objects"
            placeholder="Все объекты"
          />

          <Picker
            v-model="filters.estimate_id"
            label="Смета"
            :items="estimates"
            placeholder="Все сметы"
          />

          <Picker
            v-model="filters.work_id"
            label="Работа"
            :items="works"
            placeholder="Все работы"
          />

          <FormField
            v-model="filters.group_by"
            label="Группировка"
            type="select"
            :options="groupByOptions"
          />
        </div>

        <div class="mt-4 flex space-x-3">
          <button
            @click="handleApplyFilters"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Применить
          </button>
          <button
            @click="handleResetFilters"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Сбросить
          </button>
        </div>
      </div>

      <!-- Results -->
      <div class="bg-white shadow rounded-lg p-6">
        <div v-if="loading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p class="mt-2 text-sm text-gray-600">Загрузка...</p>
        </div>

        <div v-else-if="movements.length > 0" class="space-y-4">
          <!-- Desktop table -->
          <div class="hidden md:block overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Период
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Объект
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Смета
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Работа
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Приход кол.
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Приход сумма
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Расход кол.
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Расход сумма
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Остаток кол.
                  </th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Остаток сумма
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr
                  v-for="(movement, index) in movements"
                  :key="index"
                  class="hover:bg-gray-50 cursor-pointer"
                  @dblclick="handleShowDetail(movement)"
                >
                  <td class="px-4 py-3 text-sm text-gray-900">{{ formatDate(movement.period) }}</td>
                  <td class="px-4 py-3 text-sm text-gray-900">{{ movement.object_name }}</td>
                  <td class="px-4 py-3 text-sm text-gray-900">{{ movement.estimate_number }}</td>
                  <td class="px-4 py-3 text-sm text-gray-900">{{ movement.work_name }}</td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.income_quantity) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.income_sum) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.expense_quantity) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(movement.expense_sum) }}
                  </td>
                  <td
                    class="px-4 py-3 text-sm text-right font-medium"
                    :class="movement.balance_quantity >= 0 ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ formatNumber(movement.balance_quantity) }}
                  </td>
                  <td
                    class="px-4 py-3 text-sm text-right font-medium"
                    :class="movement.balance_sum >= 0 ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ formatNumber(movement.balance_sum) }}
                  </td>
                </tr>
                <!-- Totals row -->
                <tr class="bg-gray-50 font-semibold">
                  <td colspan="4" class="px-4 py-3 text-sm text-gray-900">Итого:</td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(totals.income_quantity) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(totals.income_sum) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(totals.expense_quantity) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-900">
                    {{ formatNumber(totals.expense_sum) }}
                  </td>
                  <td
                    class="px-4 py-3 text-sm text-right"
                    :class="totals.balance_quantity >= 0 ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ formatNumber(totals.balance_quantity) }}
                  </td>
                  <td
                    class="px-4 py-3 text-sm text-right"
                    :class="totals.balance_sum >= 0 ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ formatNumber(totals.balance_sum) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile cards -->
          <div class="md:hidden space-y-4">
            <div
              v-for="(movement, index) in movements"
              :key="index"
              class="border border-gray-200 rounded-lg p-4 space-y-2 cursor-pointer hover:bg-gray-50"
              @click="handleShowDetail(movement)"
            >
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span class="text-gray-500">Период:</span>
                  <span class="ml-2 text-gray-900">{{ formatDate(movement.period) }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Объект:</span>
                  <span class="ml-2 text-gray-900">{{ movement.object_name }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Смета:</span>
                  <span class="ml-2 text-gray-900">{{ movement.estimate_number }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Работа:</span>
                  <span class="ml-2 text-gray-900">{{ movement.work_name }}</span>
                </div>
              </div>
              <div class="border-t pt-2 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span class="text-gray-500">Приход:</span>
                  <span class="ml-2 text-gray-900">
                    {{ formatNumber(movement.income_quantity) }} /
                    {{ formatNumber(movement.income_sum) }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500">Расход:</span>
                  <span class="ml-2 text-gray-900">
                    {{ formatNumber(movement.expense_quantity) }} /
                    {{ formatNumber(movement.expense_sum) }}
                  </span>
                </div>
                <div class="col-span-2">
                  <span class="text-gray-500">Остаток:</span>
                  <span
                    class="ml-2 font-medium"
                    :class="movement.balance_quantity >= 0 ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ formatNumber(movement.balance_quantity) }} /
                    {{ formatNumber(movement.balance_sum) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Mobile totals -->
            <div class="border-2 border-gray-300 rounded-lg p-4 bg-gray-50">
              <div class="text-sm font-semibold text-gray-900 mb-2">Итого:</div>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span class="text-gray-500">Приход:</span>
                  <span class="ml-2 text-gray-900">
                    {{ formatNumber(totals.income_quantity) }} /
                    {{ formatNumber(totals.income_sum) }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500">Расход:</span>
                  <span class="ml-2 text-gray-900">
                    {{ formatNumber(totals.expense_quantity) }} /
                    {{ formatNumber(totals.expense_sum) }}
                  </span>
                </div>
                <div class="col-span-2">
                  <span class="text-gray-500">Остаток:</span>
                  <span
                    class="ml-2 font-semibold"
                    :class="totals.balance_sum >= 0 ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ formatNumber(totals.balance_quantity) }} /
                    {{ formatNumber(totals.balance_sum) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-500">
          Нет данных. Примените фильтры для поиска.
        </div>

        <p v-if="movements.length > 0" class="mt-4 text-sm text-gray-500 italic">
          Дважды кликните на строку, чтобы открыть детализацию
        </p>
      </div>
    </div>

    <!-- Detail Dialog -->
    <WorkExecutionDetailDialog
      :is-open="detailDialog.isOpen"
      :period-start="detailDialog.periodStart"
      :period-end="detailDialog.periodEnd"
      :filters="detailDialog.filters"
      @close="detailDialog.isOpen = false"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useReferencesStore } from '@/stores/references'
import * as registersApi from '@/api/registers'
import type { WorkExecutionMovement } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import FormField from '@/components/common/FormField.vue'
import Picker from '@/components/common/Picker.vue'
import WorkExecutionDetailDialog from '@/components/registers/WorkExecutionDetailDialog.vue'

const referencesStore = useReferencesStore()

const filters = ref({
  period_from: '',
  period_to: '',
  object_id: null as number | null,
  estimate_id: null as number | null,
  work_id: null as number | null,
  group_by: '',
})

const loading = ref(false)
const movements = ref<WorkExecutionMovement[]>([])
const estimatesData = ref<{ id: number; number: string; date: string }[]>([])

const detailDialog = ref({
  isOpen: false,
  periodStart: '',
  periodEnd: '',
  filters: {} as { object_id?: number | null; estimate_id?: number | null; work_id?: number | null },
})

const groupByOptions = [
  { value: '', label: 'Без группировки' },
  { value: 'object', label: 'По объекту' },
  { value: 'estimate', label: 'По смете' },
  { value: 'work', label: 'По работе' },
]

const objects = computed(() =>
  referencesStore.objects
    .filter((o) => !o.is_deleted)
    .map((o) => ({ id: o.id!, name: o.name }))
)

const works = computed(() =>
  referencesStore.works
    .filter((w) => !w.is_deleted)
    .map((w) => ({ id: w.id!, name: w.name }))
)

const estimates = computed(() =>
  estimatesData.value.map((e) => ({
    id: e.id,
    name: `${e.number} от ${formatDate(e.date)}`,
  }))
)

const totals = computed(() => {
  return movements.value.reduce(
    (acc, movement) => {
      acc.income_quantity += movement.income_quantity
      acc.income_sum += movement.income_sum
      acc.expense_quantity += movement.expense_quantity
      acc.expense_sum += movement.expense_sum
      acc.balance_quantity += movement.balance_quantity
      acc.balance_sum += movement.balance_sum
      return acc
    },
    {
      income_quantity: 0,
      income_sum: 0,
      expense_quantity: 0,
      expense_sum: 0,
      balance_quantity: 0,
      balance_sum: 0,
    }
  )
})

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
  loading.value = true
  try {
    const params: registersApi.WorkExecutionParams = {}
    
    if (filters.value.period_from) params.period_from = filters.value.period_from
    if (filters.value.period_to) params.period_to = filters.value.period_to
    if (filters.value.object_id) params.object_id = filters.value.object_id
    if (filters.value.estimate_id) params.estimate_id = filters.value.estimate_id
    if (filters.value.work_id) params.work_id = filters.value.work_id
    if (filters.value.group_by) params.group_by = filters.value.group_by

    const response = await registersApi.getWorkExecutionRegister(params)
    movements.value = response.data
  } catch (error) {
    console.error('Failed to load work execution register:', error)
  } finally {
    loading.value = false
  }
}

function handleApplyFilters() {
  loadData()
}

function handleResetFilters() {
  filters.value = {
    period_from: '',
    period_to: '',
    object_id: null,
    estimate_id: null,
    work_id: null,
    group_by: '',
  }
  movements.value = []
}

function handleShowDetail(movement: WorkExecutionMovement) {
  if (!filters.value.period_from || !filters.value.period_to) {
    return
  }

  detailDialog.value = {
    isOpen: true,
    periodStart: filters.value.period_from,
    periodEnd: filters.value.period_to,
    filters: {
      object_id: movement.object_id || filters.value.object_id,
      estimate_id: movement.estimate_id || filters.value.estimate_id,
      work_id: movement.work_id || filters.value.work_id,
    },
  }
}

onMounted(async () => {
  // Load references
  await Promise.all([
    referencesStore.fetchObjects(),
    referencesStore.fetchWorks(),
  ])

  // Load estimates for filter
  try {
    const documentsApi = await import("@/api/documents")
    
    // Load all estimates with pagination
    const allEstimates = []
    let page = 1
    let hasMore = true
    
    while (hasMore) {
      const response = await documentsApi.getEstimates({ page, page_size: 100 })
      allEstimates.push(...response.data)
      hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
      page++
    }
    
    estimatesData.value = allEstimates.map((e) => ({
      id: e.id!,
      number: e.number,
      date: e.date,
    }))
  } catch (error) {
    console.error('Failed to load estimates:', error)
  }
})
</script>
