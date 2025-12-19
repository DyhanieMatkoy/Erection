<template>
  <AppLayout>
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">Работы</h2>
          <p class="mt-1 text-sm text-gray-600">Управление справочником работ</p>
        </div>
        
        <!-- Переключатель режима просмотра -->
        <div class="flex items-center gap-2 bg-white border border-gray-300 rounded-lg p-1">
          <button
            @click="viewMode = 'flat'"
            :class="[
              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
              viewMode === 'flat'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            ]"
            title="Плоский список"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button
            @click="viewMode = 'hierarchy'"
            :class="[
              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
              viewMode === 'hierarchy'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            ]"
            title="Иерархический список"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </button>
        </div>
      </div>

      <DataTable
        ref="tableRef"
        :columns="columns"
        :data="displayData"
        :loading="view.table.loading.value"
        :pagination="paginationInfo"
        :selectable="true"
        :has-filters="true"
        @row-click="handleEditWork"
        @page-change="handlePageChange"
        @search="view.handleSearch"
        @sort="view.handleSort"
        @selection-change="handleSelectionChange"
        @refresh="loadData"
        @apply-filters="handleApplyFilters"
        @clear-filters="handleClearFilters"
      >
        <template #filters>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Элементов на странице</label>
            <select
              v-model.number="pageSize"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              @change="handlePageSizeChange"
            >
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
              <option :value="500">500</option>
              <option :value="1000">1000</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Категория</label>
            <select
              v-model="filters.filters.value.category"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все категории</option>
              <option value="construction">Строительные работы</option>
              <option value="electrical">Электромонтажные работы</option>
              <option value="plumbing">Сантехнические работы</option>
              <option value="finishing">Отделочные работы</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Единица измерения</label>
            <select
              v-model="filters.filters.value.unit_name"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option :value="null">Все единицы</option>
              <option value="м²">м²</option>
              <option value="м³">м³</option>
              <option value="м">м</option>
              <option value="шт">шт</option>
              <option value="т">т</option>
              <option value="кг">кг</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Стоимость от</label>
            <input
              v-model.number="filters.filters.value.priceFrom"
              type="number"
              step="0.01"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="0.00"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Стоимость до</label>
            <input
              v-model.number="filters.filters.value.priceTo"
              type="number"
              step="0.01"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="0.00"
            />
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
          <div class="flex items-center gap-2">
            <button
              @click="showMoveGroupModal = true"
              class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              Сменить группу
            </button>
            <button
              @click="handleBulkDelete"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
            >
              <svg class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Пометить на удаление ({{ selected.length }})
            </button>
          </div>
        </template>
        <template #header-actions>
          <button
            @click="view.handleCreate"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 mr-2"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Создать
          </button>
          
          <!-- More Actions Menu -->
          <div class="relative inline-block text-left">
            <button
              @click="showMoreMenu = !showMoreMenu"
              class="inline-flex items-center px-2 py-2 border border-gray-300 rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              title="Дополнительные действия"
            >
              <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
              </svg>
            </button>

            <!-- Dropdown menu -->
            <div
              v-if="showMoreMenu"
              class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
              @click.away="showMoreMenu = false"
            >
              <div class="py-1" role="menu" aria-orientation="vertical">
                <button
                  @click="showImportModal = true; showMoreMenu = false"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                  role="menuitem"
                >
                  <svg class="h-4 w-4 mr-2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Импорт CSV
                </button>
                <button
                  v-if="hasDeletedItems"
                  @click="handlePermanentDelete; showMoreMenu = false"
                  class="w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-gray-100 flex items-center"
                  role="menuitem"
                >
                  <svg class="h-4 w-4 mr-2 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Удалить помеченные
                </button>
              </div>
            </div>
          </div>
        </template>

        <template #cell-price="{ value }">
          {{ formatNumber(value) }}
        </template>

        <template #cell-code="{ row, value }">
          <a
            href="#"
            class="text-blue-600 hover:text-blue-800 hover:underline"
            @click.prevent.stop="handleEditWork(row)"
          >
            {{ value && value !== '—' ? value : (row.code || '—') }}
          </a>
        </template>

        <template #cell-name="{ row, value }">
          <div :style="{ paddingLeft: `${row._level * 24}px` }" class="flex items-center">
            <!-- Кнопка раскрытия/скрытия для групп -->
            <button
              v-if="row._hasChildren && viewMode === 'hierarchy'"
              @click.stop="toggleExpand(row.id as number)"
              class="mr-2 p-0.5 hover:bg-gray-100 rounded"
            >
              <svg
                class="w-4 h-4 transition-transform"
                :class="{ 'transform rotate-90': expandedNodes.has(row.id as number) }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <!-- Иконка папки для групп -->
            <svg
              v-if="row._hasChildren"
              class="w-4 h-4 mr-2 text-yellow-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
            </svg>
            <!-- Иконка документа для элементов -->
            <svg
              v-else
              class="w-4 h-4 mr-2 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span
              :class="{ 'font-semibold': row._hasChildren }"
              class="cursor-pointer hover:text-blue-600"
              @click.stop="handleEditWork(row)"
            >
              {{ value }}
            </span>
          </div>
        </template>

        <template #cell-category="{ value }">
          <span v-if="value" class="text-sm text-gray-900">
            {{ getCategoryLabel(value) }}
          </span>
          <span v-else class="text-gray-400">—</span>
        </template>

        <template #cell-standard_price="{ value }">
          {{ formatNumber(value) }}
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

        <!-- Actions removed - use double-click to edit, Del key to delete -->
      </DataTable>

      <!-- Import Modal -->
      <Modal
        :open="showImportModal"
        title="Импорт работ из CSV"
        size="md"
        @close="closeImportModal"
      >
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Выберите CSV файл
            </label>
            <input
              type="file"
              accept=".csv"
              @change="handleFileSelect"
              class="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
            />
            <p class="mt-1 text-xs text-gray-500">
              Формат: Тип работ; Наименование работы; Цена; Единица измерения
            </p>
          </div>

          <Picker
            v-model="importParentId"
            label="Родительская группа (необязательно)"
            :items="view.parentItems.value"
            placeholder="Выберите группу или оставьте пустым"
          />

          <div class="space-y-2">
            <div class="flex items-center">
              <input
                id="delete-mode"
                v-model="importDeleteMode"
                type="checkbox"
                class="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                @change="handleDeleteModeChange"
              />
              <label for="delete-mode" class="ml-2 block text-sm text-gray-900">
                <span class="font-medium text-red-600">Режим удаления:</span> помечать работы на удаление по наименованиям из файла
              </label>
            </div>
            
            <div v-if="!importDeleteMode" class="flex items-center">
              <input
                id="skip-existing"
                v-model="importSkipExisting"
                type="checkbox"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label for="skip-existing" class="ml-2 block text-sm text-gray-900">
                Пропускать существующие работы
              </label>
            </div>
          </div>

          <div v-if="importError" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ importError }}</p>
          </div>

          <div v-if="importResult" class="rounded-md bg-green-50 p-4">
            <p class="text-sm text-green-800 font-medium">{{ importResult.message }}</p>
            <div class="mt-2 text-xs text-green-700">
              <p>Добавлено: {{ importResult.added }}</p>
              <p>Пропущено: {{ importResult.skipped }}</p>
              <div v-if="importResult.errors.length > 0" class="mt-2">
                <p class="font-medium">Ошибки:</p>
                <ul class="list-disc list-inside">
                  <li v-for="(error, idx) in importResult.errors.slice(0, 5)" :key="idx">
                    {{ error }}
                  </li>
                  <li v-if="importResult.errors.length > 5">
                    ... и еще {{ importResult.errors.length - 5 }} ошибок
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <template #footer>
          <button
            @click="closeImportModal"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
          >
            {{ importResult ? 'Закрыть' : 'Отмена' }}
          </button>
          <button
            v-if="!importResult"
            @click="handleImport"
            type="button"
            :disabled="!selectedFile || importing"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
          >
            {{ importing ? 'Импорт...' : 'Импортировать' }}
          </button>
        </template>
      </Modal>

      <!-- Move Group Modal -->
      <Modal
        :open="showMoveGroupModal"
        title="Смена группы"
        size="md"
        @close="closeMoveGroupModal"
      >
        <div class="space-y-4">
          <p class="text-sm text-gray-600">
            Выбрано работ: <span class="font-semibold">{{ selectedItems.length }}</span>
          </p>

          <Picker
            v-model="moveToGroupId"
            label="Новая родительская группа"
            :items="view.parentItems.value"
            placeholder="Выберите группу или оставьте пустым для корня"
          />

          <div v-if="moveError" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ moveError }}</p>
          </div>
        </div>

        <template #footer>
          <button
            @click="closeMoveGroupModal"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
          >
            Отмена
          </button>
          <button
            @click="handleMoveToGroup"
            type="button"
            :disabled="moving"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
          >
            {{ moving ? 'Перемещение...' : 'Переместить' }}
          </button>
        </template>
      </Modal>

      <!-- Create/Edit Modal -->
    <Modal
      :open="view.modalOpen.value"
      :title="view.editingItem.value ? 'Редактирование работы' : 'Создание работы'"
      size="xl"
      @close="view.handleCloseModal"
    >
      <WorkForm
        v-if="view.modalOpen.value"
        :work-id="view.editingItem.value?.id || 0"
        :is-modal="true"
        @saved="handleSaved"
        @cancelled="view.handleCloseModal"
      />
    </Modal>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useReferenceView } from '@/composables/useReferenceView'
