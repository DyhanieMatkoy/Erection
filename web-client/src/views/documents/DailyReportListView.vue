<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Ежедневные отчеты</h2>
        <p class="mt-1 text-sm text-gray-600">Управление ежедневными отчетами</p>
      </div>

      <DataTable
        ref="tableRef"
        :columns="columns"
        :data="table.data.value"
        :loading="table.loading.value"
        :pagination="table.pagination.value"
        :selectable="true"
        @row-click="handleEdit"
        @page-change="handlePageChange"
        @search="handleSearch"
        @sort="handleSort"
        @selection-change="handleSelectionChange"
      >
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
            Создать отчет
          </button>
        </template>

        <template #cell-date="{ value }">
          {{ formatDate(value) }}
        </template>

        <template #cell-is_posted="{ value }">
          <span
            :class="[
              'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
              value ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800',
            ]"
          >
            {{ value ? 'Проведен' : 'Не проведен' }}
          </span>
        </template>

        <template #actions="{ row }">
          <button @click.stop="handleEdit(row as DailyReport)" class="text-blue-600 hover:text-blue-900 mr-4">
            Открыть
          </button>
          <button
            v-if="!row.is_posted"
            @click.stop="handleDelete(row as DailyReport)"
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
import * as documentsApi from '@/api/documents'
import type { DailyReport } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'

const router = useRouter()
const table = useTable()
const tableRef = ref<InstanceType<typeof DataTable>>()
const selectedItems = ref<DailyReport[]>([])

const columns = [
  { key: 'date', label: 'Дата' },
  { key: 'estimate_number', label: 'Смета' },
  { key: 'foreman_name', label: 'Бригадир' },
  { key: 'is_posted', label: 'Статус' },
]

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

async function loadData() {
  table.loading.value = true
  try {
    const response = await documentsApi.getDailyReports(table.queryParams.value)
    table.data.value = response.data
    table.pagination.value = response.pagination
  } catch (error) {
    console.error('Failed to load daily reports:', error)
  } finally {
    table.loading.value = false
  }
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
  router.push('/documents/daily-reports/new')
}

function handleEdit(item: DailyReport) {
  router.push(`/documents/daily-reports/${item.id}`)
}

async function handleDelete(item: DailyReport) {
  if (!confirm(`Удалить отчет от ${formatDate(item.date)}?`)) {
    return
  }

  try {
    await documentsApi.deleteDailyReport(item.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при удалении')
  }
}

function handleSelectionChange(items: DailyReport[]) {
  selectedItems.value = items
}

async function handleBulkDelete() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Удалить выбранные отчеты (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkDeleteDailyReports(ids)
    
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
  
  if (!confirm(`Провести выбранные отчеты (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkPostDailyReports(ids)
    
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
  
  if (!confirm(`Отменить проведение выбранных отчетов (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await documentsApi.bulkUnpostDailyReports(ids)
    
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

onMounted(() => {
  loadData()
})
</script>
