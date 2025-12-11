<template>
  <div class="cost-items-table">
    <div class="table-header">
      <h3>Cost Items</h3>
      <button @click="$emit('add-cost-item')" class="btn btn-primary btn-sm">
        <span class="icon">+</span> Add
      </button>
    </div>

    <div v-if="costItems.length === 0" class="empty-state">
      No cost items added yet. Click "Add" to add cost items to this work.
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Code</th>
          <th>Description</th>
          <th>Unit</th>
          <th class="text-right">Price</th>
          <th class="text-right">Labor</th>
          <th class="actions-column">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in costItems" :key="item.id">
          <td>{{ item.cost_item?.code || '-' }}</td>
          <td>{{ item.cost_item?.description || '-' }}</td>
          <td>{{ item.cost_item?.unit_name || '-' }}</td>
          <td class="text-right">{{ formatPrice(item.cost_item?.price) }}</td>
          <td class="text-right">{{ formatNumber(item.cost_item?.labor_coefficient) }}</td>
          <td class="actions-column">
            <button
              @click="handleDelete(item)"
              class="btn btn-sm btn-danger"
              :disabled="hasMaterials(item.cost_item_id)"
              :title="hasMaterials(item.cost_item_id) ? 'Cannot delete: has associated materials' : 'Delete cost item'"
            >
              🗑
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { CostItemMaterial } from '@/types/models'

interface Props {
  costItems: CostItemMaterial[]
  hasMaterials: (costItemId: number) => boolean
}

interface Emits {
  (e: 'add-cost-item'): void
  (e: 'delete-cost-item', costItemId: number): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}

function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(2)
}

function handleDelete(item: CostItemMaterial) {
  if (item.cost_item_id) {
    emit('delete-cost-item', item.cost_item_id)
  }
}
</script>

<style scoped>
.cost-items-table {
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
  border-bottom: none;
}

.text-right {
  text-align: right;
}

.actions-column {
  width: 80px;
  text-align: center;
}

.btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
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
