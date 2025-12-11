<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Контрагенты</h2>
        <p class="mt-1 text-sm text-gray-600">Управление справочником контрагентов</p>
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
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Тип</label>
            <select
              v-model="filters.filters.value.type"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все типы</option>
              <option value="customer">Заказчик</option>
              <option value="contractor">Подрядчик</option>
              <option value="supplier">Поставщик</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
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
          <div v-if="selected.length > 0" class="flex gap-2">
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
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Создать
          </button>
        </template>

        <template #cell-parent_id="{ row }">
          <span v-if="row.parent_id" class="text-gray-500">
            {{ getParentName(row.parent_id) }}
          </span>
          <span v-else class="text-gray-400">—</span>
        </template>

        <template #cell-type="{ value }">
          <span v-if="value" class="text-sm text-gray-900">
            {{ getTypeLabel(value) }}
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
          <button
            @click.stop="handleEdit(row)"
            class="text-blue-600 hover:text-blue-900 mr-4"
          >
            Изменить
          </button>
          <button
            @click.stop="handleDelete(row)"
            class="text-red-600 hover:text-red-900"
          >
            Удалить
          </button>
        </template>
      </DataTable>

      <!-- Edit/Create Modal -->
      <Modal
        :open="modalOpen"
        :title="editingItem ? 'Редактирование контрагента' : 'Создание контрагента'"
        size="md"
        @close="handleCloseModal"
      >
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <FormField
            v-model="formData.name"
            label="Наименование"
            type="text"
            required
            :error="errors.name"
          />

          <Picker
            v-model="formData.parent_id"
            label="Родительский элемент"
            :items="parentItems"
            :error="errors.parent_id"
          />

          <div v-if="submitError" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ submitError }}</p>
          </div>
        </form>

        <template #footer>
          <button
            @click="handleCloseModal"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
          >
            Отмена
          </button>
          <button
            @click="handleSubmit"
            type="button"
            :disabled="submitting"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
          >
            {{ submitting ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </template>
      </Modal>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTable } from '@/composables/useTable'
import { useFilters } from '@/composables/useFilters'
import { useReferencesStore } from '@/stores/references'
import * as referencesApi from '@/api/references'
import type { Counterparty } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'
import Modal from '@/components/common/Modal.vue'
import FormField from '@/components/common/FormField.vue'
import Picker from '@/components/common/Picker.vue'

const referencesStore = useReferencesStore()
const table = useTable()
const tableRef = ref<InstanceType<typeof DataTable>>()
const selectedItems = ref<Counterparty[]>([])

// Filters
const filters = useFilters({
  type: null as string | null,
  isDeleted: null as boolean | null,
})

const columns = [
  { key: 'code', label: 'Код', width: '100px' },
  { key: 'name', label: 'Наименование', width: '300px' },
  { key: 'inn', label: 'ИНН', width: '120px' },
  { key: 'phone', label: 'Телефон', width: '150px' },
  { key: 'email', label: 'Email', width: '200px' },
  { key: 'type', label: 'Тип', width: '100px' },
  { key: 'is_deleted', label: 'Статус', width: '40px', sortable: false },
]

const modalOpen = ref(false)
const editingItem = ref<Counterparty | null>(null)
const formData = ref({
  name: '',
  parent_id: null as number | null,
})
const errors = ref<Record<string, string>>({})
const submitError = ref('')
const submitting = ref(false)

const parentItems = computed(() => {
  return table.data.value
    .filter((item) => !item.is_deleted && item.id !== editingItem.value?.id)
    .map((item) => ({
      id: item.id,
      name: item.name,
    }))
})

function getParentName(parentId: number): string {
  const parent = table.data.value.find((item) => item.id === parentId)
  return parent?.name || ''
}

async function loadData() {
  table.loading.value = true
  try {
    const params = {
      ...table.queryParams.value,
      ...filters.getQueryParams()
    }
    const response = await referencesApi.getCounterparties(params)
    table.data.value = response.data
    table.pagination.value = response.pagination
    
    // Update cache
    await referencesStore.fetchCounterparties(true)
  } catch (error: unknown) {
    console.error('Failed to load counterparties:', error)
    alert(error.response?.data?.detail || 'Ошибка при загрузке')
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

function handleSearch(query: string) {
  table.setSearch(query)
  loadData()
}

function handleSort(sortBy: string, sortOrder: 'asc' | 'desc') {
  table.setSort(sortBy, sortOrder)
  loadData()
}

function handleCreate() {
  editingItem.value = null
  formData.value = {
    name: '',
    parent_id: null,
  }
  errors.value = {}
  submitError.value = ''
  modalOpen.value = true
}

function handleEdit(item: Counterparty) {
  editingItem.value = item
  formData.value = {
    name: item.name,
    parent_id: item.parent_id,
  }
  errors.value = {}
  submitError.value = ''
  modalOpen.value = true
}

async function handleSubmit() {
  // Validate
  errors.value = {}
  if (!formData.value.name.trim()) {
    errors.value.name = 'Обязательное поле'
    return
  }

  submitting.value = true
  submitError.value = ''

  try {
    if (editingItem.value) {
      await referencesApi.updateCounterparty(editingItem.value.id!, formData.value)
    } else {
      await referencesApi.createCounterparty(formData.value)
    }
    
    modalOpen.value = false
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    submitError.value = apiError.response?.data?.detail || 'Ошибка при сохранении'
  } finally {
    submitting.value = false
  }
}

async function handleDelete(item: Counterparty) {
  if (!confirm(`Удалить контрагента "${item.name}"?`)) {
    return
  }

  try {
    await referencesApi.deleteCounterparty(item.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при удалении')
  }
}

function handleSelectionChange(items: Counterparty[]) {
  selectedItems.value = items
}

async function handleBulkDelete() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Удалить выбранные контрагенты (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await referencesApi.bulkDeleteCounterparties(ids)
    
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

function handleCloseModal() {
  modalOpen.value = false
  editingItem.value = null
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    customer: 'Заказчик',
    contractor: 'Подрядчик',
    supplier: 'Поставщик'
  }
  return labels[type] || type
}

onMounted(() => {
  loadData()
})
</script>