import { useFilters } from '@/composables/useFilters'
import { useReferencesStore } from '@/stores/references'
import * as referencesApi from '@/api/references'
import type { Work } from '@/types/models'
import type { ImportWorksResult } from '@/api/references'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'
import Modal from '@/components/common/Modal.vue'
import FormField from '@/components/common/FormField.vue'
import WorkForm from '@/components/work/WorkForm.vue'
import Picker from '@/components/common/Picker.vue'

const router = useRouter()

const referencesStore = useReferencesStore()
const tableRef = ref<InstanceType<typeof DataTable>>()
const selectedItems = ref<Work[]>([])

// Import state
const showImportModal = ref(false)
const selectedFile = ref<File | null>(null)
const importParentId = ref<number | null>(null)
const importSkipExisting = ref(true)
const importDeleteMode = ref(false)
const importing = ref(false)
const importError = ref<string | null>(null)
const importResult = ref<ImportWorksResult | null>(null)

// Move group state
const showMoveGroupModal = ref(false)
const moveToGroupId = ref<number | null>(null)
const moving = ref(false)
const moveError = ref<string | null>(null)
const showMoreMenu = ref(false) // State for the "more" dropdown menu

// View mode: flat or hierarchy
const viewMode = ref<'flat' | 'hierarchy'>('hierarchy')
const expandedNodes = ref<Set<number>>(new Set())
const pageSize = ref(1000) // По умолчанию 1000 элементов

