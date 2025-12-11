<template>
  <div v-if="isOpen" class="dialog-overlay" @click.self="close">
    <div class="dialog">
      <div class="dialog-header">
        <h2>Select Cost Item</h2>
        <button @click="close" class="close-btn">&times;</button>
      </div>

      <div class="dialog-body">
        <!-- Search Box -->
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by code or description..."
            class="search-input"
            @input="filterItems"
          />
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading cost items...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <p class="error-message">{{ error }}</p>
          <button @click="loadCostItems" class="btn btn-primary">Retry</button>
        </div>

        <!-- Cost Items List -->
        <div v-else class="items-list">
          <div v-if="filteredItems.length === 0" class="empty-state">
            No cost items found matching "{{ searchQuery }}"
          </div>

          <div
            v-for="item in filteredItems"
            :key="item.id"
            :class="['item-row', { 
              'item-folder': item.is_folder, 
              'item-disabled': item.is_folder || isAlreadyAdded(item.id),
              'item-selected': selectedItem?.id === item.id 
            }]"
            @click="selectItem(item)"
          >
            <div class="item-icon">
              {{ item.is_folder ? '📁' : '📄' }}
            </div>
            <div class="item-content">
              <div class="item-header">
                <span class="item-code">{{ item.code || '-' }}</span>
                <span v-if="isAlreadyAdded(item.id)" class="badge badge-info">Already Added</span>
              </div>
              <div class="item-description">{{ item.description }}</div>
              <div class="item-details">
                <span v-if="!item.is_folder">
                  Unit: {{ item.unit_name || '-' }} | 
                  Price: {{ formatPrice(item.price) }} | 
                  Labor: {{ formatNumber(item.labor_coefficient) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="close" class="btn btn-secondary">Cancel</button>
        <button 
          @click="confirm" 
          class="btn btn-primary"
          :disabled="!selectedItem || selectedItem.is_folder || isAlreadyAdded(selectedItem.id)"
        >
          Add Cost Item
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { costItemsApi } from '@/api/costs-materials'
import type { CostItem } from '@/types/models'

interface Props {
  isOpen: boolean
  existingCostItemIds: number[]
}

interface Emits {
  (e: 'close'): void
  (e: 'select', costItem: CostItem): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const costItems = ref<CostItem[]>([])
const filteredItems = ref<CostItem[]>([])
const selectedItem = ref<CostItem | null>(null)
const searchQuery = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

// Watch for dialog open to load data
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && costItems.value.length === 0) {
    loadCostItems()
  }
  if (isOpen) {
    selectedItem.value = null
    searchQuery.value = ''
    filterItems()
  }
})

async function loadCostItems() {
  loading.value = true
  error.value = null
  try {
    costItems.value = await costItemsApi.getAll(false)
    filterItems()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load cost items'
    console.error('Error loading cost items:', err)
  } finally {
    loading.value = false
  }
}

function filterItems() {
  const query = searchQuery.value.toLowerCase().trim()
  
  if (!query) {
    filteredItems.value = costItems.value
    return
  }

  filteredItems.value = costItems.value.filter(item => {
    const codeMatch = item.code?.toLowerCase().includes(query)
    const descMatch = item.description?.toLowerCase().includes(query)
    return codeMatch || descMatch
  })
}

function isAlreadyAdded(costItemId: number): boolean {
  return props.existingCostItemIds.includes(costItemId)
}

function selectItem(item: CostItem) {
  // Don't select folders or already added items
  if (item.is_folder || isAlreadyAdded(item.id)) {
    return
  }
  selectedItem.value = item
}

function confirm() {
  if (selectedItem.value && !selectedItem.value.is_folder && !isAlreadyAdded(selectedItem.value.id)) {
    emit('select', selectedItem.value)
    close()
  }
}

function close() {
  emit('close')
  selectedItem.value = null
  searchQuery.value = ''
}

function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}

function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(2)
}
</script>

<style scoped>
.dialog-overlay {
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

.dialog {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #dee2e6;
}

.dialog-header h2 {
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

.dialog-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.search-box {
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
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

.items-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
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
}

.item-row.item-folder {
  background-color: #f8f9fa;
}

.item-icon {
  font-size: 1.5rem;
  margin-right: 1rem;
  flex-shrink: 0;
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
  margin-bottom: 0.25rem;
}

.item-details {
  font-size: 0.875rem;
  color: #6c757d;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.25rem;
}

.badge-info {
  background-color: #17a2b8;
  color: white;
}

.dialog-footer {
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

.btn-secondary:hover {
  background-color: #545b62;
}
</style>
