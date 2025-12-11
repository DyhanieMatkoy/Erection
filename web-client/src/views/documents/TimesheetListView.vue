<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Табели</h2>
        <p class="mt-1 text-sm text-gray-600">Управление табелями учета рабочего времени</p>
      </div>

      <DataTable
        ref="tableRef"
        :columns="columns"
        :data="table.data.value"
        :loading="table.loading.value"
        :pagination="table.pagination.value"
        :selectable="true"
        :has-filters="true"
        @row-click="handleEdit"
        @page-change="handlePageChange"
        @search="handleSearch"
        @sort="handleSort"
        @selection-change="handleSelectionChange"
        @refresh="loadData"
        @apply-filters="handleApplyFilters"
        @clear-filters="handleClearFilters"
      >
        <template #filters>
          <DateRangePicker
            v-model:from="filters.filters.value.dateFrom"
            v-model:to="filters.filters.value.dateTo"
            label="Период документа"
          />
          
          <DateRangePicker
            v-model:from="filters.filters.value.periodFrom"
            v-model:to="filters.filters.value.periodTo"
            label="Табельный период"
            :show-quick-periods="false"
          />
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Объект</label>
            <select
              v-model="filters.filters.value.objectId"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все объекты</option>
              <option v-for="obj in objects" :key="obj.id" :value="obj.id">
                {{ obj.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Смета</label>
            <select
              v-model="filters.filters.value.estimateId"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все сметы</option>
              <option v-for="est in estimates" :key="est.id" :value="est.id">
                {{ est.number }} - {{ est.object_name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Статус проведения</label>
            <select
              v-model="filters.filters.value.isPosted"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все</option>
              <option :value="true">Проведенные</option>
              <option :value="false">Не проведенные</option>
            </select>
          </div>
        </template>
        <template #bulk-actions="{ selected }">
          <div v-if="selected.length > 0" class="flex gap-2">
            <button
              @click="handleBulkPost"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
            >
              Провести ({{ selected.length }})
            </button>
            <button
              @click="handleBulkUnpost"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700"
            >
              Отменить проведение ({{ selected.length }})
            </button>
            <button
              @click="handleBulkDelete"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
            >
              Удалить ({{ selected.length }})
            </button>
          </div>
        </template>
        <template #header-actions>
          <button
            @click="handleCreate"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Создать табель
          </button>
        </template>

        <template #cell-date="{ value }">
          {{ formatDate(value) }}
        </template>

        <template #cell-month_year="{ value }">
          {{ formatMonthYear(value) }}
        </template>

        <template #cell-is_posted="{ value }">
          <div class="flex items-center justify-center">
            <span
              :class="[
                'inline-flex items-center justify-center w-6 h-6 rounded-full',
                value ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
              ]"
              :title="value ? 'Проведен' : 'Не проведен'"
            >
              <svg v-if="value" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <circle cx="10" cy="10" r="3" />
              </svg>
            </span>
          </div>
        </template>

        <template #actions="{ row }">
          <button @click.stop="handleEdit(row as Timesheet)" class="text-blue-600 hover:text-blue-900 mr-4">
            Открыть
          </button>
          <button
            v-if="!row.is_posted"
            @click.stop="handleDelete(row as Timesheet)"
            class="text-red-600 hover:text-red-900"
          >
            Удалить
          </button>
        </template>
      </DataTable>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTable } from '@/composables/useTable'
import { useFilters } from '@/composables/useFilters'
import { useReferencesStore } from '@/stores/references'
import * as documentsApi from '@/api/documents'
import type { Timesheet, Estimate } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'
import DateRangePicker from '@/components/common/DateRangePicker.vue'

const router = useRouter()
const table = useTable()
const referencesStore = useReferencesStore()
const tableRef = ref<InstanceType<typeof DataTable>>()
const selectedItems = ref<Timesheet[]>([])

// Filters
const filters = useFilters({
  dateFrom: null as string | null,
  dateTo: null as string | null,
  periodFrom: null as string | null,
  periodTo: null as string | null,
  objectId: null as number | null,
  estimateId: null as number | null,
  isPosted: null as boolean | null,
})

// Reference data
const objects = ref<any[]>([])
const estimates = ref<Estimate[]>([])

const columns = [
  { key: 'number', label: 'Номер', width: '100px' },
  { key: 'date', label: 'Дата', width: '100px' },
  { key: 'is_posted', label: 'Статус', width: '40px', sortable: false },
  { key: 'month_year', label: 'Период', width: '150px' },
  { key: 'object_name', label: 'Объект', width: '250px' },
  { key: 'estimate_number', label: 'Смета', width: '120px' },
  { key: 'foreman_name', label: 'Бригадир', width: '200px' },
  { key: 'total_hours', label: 'Часов', width: '100px' },
  { key: 'author', label: 'Автор', width: '150px' },
]

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

function formatMonthYear(monthYear: string): string {
  if (!monthYear) return ''
  const parts = monthYear.split('-')
  if (parts.length < 2) return monthYear
  const year = parts[0]!
  const month = parts[1]!
  const date = new Date(parseInt(year), parseInt(month) - 1)
  return date.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long' })
}

async function loadData() {
  table.loading.value = true
  try {
    const params = {
      ...table.queryParams.value,
      ...filters.getQueryParams()
    }
    const response = await documentsApi.getTimesheets(params)
    table.data.value = response.data || []
    table.pagination.value = response.pagination
  } catch (error: any) {
    console.error('Failed to load timesheets:', error)
    alert(error.response?.data?.detail || 'Ошибка при загрузке')
  } finally {
    table.loading.value = false
  }
}

async function loadReferences() {
  try {
    await referencesStore.fetchObjects()
    objects.value = referencesStore.objects
    
    // Load estimates for filter with pagination
    const allEstimates = []
    let page = 1
    let hasMore = true
    
    while (hasMore) {
      const response = await documentsApi.getEstimates({ page, page_size: 100 })
      allEstimates.push(...response.data)
      hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
      page++
    }
    
    estimates.value = allEstimates
    console.log(`Loaded ${estimates.value.length} estimates`)
  } catch (error) {
    console.error('Failed to load references:', error)
  }
}

function handleApplyFilters() {
  filters.applyFilters()
  table.setPage(1)
  loadData()
}

function handleClearFilters() {
  filters.clearAllFilters()
  table.setPage(1)
  loadData()
}

function handlePageChange(page: number) {
  table.setPage(page)
  loadData()
}

function handleSearch(query: string) {
  table.setSearch(query)
  loadData()
}

function handleSort(sortBy: string, sortOrder: 'asc' | 'desc') {
  table.setSort(sortBy, sortOrder)
  loadData()
}

function handleCreate() {
  router.push('/documents/timesheets/new')
}

function handleEdit(item: Timesheet) {
  router.push(`/documents/timesheets/${item.id}`)
}

async function handleDelete(item: Timesheet) {
  if (!confirm(`Удалить табель ${item.number}?`)) {
    return
  }

  try {
    await documentsApi.deleteTimesheet(item.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при удалении')
  }
}

function handleSelectionChange(items: Timesheet[]) {
  selectedItems.value = items
}

async function handleBulkDelete() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Удалить выбранные табели (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkDeleteTimesheets(ids)
    
    if (result.errors.length > 0) {
      alert(`${result.message}\n\nОшибки:\n${result.errors.join('\n')}`)
    } else {
      alert(result.message)
    }
    
    tableRef.value?.clearSelection()
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при групповом удалении')
  }
}

async function handleBulkPost() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Провести выбранные табели (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkPostTimesheets(ids)
    
    if (result.errors.length > 0) {
      alert(`${result.message}\n\nОшибки:\n${result.errors.join('\n')}`)
    } else {
      alert(result.message)
    }
    
    tableRef.value?.clearSelection()
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при групповом проведении')
  }
}

async function handleBulkUnpost() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Отменить проведение выбранных табелей (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkUnpostTimesheets(ids)
    
    if (result.errors.length > 0) {
      alert(`${result.message}\n\nОшибки:\n${result.errors.join('\n')}`)
    } else {
      alert(result.message)
    }
    
    tableRef.value?.clearSelection()
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при отмене проведения')
  }
}

onMounted(async () => {
  await loadReferences()
  
  // Set default period to current month
  const today = new Date()
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
  const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
  
  filters.filters.value.dateFrom = formatDateToISO(firstDay)
  filters.filters.value.dateTo = formatDateToISO(lastDay)
  filters.applyFilters()
  
  loadData()
})

function formatDateToISO(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
</script>
