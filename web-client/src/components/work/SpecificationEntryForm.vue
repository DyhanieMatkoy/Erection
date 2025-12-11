<template>
  <div v-if="isOpen" class="dialog-overlay" @click.self="close">
    <div class="dialog">
      <div class="dialog-header">
        <h2>{{ isEdit ? 'Edit Specification' : 'Add Specification' }}</h2>
        <button @click="close" class="close-btn">&times;</button>
      </div>

      <div class="dialog-body">
        <!-- Component Type -->
        <div class="form-section">
          <label class="form-label">Type <span class="required">*</span></label>
          <select v-model="form.component_type" class="form-select">
            <option value="Material">Material</option>
            <option value="Labor">Labor</option>
            <option value="Equipment">Equipment</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <!-- Component Name -->
        <div class="form-section">
          <label class="form-label">Name <span class="required">*</span></label>
          <div class="input-group">
            <input 
              v-model="form.component_name" 
              type="text" 
              class="form-input"
              placeholder="Enter component name"
            />
            <button 
              v-if="form.component_type === 'Material'"
              @click="showMaterialPicker = true"
              class="btn btn-outline"
              type="button"
            >
              Select Material
            </button>
          </div>
        </div>

        <!-- Unit -->
        <div class="form-section">
          <label class="form-label">Unit</label>
          <input 
            v-model="form.unit_name" 
            type="text" 
            class="form-input"
            placeholder="e.g. pcs, m2, kg"
          />
        </div>

        <!-- Consumption Rate & Unit Price -->
        <div class="form-row">
          <div class="form-section half">
            <label class="form-label">Consumption Rate <span class="required">*</span></label>
            <input 
              v-model.number="form.consumption_rate" 
              type="number" 
              step="0.001"
              min="0.001"
              class="form-input"
            />
          </div>
          <div class="form-section half">
            <label class="form-label">Unit Price <span class="required">*</span></label>
            <input 
              v-model.number="form.unit_price" 
              type="number" 
              step="0.01"
              min="0"
              class="form-input"
            />
          </div>
        </div>

        <!-- Total Cost Preview -->
        <div class="total-preview">
          <span>Total Cost:</span>
          <span class="amount">{{ formatCurrency(totalCost) }}</span>
        </div>

      </div>

      <div class="dialog-footer">
        <button @click="close" class="btn btn-secondary">Cancel</button>
        <button 
          @click="save" 
          class="btn btn-primary"
          :disabled="!isValid"
        >
          {{ isEdit ? 'Update' : 'Add' }}
        </button>
      </div>
    </div>
    
    <SimpleMaterialSelectorDialog
      :is-open="showMaterialPicker"
      @close="showMaterialPicker = false"
      @select="handleMaterialSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { WorkSpecification, WorkSpecificationCreate, ComponentType, Material } from '@/types/models'
import SimpleMaterialSelectorDialog from '@/components/common/SimpleMaterialSelectorDialog.vue'

interface Props {
  isOpen: boolean
  editItem?: WorkSpecification | null
  workId: number
}

interface Emits {
  (e: 'close'): void
  (e: 'save', data: WorkSpecificationCreate): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isEdit = computed(() => !!props.editItem)
const showMaterialPicker = ref(false)

const form = ref({
  component_type: 'Material' as ComponentType,
  component_name: '',
  unit_name: '',
  unit_id: null as number | null,
  consumption_rate: 0,
  unit_price: 0,
  material_id: null as number | null
})

const totalCost = computed(() => {
  return (form.value.consumption_rate || 0) * (form.value.unit_price || 0)
})

const isValid = computed(() => {
  return form.value.component_name.trim().length > 0 &&
         form.value.consumption_rate > 0 &&
         form.value.unit_price >= 0
})

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    if (props.editItem) {
      form.value = {
        component_type: props.editItem.component_type,
        component_name: props.editItem.component_name,
        unit_name: props.editItem.unit_name || '',
        unit_id: props.editItem.unit_id,
        consumption_rate: props.editItem.consumption_rate,
        unit_price: props.editItem.unit_price,
        material_id: props.editItem.material_id || null
      }
    } else {
      resetForm()
    }
  }
})

function resetForm() {
  form.value = {
    component_type: 'Material',
    component_name: '',
    unit_name: '',
    unit_id: null,
    consumption_rate: 0,
    unit_price: 0,
    material_id: null
  }
}

function close() {
  emit('close')
}

function save() {
  if (!isValid.value) return
  
  emit('save', {
    work_id: props.workId,
    ...form.value
  })
  close()
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB'
  }).format(value)
}

function handleMaterialSelect(material: Material) {
  form.value.component_name = material.description
  form.value.unit_name = material.unit_name || ''
  form.value.unit_price = material.price
  form.value.material_id = material.id
  showMaterialPicker.value = false
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
  max-width: 500px;
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
}

.form-section {
  margin-bottom: 1rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.half {
  flex: 1;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #495057;
}

.required {
  color: #dc3545;
}

.form-select,
.form-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

.total-preview {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.amount {
  color: #007bff;
  font-size: 1.25rem;
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
  font-size: 1rem;
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

.btn-outline {
  background-color: transparent;
  border: 1px solid #007bff;
  color: #007bff;
}
</style>
