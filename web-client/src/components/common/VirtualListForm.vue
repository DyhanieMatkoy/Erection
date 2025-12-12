<!--
  Virtual List Form Component with Virtual Scrolling
  Optimized for large datasets (1000+ items)
  Uses virtual scrolling to render only visible items
-->
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
          <LoadingSkeleton type="list" :rows="5" />
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <p class="error-message">{{ error }}</p>
          <button @click="$emit('retry')" class="btn btn-primary btn-sm">Retry</button>
        </div>

        <!-- Virtual Scrolling Container -->
        <div v-else class="items-container">
          <!-- Empty State -->
          <div v-if="displayedItems.length === 0" class="empty-state">
            <p>{{ emptyMessage }}</p>
          </div>

          <!-- Virtual Scroll List -->
          <div
            v-else
            ref="scrollContainer"
            class="virtual-scroll-container"
            :style="{ height: containerHeight + 'px' }"
          >
            <div class="virtual-scroll-spacer" :style="{ height: totalHeight + 'px' }">
              <div
                class="virtual-scroll-content"
                :style="{ transform: `translateY(${offsetY}px)` }"
              >
                <div
                  v-for="{ item, index } in visibleItems"
                  :key="getItemKey(item)"
                  :class="['item-row', { 
                    'item-selected': isSelected(item),
                    'item-disabled': isDisabled(item)
                  }]"
                  :style="{ height: itemHeight + 'px' }"
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
              </div>
            </div>
          </div>

          <!-- Result Count -->
          <div v-if="displayedItems.length > 0" class="result-info">
            Showing {{ visibleItems.length }} of {{ displayedItems.length }} items
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
import { ref, computed, watch } from 'vue'
import { debounce } from '@/utils/debounce'
import { useVirtualScroll } from '@/composables/useVirtualScroll'
import LoadingSkeleton from './LoadingSkeleton.vue'

export interface Props<T> {
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
  itemHeight?: number
  containerHeight?: number
  getItemKey?: (item: T) => string | number
  getItemCode?: (item: T) => string
  getItemDescription?: (item: T) => string
  isItemDisabled?: (item: T) => boolean
  highlightMatches?: boolean
}

interface Emits<T> {
  (e: 'close'): void
  (e: 'select', item: T): void
  (e: 'retry'): void
  (e: 'search', query: string): void
}

const props = withDefaults(defineProps<Props<T>>(), {
  title: 'Select Item',
  searchPlaceholder: 'Search...',
  loadingMessage: 'Loading...',
  emptyMessage: 'No items found',
  confirmButtonText: 'Select',
  loading: false,
  error: null,
  selectedItem: null,
  disabledItems: () => [],
  itemHeight: 60,
  containerHeight: 400,
  getItemKey: (item: any) => item.id,
  getItemCode: (item: any) => item.code || '-',
  getItemDescription: (item: any) => item.description || item.name || '',
  isItemDisabled: () => false,
  highlightMatches: true
})

const emit = defineEmits<Emits<T>>()

// Local state
const searchQuery = ref('')
const debouncedSearchQuery = ref('')
const internalSelectedItem = ref<T | null>(null)
const scrollContainer = ref<HTMLElement | null>(null)

// Debounced search handler
const debouncedSearch = debounce((query: string) => {
  debouncedSearchQuery.value = query
  emit('search', query)
}, 300)

// Computed
const filteredItems = computed(() => {
  const query = debouncedSearchQuery.value.toLowerCase().trim()
  
  if (!query) {
    return props.items
  }

  return props.items.filter(item => {
    const code = props.getItemCode(item).toLowerCase()
    if (code.includes(query)) return true
    
    const description = props.getItemDescription(item).toLowerCase()
    return description.includes(query)
  })
})

const displayedItems = computed(() => filteredItems.value)

// Virtual scrolling
const {
  visibleItems,
  totalHeight,
  offsetY
} = useVirtualScroll(displayedItems.value, {
  itemHeight: props.itemHeight,
  bufferSize: 5,
  containerHeight: props.containerHeight
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
  debouncedSearchQuery.value = ''
  internalSelectedItem.value = props.selectedItem || null
}

function handleSearch() {
  debouncedSearch(searchQuery.value)
}

function handleEnterKey() {
  if (displayedItems.value.length > 0) {
    const firstItem = displayedItems.value[0]
    if (firstItem && !isDisabled(firstItem)) {
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

function highlightText(text: string): string {
  if (!props.highlightMatches || !debouncedSearchQuery.value.trim()) {
    return text
  }
  
  const query = debouncedSearchQuery.value.trim()
  const regex = new RegExp(`(${escapeRegex(query)})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
</script>

<style scoped>
/* Reuse styles from ListForm.vue */
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
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.search-section {
  margin-bottom: 1rem;
  flex-shrink: 0;
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

/* Virtual Scrolling Styles */
.virtual-scroll-container {
  overflow-y: auto;
  overflow-x: hidden;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  position: relative;
}

.virtual-scroll-spacer {
  position: relative;
  width: 100%;
}

.virtual-scroll-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  will-change: transform;
}

.item-row {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
  transition: background-color 0.2s;
  box-sizing: border-box;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-info {
  padding: 0.75rem;
  text-align: center;
  font-size: 0.875rem;
  color: #6c757d;
  border-top: 1px solid #dee2e6;
  flex-shrink: 0;
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

:deep(mark) {
  background-color: #fff3cd;
  color: #856404;
  padding: 0.1rem 0.2rem;
  border-radius: 0.2rem;
  font-weight: 600;
}
</style>
