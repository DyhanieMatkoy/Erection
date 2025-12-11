<template>
  <div v-if="isOpen" class="list-form-overlay" @click.self="handleBackdropClick">
    <div class="list-form-dialog">
      <!-- Header -->
      <div class="list-form-header">
        <h2>{{ title }}</h2>
        <button @click="close" class="close-btn" aria-label="Close">&times;</button>
      </div>

      <!-- Body -->
      <div class="list-form-body">
        <!-- Search and Filters -->
        <div class="search-section">
          <div class="search-box">
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="searchPlaceholder"
              class="search-input"
              @input="handleSearch"
              @keyup.enter="handleEnterKey"
            />
            <span class="search-icon">🔍</span>
          </div>
          
          <!-- Custom filters slot -->
          <div v-if="$slots.filters" class="filters-section">
            <slot name="filters"></slot>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>{{ loadingMessage }}</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <p class="error-message">{{ error }}</p>
          <button @click="$emit('retry')" class="btn btn-primary btn-sm">Retry</button>
        </div>

        <!-- Items List -->
        <div v-else class="items-container">
          <!-- Empty State -->
          <div v-if="displayedItems.length === 0" class="empty-state">
            <p>{{ emptyMessage }}</p>
          </div>

          <!-- Items -->
          <div v-else class="items-list">
            <slot name="items" :items="displayedItems" :select-item="selectItem" :highlight-text="highlightText">
              <!-- Default item rendering -->
              <div
                v-for="item in displayedItems"
                :key="getItemKey(item)"
                :class="['item-row', { 
                  'item-selected': isSelected(item),
                  'item-disabled': isDisabled(item)
                }]"
                @click="selectItem(item)"
              >
                <slot name="item" :item="item" :highlight-text="highlightText">
                  <div class="item-content">
                    <div class="item-header">
                      <span class="item-code" v-html="highlightText(getItemCode(item))"></span>
                    </div>
                    <div class="item-description" v-html="highlightText(getItemDescription(item))"></div>
                  </div>
                </slot>
              </div>
            </slot>
          </div>

          <!-- Pagination -->
          <div v-if="showPagination && totalPages > 1" class="pagination">
            <button 
              @click="goToPage(currentPage - 1)" 
              :disabled="currentPage === 1"
              class="btn btn-sm btn-secondary"
            >
              &lt; Previous
            </button>
            <span class="page-info">
              Page {{ currentPage }} of {{ totalPages }}
              <span v-if="totalItems > 0" class="total-items">({{ totalItems }} items)</span>
            </span>
            <button 
              @click="goToPage(currentPage + 1)" 
              :disabled="currentPage === totalPages"
              class="btn btn-sm btn-secondary"
            >
              Next &gt;
            </button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="list-form-footer">
        <button @click="close" class="btn btn-secondary">Cancel</button>
        <button 
          @click="confirm" 
          class="btn btn-primary"
          :disabled="!canConfirm"
        >
          {{ confirmButtonText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T">
import { ref, computed, watch, shallowRef } from 'vue'
import { debounce } from '@/utils/debounce'

export interface Props {
  isOpen: boolean
  title?: string
  searchPlaceholder?: string
  loadingMessage?: string
  emptyMessage?: string
  confirmButtonText?: string
  items: T[]
  loading?: boolean
  error?: string | null
  selectedItem?: T | null
  disabledItems?: T[]
  showPagination?: boolean
  itemsPerPage?: number
  getItemKey?: (item: T) => string | number
  getItemCode?: (item: T) => string
  getItemDescription?: (item: T) => string
  isItemDisabled?: (item: T) => boolean
  highlightMatches?: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'select', item: T): void
  (e: 'retry'): void
  (e: 'search', query: string): void
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Select Item',
  searchPlaceholder: 'Search...',
  loadingMessage: 'Loading...',
  emptyMessage: 'No items found',
  confirmButtonText: 'Select',
  loading: false,
  error: null,
  selectedItem: null,
  disabledItems: () => [],
  showPagination: false,
  itemsPerPage: 20,
  getItemKey: (item: any) => item.id,
  getItemCode: (item: unknown) => item.code || '-',
  getItemDescription: (item: unknown) => item.description || item.name || '',
  isItemDisabled: () => false,
  highlightMatches: true
})

const emit = defineEmits<Emits>()

// Local state
const searchQuery = ref('')
const debouncedSearchQuery = ref('')
const internalSelectedItem = ref<T | null>(null)
const currentPage = ref(1)