// Filters
const filters = useFilters({
  category: null as string | null,
  unit: null as string | null,
  priceFrom: null as number | null,
  priceTo: null as number | null,
  isDeleted: null as boolean | null,
})

const view = useReferenceView<Work>(
  {
    getAll: referencesApi.getWorks,
    create: referencesApi.createWork,
    update: referencesApi.updateWork,
    delete: referencesApi.deleteWork,
  }
)

const columns = [
  { key: 'code', label: 'Код', width: '100px' },
  { key: 'name', label: 'Наименование', width: '400px' },
  { key: 'unit', label: 'Ед. изм.', width: '100px' },
  { key: 'price', label: 'Цена', width: '120px' },
]

function handleEditWork(work: Work | any) {
  view.handleEdit(work as Work)
}

function handleSelectionChange(items: Work[]) {
  selectedItems.value = items
}

async function handleBulkDelete() {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`Пометить выбранные виды работ на удаление (${selectedItems.value.length})?`)) {
    return
  }

  try {
    const ids = selectedItems.value.map(item => item.id!)
    const result = await referencesApi.bulkDeleteWorks(ids)
    
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

async function handlePermanentDelete() {
  if (!confirm('Вы уверены, что хотите НАВСЕГДА удалить все помеченные элементы? Это действие необратимо!')) {
    return
  }

  try {
    const result = await referencesApi.permanentDeleteMarkedWorks()
    
    if (result.errors.length > 0) {
      alert(`${result.message}\n\nОшибки:\n${result.errors.join('\n')}`)
    } else {
      alert(result.message)
    }
    
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при удалении помеченных элементов')
  }
}

const hasDeletedItems = computed(() => {
  return (view.table.data.value as Work[]).some((item: Work) => item.marked_for_deletion === true)
})

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

function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    construction: 'Строительные работы',
    electrical: 'Электромонтажные работы',
    plumbing: 'Сантехнические работы',
    finishing: 'Отделочные работы'
  }
  return labels[category] || category
}

