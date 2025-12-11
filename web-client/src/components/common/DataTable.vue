<template>
  <div class="space-y-4">
    <!-- Toolbar: Search, Filters, Actions -->
    <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <!-- Top row: Search and Actions -->
      <div class="flex flex-col sm:flex-row gap-4 justify-between">
        <div class="flex-1 max-w-md">
          <div class="relative">
            <input
              ref="searchInput"
              v-model="searchQuery"
              type="text"
              placeholder="Быстрый поиск..."
              class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              @input="debouncedSearch"
            />
            <svg class="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
        <div class="flex gap-2 flex-wrap">
          <button
            v-if="hasFilters"
            @click="toggleFilters"
            :class="[
              'inline-flex items-center px-3 py-2 border text-sm font-medium rounded-md',
              showFilters ? 'border-blue-500 text-blue-700 bg-blue-50' : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
            ]"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            {{ showFilters ? 'Скрыть отборы' : 'Показать отборы' }}
          </button>
          <button
            @click="handleRefresh"
            class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            title="Обновить (F5)"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <slot name="header-actions"></slot>
        </div>
      </div>

      <!-- Filters panel (collapsible) -->
      <div v-if="hasFilters && showFilters" class="border-t border-gray-200 pt-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <slot name="filters"></slot>
        </div>
        <div class="mt-4 flex gap-2">
          <button
            @click="handleApplyFilters"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Применить
          </button>
          <button
            @click="handleClearFilters"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Очистить
          </button>
        </div>
      </div>
    </div>

    <!-- Bulk actions bar (appears when items selected) -->
    <div v-if="selectedRows.length > 0" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div class="flex items-center gap-4">
          <span class="text-sm font-medium text-blue-900">
            Выбрано: {{ selectedRows.length }}
          </span>
          <button
            @click="clearSelection"
            class="text-sm text-blue-700 hover:text-blue-900 underline"
          >
            Снять выделение
          </button>
        </div>
        <div class="flex gap-2">
          <slot name="bulk-actions" :selected="selectedRows"></slot>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="bg-white border border-gray-200 rounded-lg text-center py-12">
      <div class="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      <p class="mt-3 text-sm text-gray-600">Загрузка данных...</p>
    </div>

    <!-- Data views -->
    <div v-else-if="data && data.length > 0">
      <!-- Desktop table view -->
      <div class="hidden md:block bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th v-if="selectable" class="px-6 py-3 text-left w-12">
                  <input
                    type="checkbox"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
                    title="Выбрать все на странице"
                  />
                </th>
                <th
                  v-for="column in columns"
                  :key="column.key"
                  :style="column.width ? { width: column.width } : {}"
                  :class="[
                    'px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider',
                    column.sortable !== false ? 'cursor-pointer hover:bg-gray-100 select-none' : ''
                  ]"
                  @click="handleSort(column.key)"
                >
                  <div class="flex items-center space-x-1">
                    <span>{{ column.label }}</span>
                    <span v-if="column.sortable !== false" class="inline-flex flex-col">
                      <svg
                        v-if="sortBy === column.key && sortOrder === 'asc'"
                        class="w-4 h-4 text-blue-600"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                      <svg
                        v-else-if="sortBy === column.key && sortOrder === 'desc'"
                        class="w-4 h-4 text-blue-600 transform rotate-180"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                      <svg
                        v-else
                        class="w-4 h-4 text-gray-300"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                    </span>
                  </div>
                </th>
                <th v-if="$slots.actions" class="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="(row, index) in data"
                :key="row.id || index"
                :class="[
                  'transition-colors',
                  index % 2 === 0 ? 'bg-white' : 'bg-gray-50',
                  'hover:bg-blue-50',
                  selectable ? '' : 'cursor-pointer',
                  isRowSelected(row) ? 'bg-blue-100 hover:bg-blue-100' : ''
                ]"
                @click="selectable ? null : $emit('row-click', row)"
                @dblclick="$emit('row-click', row)"
              >
                <td v-if="selectable" class="px-6 py-4 whitespace-nowrap" @click.stop>
                  <input
                    type="checkbox"
                    :checked="isRowSelected(row)"
                    @change="toggleRowSelection(row)"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
                  />
                </td>
                <td
                  v-for="column in columns"
                  :key="column.key"
                  class="px-6 py-4 text-sm text-gray-900"
                  :class="column.key === 'number' || column.key === 'code' ? 'whitespace-nowrap' : ''"
                >
                  <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                    {{ row[column.key] ?? '—' }}
                  </slot>
                </td>
                <td v-if="$slots.actions" class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <slot name="actions" :row="row"></slot>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Mobile card view -->
      <div class="md:hidden space-y-3">
        <div
          v-for="(row, index) in data"
          :key="row.id || index"
          :class="[
            'bg-white border border-gray-200 rounded-lg p-4 cursor-pointer transition-shadow',
            isRowSelected(row) ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
          ]"
          @click="$emit('row-click', row)"
        >
          <div v-if="selectable" class="mb-3 pb-3 border-b border-gray-200">
            <input
              type="checkbox"
              :checked="isRowSelected(row)"
              @change.stop="toggleRowSelection(row)"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
            />
          </div>
          <div class="space-y-2">
            <div v-for="column in columns" :key="column.key">
              <div class="text-xs font-medium text-gray-500 uppercase">{{ column.label }}</div>
              <div class="text-sm text-gray-900 mt-1">
                <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                  {{ row[column.key] ?? '—' }}
                </slot>
              </div>
            </div>
          </div>
          <div v-if="$slots.actions" class="mt-4 pt-4 border-t border-gray-200 flex gap-2">
            <slot name="actions" :row="row"></slot>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && (!data || data.length === 0)" class="bg-white border border-gray-200 rounded-lg text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <p class="mt-4 text-sm text-gray-500">Нет данных для отображения</p>
      <p class="mt-1 text-xs text-gray-400">Попробуйте изменить параметры поиска или создать новую запись</p>
    </div>

    <!-- Pagination -->
    <div v-if="pagination" class="bg-white border border-gray-200 rounded-lg px-4 py-3 sm:px-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <!-- Mobile pagination -->
        <div class="flex flex-1 justify-between sm:hidden">
          <button
            @click="handlePageChange(1)"
            :disabled="pagination.page === 1"
            class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Первая
          </button>
          <button
            @click="handlePageChange(pagination.page - 1)"
            :disabled="pagination.page === 1"
            class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Назад
          </button>
          <span class="inline-flex items-center px-3 py-2 text-sm text-gray-700">
            {{ pagination.page }} / {{ pagination.total_pages }}
          </span>
          <button
            @click="handlePageChange(pagination.page + 1)"
            :disabled="pagination.page === pagination.total_pages"
            class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Вперед
          </button>
          <button
            @click="handlePageChange(pagination.total_pages)"
            :disabled="pagination.page === pagination.total_pages"
            class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Последняя
          </button>
        </div>

        <!-- Desktop pagination -->
        <div class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
          <div class="flex items-center gap-4">
            <p class="text-sm text-gray-700">
              Показано 
              <span class="font-medium">{{ (pagination.page - 1) * pagination.page_size + 1 }}</span>
              —
              <span class="font-medium">{{ Math.min(pagination.page * pagination.page_size, pagination.total_items) }}</span>
              из
              <span class="font-medium">{{ pagination.total_items }}</span>
              {{ pagination.total_items === 1 ? 'записи' : pagination.total_items < 5 ? 'записей' : 'записей' }}
            </p>
            <slot name="page-size-selector"></slot>
          </div>
          <div class="flex items-center gap-2">
            <nav class="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
              <!-- First page -->
              <button
                @click="handlePageChange(1)"
                :disabled="pagination.page === 1"
                class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Первая страница"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                </svg>
              </button>
              
              <!-- Previous page -->
              <button
                @click="handlePageChange(pagination.page - 1)"
                :disabled="pagination.page === 1"
                class="relative inline-flex items-center px-2 py-2 text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Предыдущая страница"
              >
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clip-rule="evenodd" />
                </svg>
              </button>
              
              <!-- Page numbers -->
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="handlePageChange(page)"
                :class="[
                  page === pagination.page
                    ? 'z-10 bg-blue-600 text-white focus:z-20'
                    : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50',
                  'relative inline-flex items-center px-4 py-2 text-sm font-semibold focus:outline-none'
                ]"
              >
                {{ page }}
              </button>
              
              <!-- Next page -->
              <button
                @click="handlePageChange(pagination.page + 1)"
                :disabled="pagination.page === pagination.total_pages"
                class="relative inline-flex items-center px-2 py-2 text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Следующая страница"
              >
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" />
                </svg>
              </button>
              
              <!-- Last page -->
              <button
                @click="handlePageChange(pagination.total_pages)"
                :disabled="pagination.page === pagination.total_pages"
                class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Последняя страница"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

