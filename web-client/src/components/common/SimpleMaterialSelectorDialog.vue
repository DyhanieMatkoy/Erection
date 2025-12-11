<template>
  <div v-if="isOpen" class="dialog-overlay" @click.self="close">
    <div class="dialog">
      <div class="dialog-header">
        <h2>Select Material</h2>
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
            :class="['material-row', { 'material-selected': selectedMaterial?.id === material.id }]"
            @click="selectMaterial(material)"
            @dblclick="confirm"
          >
            <div class="material-content">
              <div class="material-header">
                <span class="material-code">{{ material.code || '-' }}</span>
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

      <div class="dialog-footer">
        <button @click="close" class="btn btn-secondary">Cancel</button>
        <button 
          @click="confirm" 
          class="btn btn-primary"
          :disabled="!selectedMaterial"
        >
          Select
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { materialsApi } from '@/api/costs-materials'
import type { Material } from '@/types/models'

interface Props {
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'select', material: Material): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const materials = ref<Material[]>([])
const filteredMaterials = ref<Material[]>([])
const selectedMaterial = ref<Material | null>(null)
const searchQuery = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    selectedMaterial.value = null
    searchQuery.value = ''
    if (materials.value.length === 0) {
      loadMaterials()
    } else {
      filterMaterials()
    }
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

function selectMaterial(material: Material) {
  selectedMaterial.value = material
}

function confirm() {
  if (selectedMaterial.value) {
    emit('select', selectedMaterial.value)
    close()
  }
}

function close() {
  emit('close')
}

function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}
</script>

<style scoped>
/* Reuse styles */
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
  z-index: 1010; /* Higher than parent dialog */
}

.dialog {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
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
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
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

.materials-list {
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  max-height: 400px;
  overflow-y: auto;
}

.material-row {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
}

.material-row:hover {
  background-color: #f8f9fa;
}

.material-row.material-selected {
  background-color: #e7f3ff;
  border-left: 3px solid #007bff;
}

.material-code {
  font-weight: 600;
  color: #495057;
}

.material-details {
  font-size: 0.875rem;
  color: #6c757d;
}

.dialog-footer {
  padding: 1.5rem;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:disabled {
  background-color: #a0c4ff;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.loading-state, .error-state, .empty-state {
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
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
