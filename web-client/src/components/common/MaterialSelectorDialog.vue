<template>
  <div v-if="isOpen" class="dialog-overlay" @click.self="close">
    <div class="dialog">
      <div class="dialog-header">
        <h2>Add Material</h2>
        <button @click="close" class="close-btn">&times;</button>
      </div>

      <div class="dialog-body">
        <!-- Step 1: Select Cost Item -->
        <div class="form-section">
          <label class="form-label">
            1. Select Cost Item <span class="required">*</span>
          </label>
          <select v-model="selectedCostItemId" class="form-select" @change="onCostItemChange">
            <option :value="null">-- Select a cost item --</option>
            <option 
              v-for="item in availableCostItems" 
              :key="item.id" 
              :value="item.cost_item_id"
            >
              {{ item.cost_item?.description || 'Unknown' }}
            </option>
          </select>
          <p v-if="!selectedCostItemId" class="help-text">
            Select which cost item this material belongs to
          </p>
        </div>

        <!-- Step 2: Select Material -->
        <div v-if="selectedCostItemId" class="form-section">
          <label class="form-label">
            2. Select Material <span class="required">*</span>
          </label>
          
          <!-- Search Box -->
          <div class="search-box">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search by code or description..."
              class="search-input"
              @input="filterMaterials"
            />
          </div>

          <!-- Loading State -->
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading materials...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="error-state">
            <p class="error-message">{{ error }}</p>
            <button @click="loadMaterials" class="btn btn-primary btn-sm">Retry</button>
          </div>

          <!-- Materials List -->
          <div v-else class="materials-list">
            <div v-if="filteredMaterials.length === 0" class="empty-state">
              No materials found matching "{{ searchQuery }}"
            </div>

            <div
              v-for="material in filteredMaterials"
              :key="material.id"
              :class="['material-row', { 
                'material-disabled': isAlreadyAdded(material.id),
                'material-selected': selectedMaterial?.id === material.id 
              }]"
              @click="selectMaterial(material)"
            >
              <div class="material-content">
                <div class="material-header">
                  <span class="material-code">{{ material.code || '-' }}</span>
                  <span v-if="isAlreadyAdded(material.id)" class="badge badge-info">Already Added</span>
                </div>
                <div class="material-description">{{ material.description }}</div>
                <div class="material-details">
                  Unit: {{ material.unit_name || '-' }} | 
                  Price: {{ formatPrice(material.price) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: Enter Quantity -->
        <div v-if="selectedMaterial" class="form-section">
          <label class="form-label">
            3. Quantity per Unit <span class="required">*</span>
          </label>
          <div class="quantity-input-group">
            <input
              v-model.number="quantity"
              type="number"
              step="0.001"
              min="0.001"
              class="form-input"
              placeholder="Enter quantity"
              @keyup.enter="confirm"
            />
            <span class="input-suffix">{{ selectedMaterial.unit_name || 'units' }}</span>
          </div>
          <p class="help-text">
            How much of this material is needed per unit of work
          </p>
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="close" class="btn btn-secondary">Cancel</button>
        <button 
          @click="confirm" 
          class="btn btn-primary"
          :disabled="!canConfirm"
        >
          Add Material
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { materialsApi } from '@/api/costs-materials'
import type { Material, CostItemMaterial } from '@/types/models'

interface Props {
  isOpen: boolean
  availableCostItems: CostItemMaterial[]
  existingMaterials: CostItemMaterial[]
}

interface Emits {
  (e: 'close'): void
  (e: 'select', data: { costItemId: number; materialId: number; quantity: number }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const materials = ref<Material[]>([])
const filteredMaterials = ref<Material[]>([])
const selectedCostItemId = ref<number | null>(null)
const selectedMaterial = ref<Material | null>(null)
const quantity = ref<number>(1.0)
const searchQuery = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

const canConfirm = computed(() => {
  return selectedCostItemId.value !== null &&
         selectedMaterial.value !== null &&
         quantity.value > 0 &&
         !isAlreadyAdded(selectedMaterial.value.id)
})

// Watch for dialog open to load data
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && materials.value.length === 0) {
    loadMaterials()
  }
  if (isOpen) {
    resetForm()
  }
})

async function loadMaterials() {
  loading.value = true
  error.value = null
  try {
    materials.value = await materialsApi.getAll(false)
    filterMaterials()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load materials'
    console.error('Error loading materials:', err)
  } finally {
    loading.value = false
  }
}

function filterMaterials() {
  const query = searchQuery.value.toLowerCase().trim()
  
  if (!query) {
    filteredMaterials.value = materials.value
    return
  }

  filteredMaterials.value = materials.value.filter(material => {
    const codeMatch = material.code?.toLowerCase().includes(query)
    const descMatch = material.description?.toLowerCase().includes(query)
    return codeMatch || descMatch
  })
}

function isAlreadyAdded(materialId: number): boolean {
  if (!selectedCostItemId.value) return false
  
  return props.existingMaterials.some(m => 
    m.cost_item_id === selectedCostItemId.value && 
    m.material_id === materialId
  )
}

function onCostItemChange() {
  // Reset material selection when cost item changes
  selectedMaterial.value = null
  searchQuery.value = ''
  filterMaterials()
}

function selectMaterial(material: Material) {
  // Don't select already added materials
  if (isAlreadyAdded(material.id)) {
    return
  }
  selectedMaterial.value = material
}

function confirm() {
  if (canConfirm.value && selectedCostItemId.value && selectedMaterial.value) {
    emit('select', {
      costItemId: selectedCostItemId.value,
      materialId: selectedMaterial.value.id,
      quantity: quantity.value
    })
    close()
  }
}

function close() {
  emit('close')
  resetForm()
}

function resetForm() {
  selectedCostItemId.value = null
  selectedMaterial.value = null
  quantity.value = 1.0
  searchQuery.value = ''
}

function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
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
  max-width: 700px;
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

.form-section {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #495057;
}

.required {
  color: #dc3545;
}

.form-select,
.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.help-text {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #6c757d;
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
  padding: 2rem;
  text-align: center;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 0.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  margin-bottom: 0.5rem;
}

.empty-state {
  padding: 1.5rem;
  text-align: center;
  color: #6c757d;
}

.materials-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}

.material-row {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
  transition: background-color 0.2s;
}

.material-row:last-child {
  border-bottom: none;
}

.material-row:hover:not(.material-disabled) {
  background-color: #f8f9fa;
}

.material-row.material-selected {
  background-color: #e7f3ff;
  border-left: 3px solid #007bff;
}

.material-row.material-disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.material-content {
  flex: 1;
  min-width: 0;
}

.material-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.material-code {
  font-weight: 600;
  color: #495057;
}

.material-description {
  color: #212529;
  margin-bottom: 0.25rem;
}

.material-details {
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

.quantity-input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.quantity-input-group .form-input {
  flex: 1;
}

.input-suffix {
  color: #6c757d;
  font-size: 0.875rem;
  white-space: nowrap;
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

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}
</style>