// Debounced search handler (300ms delay)
const debouncedSearch = debounce((query: string) => {
  debouncedSearchQuery.value = query
  currentPage.value = 1
  emit('search', query)
}, 300)

// Computed with memoization
const filteredItems = computed(() => {
  // Ensure items is always an array
  const items = Array.isArray(props.items) ? props.items : []
  const query = debouncedSearchQuery.value.toLowerCase().trim()
  
  if (!query) {
    return items
  }

  // Use filter with early return for better performance
  return items.filter(item => {
    const code = props.getItemCode(item).toLowerCase()
    if (code.includes(query)) return true
    
    const description = props.getItemDescription(item).toLowerCase()
    return description.includes(query)
  })
})

const totalItems = computed(() => filteredItems.value.length)

const totalPages = computed(() => {
  if (!props.showPagination) return 1
  return Math.ceil(totalItems.value / props.itemsPerPage)
})

const displayedItems = computed(() => {
  if (!props.showPagination) {
    return filteredItems.value
  }

  const start = (currentPage.value - 1) * props.itemsPerPage
  const end = start + props.itemsPerPage
  return filteredItems.value.slice(start, end)
})

const canConfirm = computed(() => {
  const selected = internalSelectedItem.value
  return selected !== null && !isDisabled(selected)
})

// Watch for dialog open/close
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    resetState()
  }
})

// Watch for external selected item changes
watch(() => props.selectedItem, (newValue) => {
  internalSelectedItem.value = newValue
})

// Methods
function resetState() {
  searchQuery.value = ''
  internalSelectedItem.value = props.selectedItem || null
  currentPage.value = 1
}

function handleSearch() {
  // Use debounced search for better performance
  debouncedSearch(searchQuery.value)
}

function handleEnterKey() {
  // Select first item if available and not disabled
  if (displayedItems.value.length > 0) {
    const firstItem = displayedItems.value[0]
    if (!isDisabled(firstItem)) {
      selectItem(firstItem)
      confirm()
    }
  }
}

function selectItem(item: T) {
  if (isDisabled(item)) {
    return
  }
  internalSelectedItem.value = item
}

function isSelected(item: T): boolean {
  if (!internalSelectedItem.value) return false
  return props.getItemKey(item) === props.getItemKey(internalSelectedItem.value)
}

function isDisabled(item: T): boolean {
  return props.isItemDisabled(item)
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

function confirm() {
  if (canConfirm.value && internalSelectedItem.value) {
    emit('select', internalSelectedItem.value)
    close()
  }
}

function close() {
  emit('close')
}

function handleBackdropClick() {
  close()
}

// Highlight matching text in a string
function highlightText(text: string): string {
  if (!props.highlightMatches || !searchQuery.value.trim()) {
    return text
  }
  
  const query = searchQuery.value.trim()
  const regex = new RegExp(`(${escapeRegex(query)})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

// Escape special regex characters
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Expose highlight function for use in slots
defineExpose({
  highlightText,
  searchQuery: computed(() => searchQuery.value)
})
</script>

<style scoped>
.list-form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.list-form-dialog {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.list-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #dee2e6;
}

.list-form-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 2rem;
  height: 2rem;
}

.close-btn:hover {
  color: #000;
}

.list-form-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.search-section {
  margin-bottom: 1rem;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.search-icon {
  position: absolute;
  right: 0.75rem;
  pointer-events: none;
}

.filters-section {
  margin-top: 0.75rem;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

.items-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.items-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  min-height: 300px;
  max-height: 400px;
}

.item-row {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
  transition: background-color 0.2s;
}

.item-row:last-child {
  border-bottom: none;
}

.item-row:hover:not(.item-disabled) {
  background-color: #f8f9fa;
}

.item-row.item-selected {
  background-color: #e7f3ff;
  border-left: 3px solid #007bff;
}

.item-row.item-disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #f8f9fa;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.item-code {
  font-weight: 600;
  color: #495057;
}

.item-description {
  color: #212529;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #dee2e6;
}

.page-info {
  font-size: 0.875rem;
  color: #6c757d;
}

.total-items {
  margin-left: 0.5rem;
}

.list-form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1.5rem;
  border-top: 1px solid #dee2e6;
}

.btn {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

/* Highlighted text styling */
:deep(mark) {
  background-color: #fff3cd;
  color: #856404;
  padding: 0.1rem 0.2rem;
  border-radius: 0.2rem;
  font-weight: 600;
}
</style>
