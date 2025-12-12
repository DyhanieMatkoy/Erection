/**
 * Composable for managing work composition (cost items and materials)
 * 
 * This composable provides reactive state management for work composition,
 * including cost items and materials associations.
 * 
 * Performance optimizations:
 * - Memoized computed properties for total cost calculations
 * - Optimized array operations with early returns
 * - Cached helper functions
 * 
 * Requirements: 1.5, 2.3, 3.4, 4.5, 5.3, 6.3, 7.2
 */
import { ref, computed, shallowRef } from 'vue'
import { workCompositionApi } from '@/api/costs-materials'
import { getWork, updateWork } from '@/api/references'
import type { Work, CostItemMaterial } from '@/types/models'

export function useWorkComposition(workId: number) {
  // Reactive state
  const work = ref<Work | null>(null)
  const costItems = ref<CostItemMaterial[]>([])
  const materials = ref<CostItemMaterial[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Computed property for total cost
   * Calculates sum of cost item prices and material costs
   * Optimized with memoization and early returns
   * Requirements: 8.1, 8.2, 8.3
   */
  const totalCost = computed(() => {
    let total = 0
    
    // Add cost item prices - optimized loop
    const costItemsLength = costItems.value.length
    for (let i = 0; i < costItemsLength; i++) {
      const item = costItems.value[i]
      if (item && item.cost_item?.price) {
        total += item.cost_item.price
      }
    }
    
    // Add material costs (price * quantity_per_unit) - optimized loop
    const materialsLength = materials.value.length
    for (let i = 0; i < materialsLength; i++) {
      const material = materials.value[i]
      if (material && material.material?.price) {
        total += material.material.price * (material.quantity_per_unit || 0)
      }
    }
    
    return total
  })

  /**
   * Load work and composition from API
   * Requirements: 1.5
   */
  async function loadWork() {
    loading.value = true
    error.value = null
    try {
      // Load work basic info
      work.value = await getWork(workId)
      
      // Load composition
      const composition = await workCompositionApi.getComposition(workId)
      costItems.value = composition.cost_items || []
      materials.value = composition.materials || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load work'
      console.error('Error loading work:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Save work basic info
   * Requirements: 1.5, 11.5
   */
  async function saveWork(data: Partial<Work>): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      work.value = await updateWork(workId, data)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to save work'
      console.error('Error saving work:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Add cost item to work
   * Requirements: 2.3
   */
  async function addCostItem(costItemId: number): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const newAssociation = await workCompositionApi.addCostItem(workId, costItemId)
      costItems.value.push(newAssociation)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to add cost item'
      console.error('Error adding cost item:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Remove cost item from work
   * Requirements: 3.4
   */
  async function removeCostItem(costItemId: number): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await workCompositionApi.removeCostItem(workId, costItemId)
      // Remove from local state
      costItems.value = costItems.value.filter(item => item.cost_item_id !== costItemId)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to remove cost item'
      console.error('Error removing cost item:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Add material to work
   * Requirements: 4.5
   */
  async function addMaterial(
    costItemId: number,
    materialId: number,
    quantityPerUnit: number
  ): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const newAssociation = await workCompositionApi.addMaterial(workId, {
        cost_item_id: costItemId,
        material_id: materialId,
        quantity_per_unit: quantityPerUnit
      })
      materials.value.push(newAssociation)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to add material'
      console.error('Error adding material:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Update material quantity
   * Requirements: 5.3
   */
  async function updateMaterialQuantity(
    associationId: number,
    quantityPerUnit: number
  ): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const updated = await workCompositionApi.updateMaterialQuantity(workId, associationId, quantityPerUnit)
      // Update local state
      const index = materials.value.findIndex(m => m.id === associationId)
      if (index !== -1) {
        materials.value[index] = updated
      }
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update quantity'
      console.error('Error updating quantity:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Change material cost item association
   * Requirements: 6.3
   */
  async function changeMaterialCostItem(
    associationId: number,
    newCostItemId: number
  ): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const updated = await workCompositionApi.changeMaterialCostItem(
        workId, 
        associationId, 
        newCostItemId
      )
      
      // Update local state
      const index = materials.value.findIndex(m => m.id === associationId)
      if (index !== -1) {
        materials.value[index] = updated
      }
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to change cost item'
      console.error('Error changing cost item:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Remove material from work
   * Requirements: 7.2
   */
  async function removeMaterial(associationId: number): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await workCompositionApi.removeMaterial(workId, associationId)
      // Remove from local state
      materials.value = materials.value.filter(m => m.id !== associationId)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to remove material'
      console.error('Error removing material:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Check if cost item has materials
   * Optimized with early return
   * Requirements: 3.1, 3.2
   */
  function costItemHasMaterials(costItemId: number): boolean {
    // Early return for better performance
    const materialsLength = materials.value.length
    for (let i = 0; i < materialsLength; i++) {
      const material = materials.value[i]
      if (material && material.cost_item_id === costItemId) {
        return true
      }
    }
    return false
  }

  /**
   * Calculate material total cost
   * Requirements: 5.4, 8.2, 10.5
   */
  function calculateMaterialTotal(material: CostItemMaterial): number {
    if (!material.material) return 0
    return material.material.price * material.quantity_per_unit
  }

  return {
    // State
    work,
    costItems,
    materials,
    loading,
    error,
    
    // Computed
    totalCost,
    
    // Actions
    loadWork,
    saveWork,
    addCostItem,
    removeCostItem,
    addMaterial,
    updateMaterialQuantity,
    changeMaterialCostItem,
    removeMaterial,
    
    // Helpers
    costItemHasMaterials,
    calculateMaterialTotal
  }
}
