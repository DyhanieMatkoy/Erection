<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Журнал аудита</h2>
        <p class="mt-1 text-sm text-gray-600">История действий пользователей</p>
      </div>

      <DataTable
        ref="tableRef"
        :columns="columns"
        :data="table.data.value"
        :loading="table.loading.value"
        :pagination="table.pagination.value"
        :has-filters="true"
        @page-change="handlePageChange"
        @refresh="loadData"
        @apply-filters="handleApplyFilters"
        @clear-filters="handleClearFilters"
      >
        <template #filters>
            <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Тип ресурса</label>
            <select
              v-model="filters.filters.value.resourceType"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все</option>
              <option value="estimate">Смета</option>
              <option value="daily_report">Ежедневный отчет</option>
              <option value="timesheet">Табель</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">ID ресурса</label>
            <input
              v-model.number="filters.filters.value.resourceId"
              type="number"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="ID"
            />
          </div>
        </template>

        <template #cell-created_at="{ value }">
          {{ formatDateTime(value) }}
        </template>

        <template #cell-action="{ value }">
          <span :class="getActionClass(value)">
            {{ getActionLabel(value) }}
          </span>
        </template>
      </DataTable>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useTable } from '@/composables/useTable'
import { useFilters } from '@/composables/useFilters'
import { getAuditLogs, type AuditLog } from '@/api/audit'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'

const table = useTable<AuditLog>()
const tableRef = ref<InstanceType<typeof DataTable>>()

const filters = useFilters({
  resourceType: null as string | null,
  resourceId: null as number | null,
})

const columns = [
  { key: 'created_at', label: 'Дата/Время', width: '180px' },
  { key: 'username', label: 'Пользователь', width: '150px' },
  { key: 'action', label: 'Действие', width: '120px' },
  { key: 'resource_type', label: 'Ресурс', width: '120px' },
  { key: 'resource_id', label: 'ID', width: '80px' },
  { key: 'details', label: 'Детали' },
]

function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('ru-RU')
}

function getActionLabel(action: string): string {
  const map: Record<string, string> = {
    create: 'Создание',
    update: 'Обновление',
    delete: 'Удаление',
    post: 'Проведение',
    unpost: 'Отмена проведения',
    modify_hierarchy: 'Изменение иерархии'
  }
  return map[action] || action
}

function getActionClass(action: string): string {
  const base = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium '
  switch (action) {
    case 'create': return base + 'bg-green-100 text-green-800'
    case 'update': return base + 'bg-blue-100 text-blue-800'
    case 'delete': return base + 'bg-red-100 text-red-800'
    case 'post': return base + 'bg-indigo-100 text-indigo-800'
    case 'modify_hierarchy': return base + 'bg-purple-100 text-purple-800'
    default: return base + 'bg-gray-100 text-gray-800'
  }
}

async function loadData() {
  table.loading.value = true
  try {
    const params = {
      ...table.queryParams.value,
      resource_type: filters.filters.value.resourceType,
      resource_id: filters.filters.value.resourceId
    }
    const response = await getAuditLogs(params)
    table.data.value = response.data
    table.pagination.value = response.pagination
  } catch (error) {
    console.error('Failed to load audit logs:', error)
  } finally {
    table.loading.value = false
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

onMounted(() => {
  loadData()
})
</script>
