<template>
  <div class="demo-container">
    <h1>Materials Table Demo</h1>
    
    <div class="demo-section">
      <h2>Work Information</h2>
      <div class="info-card">
        <p><strong>Work:</strong> {{ workName }}</p>
        <p><strong>Total Materials Cost:</strong> {{ formatPrice(totalMaterialsCost) }}</p>
      </div>
    </div>

    <div class="demo-section">
      <MaterialsTable
        :materials="materials"
        :cost-items="costItems"
        @add-material="handleAddMaterial"
        @update-quantity="handleUpdateQuantity"
        @change-cost-item="handleChangeCostItem"
        @delete-material="handleDeleteMaterial"
      />
    </div>

    <div class="demo-section">
      <h2>Debug Info</h2>
      <div class="debug-info">
        <h3>Cost Items ({{ costItems.length }})</h3>
        <pre>{{ JSON.stringify(costItems, null, 2) }}</pre>
        
        <h3>Materials ({{ materials.length }})</h3>
        <pre>{{ JSON.stringify(materials, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import MaterialsTable from '@/components/work/MaterialsTable.vue'
import type { CostItemMaterial } from '../types/models'

// Mock data
const workName = ref('Штукатурка стен')

// Mock cost items (already added to work)
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
      description: 'Труд рабочих',
      is_folder: false,
      price: 500,
      unit_id: 1,
      unit_name: 'час',
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
      description: 'Аренда оборудования',
      is_folder: false,
      price: 200,
      unit_id: 1,
      unit_name: 'час',
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
      description: 'Материалы',
      is_folder: false,
      price: 0,
      unit_id: 2,
      unit_name: 'руб',
      labor_coefficient: 0,
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    }
  }
])

// Mock materials (already added to work)
const materials = ref<CostItemMaterial[]>([
  {
    id: 10,
    work_id: 1,
    cost_item_id: 103,
    material_id: 201,
    quantity_per_unit: 0.015,
    cost_item: {
      id: 103,
      parent_id: null,
      code: 'CI-003',
      description: 'Материалы',
      is_folder: false,
      price: 0,
      unit_id: 2,
      unit_name: 'руб',
      labor_coefficient: 0,
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    },
    material: {
      id: 201,
      code: 'M-001',
      description: 'Цемент М400',
      price: 5000,
      unit_id: 3,
      unit_name: 'т',
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    }
  },
  {
    id: 11,
    work_id: 1,
    cost_item_id: 103,
    material_id: 202,
    quantity_per_unit: 0.05,
    cost_item: {
      id: 103,
      parent_id: null,
      code: 'CI-003',
      description: 'Материалы',
      is_folder: false,
      price: 0,
      unit_id: 2,
      unit_name: 'руб',
      labor_coefficient: 0,
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    },
    material: {
      id: 202,
      code: 'M-002',
      description: 'Песок речной',
      price: 800,
      unit_id: 3,
      unit_name: 'т',
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    }
  }
])

// Computed
const totalMaterialsCost = computed(() => {
  return materials.value.reduce((sum, item) => {
    const price = item.material?.price || 0
    const quantity = item.quantity_per_unit || 0
    return sum + (price * quantity)
  }, 0)
})

// Methods
function formatPrice(price: number): string {
  return price.toFixed(2)
}

function handleAddMaterial(data: { costItemId: number; materialId: number; quantity: number }) {
  console.log('Add material:', data)
  
  // Find the cost item
  const costItem = costItems.value.find(ci => ci.cost_item_id === data.costItemId)
  if (!costItem) {
    alert('Cost item not found')
    return
  }
  
  // Create mock material (in real app, would fetch from API)
  const newMaterial: CostItemMaterial = {
    id: Date.now(), // Mock ID
    work_id: 1,
    cost_item_id: data.costItemId,
    material_id: data.materialId,
    quantity_per_unit: data.quantity,
    cost_item: costItem.cost_item,
    material: {
      id: data.materialId,
      code: `M-${data.materialId}`,
      description: `Material ${data.materialId}`,
      price: 1000,
      unit_id: 3,
      unit_name: 'т',
      marked_for_deletion: false,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString()
    }
  }
  
  materials.value.push(newMaterial)
  alert(`Material added successfully!\nCost Item: ${costItem.cost_item?.description}\nQuantity: ${data.quantity}`)
}

function handleUpdateQuantity(data: { id: number; quantity: number }) {
  console.log('Update quantity:', data)
  
  const material = materials.value.find(m => m.id === data.id)
  if (material) {
    material.quantity_per_unit = data.quantity
    alert(`Quantity updated to ${data.quantity}`)
  }
}

function handleChangeCostItem(data: { id: number; newCostItemId: number }) {
  console.log('Change cost item:', data)
  
  const material = materials.value.find(m => m.id === data.id)
  const newCostItem = costItems.value.find(ci => ci.cost_item_id === data.newCostItemId)
  
  if (material && newCostItem) {
    material.cost_item_id = data.newCostItemId
    material.cost_item = newCostItem.cost_item
    alert(`Cost item changed to: ${newCostItem.cost_item?.description}`)
  }
}

function handleDeleteMaterial(id: number) {
  console.log('Delete material:', id)
  
  const index = materials.value.findIndex(m => m.id === id)
  if (index !== -1) {
    const material = materials.value[index]
    const materialName = material.material?.description || 'Unknown'
    materials.value.splice(index, 1)
    alert(`Material "${materialName}" deleted`)
  }
}
</script>

<style scoped>
.demo-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
  color: #212529;
}

h2 {
  margin-bottom: 1rem;
  color: #495057;
  font-size: 1.25rem;
}

.demo-section {
  margin-bottom: 3rem;
}

.info-card {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 1rem;
}

.info-card p {
  margin: 0.5rem 0;
}

.debug-info {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 1rem;
}

.debug-info h3 {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  font-size: 1rem;
  color: #495057;
}

.debug-info h3:first-child {
  margin-top: 0;
}

.debug-info pre {
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 1rem;
  overflow-x: auto;
  font-size: 0.875rem;
  max-height: 300px;
  overflow-y: auto;
}
</style>
