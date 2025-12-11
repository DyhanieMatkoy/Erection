<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Сметы</h2>
        <p class="mt-1 text-sm text-gray-600">Управление сметами</p>
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
            label="Период"
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
            <label class="block text-sm font-medium text-gray-700 mb-1">Заказчик</label>
            <select
              v-model="filters.filters.value.customerId"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все заказчики</option>
              <option v-for="customer in customers" :key="customer.id" :value="customer.id">
                {{ customer.name }}
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
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Сумма от</label>
            <input
              v-model.number="filters.filters.value.sumFrom"
              type="number"
              step="0.01"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="0.00"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Сумма до</label>
            <input
              v-model.number="filters.filters.value.sumTo"
              type="number"
              step="0.01"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="0.00"
            />
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
          <div class="flex gap-2">
            <button
              @click="handleCreateFromTimesheet"
              class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Ввод на основании ежедневного отчета
            </button>
            <button
              @click="handleImportExcel"
              class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              Импорт из Excel
            </button>
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
              Создать смету
            </button>
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept=".xlsx,.xls"
            style="display: none"
            @change="handleFileSelected"
          />
        </template>

        <template #cell-date="{ value }">
          {{ formatDate(value) }}
        </template>

        <template #cell-total_sum="{ value }">
          {{ formatNumber(value) }}
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
          <button @click.stop="handleEdit(row as Estimate)" class="text-blue-600 hover:text-blue-900 mr-3">
            Открыть
          </button>
          <button
            @click.stop="handlePrint(row as Estimate, 'excel')"
            class="text-green-600 hover:text-green-900 mr-3"
            title="Печать в Excel"
          >
            Excel
          </button>
          <button
            @click.stop="handlePrint(row as Estimate, 'pdf')"
            class="text-purple-600 hover:text-purple-900 mr-3"
            title="Печать в PDF"
          >
            PDF
          </button>
          <button
            v-if="!row.is_posted"
            @click.stop="handleDelete(row as Estimate)"
            class="text-red-600 hover:text-red-900"
          >
            Удалить
          </button>
        </template>
      </DataTable>

      <!-- Modal for selecting timesheet -->
      <Modal
        :open="showTimesheetModal"
        title="Выбор ежедневного отчета"
        size="lg"
        @close="handleCloseTimesheetModal"
      >
        <div class="space-y-4">
          <p class="text-sm text-gray-600">
            Выберите ежедневный отчет для создания сметы на его основании
          </p>
          
          <div class="max-h-96 overflow-y-auto border border-gray-300 rounded-md">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50 sticky top-0">
                <tr>
                  <th class="w-12 px-3 py-3"></th>
                  <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Номер</th>
                  <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Дата</th>
                  <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Объект</th>
                  <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Заказчик</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr
                  v-for="timesheet in timesheets"
                  :key="timesheet.id"
                  @click="selectedTimesheetId = timesheet.id || null"
                  :class="[
                    'cursor-pointer hover:bg-gray-50',
                    selectedTimesheetId === timesheet.id ? 'bg-blue-50' : ''
                  ]"
                >
                  <td class="px-3 py-2 text-center">
                    <input
                      type="radio"
                      :checked="selectedTimesheetId === timesheet.id"
                      @change="selectedTimesheetId = timesheet.id || null"
                      class="h-4 w-4 text-blue-600"
                    />
                  </td>
                  <td class="px-3 py-2 text-sm">{{ timesheet.number }}</td>
                  <td class="px-3 py-2 text-sm">{{ formatDate(timesheet.date) }}</td>
                  <td class="px-3 py-2 text-sm">{{ timesheet.object_name }}</td>
                  <td class="px-3 py-2 text-sm">{{ timesheet.customer_name }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <template #footer>
          <button
            @click="handleCloseTimesheetModal"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
          >
            Отмена
          </button>
          <button
            @click="handleTimesheetSelected"
            type="button"
            :disabled="!selectedTimesheetId"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Создать смету
          </button>
        </template>
      </Modal>
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
import type { Estimate, Timesheet } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'
import DateRangePicker from '@/components/common/DateRangePicker.vue'
import Modal from '@/components/common/Modal.vue'

const router = useRouter()
const table = useTable()
const referencesStore = useReferencesStore()
const tableRef = ref<InstanceType<typeof DataTable>>()
const selectedItems = ref<Estimate[]>([])
const fileInputRef = ref<HTMLInputElement>()
const showTimesheetModal = ref(false)
const timesheets = ref<Timesheet[]>([])
const selectedTimesheetId = ref<number | null>(null)

// Filters
const filters = useFilters({
  dateFrom: null as string | null,
  dateTo: null as string | null,
  objectId: null as number | null,
  customerId: null as number | null,
  isPosted: null as boolean | null,
  sumFrom: null as number | null,
  sumTo: null as number | null,
})

// Reference data
const objects = ref<any[]>([])
const customers = ref<any[]>([])

const columns = [
  { key: 'number', label: 'Номер', width: '100px' },
  { key: 'date', label: 'Дата', width: '100px' },
  { key: 'is_posted', label: 'Статус', width: '40px', sortable: false },
  { key: 'customer_name', label: 'Заказчик', width: '200px' },
  { key: 'object_name', label: 'Объект', width: '250px' },
  { key: 'total_sum', label: 'Сумма', width: '120px' },
  { key: 'author', label: 'Автор', width: '150px' },
]

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
  table.loading.value = true
  try {
    const params = {
      ...table.queryParams.value,
      ...filters.getQueryParams()
    }
    const response = await documentsApi.getEstimates(params)
    table.data.value = response.data
    table.pagination.value = response.pagination
  } catch (error) {
    console.error('Failed to load estimates:', error)
  } finally {
    table.loading.value = false
  }
}

