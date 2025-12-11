<template>
  <div class="specification-table">
    <div class="table-header">
      <h3>Specifications</h3>
      <div class="actions">
        <button @click="$emit('add')" class="btn btn-primary btn-sm">
          <span class="icon">+</span> Add Entry
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="specifications.length === 0" class="empty-state">
      <p>No specifications added yet.</p>
      <p class="hint">Click "Add Entry" to add components to this work.</p>
    </div>

    <!-- Specifications Table -->
    <table v-else class="table">
      <thead>
        <tr>
          <th>Type</th>
          <th>Name</th>
          <th>Unit</th>
          <th class="text-right">Rate</th>
          <th class="text-right">Price</th>
          <th class="text-right">Total</th>
          <th class="actions-column">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="spec in specifications" :key="spec.id">
          <td>
            <span :class="['badge', getTypeClass(spec.component_type)]">
              {{ spec.component_type }}
            </span>
          </td>
          <td>{{ spec.component_name }}</td>
          <td>{{ spec.unit_name || '-' }}</td>
          
          <!-- Editable Rate -->
          <td class="text-right editable-cell" @click="startEditing(spec, 'rate')">
            <input 
              v-if="editingId === spec.id && editingField === 'rate'"
              ref="editInput"
              v-model.number="editValue"
              type="number"
              step="0.001"
              class="inline-input"
              @blur="saveEdit(spec)"
              @keyup.enter="saveEdit(spec)"
              @keyup.esc="cancelEdit"
            />
            <span v-else>{{ formatNumber(spec.consumption_rate) }}</span>
          </td>

          <!-- Editable Price -->
          <td class="text-right editable-cell" @click="startEditing(spec, 'price')">
            <input 
              v-if="editingId === spec.id && editingField === 'price'"
              ref="editInput"
              v-model.number="editValue"
              type="number"
              step="0.01"
              class="inline-input"
              @blur="saveEdit(spec)"
              @keyup.enter="saveEdit(spec)"
              @keyup.esc="cancelEdit"
            />
            <span v-else>{{ formatPrice(spec.unit_price) }}</span>
          </td>

          <td class="text-right font-weight-bold">
            {{ formatCurrency(spec.total_cost) }}
          </td>
          
          <td class="actions-column">
            <button @click="$emit('edit', spec)" class="btn-icon" title="Edit">
              ✎
            </button>
            <button @click="handleDelete(spec)" class="btn-icon delete" title="Delete">
              🗑
            </button>
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr class="total-row">
          <td colspan="5" class="text-right">Total Cost:</td>
          <td class="text-right">{{ formatCurrency(totalCost) }}</td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import type { WorkSpecification, ComponentType } from '@/types/models'

interface Props {
  specifications: WorkSpecification[]
  totalCost: number
}

interface Emits {
  (e: 'add'): void
  (e: 'edit', spec: WorkSpecification): void
  (e: 'delete', specId: number): void
  (e: 'update-inline', specId: number, field: 'consumption_rate' | 'unit_price', value: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const editingId = ref<number | null>(null)
const editingField = ref<'rate' | 'price' | null>(null)
const editValue = ref<number>(0)
const editInput = ref<HTMLInputElement | null>(null)

function getTypeClass(type: ComponentType): string {
  switch (type) {
    case 'Material': return 'badge-info'
    case 'Labor': return 'badge-success'
    case 'Equipment': return 'badge-warning'
    default: return 'badge-secondary'
  }
}

function formatNumber(value: number) {
  return value.toLocaleString('ru-RU', { maximumFractionDigits: 3 })
}

function formatPrice(value: number) {
  return value.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB'
  }).format(value)
}

function startEditing(spec: WorkSpecification, field: 'rate' | 'price') {
  editingId.value = spec.id
  editingField.value = field
  editValue.value = field === 'rate' ? spec.consumption_rate : spec.unit_price
  
  nextTick(() => {
    if (editInput.value) {
      // If editInput is an array (due to v-for), get the first element
      const input = Array.isArray(editInput.value) ? editInput.value[0] : editInput.value
      input?.focus()
    }
  })
}

function saveEdit(spec: WorkSpecification) {
  if (editingId.value === null) return
  
  const field = editingField.value === 'rate' ? 'consumption_rate' : 'unit_price'
  const value = editValue.value
  
  // Validation
  if (value < 0) {
    alert('Value must be positive')
    cancelEdit()
    return
  }
  
  // Only emit update if value changed
  if (field === 'consumption_rate' && value !== spec.consumption_rate) {
    emit('update-inline', spec.id, field, value)
  } else if (field === 'unit_price' && value !== spec.unit_price) {
    emit('update-inline', spec.id, field, value)
  }
  
  cancelEdit()
}

function cancelEdit() {
  editingId.value = null
  editingField.value = null
}

function handleDelete(spec: WorkSpecification) {
  if (confirm(`Are you sure you want to delete "${spec.component_name}"?`)) {
    emit('delete', spec.id)
  }
}
</script>

<style scoped>
.specification-table {
  margin-bottom: 2rem;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.table-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.empty-state {
  padding: 3rem 2rem;
  text-align: center;
  color: #6c757d;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  border: 2px dashed #dee2e6;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  overflow: hidden;
}

.table thead {
  background-color: #f8f9fa;
}

.table th,
.table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.table th {
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  color: #495057;
}

.text-right {
  text-align: right;
}

.actions-column {
  width: 100px;
  text-align: center;
}

.badge {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  border-radius: 0.25rem;
  color: white;
  font-weight: 600;
}

.badge-info { background-color: #17a2b8; }
.badge-success { background-color: #28a745; }
.badge-warning { background-color: #ffc107; color: #212529; }
.badge-secondary { background-color: #6c757d; }

.editable-cell {
  cursor: pointer;
  position: relative;
}

.editable-cell:hover {
  background-color: #f8f9fa;
}

.inline-input {
  width: 100%;
  padding: 0.25rem;
  border: 1px solid #007bff;
  border-radius: 0.25rem;
  text-align: right;
}

.btn {
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  color: #6c757d;
  padding: 0.25rem;
}

.btn-icon:hover {
  color: #007bff;
}

.btn-icon.delete:hover {
  color: #dc3545;
}

.total-row {
  background-color: #f8f9fa;
  font-weight: bold;
}
</style>