function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '—'
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
}

// Extended Work type with hierarchy properties
interface WorkWithHierarchy {
  id: number
  code?: string
  name: string
  unit?: string
  price?: number
  parent_id: number | null
  is_deleted: boolean
  marked_for_deletion?: boolean
  created_at: string
  updated_at: string
  _children?: WorkWithHierarchy[]
  _level?: number
  _hasChildren?: boolean
}

// Построение иерархии
function buildHierarchy(items: Work[]): WorkWithHierarchy[] {
  const itemMap = new Map<number, WorkWithHierarchy>()
  const roots: WorkWithHierarchy[] = []
  
  // Создаем карту всех элементов
  items.forEach(item => {
    // Explicitly copy all properties including code and price
    itemMap.set(item.id!, { 
      ...item, 
      code: item.code,
      price: item.price,
      _children: [], 
      _level: 0, 
      _hasChildren: false 
    })
  })
  
  // Строим дерево
  items.forEach(item => {
    const node = itemMap.get(item.id!)!
    if (item.parent_id && itemMap.has(item.parent_id)) {
      const parent = itemMap.get(item.parent_id)!
      parent._children!.push(node)
      parent._hasChildren = true
    } else {
      roots.push(node)
    }
  })
  
  // Устанавливаем уровни вложенности
  function setLevels(nodes: WorkWithHierarchy[], level: number) {
    nodes.forEach(node => {
      node._level = level
      if (node._children && node._children.length > 0) {
        setLevels(node._children, level + 1)
      }
    })
  }
  setLevels(roots, 0)
  
  return roots
}

// Разворачивание иерархии в плоский список
function flattenHierarchy(nodes: WorkWithHierarchy[]): WorkWithHierarchy[] {
  const result: WorkWithHierarchy[] = []
  
  function traverse(nodes: WorkWithHierarchy[]) {
    nodes.forEach(node => {
      result.push(node)
      if (node._hasChildren && node.id && expandedNodes.value.has(node.id) && node._children) {
        traverse(node._children)
      }
    })
  }
  
  traverse(nodes)
  return result
}

// Переключение раскрытия узла
function toggleExpand(nodeId: number) {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
}

// Вычисляемые данные для отображения
const displayData = computed(() => {
  const data = view.table.data.value as Work[]
  
  if (viewMode.value === 'hierarchy') {
    const hierarchy = buildHierarchy(data)
    return flattenHierarchy(hierarchy)
  }
  
  return data.map(item => ({ ...item, _level: 0, _hasChildren: false } as WorkWithHierarchy))
})

// Информация о пагинации (для иерархии отключаем пагинацию)
const paginationInfo = computed(() => {
  if (viewMode.value === 'hierarchy') {
    // В иерархическом режиме показываем все элементы
    return {
      page: 1,
      page_size: displayData.value.length,
      total_items: displayData.value.length,
      total_pages: 1
    }
  }
  return view.table.pagination.value
})

