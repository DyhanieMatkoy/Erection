<template>
  <div class="work-basic-info">
    <h3 class="section-title">Basic Information</h3>
    
    <div class="form-grid">
      <!-- Code -->
      <div class="form-group">
        <label for="work-code" class="form-label">Code</label>
        <input
          id="work-code"
          v-model="localWork.code"
          type="text"
          class="form-control"
          placeholder="Enter work code"
          maxlength="50"
          @input="handleInput"
        />
      </div>

      <!-- Name -->
      <div class="form-group full-width">
        <label for="work-name" class="form-label required">Name</label>
        <input
          id="work-name"
          v-model="localWork.name"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.name }"
          placeholder="Enter work name"
          maxlength="500"
          required
          @input="handleInput"
        />
        <div v-if="errors.name" class="invalid-feedback">
          {{ errors.name }}
        </div>
      </div>

      <!-- Unit -->
      <div class="form-group">
        <label for="work-unit" class="form-label">Unit</label>
        <div class="input-with-button">
          <input
            id="work-unit"
            v-model="selectedUnitName"
            type="text"
            class="form-control"
            placeholder="Select unit..."
            readonly
            @click="showUnitSelector = true"
          />
          <button
            type="button"
            class="btn btn-outline-secondary"
            @click="showUnitSelector = true"
            title="Select unit"
          >
            <span class="icon">📋</span>
          </button>
          <button
            v-if="localWork.unit_id"
            type="button"
            class="btn btn-outline-danger"
            @click="clearUnit"
            title="Clear unit"
          >
            <span class="icon">✕</span>
          </button>
        </div>
      </div>

      <!-- Is Group Checkbox -->
      <div class="form-group checkbox-group">
        <div class="form-check">
          <input
            id="work-is-group"
            v-model="localWork.is_group"
            type="checkbox"
            class="form-check-input"
            @change="handleGroupChange"
          />
          <label for="work-is-group" class="form-check-label">
            Is Group
          </label>
        </div>
        <small class="form-text text-muted">
          Groups organize works hierarchically and cannot have price or labor rate
        </small>
      </div>

      <!-- Price -->
      <div class="form-group">
        <label for="work-price" class="form-label">Price</label>
        <input
          id="work-price"
          v-model.number="localWork.price"
          type="number"
          class="form-control"
          :class="{ 'is-invalid': errors.price }"
          placeholder="0.00"
          step="0.01"
          min="0"
          :disabled="localWork.is_group"
          @input="handleInput"
        />
        <div v-if="errors.price" class="invalid-feedback">
          {{ errors.price }}
        </div>
      </div>

      <!-- Labor Rate -->
      <div class="form-group">
        <label for="work-labor-rate" class="form-label">Labor Rate</label>
        <input
          id="work-labor-rate"
          v-model.number="localWork.labor_rate"
          type="number"
          class="form-control"
          :class="{ 'is-invalid': errors.labor_rate }"
          placeholder="0.00"
          step="0.01"
          min="0"
          :disabled="localWork.is_group"
          @input="handleInput"
        />
        <div v-if="errors.labor_rate" class="invalid-feedback">
          {{ errors.labor_rate }}
        </div>
      </div>

      <!-- Parent Work -->
      <div class="form-group full-width">
        <label for="work-parent" class="form-label">Parent Work</label>
        <div class="input-with-button">
          <input
            id="work-parent"
            v-model="selectedParentName"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors.parent_id }"
            placeholder="Select parent work..."
            readonly
            @click="showParentSelector = true"
          />
          <button
            type="button"
            class="btn btn-outline-secondary"
            @click="showParentSelector = true"
            title="Select parent work"
          >
            <span class="icon">📁</span>
          </button>
          <button
            v-if="localWork.parent_id"
            type="button"
            class="btn btn-outline-danger"
            @click="clearParent"
            title="Clear parent"
          >
            <span class="icon">✕</span>
          </button>
        </div>
        <div v-if="errors.parent_id" class="invalid-feedback d-block">
          {{ errors.parent_id }}
        </div>
        <small v-if="hierarchyPath" class="form-text text-muted">
          Path: {{ hierarchyPath }}
        </small>
      </div>
    </div>

    <!-- Unit Selector Dialog -->
    <UnitListForm
      :is-open="showUnitSelector"
      title="Select Unit"
      @close="showUnitSelector = false"
      @select="handleUnitSelect"
    />

    <!-- Parent Work Selector Dialog -->
    <WorkListForm
      :is-open="showParentSelector"
      title="Select Parent Work"
      :current-work-id="localWork.id"
      :groups-only="true"
      @close="showParentSelector = false"
      @select="handleParentSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import UnitListForm from '@/components/common/UnitListForm.vue'
import WorkListForm from '@/components/common/WorkListForm.vue'
import type { Work, Unit } from '@/types/models'

interface Props {
  work: Partial<Work>
  units?: Unit[]
  works?: Work[]
}

interface Emits {
  (e: 'update:work', work: Partial<Work>): void
  (e: 'validate'): void
}

const props = withDefaults(defineProps<Props>(), {
  units: () => [],
  works: () => []
})

const emit = defineEmits<Emits>()

// Local state
const localWork = ref<Partial<Work>>({ ...props.work })
const showUnitSelector = ref(false)
const showParentSelector = ref(false)
const errors = ref<Record<string, string>>({})

