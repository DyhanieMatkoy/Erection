<template>
  <div class="work-composition-panel">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading composition...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <button @click="loadComposition" class="btn btn-primary">Retry</button>
    </div>

    <div v-else>
      <!-- Cost Items Table -->
      <CostItemsTable
        :cost-items="costItems"
        :has-materials="costItemHasMaterials"
        @add-cost-item="showAddCostItemDialog"
        @delete-cost-item="handleDeleteCostItem"
      />

      <!-- Materials Table -->
      <MaterialsTable
        :materials="materials"
        @add-material="showAddMaterialDialog"
        @update-quantity="handleUpdateQuantity"
        @delete-material="handleDeleteMaterial"
      />

      <!-- Total Cost Display -->
      <div class="total-cost">
        <div class="total-label">Total Work Cost:</div>
        <div class="total-value">{{ formatPrice(totalCost) }} руб.</div>
      </div>
    </div>

    <!-- Dialogs -->
    <CostItemSelectorDialog
      :is-open="showCostItemDialog"
      :existing-cost-item-ids="existingCostItemIds"
      @close="showCostItemDialog = false"
      @select="handleCostItemSelected"
    />

    <MaterialSelectorDialog
      :is-open="showMaterialDialog"
      :available-cost-items="costItems"
      :existing-materials="materials"
      @close="showMaterialDialog = false"
      @select="handleMaterialSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useWorkComposition } from '@/composables/useWorkComposition'
import CostItemsTable from './CostItemsTable.vue'
import MaterialsTable from './MaterialsTable.vue'
import CostItemSelectorDialog from './CostItemSelectorDialog.vue'
import MaterialSelectorDialog from './MaterialSelectorDialog.vue'
import type { CostItem } from '@/types/models'

interface Props {
  workId: number
}

const props = defineProps<Props>()

const {
  work,
  loading,
  error,
  costItems,
  materials,
  totalCost,
  loadWork,
  addCostItem,
  removeCostItem,
  addMaterial,
  updateMaterialQuantity,
  removeMaterial,
  costItemHasMaterials
} = useWorkComposition(props.workId)

const showCostItemDialog = ref(false)
const showMaterialDialog = ref(false)

const existingCostItemIds = computed(() => {
  return costItems.value.map(item => item.cost_item_id).filter(id => id !== undefined) as number[]
})

onMounted(() => {
  loadWork()
})

function formatPrice(price: number): string {
  return price.toFixed(2)
}

// Cost Item handlers
function showAddCostItemDialog() {
  showCostItemDialog.value = true
}

async function handleCostItemSelected(costItem: CostItem) {
  const success = await addCostItem(costItem.id)
  if (!success && error.value) {
    alert(`Error: ${error.value}`)
  }
}

async function handleDeleteCostItem(costItemId: number) {
  if (costItemHasMaterials(costItemId)) {
    alert('Cannot delete cost item: it has associated materials. Delete materials first.')
    return
  }

  if (confirm('Delete this cost item from the work?')) {
    const success = await removeCostItem(costItemId)
    if (!success && error.value) {
      alert(`Error: ${error.value}`)
    }
  }
}

// Material handlers
function showAddMaterialDialog() {
  if (costItems.value.length === 0) {
    alert('Please add at least one cost item first before adding materials.')
    return
  }
  showMaterialDialog.value = true
}

async function handleMaterialSelected(data: { costItemId: number; materialId: number; quantity: number }) {
  const success = await addMaterial(data.costItemId, data.materialId, data.quantity)
  if (!success && error.value) {
    alert(`Error: ${error.value}`)
  }
}

async function handleUpdateQuantity(associationId: number, quantity: number) {
  const success = await updateMaterialQuantity(associationId, quantity)
  if (!success && error.value) {
    alert(`Error: ${error.value}`)
  }
}

async function handleDeleteMaterial(associationId: number) {
  if (confirm('Delete this material from the work?')) {
    const success = await removeMaterial(associationId)
    if (!success && error.value) {
      alert(`Error: ${error.value}`)
    }
  }
}
</script>

<style scoped>
.work-composition-panel {
  padding: 1.5rem;
  background-color: #ffffff;
  border-radius: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
}

.total-cost {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  margin-top: 1rem;
}

.total-label {
  font-size: 1.125rem;
  font-weight: 600;
  margin-right: 1rem;
  color: #495057;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #007bff;
}

.btn {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}
</style>
