<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Физические лица</h2>
        <p class="mt-1 text-sm text-gray-600">Управление справочником физических лиц</p>
      </div>

      <DataTable
        ref="tableRef"
        :columns="columns"
        :data="view.table.data.value"
        :loading="view.table.loading.value"
        :pagination="view.table.pagination.value"
        :selectable="true"
        :has-filters="true"
        @row-click="view.handleEdit"
        @page-change="view.handlePageChange"
        @search="view.handleSearch"
        @sort="view.handleSort"
        @selection-change="handleSelectionChange"
        @refresh="view.loadData"
        @apply-filters="handleApplyFilters"
        @clear-filters="handleClearFilters"
      >
        <template #filters>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Должность</label>
            <select
              v-model="filters.filters.value.position"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все должности</option>
              <option value="foreman">Бригадир</option>
              <option value="worker">Рабочий</option>
              <option value="engineer">Инженер</option>
              <option value="manager">Менеджер</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Специальность</label>
            <select
              v-model="filters.filters.value.specialty"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все специальности</option>
              <option value="electrician">Электрик</option>
              <option value="plumber">Сантехник</option>
              <option value="carpenter">Плотник</option>
              <option value="mason">Каменщик</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
            <select
              v-model="filters.filters.value.status"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все</option>
              <option value="active">Работает</option>
              <option value="dismissed">Уволен</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Удаленные</label>
            <select
              v-model="filters.filters.value.isDeleted"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все</option>
              <option :value="false">Активные</option>
              <option :value="true">Удаленные</option>
            </select>
          </div>
        </template>
        
        <template #bulk-actions="{ selected }">
          <button
            @click="handleBulkDelete"
            class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
          >
            Удалить ({{ selected.length }})
          </button>
        </template>
        <template #header-actions>
          <button
            @click="view.handleCreate"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Создать
          </button>
        </template>

        <template #cell-position="{ value }">
          <span v-if="value" class="text-sm text-gray-900">
            {{ getPositionLabel(value) }}
          </span>
          <span v-else class="text-gray-400">—</span>
        </template>

        <template #cell-specialty="{ value }">
          <span v-if="value" class="text-sm text-gray-900">
            {{ getSpecialtyLabel(value) }}
          </span>
          <span v-else class="text-gray-400">—</span>
        </template>

        <template #cell-hire_date="{ value }">
          {{ formatDate(value) }}
        </template>

        <template #cell-status="{ value }">
          <span v-if="value" class="text-sm text-gray-900">
            {{ getStatusLabel(value) }}
          </span>
          <span v-else class="text-gray-400">—</span>
        </template>

        <template #cell-is_deleted="{ value }">
          <div class="flex items-center justify-center">
            <span
              :class="[
                'inline-flex items-center justify-center w-6 h-6 rounded-full',
                value ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
              ]"
              :title="value ? 'Удален' : 'Активен'"
            >
              <svg v-if="value" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
              <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </span>
          </div>
        </template>

        <template #actions="{ row }">
          <button @click.stop="view.handleEdit(row as Person)" class="text-blue-600 hover:text-blue-900 mr-4">
            Изменить
          </button>
          <button @click.stop="view.handleDelete(row as Person)" class="text-red-600 hover:text-red-900">
            Удалить
          </button>
        </template>
      </DataTable>

      <Modal
        :open="view.modalOpen.value"
        :title="view.editingItem.value ? 'Редактирование физического лица' : 'Создание физического лица'"
        size="md"
        @close="view.handleCloseModal"
      >
        <form @submit.prevent="view.handleSubmit" class="space-y-4">
          <FormField
            v-model="view.formData.value.full_name"
            label="ФИО"
            type="text"
            required
            :error="view.errors.value.full_name"
          />

          <div v-if="view.submitError.value" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ view.submitError.value }}</p>
          </div>
        </form>

        <template #footer>
          <button
            @click="view.handleCloseModal"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
          >
            Отмена
          </button>
          <button
            @click="view.handleSubmit"
            type="button"
            :disabled="view.submitting.value"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
          >
            {{ view.submitting.value ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </template>
      </Modal>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useReferenceView } from '@/composables/useReferenceView'
import { useFilters } from '@/composables/useFilters'
import { useReferencesStore } from '@/stores/references'
import * as referencesApi from '@/api/references'
import type { Person } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'
import Modal from '@/components/common/Modal.vue'
import FormField from '@/components/common/FormField.vue'

const referencesStore = useReferencesStore()

const view = useReferenceView<Person>(
  {
    getAll: referencesApi.getPersons as any,
    create: referencesApi.createPerson,
    update: referencesApi.updatePerson,
    delete: referencesApi.deletePerson,
  },
  () => referencesStore.fetchPersons(true)
)

const tableRef = ref<InstanceType<typeof DataTable>>()
const selectedItems = ref<Person[]>([])

// Filters
const filters = useFilters({
  position: null as string | null,
  specialty: null as string | null,
  status: null as string | null,
  isDeleted: null as boolean | null,
})

const columns = [
  { key: 'personnel_number', label: 'Табельный №', width: '100px' },
  { key: 'full_name', label: 'ФИО', width: '250px' },
  { key: 'position', label: 'Должность', width: '150px' },
  { key: 'specialty', label: 'Специальность', width: '150px' },
  { key: 'phone', label: 'Телефон', width: '150px' },
  { key: 'hire_date', label: 'Дата приема', width: '100px' },
  { key: 'status', label: 'Статус', width: '100px' },
  { key: 'is_deleted', label: '', width: '40px', sortable: false },
]

function handleSelectionChange(items: Person[]) {
  selectedItems.value = items
}

async function handleBulkDelete() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Удалить выбранных работников (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await referencesApi.bulkDeletePersons(ids)
    
    if (result.errors.length > 0) {
      alert(`${result.message}\n\nОшибки:\n${result.errors.join('\n')}`)
    } else {
      alert(result.message)
    }
    
    tableRef.value?.clearSelection()
    await view.loadData()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Ошибка при групповом удалении')
  }
}

function handleApplyFilters() {
  filters.applyFilters()
  view.table.setPage(1)
  view.loadData()
}

function handleClearFilters() {
  filters.clearAllFilters()
  view.table.setPage(1)
  view.loadData()
}

function getPositionLabel(position: string): string {
  const labels: Record<string, string> = {
    foreman: 'Бригадир',
    worker: 'Рабочий',
    engineer: 'Инженер',
    manager: 'Менеджер'
  }
  return labels[position] || position
}

function getSpecialtyLabel(specialty: string): string {
  const labels: Record<string, string> = {
    electrician: 'Электрик',
    plumber: 'Сантехник',
    carpenter: 'Плотник',
    mason: 'Каменщик'
  }
  return labels[specialty] || specialty
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: 'Работает',
    dismissed: 'Уволен'
  }
  return labels[status] || status
}

function formatDate(dateString: string): string {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleDateString('ru-RU')
}

onMounted(() => {
  view.loadData()
})
</script>
