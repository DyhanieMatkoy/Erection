<template>
  <div class="demo-container">
    <h1>Cost Items Table Demo</h1>
    <p class="description">
      This demo shows the CostItemsTable component with sample data.
    </p>

    <div class="demo-section">
      <CostItemsTable
        :cost-items="costItems"
        :has-materials="hasMaterials"
        @add-cost-item="handleAddCostItem"
        @delete-cost-item="handleDeleteCostItem"
      />
    </div>

    <div class="debug-section">
      <h3>Debug Info</h3>
      <pre>{{ debugInfo }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import CostItemsTable from '@/components/work/CostItemsTable.vue'
import type { CostItemMaterial, CostItem } from '@/types/models'

// Sample data
const costItems = ref<CostItemMaterial[]>([
  {
    id: 1,
    work_id: 1,
    cost_item_id: 101,
    material_id: null,
    quantity_per_unit: 0,
    cost_item: {
      id: 101,
      parent_id: null,
      code: 'CI-001',
      description: 'Labor - Skilled Workers',
      is_folder: false,
      price: 500.00,
      unit_id: 1,
      unit_name: 'hour',
      labor_coefficient: 2.5,
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    }
  },
  {
    id: 2,
    work_id: 1,
    cost_item_id: 102,
    material_id: null,
    quantity_per_unit: 0,
    cost_item: {
      id: 102,
      parent_id: null,
      code: 'CI-002',
      description: 'Equipment Rental',
      is_folder: false,
      price: 200.00,
      unit_id: 1,
      unit_name: 'hour',
      labor_coefficient: 0.5,
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    }
  },
  {
    id: 3,
    work_id: 1,
    cost_item_id: 103,
    material_id: null,
    quantity_per_unit: 0,
    cost_item: {
      id: 103,
      parent_id: null,
      code: 'CI-003',
      description: 'Transportation',
      is_folder: false,
      price: 150.00,
      unit_id: 2,
      unit_name: 'km',
      labor_coefficient: 0.0,
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    }
  }
])

// Track which cost items have materials
const costItemsWithMaterials = ref<Set<number>>(new Set([102])) // CI-002 has materials

// Methods
function hasMaterials(costItemId: number): boolean {
  return costItemsWithMaterials.value.has(costItemId)
}

function handleAddCostItem(costItem: CostItem) {
  console.log('Adding cost item:', costItem)
  
  // Create new association
  const newAssociation: CostItemMaterial = {
    id: Date.now(),
    work_id: 1,
    cost_item_id: costItem.id,
    material_id: null,
    quantity_per_unit: 0,
    cost_item: costItem
  }
  
  costItems.value.push(newAssociation)
  alert(`Added cost item: ${costItem.description}`)
}

function handleDeleteCostItem(costItemId: number) {
  console.log('Deleting cost item:', costItemId)
  
  const index = costItems.value.findIndex(item => item.cost_item_id === costItemId)
  if (index !== -1) {
    const deleted = costItems.value.splice(index, 1)[0]
    alert(`Deleted cost item: ${deleted?.cost_item?.description}`)
  }
}

// Debug info
const debugInfo = computed(() => ({
  totalCostItems: costItems.value.length,
  costItemIds: costItems.value.map(item => item.cost_item_id),
  costItemsWithMaterials: Array.from(costItemsWithMaterials.value)
}))
</script>

<style scoped>
.demo-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #212529;
  margin-bottom: 0.5rem;
}

.description {
  color: #6c757d;
  margin-bottom: 2rem;
}

.demo-section {
  background-color: white;
  padding: 2rem;
  border-radius: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.debug-section {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #dee2e6;
}

.debug-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.125rem;
  color: #495057;
}

.debug-section pre {
  background-color: white;
  padding: 1rem;
  border-radius: 0.25rem;
  border: 1px solid #dee2e6;
  overflow-x: auto;
  font-size: 0.875rem;
  margin: 0;
}
</style>
