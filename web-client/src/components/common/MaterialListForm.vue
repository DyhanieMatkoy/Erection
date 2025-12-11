<template>
  <ListForm
    :is-open="isOpen"
    :title="title"
    search-placeholder="Search by code or description..."
    loading-message="Loading materials..."
    empty-message="No materials found"
    confirm-button-text="Select Material"
    :items="filteredMaterials"
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
    @retry="loadMaterials"
  >
    <template #filters>
      <div class="filter-section">
        <label class="filter-label">Filter by Unit:</label>
        <select v-model="selectedUnitId" class="filter-select">
          <option :value="null">All Units</option>
          <option v-for="unit in units" :key="unit.id" :value="unit.id">
            {{ unit.name }}
          </option>
        </select>
      </div>
    </template>

    <template #item="{ item, highlightText }">
      <div class="material-content">
        <div class="item-details">
          <div class="item-header">
            <span class="item-code" v-html="highlightText(item.code || '-')"></span>
            <span v-if="isAlreadyAdded(item.id)" class="badge badge-info">Already Added</span>
          </div>
          <div class="item-description" v-html="highlightText(item.description)"></div>
          <div class="item-metadata">
            <span>Unit: {{ item.unit_name || '-' }}</span>
            <span>Price: {{ formatPrice(item.price) }}</span>
          </div>
        </div>
      </div>
    </template>
  </ListForm>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import ListForm from './ListForm.vue'
import { materialsApi, unitsApi } from '@/api/costs-materials'
import type { Material, Unit } from '@/types/models'

interface Props {
  isOpen: boolean
  title?: string
  existingMaterialIds?: number[]
}

interface Emits {
  (e: 'close'): void
  (e: 'select', material: Material): void
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Select Material',
  existingMaterialIds: () => []
})

const emit = defineEmits<Emits>()

// State
const materials = ref<Material[]>([])
const units = ref<Unit[]>([])
const selectedItem = ref<Material | null>(null)
const selectedUnitId = ref<number | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Computed
const filteredMaterials = computed(() => {
  if (selectedUnitId.value === null) {
    return materials.value
  }
  return materials.value.filter(m => m.unit_id === selectedUnitId.value)
})

// Watch for dialog open
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    if (materials.value.length === 0) {
      loadMaterials()
    }
    if (units.value.length === 0) {
      loadUnits()
    }
    selectedItem.value = null
    selectedUnitId.value = null
  }
})

// Methods
async function loadMaterials() {
  loading.value = true
  error.value = null
  try {
    materials.value = await materialsApi.getAll(false)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load materials'
    console.error('Error loading materials:', err)
  } finally {
    loading.value = false
  }
}

async function loadUnits() {
  try {
    units.value = await unitsApi.getAll(false)
  } catch (err) {
    console.error('Error loading units:', err)
  }
}

function isAlreadyAdded(materialId: number): boolean {
  return props.existingMaterialIds.includes(materialId)
}

function isItemDisabled(item: Material): boolean {
  return isAlreadyAdded(item.id)
}

function handleSelect(item: Material) {
  emit('select', item)
}

function handleClose() {
  emit('close')
}

function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}
</script>

<style scoped>
.filter-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #495057;
}

.filter-select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  background-color: white;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.material-content {
  display: flex;
  width: 100%;
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
</style>