// Watch for external changes
watch(() => props.work, (newWork) => {
  localWork.value = { ...newWork }
}, { deep: true })

// Computed properties
const selectedUnitName = computed(() => {
  if (!localWork.value.unit_id) return ''
  const unit = props.units.find(u => u.id === localWork.value.unit_id)
  return unit?.name || localWork.value.unit || ''
})

const selectedParentName = computed(() => {
  if (!localWork.value.parent_id) return ''
  const parent = props.works.find(w => w.id === localWork.value.parent_id)
  return parent ? `${parent.code || ''} - ${parent.name}` : ''
})

const hierarchyPath = computed(() => {
  if (!localWork.value.parent_id) return ''
  return buildHierarchyPath(localWork.value.parent_id)
})

// Methods
function buildHierarchyPath(workId: number, visited = new Set<number>()): string {
  if (visited.has(workId)) {
    return '[Circular Reference]'
  }
  
  const work = props.works.find(w => w.id === workId)
  if (!work) return ''
  
  if (!work.parent_id) {
    return work.name
  }
  
  visited.add(workId)
  const parentPath = buildHierarchyPath(work.parent_id, visited)
  return parentPath ? `${parentPath} > ${work.name}` : work.name
}

function handleInput() {
  validateFields()
  emit('update:work', localWork.value)
}

function handleGroupChange() {
  // Clear price and labor_rate when is_group is checked
  if (localWork.value.is_group) {
    localWork.value.price = 0
    localWork.value.labor_rate = 0
  }
  validateFields()
  emit('update:work', localWork.value)
}

function handleUnitSelect(unit: Unit) {
  localWork.value.unit_id = unit.id
  localWork.value.unit = unit.name
  showUnitSelector.value = false
  emit('update:work', localWork.value)
}

function handleParentSelect(work: Work) {
  localWork.value.parent_id = work.id
  showParentSelector.value = false
  validateFields()
  emit('update:work', localWork.value)
}

function clearUnit() {
  localWork.value.unit_id = undefined
  localWork.value.unit = undefined
  emit('update:work', localWork.value)
}

function clearParent() {
  localWork.value.parent_id = null
  errors.value.parent_id = ''
  emit('update:work', localWork.value)
}

function validateFields() {
  errors.value = {}
  
  // Validate name (required, not empty or whitespace)
  if (!localWork.value.name || localWork.value.name.trim() === '') {
    errors.value.name = 'Work name is required'
  }
  
  // Validate group work constraints
  if (localWork.value.is_group) {
    if (localWork.value.price && localWork.value.price > 0) {
      errors.value.price = 'Group works cannot have a price'
    }
    if (localWork.value.labor_rate && localWork.value.labor_rate > 0) {
      errors.value.labor_rate = 'Group works cannot have a labor rate'
    }
  }
  
  // Validate circular reference
  if (localWork.value.parent_id && localWork.value.id) {
    if (isCircularReference(localWork.value.parent_id, localWork.value.id)) {
      errors.value.parent_id = 'Cannot set parent: would create circular reference'
    }
  }
  
  emit('validate')
  return Object.keys(errors.value).length === 0
}

function isCircularReference(parentId: number, currentId: number, visited = new Set<number>()): boolean {
  if (parentId === currentId) return true
  if (visited.has(parentId)) return false
  
  visited.add(parentId)
  
  const parent = props.works.find(w => w.id === parentId)
  if (!parent || !parent.parent_id) return false
  
  return isCircularReference(parent.parent_id, currentId, visited)
}

// Expose validation method
defineExpose({
  validate: validateFields
})
</script>

<style scoped>
.work-basic-info {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #212529;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e9ecef;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group.checkbox-group {
  grid-column: 1 / -1;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
}

.form-label {
  font-weight: 500;
  color: #495057;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.form-label.required::after {
  content: ' *';
  color: #dc3545;
}

.form-control {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus {
  border-color: #80bdff;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.form-control:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
  opacity: 0.6;
}

.form-control.is-invalid {
  border-color: #dc3545;
}

.form-control.is-invalid:focus {
  border-color: #dc3545;
  box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

.invalid-feedback {
  display: none;
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.invalid-feedback.d-block,
.form-control.is-invalid ~ .invalid-feedback {
  display: block;
}

.form-check {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}

.form-check-input {
  width: 1.25rem;
  height: 1.25rem;
  margin-right: 0.5rem;
  cursor: pointer;
}

.form-check-label {
  font-weight: 500;
  cursor: pointer;
  user-select: none;
}

.form-text {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.input-with-button {
  display: flex;
  gap: 0.5rem;
}

.input-with-button .form-control {
  flex: 1;
  cursor: pointer;
}

.btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  background-color: white;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.15s ease-in-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn:hover {
  background-color: #f8f9fa;
}

.btn:active {
  transform: translateY(1px);
}

.btn-outline-secondary {
  color: #6c757d;
  border-color: #6c757d;
}

.btn-outline-secondary:hover {
  background-color: #6c757d;
  color: white;
}

.btn-outline-danger {
  color: #dc3545;
  border-color: #dc3545;
}

.btn-outline-danger:hover {
  background-color: #dc3545;
  color: white;
}

.icon {
  font-size: 1rem;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-group.full-width {
    grid-column: 1;
  }
}
</style>
