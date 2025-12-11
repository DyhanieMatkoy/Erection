<template>
  <ListForm
    :is-open="isOpen"
    :title="title"
    search-placeholder="Search by code or description..."
    loading-message="Loading cost items..."
    empty-message="No cost items found"
    confirm-button-text="Select Cost Item"
    :items="filteredCostItems"
    :loading="loading"
    :error="error"
    :selected-item="selectedItem"
    :show-pagination="true"
    :items-per-page="20"
    :get-item-key="(item) => item.id"
    :get-item-code="(item) => item.code || '-'"
    :get-item-description="(item) => item.description"
    :is-item-disabled="isItemDisabled"
    @close="handleClose"
    @select="handleSelect"
    @retry="loadCostItems"
  >
    <template #filters>
      <div class="filter-buttons">
        <button 
          :class="['filter-btn', { active: !showFoldersOnly }]"
          @click="showFoldersOnly = false"
        >
          All Items
        </button>
        <button 
          :class="['filter-btn', { active: showFoldersOnly }]"
          @click="showFoldersOnly = true"
        >
          Folders Only
        </button>
      </div>
    </template>

    <template #item="{ item, highlightText }">
      <div class="cost-item-content">
        <div class="item-icon">
          {{ item.is_folder ? '📁' : '📄' }}
        </div>
        <div class="item-details">
          <div class="item-header">
            <span class="item-code" v-html="highlightText(item.code || '-')"></span>
            <span v-if="isAlreadyAdded(item.id)" class="badge badge-info">Already Added</span>
            <span v-if="item.is_folder" class="badge badge-secondary">Folder</span>
          </div>
          <div class="item-description" v-html="highlightText(item.description)"></div>
          <div v-if="!item.is_folder" class="item-metadata">
            <span>Unit: {{ item.unit_name || '-' }}</span>
            <span>Price: {{ formatPrice(item.price) }}</span>
            <span>Labor: {{ formatNumber(item.labor_coefficient) }}</span>
          </div>
        </div>
      </div>
    </template>
  </ListForm>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import ListForm from './ListForm.vue'
import { costItemsApi } from '@/api/costs-materials'
import type { CostItem } from '@/types/models'

interface Props {
  isOpen: boolean
  title?: string
  existingCostItemIds?: number[]
  allowFolders?: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'select', costItem: CostItem): void
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Select Cost Item',
  existingCostItemIds: () => [],
  allowFolders: false
})

const emit = defineEmits<Emits>()

// State
const costItems = ref<CostItem[]>([])
const selectedItem = ref<CostItem | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const showFoldersOnly = ref(false)

// Computed
const filteredCostItems = computed(() => {
  if (showFoldersOnly.value) {
    return costItems.value.filter(item => item.is_folder)
  }
  return costItems.value
})

// Watch for dialog open
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && costItems.value.length === 0) {
    loadCostItems()
  }
  if (isOpen) {
    selectedItem.value = null
    showFoldersOnly.value = false
  }
})

// Methods
async function loadCostItems() {
  loading.value = true
  error.value = null
  try {
    costItems.value = await costItemsApi.getAll(false)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load cost items'
    console.error('Error loading cost items:', err)
  } finally {
    loading.value = false
  }
}

function isAlreadyAdded(costItemId: number): boolean {
  return props.existingCostItemIds.includes(costItemId)
}

function isItemDisabled(item: CostItem): boolean {
  // Disable if already added
  if (isAlreadyAdded(item.id)) {
    return true
  }
  // Disable folders if not allowed
  if (item.is_folder && !props.allowFolders) {
    return true
  }
  return false
}

function handleSelect(item: CostItem) {
  emit('select', item)
}

function handleClose() {
  emit('close')
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
.filter-buttons {
  display: flex;
  gap: 0.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ced4da;
  background-color: white;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.filter-btn:hover {
  background-color: #f8f9fa;
}

.filter-btn.active {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.cost-item-content {
  display: flex;
  gap: 1rem;
  width: 100%;
}

.item-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.item-details {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  flex-wrap: wrap;
}

.item-code {
  font-weight: 600;
  color: #495057;
}

.item-description {
  color: #212529;
  margin-bottom: 0.25rem;
}

.item-metadata {
  display: flex;
  gap: 1rem;
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

.badge-secondary {
  background-color: #6c757d;
  color: white;
}
</style>