async function loadReferences() {
  try {
    await referencesStore.fetchObjects()
    await referencesStore.fetchCounterparties()
    objects.value = referencesStore.objects
    customers.value = referencesStore.counterparties
  } catch (error) {
    console.error('Failed to load references:', error)
  }
}

function handleApplyFilters() {
  filters.applyFilters()
  table.setPage(1) // Reset to first page
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
  router.push('/documents/estimates/new')
}

async function handleCreateFromTimesheet() {
  try {
    // Загружаем список ежедневных отчетов
    const response = await documentsApi.getTimesheets({
      page: 1,
      page_size: 100,
      sort_by: 'date',
      sort_order: 'desc'
    })
    timesheets.value = response.data
    selectedTimesheetId.value = null
    showTimesheetModal.value = true
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при загрузке ежедневных отчетов')
  }
}

async function handleTimesheetSelected() {
  if (!selectedTimesheetId.value) {
    alert('Выберите ежедневный отчет')
    return
  }
  
  showTimesheetModal.value = false
  router.push(`/documents/estimates/new?timesheet_id=${selectedTimesheetId.value}`)
}

function handleCloseTimesheetModal() {
  showTimesheetModal.value = false
  selectedTimesheetId.value = null
}

function handleImportExcel() {
  fileInputRef.value?.click()
}

async function handleFileSelected(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  try {
    const estimate = await documentsApi.importEstimateFromExcel(file)
    alert(`Смета "${estimate.number}" успешно импортирована`)
    await loadData()
    // Open imported estimate
    router.push(`/documents/estimates/${estimate.id}`)
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при импорте')
  } finally {
    // Reset file input
    if (target) {
      target.value = ''
    }
  }
}

async function handlePrint(item: Estimate, format: 'pdf' | 'excel') {
  try {
    const blob = await documentsApi.printEstimate(item.id!, format)
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `estimate_${item.number}.${format === 'pdf' ? 'pdf' : 'xlsx'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при печати')
  }
}

function handleEdit(item: Estimate) {
  router.push(`/documents/estimates/${item.id}`)
}

async function handleDelete(item: Estimate) {
  if (!confirm(`Удалить смету "${item.number}"?`)) {
    return
  }

  try {
    await documentsApi.deleteEstimate(item.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при удалении')
  }
}

function handleSelectionChange(items: Estimate[]) {
  selectedItems.value = items
}

async function handleBulkDelete() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Удалить выбранные сметы (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkDeleteEstimates(ids)
    
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
  
  if (!confirm(`Провести выбранные сметы (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkPostEstimates(ids)
    
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
  
  if (!confirm(`Отменить проведение выбранных смет (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkUnpostEstimates(ids)
    
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
