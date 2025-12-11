<template>
  <div class="materials-table">
    <div class="table-header">
      <h3>Materials</h3>
      <button @click="$emit('add-material')" class="btn btn-primary btn-sm">
        <span class="icon">+</span> Add
      </button>
    </div>

    <div v-if="materials.length === 0" class="empty-state">
      No materials added yet. Click "Add" to add materials to this work.
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Cost Item</th>
          <th>Code</th>
          <th>Material</th>
          <th>Unit</th>
          <th class="text-right">Price</th>
          <th class="text-right">Qty</th>
          <th class="text-right">Total</th>
          <th class="actions-column">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in materials" :key="item.id">
          <td>{{ item.cost_item?.description || '-' }}</td>
          <td>{{ item.material?.code || '-' }}</td>
          <td>{{ item.material?.description || '-' }}</td>
          <td>{{ item.material?.unit_name || '-' }}</td>
          <td class="text-right">{{ formatPrice(item.material?.price) }}</td>
          <td class="text-right">
            <input
              v-if="editingId === item.id"
              v-model.number="editingQuantity"
              @blur="saveQuantity(item)"
              @keyup.enter="saveQuantity(item)"
              @keyup.esc="cancelEdit"
              type="number"
              step="0.001"
              min="0.001"
              class="quantity-input"
              ref="quantityInput"
            />
            <span v-else @dblclick="startEdit(item)" class="quantity-cell">
              {{ formatQuantity(item.quantity_per_unit) }}
            </span>
          </td>
          <td class="text-right">{{ formatPrice(calculateTotal(item)) }}</td>
          <td class="actions-column">
            <button
              v-if="editingId !== item.id"
              @click="startEdit(item)"
              class="btn btn-sm btn-secondary"
              title="Edit quantity"
            >
              ✎
            </button>
            <button
              @click="handleDelete(item)"
              class="btn btn-sm btn-danger"
              title="Delete material"
            >
              🗑
            </button>
          </td>
        </tr>
      </tbody>
      <tfoot v-if="materials.length > 0">
        <tr>
          <td colspan="6" class="text-right"><strong>Total Materials Cost:</strong></td>
          <td class="text-right"><strong>{{ formatPrice(totalMaterialsCost) }}</strong></td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import type { CostItemMaterial } from '@/types/models'

interface Props {
  materials: CostItemMaterial[]
}

interface Emits {
  (e: 'add-material'): void
  (e: 'update-quantity', associationId: number, quantity: number): void
  (e: 'delete-material', associationId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const editingId = ref<number | null>(null)
const editingQuantity = ref<number>(0)
const quantityInput = ref<HTMLInputElement | null>(null)

const totalMaterialsCost = computed(() => {
  return props.materials.reduce((sum, item) => sum + calculateTotal(item), 0)
})

function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}

function formatQuantity(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(3)
}

function calculateTotal(item: CostItemMaterial): number {
  if (!item.material) return 0
  return item.material.price * item.quantity_per_unit
}

async function startEdit(item: CostItemMaterial) {
  editingId.value = item.id
  editingQuantity.value = item.quantity_per_unit
  await nextTick()
  quantityInput.value?.focus()
  quantityInput.value?.select()
}

function cancelEdit() {
  editingId.value = null
  editingQuantity.value = 0
}

function saveQuantity(item: CostItemMaterial) {
  if (editingQuantity.value <= 0) {
    alert('Quantity must be greater than 0')
    return
  }
  
  if (editingQuantity.value !== item.quantity_per_unit) {
    emit('update-quantity', item.id, editingQuantity.value)
  }
  
  cancelEdit()
}

function handleDelete(item: CostItemMaterial) {
  emit('delete-material', item.id)
}
</script>

<style scoped>
.materials-table {
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
  padding: 2rem;
  text-align: center;
  color: #6c757d;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  border: 1px dashed #dee2e6;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}

.table thead {
  background-color: #f8f9fa;
}

.table th,
.table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.table th {
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  color: #495057;
}

.table tbody tr:hover {
  background-color: #f8f9fa;
}

.table tbody tr:last-child td {
  border-bottom: 1px solid #dee2e6;
}

.table tfoot {
  background-color: #f8f9fa;
  font-weight: 600;
}

.table tfoot td {
  border-bottom: none;
}

.text-right {
  text-align: right;
}

.actions-column {
  width: 100px;
  text-align: center;
}

.quantity-cell {
  cursor: pointer;
  display: block;
  padding: 0.25rem;
}

.quantity-cell:hover {
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

.quantity-input {
  width: 80px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #007bff;
  border-radius: 0.25rem;
  text-align: right;
}

.quantity-input:focus {
  outline: none;
  border-color: #0056b3;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0 0.125rem;
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

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c82333;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.icon {
  font-weight: bold;
  margin-right: 0.25rem;
}
</style>