// Загрузка данных с учетом размера страницы
    async function loadData() {
      view.table.loading.value = true
      try {
        // В иерархическом режиме загружаем все данные с пагинацией
        if (viewMode.value === 'hierarchy') {
          const allWorks = []
          let page = 1
          let hasMore = true
          
          while (hasMore) {
            const params = {
              page,
              page_size: 100,
              search: view.table.queryParams.value.search,
              sort_by: view.table.queryParams.value.sort_by,
              sort_order: view.table.queryParams.value.sort_order,
              ...filters.getQueryParams()
            }
            
            const response = await referencesApi.getWorks(params)
            allWorks.push(...response.data)
            hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
            page++
          }
          
          view.table.data.value = allWorks
          view.table.pagination.value = {
            page: 1,
            page_size: allWorks.length,
            total_items: allWorks.length,
            total_pages: 1
          }
        } else {
          // В обычном режиме загружаем с пагинацией
          const params = {
            page: view.table.pagination.value?.page || 1,
            page_size: pageSize.value,
            search: view.table.queryParams.value.search,
            sort_by: view.table.queryParams.value.sort_by,
            sort_order: view.table.queryParams.value.sort_order,
            ...filters.getQueryParams()
          }
          
          const response = await referencesApi.getWorks(params)
          view.table.data.value = response.data
          view.table.pagination.value = response.pagination
        }
        
        // Обновляем кэш
        await referencesStore.fetchWorks(true)
      } catch (error: unknown) {
        console.error('Failed to load works:', error)
        const apiError = error as { response?: { data?: { detail?: string } } }
        alert(apiError.response?.data?.detail || 'Ошибка при загрузке данных')
      } finally {
        view.table.loading.value = false
      }
    }

function handlePageChange(page: number) {
  view.table.setPage(page)
  loadData()
}

function handlePageSizeChange() {
  view.table.setPage(1)
  loadData()
}

// Import functions
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0] || null
    importError.value = null
    importResult.value = null
  }
}

async function handleImport() {
  if (!selectedFile.value) {
    importError.value = 'Выберите файл для импорта'
    return
  }

  importing.value = true
  importError.value = null
  importResult.value = null

  try {
    const result = await referencesApi.importWorksFromCSV(
      selectedFile.value,
      importParentId.value,
      importSkipExisting.value,
      importDeleteMode.value
    )
    
    importResult.value = result
    
    // Reload data
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    importError.value = apiError.response?.data?.detail || 'Ошибка при импорте файла'
  } finally {
    importing.value = false
  }
}

function handleDeleteModeChange() {
  if (importDeleteMode.value) {
    importSkipExisting.value = false
  }
}

function closeImportModal() {
  showImportModal.value = false
  selectedFile.value = null
  importParentId.value = null
  importSkipExisting.value = true
  importDeleteMode.value = false
  importError.value = null
  importResult.value = null
  
  // Reset file input
  const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
  if (fileInput) {
    fileInput.value = ''
  }
}

// Move group functions
async function handleMoveToGroup() {
  if (selectedItems.value.length === 0) {
    moveError.value = 'Не выбраны работы для перемещения'
    return
  }

  moving.value = true
  moveError.value = null

  try {
    const workIds = selectedItems.value.map(item => item.id!)
    await referencesApi.bulkMoveWorks(workIds, moveToGroupId.value)
    
    // Reload data
    await loadData()
    
    // Close modal
    closeMoveGroupModal()
    
    // Clear selection
    tableRef.value?.clearSelection()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    moveError.value = apiError.response?.data?.detail || 'Ошибка при перемещении работ'
  } finally {
    moving.value = false
  }
}

function closeMoveGroupModal() {
  showMoveGroupModal.value = false
  moveToGroupId.value = null
  moveError.value = null
}

function handleSaved() {
  loadData()
  view.handleCloseModal()
}

// Перезагрузка при смене режима
watch(viewMode, () => {
  loadData()
})

onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* Fix cursor behavior */
:deep(tr) {
  cursor: default !important;
}
:deep(a), :deep(.cursor-pointer), :deep(button) {
  cursor: pointer !important;
}
</style>
