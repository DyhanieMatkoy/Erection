<template>
  <div class="work-basic-info">
    <!-- Removed Caption -->
    
    <!-- Main Fields -->
    <div class="compact-form grid-layout">
      <!-- Row 1: Code, Unit, Price, Labor -->
      <div class="form-row grid-col-code">
        <label for="work-code" class="form-label">Код:</label>
        <input
          id="work-code"
          v-model="localWork.code"
          type="text"
          class="form-control"
          placeholder="Код"
          maxlength="50"
          @input="handleInput"
        />
      </div>

      <div class="form-row grid-col-unit">
        <label for="work-unit" class="form-label">Ед. изм.:</label>
        <div class="input-with-button">
          <input
            id="work-unit"
            v-model="selectedUnitName"
            type="text"
            class="form-control"
            placeholder=""
            readonly
            @click="showUnitSelector = true"
            style="min-width: 0;" 
          />
          <button
            type="button"
            class="btn btn-outline-secondary btn-icon-only"
            @click="showUnitSelector = true"
            title="Выбрать"
          >
            ...
          </button>
        </div>
      </div>

      <div class="form-row grid-col-price">
        <label for="work-price" class="form-label">Цена:</label>
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
      </div>

      <div class="form-row grid-col-labor">
        <label for="work-labor-rate" class="form-label">Трудозатраты:</label>
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
      </div>

      <!-- Row 2: Name (Full Width) -->
      <div class="form-row grid-col-full">
        <label for="work-name" class="form-label required">Наименование:</label>
        <input
          id="work-name"
          v-model="localWork.name"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.name }"
          placeholder="Введите наименование работы"
          maxlength="500"
          required
          @input="handleInput"
        />
        <div v-if="errors.name" class="invalid-feedback">
          {{ errors.name }}
        </div>
      </div>
    </div>

    <!-- Collapsible Advanced Section -->
    <details class="advanced-section">
      <summary class="advanced-toggle">
        <span class="toggle-icon">▶</span>
        Дополнительные параметры
      </summary>
      
      <div class="advanced-content">
        <!-- Is Group Checkbox -->
        <div class="form-row">
          <label class="form-label">Тип:</label>
          <div class="checkbox-container">
            <div class="form-check">
              <input
                id="work-is-group"
                v-model="localWork.is_group"
                type="checkbox"
                class="form-check-input"
                @change="handleGroupChange"
              />
              <label for="work-is-group" class="form-check-label">
                Это группа работ
              </label>
            </div>
            <small class="form-text text-muted">
              Группы организуют работы иерархически и не могут иметь цену или трудозатраты
            </small>
          </div>
        </div>

        <!-- Parent Work -->
        <div class="form-row">
          <label for="work-parent" class="form-label">Родитель:</label>
          <div class="parent-container">
            <div class="input-with-button">
              <input
                id="work-parent"
                v-model="selectedParentName"
                type="text"
                class="form-control"
                :class="{ 'is-invalid': errors.parent_id }"
                placeholder="Выберите родительскую группу..."
                readonly
                @click="showParentSelector = true"
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                @click="showParentSelector = true"
                title="Выбрать родителя"
              >
                📁
              </button>
              <button
                v-if="localWork.parent_id"
                type="button"
                class="btn btn-outline-danger"
                @click="clearParent"
                title="Очистить"
              >
                ✕
              </button>
            </div>
            <div v-if="errors.parent_id" class="invalid-feedback d-block">
              {{ errors.parent_id }}
            </div>
            <small v-if="hierarchyPath" class="form-text text-muted">
              Путь: {{ hierarchyPath }}
            </small>
          </div>
        </div>
      </div>
    </details>

    <!-- Unit Selector Dialog -->
    <UnitListForm
      :is-open="showUnitSelector"
      title="Select Unit"
      :current-id="localWork.unit_id"
      @close="showUnitSelector = false"
      @select="handleUnitSelect"
    />

    <!-- Parent Work Selector Dialog -->
    <WorkListForm
      :is-open="showParentSelector"
      title="Select Parent Work"
      :current-work-id="localWork.id"
      :selected-id="localWork.parent_id"
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
  
  // emit('validate') // REMOVED to prevent infinite recursion
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
  padding: 0.1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #212529;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e9ecef;
}

.compact-form {
  /* Default column layout for mobile/fallback */
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.grid-layout {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 0.75rem;
  align-items: end;
}

.form-row {
  display: flex;
  flex-direction: column;
}

.grid-col-code { grid-column: span 3; }
.grid-col-unit { grid-column: span 2; }
.grid-col-price { grid-column: span 3; }
.grid-col-labor { grid-column: span 4; }
.grid-col-full { grid-column: 1 / -1; }

.input-with-button {
  display: flex;
  gap: 0.25rem;
}

.btn-icon-only {
  padding: 0.25rem 0.5rem;
  min-width: 2rem;
}

@media (max-width: 768px) {
  .grid-layout {
    display: flex;
    flex-direction: column;
  }
}

.form-label {
  font-weight: 500;
  color: #495057;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.form-label.required::after {
  content: ' *';
  color: #dc3545;
}

.form-control {
  padding: 0.25rem 0.5rem;
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
