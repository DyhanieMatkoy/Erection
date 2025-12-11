<template>
  <div class="cost-items-table">
    <div class="table-header">
      <h3>Cost Items</h3>
      <button @click="showAddDialog = true" class="btn btn-primary btn-sm">
        <span class="icon">+</span> Add Cost Item
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="costItems.length === 0" class="empty-state">
      <p>No cost items added yet.</p>
      <p class="hint">Click "Add Cost Item" to add cost items to this work.</p>
    </div>

    <!-- Cost Items Table -->
    <table v-else class="table">
      <thead>
        <tr>
          <th>Code</th>
          <th>Description</th>
          <th>Unit</th>
          <th class="text-right">Price</th>
          <th class="text-right">Labor Coefficient</th>
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
              :title="getDeleteTooltip(item.cost_item_id)"
            >
              🗑
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Cost Item List Form Dialog -->
    <CostItemListForm
      :is-open="showAddDialog"
      :existing-cost-item-ids="existingCostItemIds"
      :allow-folders="false"
      @close="showAddDialog = false"
      @select="handleCostItemSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import CostItemListForm from '@/components/common/CostItemListForm.vue'
import type { CostItemMaterial, CostItem } from '@/types/models'

interface Props {
  costItems: CostItemMaterial[]
  hasMaterials: (costItemId: number) => boolean
}

interface Emits {
  (e: 'add-cost-item', costItem: CostItem): void
  (e: 'delete-cost-item', costItemId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// State
const showAddDialog = ref(false)

// Computed
const existingCostItemIds = computed(() => {
  return props.costItems
    .map(item => item.cost_item_id)
    .filter(id => id !== undefined) as number[]
})

// Methods
function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}

function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(2)
}

function getDeleteTooltip(costItemId: number): string {
  if (props.hasMaterials(costItemId)) {
    return 'Cannot delete: has associated materials. Delete materials first.'
  }
  return 'Delete cost item'
}

function handleCostItemSelected(costItem: CostItem) {
  emit('add-cost-item', costItem)
  showAddDialog.value = false
}

function handleDelete(item: CostItemMaterial) {
  if (!item.cost_item_id) {
    return
  }

  // Check if cost item has materials
  if (props.hasMaterials(item.cost_item_id)) {
    alert('Cannot delete cost item: it has associated materials. Delete materials first.')
    return
  }

  // Show confirmation dialog
  const costItemName = item.cost_item?.description || 'this cost item'
  if (confirm(`Are you sure you want to delete "${costItemName}" from this work?`)) {
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
  color: #212529;
}

.empty-state {
  padding: 3rem 2rem;
  text-align: center;
  color: #6c757d;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  border: 2px dashed #dee2e6;
}

.empty-state p {
  margin: 0.5rem 0;
}

.empty-state .hint {
  font-size: 0.875rem;
  color: #868e96;
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
  letter-spacing: 0.5px;
}

.table tbody tr {
  transition: background-color 0.2s;
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
  width: 100px;
  text-align: center;
}

/* Button Styles */
.btn {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
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
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

.btn-danger {
  background-color: #dc3545;
  color: white;
  padding: 0.25rem 0.5rem;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c82333;
  box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.icon {
  font-weight: bold;
  margin-right: 0.25rem;
  font-size: 1rem;
}
</style>
