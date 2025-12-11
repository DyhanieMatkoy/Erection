<template>
  <div class="materials-table">
    <div class="table-header">
      <h3>Materials</h3>
      <button @click="showAddDialog = true" class="btn btn-primary btn-sm">
        <span class="icon">+</span> Add Material
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="materials.length === 0" class="empty-state">
      <p>No materials added yet.</p>
      <p class="hint">Click "Add Material" to add materials to this work.</p>
    </div>

    <!-- Materials Table -->
    <table v-else class="table">
      <thead>
        <tr>
          <th>Cost Item</th>
          <th>Code</th>
          <th>Description</th>
          <th>Unit</th>
          <th class="text-right">Price</th>
          <th class="text-right">Quantity</th>
          <th class="text-right">Total</th>
          <th class="actions-column">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in materials" :key="item.id">
          <td>
            <button
              @click="showCostItemSelector(item)"
              class="link-button"
              :title="'Change cost item for this material'"
            >
              {{ item.cost_item?.description || '-' }}
            </button>
          </td>
          <td>{{ item.material?.code || '-' }}</td>
          <td>{{ item.material?.description || '-' }}</td>
          <td>{{ item.material?.unit_name || '-' }}</td>
          <td class="text-right">{{ formatPrice(item.material?.price) }}</td>
          <td class="text-right">
            <input
              v-if="editingQuantityId === item.id"
              v-model.number="editingQuantityValue"
              type="number"
              step="0.001"
              min="0.001"
              class="quantity-input"
              :class="{ 'is-invalid': editingQuantityValue <= 0 }"
              @blur="saveQuantity(item)"
              @keyup.enter="saveQuantity(item)"
              @keyup.esc="cancelQuantityEdit"
              ref="quantityInput"
              title="Enter quantity (must be > 0). Press Enter to save, Esc to cancel"
            />
            <span
              v-else
              @dblclick="startQuantityEdit(item)"
              class="quantity-display"
              title="Double-click to edit quantity"
            >
              {{ formatNumber(item.quantity_per_unit) }}
            </span>
          </td>
          <td class="text-right">{{ formatPrice(calculateTotal(item)) }}</td>
          <td class="actions-column">
            <button
              v-if="editingQuantityId !== item.id"
              @click="startQuantityEdit(item)"
              class="btn btn-sm btn-secondary"
              title="Edit quantity"
            >
              ✏️
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
    </table>

    <!-- Material Selector Dialog -->
    <MaterialSelectorDialog
      :is-open="showAddDialog"
      :available-cost-items="costItems"
      :existing-materials="materials"
      @close="showAddDialog = false"
      @select="handleMaterialSelected"
    />

    <!-- Cost Item Selector Dialog for Reassignment -->
    <div v-if="showCostItemDialog" class="dialog-overlay" @click.self="closeCostItemDialog">
      <div class="dialog dialog-small">
        <div class="dialog-header">
          <h2>Change Cost Item</h2>
          <button @click="closeCostItemDialog" class="close-btn">&times;</button>
        </div>

        <div class="dialog-body">
          <p class="help-text">Select a cost item to reassign this material to:</p>
          
          <div class="cost-items-list">
            <div
              v-for="item in costItems"
              :key="item.id"
              :class="['cost-item-row', { 
                'cost-item-selected': selectedCostItemId === item.cost_item_id 
              }]"
              @click="selectedCostItemId = item.cost_item_id"
            >
              <div class="cost-item-content">
                <div class="cost-item-code">{{ item.cost_item?.code || '-' }}</div>
                <div class="cost-item-description">{{ item.cost_item?.description || '-' }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="dialog-footer">
          <button @click="closeCostItemDialog" class="btn btn-secondary">Cancel</button>
          <button 
            @click="confirmCostItemChange" 
            class="btn btn-primary"
            :disabled="!selectedCostItemId"
          >
            Change Cost Item
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import MaterialSelectorDialog from '@/components/common/MaterialSelectorDialog.vue'
import type { CostItemMaterial } from '@/types/models'

interface Props {
  materials: CostItemMaterial[]
  costItems: CostItemMaterial[]
}

interface Emits {
  (e: 'add-material', data: { costItemId: number; materialId: number; quantity: number }): void
  (e: 'update-quantity', data: { id: number; quantity: number }): void
  (e: 'change-cost-item', data: { id: number; newCostItemId: number }): void
  (e: 'delete-material', id: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// State
const showAddDialog = ref(false)
const showCostItemDialog = ref(false)
const editingQuantityId = ref<number | null>(null)
const editingQuantityValue = ref<number>(0)
const previousQuantityValue = ref<number>(0)
const changingCostItemFor = ref<CostItemMaterial | null>(null)
const selectedCostItemId = ref<number | null>(null)
const quantityInput = ref<HTMLInputElement | null>(null)

// Methods
function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}

function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(3)
}

function calculateTotal(item: CostItemMaterial): number {
  const price = item.material?.price || 0
  const quantity = item.quantity_per_unit || 0
  return price * quantity
}

function handleMaterialSelected(data: { costItemId: number; materialId: number; quantity: number }) {
  emit('add-material', data)
  showAddDialog.value = false
}

function startQuantityEdit(item: CostItemMaterial) {
  editingQuantityId.value = item.id
  editingQuantityValue.value = item.quantity_per_unit
  previousQuantityValue.value = item.quantity_per_unit
  
  // Focus the input after it's rendered
  nextTick(() => {
    const inputs = document.querySelectorAll('.quantity-input')
    const input = inputs[inputs.length - 1] as HTMLInputElement
    if (input) {
      input.focus()
      input.select()
    }
  })
}

function saveQuantity(item: CostItemMaterial) {
  if (editingQuantityId.value !== item.id) return
  
  // Validate quantity
  if (editingQuantityValue.value <= 0 || isNaN(editingQuantityValue.value)) {
    // Show error and revert
    editingQuantityValue.value = previousQuantityValue.value
    cancelQuantityEdit()
    // Emit error event that parent can handle
    return
  }
  
  // Only emit if value changed
  if (editingQuantityValue.value !== previousQuantityValue.value) {
    emit('update-quantity', {
      id: item.id,
      quantity: editingQuantityValue.value
    })
  }
  
  cancelQuantityEdit()
}

function cancelQuantityEdit() {
  editingQuantityId.value = null
  editingQuantityValue.value = 0
  previousQuantityValue.value = 0
}

function showCostItemSelector(item: CostItemMaterial) {
  changingCostItemFor.value = item
  selectedCostItemId.value = item.cost_item_id
  showCostItemDialog.value = true
}

function confirmCostItemChange() {
  if (changingCostItemFor.value && selectedCostItemId.value) {
    emit('change-cost-item', {
      id: changingCostItemFor.value.id,
      newCostItemId: selectedCostItemId.value
    })
  }
  closeCostItemDialog()
}

function closeCostItemDialog() {
  showCostItemDialog.value = false
  changingCostItemFor.value = null
  selectedCostItemId.value = null
}

function handleDelete(item: CostItemMaterial) {
  const materialName = item.material?.description || 'this material'
  if (confirm(`Are you sure you want to delete "${materialName}" from this work?`)) {
    emit('delete-material', item.id)
  }
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
  width: 120px;
  text-align: center;
}

/* Link Button for Cost Item */
.link-button {
  background: none;
  border: none;
  color: #007bff;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  font-size: inherit;
  text-align: left;
}

.link-button:hover {
  color: #0056b3;
}

/* Quantity Editing */
.quantity-display {
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.quantity-display:hover {
  background-color: #e9ecef;
}

.quantity-input {
  width: 100px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #007bff;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  text-align: right;
}

.quantity-input:focus {
  outline: none;
  border-color: #0056b3;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.quantity-input.is-invalid {
  border-color: #dc3545;
}

.quantity-input.is-invalid:focus {
  box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
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
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  padding: 0.25rem 0.5rem;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
  box-shadow: 0 2px 4px rgba(108, 117, 125, 0.3);
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

/* Cost Item Selector Dialog */
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
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.dialog-small {
  max-width: 500px;
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1.5rem;
  border-top: 1px solid #dee2e6;
}

.help-text {
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: #6c757d;
}

.cost-items-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}

.cost-item-row {
  display: flex;
  padding: 0.75rem;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cost-item-row:last-child {
  border-bottom: none;
}

.cost-item-row:hover {
  background-color: #f8f9fa;
}

.cost-item-row.cost-item-selected {
  background-color: #e7f3ff;
  border-left: 3px solid #007bff;
}

.cost-item-content {
  flex: 1;
  min-width: 0;
}

.cost-item-code {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.25rem;
}

.cost-item-description {
  color: #212529;
}
</style>