interface PaginationInfo {
      page: number
      page_size: number
      total_items?: number
      total?: number
      pages?: number
      total_pages?: number
    }

export interface Column {
  key: string
  label: string
  sortable?: boolean
  width?: string
}

export interface TableRow extends Record<string, any> {
      id?: number | string
      [key: string]: any
    }

const props = withDefaults(defineProps<{
  columns: Column[]
  data: TableRow[]
  loading?: boolean
  pagination?: PaginationInfo
  selectable?: boolean
  hasFilters?: boolean
}>(), {
  loading: false,
  selectable: false,
  hasFilters: false
})

const emit = defineEmits<{
  'row-click': [row: any]
  'page-change': [page: number]
  'search': [query: string]
  'sort': [sortBy: string, sortOrder: 'asc' | 'desc']
  'selection-change': [rows: any[]]
  'refresh': []
  'apply-filters': []
  'clear-filters': []
}>()

const searchInput = ref<HTMLInputElement>()
const searchQuery = ref('')
const sortBy = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const selectedRows = ref<TableRow[]>([])
const showFilters = ref(false)
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const visiblePages = computed(() => {
  if (!props.pagination) return []
  
  const { page, total_pages } = props.pagination
  const pages: number[] = []
  const maxVisible = 5
  
  let start = Math.max(1, page - Math.floor(maxVisible / 2))
  const end = Math.min(total_pages, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Debounced search (300ms delay)
function debouncedSearch() {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    emit('search', searchQuery.value)
  }, 300)
}

function handleSort(key: string) {
  const column = props.columns.find(c => c.key === key)
  if (column?.sortable === false) return
  
  if (sortBy.value === key) {
    if (sortOrder.value === 'asc') {
      sortOrder.value = 'desc'
    } else if (sortOrder.value === 'desc') {
      // Third click - clear sort
      sortBy.value = ''
      sortOrder.value = 'asc'
    }
  } else {
    sortBy.value = key
    sortOrder.value = 'asc'
  }
  
  if (sortBy.value) {
    emit('sort', sortBy.value, sortOrder.value)
  } else {
    emit('refresh')
  }
}

function handlePageChange(page: number) {
  emit('page-change', page)
}

function handleRefresh() {
  emit('refresh')
}

function toggleFilters() {
  showFilters.value = !showFilters.value
}

function handleApplyFilters() {
  emit('apply-filters')
}

function handleClearFilters() {
  emit('clear-filters')
}

const isAllSelected = computed(() => {
  return props.data && props.data.length > 0 && selectedRows.value.length === props.data.length
})

function isRowSelected(row: any): boolean {
  return selectedRows.value.some(r => r.id === row.id)
}

function toggleRowSelection(row: TableRow) {
  const index = selectedRows.value.findIndex(r => r.id === row.id)
  if (index > -1) {
    selectedRows.value.splice(index, 1)
  } else {
    selectedRows.value.push(row)
  }
  emit('selection-change', selectedRows.value)
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedRows.value = []
  } else {
    selectedRows.value = [...props.data]
  }
  emit('selection-change', selectedRows.value)
}

function clearSelection() {
  selectedRows.value = []
  emit('selection-change', [])
}

// Keyboard shortcuts
function handleKeyDown(event: KeyboardEvent) {
  // F5 - Refresh
  if (event.key === 'F5') {
    event.preventDefault()
    handleRefresh()
  }
  // Ctrl+F - Focus search
  else if (event.ctrlKey && event.key === 'f') {
    event.preventDefault()
    searchInput.value?.focus()
  }
  // Ctrl+A - Select all (when table is focused)
  else if (event.ctrlKey && event.key === 'a' && props.selectable) {
    const activeElement = document.activeElement
    if (activeElement?.tagName !== 'INPUT' && activeElement?.tagName !== 'TEXTAREA') {
      event.preventDefault()
      toggleSelectAll()
    }
  }
  // Escape - Clear selection or close filters
  else if (event.key === 'Escape') {
    if (selectedRows.value.length > 0) {
      clearSelection()
    } else if (showFilters.value) {
      showFilters.value = false
    }
  }
}

// Clear selection when data changes
watch(() => props.data, () => {
  selectedRows.value = []
})

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})

// Expose methods
defineExpose({
  clearSelection,
  focusSearch: () => searchInput.value?.focus()
})
</script>
