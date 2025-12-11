<template>
  <div class="work-specification-panel">
    <!-- Toolbar Removed - Actions moved to WorkForm -->

    <!-- Loading/Error -->
    <div v-if="loading" class="loading-state">
      Loading specifications...
    </div>
    <div v-else-if="error" class="error-state">
      {{ error }}
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Table -->
      <SpecificationTable
        :specifications="specifications"
        :total-cost="totalCost"
        @add="openAdd"
        @edit="openEdit"
        @delete="handleDelete"
        @update-inline="handleInlineUpdate"
      />

      <!-- Summary Cards (Moved to bottom, toggleable) -->
      <div class="summary-section">
        <button 
          @click="showSummary = !showSummary" 
          class="toggle-summary-btn"
        >
          <span class="toggle-icon">{{ showSummary ? '▼' : '▶' }}</span>
          Итоги
        </button>
        
        <div v-if="showSummary" class="summary-cards">
          <div class="card">
            <div class="card-label">Materials</div>
            <div class="card-value">{{ formatCurrency(totalsByType.Material) }}</div>
          </div>
          <div class="card">
            <div class="card-label">Labor</div>
            <div class="card-value">{{ formatCurrency(totalsByType.Labor) }}</div>
          </div>
          <div class="card">
            <div class="card-label">Equipment</div>
            <div class="card-value">{{ formatCurrency(totalsByType.Equipment) }}</div>
          </div>
          <div class="card">
            <div class="card-label">Other</div>
            <div class="card-value">{{ formatCurrency(totalsByType.Other) }}</div>
          </div>
          <div class="card total">
            <div class="card-label">Total</div>
            <div class="card-value">{{ formatCurrency(totalCost) }}</div>
          </div>
        </div>
      </div>
    </template>

    <!-- Dialogs -->
    <SpecificationEntryForm
      :is-open="showForm"
      :work-id="workId"
      :edit-item="editingItem"
      @close="closeForm"
      @save="handleSave"
    />
    
    <WorkListForm
      :is-open="showWorkSelector"
      title="Select Work to Copy From"
      :current-work-id="workId"
      @close="showWorkSelector = false"
      @select="handleWorkSelect"
    />

    <!-- Hidden file input for import -->
    <input 
      ref="fileInput" 
      type="file" 
      accept=".xlsx,.xls" 
      class="hidden" 
      @change="handleFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useWorkSpecification } from '@/composables/useWorkSpecification'
import SpecificationTable from './SpecificationTable.vue'
import SpecificationEntryForm from './SpecificationEntryForm.vue'
import WorkListForm from '@/components/common/WorkListForm.vue'
import type { WorkSpecification, WorkSpecificationCreate, WorkSpecificationUpdate, Work } from '@/types/models'

const showSummary = ref(false)

const props = defineProps<{
  workId: number
}>()

const {
  specifications,
  loading,
  error,
  totalCost,
  totalsByType,
  loadSpecifications,
  addSpecification,
  updateSpecification,
  removeSpecification,
  copyFromWork,
  importFromExcel,
  exportToExcel
} = useWorkSpecification(props.workId)

const showForm = ref(false)
const showWorkSelector = ref(false)
const editingItem = ref<WorkSpecification | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

onMounted(() => {
  loadSpecifications()
})

function formatCurrency(value: number) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB'
  }).format(value)
}

function openAdd() {
  editingItem.value = null
  showForm.value = true
}

function openEdit(spec: WorkSpecification) {
  editingItem.value = spec
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingItem.value = null
}

async function handleSave(data: WorkSpecificationCreate) {
  if (editingItem.value) {
    await updateSpecification(editingItem.value.id, data)
  } else {
    await addSpecification(data)
  }
}

async function handleDelete(specId: number) {
  await removeSpecification(specId)
}

async function handleInlineUpdate(specId: number, field: 'consumption_rate' | 'unit_price', value: number) {
  const data: WorkSpecificationUpdate = {
    [field]: value
  }
  await updateSpecification(specId, data)
}

function openCopyFromWork() {
  showWorkSelector.value = true
}

function handleWorkSelect(work: Work) {
  copyFromWork(work.id)
  showWorkSelector.value = false
}

function openImport() {
  fileInput.value?.click()
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    await importFromExcel(target.files[0])
    target.value = ''
  }
}

async function handleExport() {
  await exportToExcel()
}

// Expose methods for parent component
defineExpose({
  openImport,
  handleExport,
  openCopyFromWork
})
</script>

<style scoped>
.work-specification-panel {
  display: flex;
  flex-direction: column;
}

/* Removed Toolbar */

.summary-section {
  margin-top: 1rem;
}

.toggle-summary-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5563;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem 0;
}

.toggle-summary-btn:hover {
  color: #1f2937;
}

.toggle-icon {
  font-size: 0.75rem;
}

.summary-cards {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.card {
  background-color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  flex: 1;
  min-width: 120px;
}

.card.total {
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
}

.card-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.125rem;
}

.card-value {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.btn {
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.loading-state,
.error-state {
  padding: 2rem;
  text-align: center;
}

.error-state {
  color: #dc3545;
}

.hidden {
  display: none;
}
</style>
