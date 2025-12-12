import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useWorkComposition } from '../useWorkComposition'
import { workCompositionApi } from '@/api/costs-materials'
import type { WorkComposition, Work } from '@/types/models'

// Mock the API modules
vi.mock('@/api/costs-materials', () => ({
  workCompositionApi: {
    getComposition: vi.fn(),
    addCostItem: vi.fn(),
    removeCostItem: vi.fn(),
    addMaterial: vi.fn(),
    updateMaterialQuantity: vi.fn(),
    changeMaterialCostItem: vi.fn(),
    removeMaterial: vi.fn(),
  },
}))

vi.mock('@/api/references', () => ({
  getWork: vi.fn(),
  updateWork: vi.fn(),
}))

describe('useWorkComposition', () => {
  const mockWorkId = 1
  
  const mockWork: Work = {
    id: 1,
    name: 'Test Work',
    code: '1.01',
    unit: 'м²',
    price: 1000,
    labor_rate: 2.5,
    parent_id: null,
    is_group: false,
    is_deleted: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  }
  
  const mockComposition: WorkComposition = {
    work_id: 1,
    work_name: 'Test Work',
    work_code: '1.01',
    work_unit: 'м²',
    work_price: 1000,
    work_labor_rate: 2.5,
    cost_items: [
      {
        id: 1,
        work_id: 1,
        cost_item_id: 10,
        material_id: null,
        quantity_per_unit: 0,
        cost_item: {
          id: 10,
          code: 'CI001',
          description: 'Labor',
          price: 500,
          unit_name: 'час',
          labor_coefficient: 2.5,
          is_folder: false,
          parent_id: null,
          marked_for_deletion: false,
          created_at: '2024-01-01',
          modified_at: '2024-01-01',
        },
      },
    ],
    materials: [
      {
        id: 2,
        work_id: 1,
        cost_item_id: 10,
        material_id: 20,
        quantity_per_unit: 0.5,
        cost_item: {
          id: 10,
          code: 'CI001',
          description: 'Labor',
          price: 500,
          unit_name: 'час',
          labor_coefficient: 2.5,
          is_folder: false,
          parent_id: null,
          marked_for_deletion: false,
          created_at: '2024-01-01',
          modified_at: '2024-01-01',
        },
        material: {
          id: 20,
          code: 'M001',
          description: 'Cement',
          price: 100,
          unit: 'т',
          unit_id: 5,
          unit_name: 'т',
          marked_for_deletion: false,
          created_at: '2024-01-01',
          modified_at: '2024-01-01',
        },
      },
    ],
    total_cost_items_price: 500,
    total_materials_cost: 50,
    total_cost: 550,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('loadWork', () => {
    it('should load work and composition successfully', async () => {
      const { getWork } = await import('@/api/references')
      vi.mocked(getWork).mockResolvedValue(mockWork)
      vi.mocked(workCompositionApi.getComposition).mockResolvedValue(mockComposition)

      const { loadWork, work, costItems, materials, loading, error } = useWorkComposition(mockWorkId)

      expect(loading.value).toBe(false)
      expect(work.value).toBeNull()

      await loadWork()

      expect(getWork).toHaveBeenCalledWith(mockWorkId)
      expect(workCompositionApi.getComposition).toHaveBeenCalledWith(mockWorkId)
      expect(work.value).toEqual(mockWork)
      expect(costItems.value).toEqual(mockComposition.cost_items)
      expect(materials.value).toEqual(mockComposition.materials)
      expect(loading.value).toBe(false)
      expect(error.value).toBeNull()
    })

    it('should handle load error', async () => {
      const { getWork } = await import('@/api/references')
      const errorMessage = 'Failed to load'
      vi.mocked(getWork).mockRejectedValue(new Error(errorMessage))

      const { loadWork, work, loading, error } = useWorkComposition(mockWorkId)

      try {
        await loadWork()
      } catch (e) {
        // Expected to throw
      }

      expect(work.value).toBeNull()
      expect(loading.value).toBe(false)
      expect(error.value).toBe(errorMessage)
    })
  })

  describe('saveWork', () => {
    it('should save work successfully', async () => {
      const { updateWork } = await import('@/api/references')
      const updatedWork = { ...mockWork, name: 'Updated Work' }
      vi.mocked(updateWork).mockResolvedValue(updatedWork)

      const { saveWork, work } = useWorkComposition(mockWorkId)
      work.value = mockWork

      const result = await saveWork({ name: 'Updated Work' })

      expect(result).toBe(true)
      expect(updateWork).toHaveBeenCalledWith(mockWorkId, { name: 'Updated Work' })
      expect(work.value).toEqual(updatedWork)
    })

    it('should handle save error', async () => {
      const { updateWork } = await import('@/api/references')
      vi.mocked(updateWork).mockRejectedValue(new Error('Failed'))

      const { saveWork, error } = useWorkComposition(mockWorkId)

      const result = await saveWork({ name: 'Updated Work' })

      expect(result).toBe(false)
      expect(error.value).toBe('Failed')
    })
  })

  describe('addCostItem', () => {
    it('should add cost item successfully', async () => {
      const newAssociation = mockComposition.cost_items[0]
      vi.mocked(workCompositionApi.addCostItem).mockResolvedValue(newAssociation as any)

      const { addCostItem, costItems } = useWorkComposition(mockWorkId)

      const result = await addCostItem(10)

      expect(result).toBe(true)
      expect(workCompositionApi.addCostItem).toHaveBeenCalledWith(mockWorkId, 10)
      expect(costItems.value).toContainEqual(newAssociation)
    })

    it('should handle add cost item error', async () => {
      vi.mocked(workCompositionApi.addCostItem).mockRejectedValue(new Error('Failed'))

      const { addCostItem, error } = useWorkComposition(mockWorkId)

      const result = await addCostItem(10)

      expect(result).toBe(false)
      expect(error.value).toBe('Failed')
    })
  })

  describe('removeCostItem', () => {
    it('should remove cost item successfully', async () => {
      vi.mocked(workCompositionApi.removeCostItem).mockResolvedValue()

      const { removeCostItem, costItems } = useWorkComposition(mockWorkId)
      costItems.value = [...mockComposition.cost_items]

      const result = await removeCostItem(10)

      expect(result).toBe(true)
      expect(workCompositionApi.removeCostItem).toHaveBeenCalledWith(mockWorkId, 10)
      expect(costItems.value).toHaveLength(0)
    })
  })

  describe('addMaterial', () => {
    it('should add material successfully', async () => {
      const newMaterial = mockComposition.materials[0]
      vi.mocked(workCompositionApi.addMaterial).mockResolvedValue(newMaterial as any)

      const { addMaterial, materials } = useWorkComposition(mockWorkId)

      const result = await addMaterial(10, 20, 0.5)

      expect(result).toBe(true)
      expect(workCompositionApi.addMaterial).toHaveBeenCalledWith(mockWorkId, {
        cost_item_id: 10,
        material_id: 20,
        quantity_per_unit: 0.5,
      })
      expect(materials.value).toContainEqual(newMaterial)
    })
  })

  describe('updateMaterialQuantity', () => {
    it('should update material quantity successfully', async () => {
      const updatedMaterial = { ...mockComposition.materials[0], quantity_per_unit: 1.5 }
      vi.mocked(workCompositionApi.updateMaterialQuantity).mockResolvedValue(updatedMaterial as any)

      const { updateMaterialQuantity, materials } = useWorkComposition(mockWorkId)
      materials.value = [...mockComposition.materials]

      const result = await updateMaterialQuantity(2, 1.5)

      expect(result).toBe(true)
      expect(workCompositionApi.updateMaterialQuantity).toHaveBeenCalledWith(mockWorkId, 2, 1.5)
      expect(materials.value[0]!.quantity_per_unit).toBe(1.5)
    })
  })

  describe('changeMaterialCostItem', () => {
    it('should change material cost item successfully', async () => {
      const updatedMaterial = { ...mockComposition.materials[0], cost_item_id: 15 }
      vi.mocked(workCompositionApi.changeMaterialCostItem).mockResolvedValue(updatedMaterial as any)

      const { changeMaterialCostItem, materials } = useWorkComposition(mockWorkId)
      materials.value = [...mockComposition.materials]

      const result = await changeMaterialCostItem(2, 15)

      expect(result).toBe(true)
      expect(workCompositionApi.changeMaterialCostItem).toHaveBeenCalledWith(mockWorkId, 2, 15)
      expect(materials.value[0]!.cost_item_id).toBe(15)
    })
  })

  describe('removeMaterial', () => {
    it('should remove material successfully', async () => {
      vi.mocked(workCompositionApi.removeMaterial).mockResolvedValue()

      const { removeMaterial, materials } = useWorkComposition(mockWorkId)
      materials.value = [...mockComposition.materials]

      const result = await removeMaterial(2)

      expect(result).toBe(true)
      expect(workCompositionApi.removeMaterial).toHaveBeenCalledWith(mockWorkId, 2)
      expect(materials.value).toHaveLength(0)
    })
  })

  describe('computed properties', () => {
    it('should calculate total cost from cost items and materials', () => {
      const { costItems, materials, totalCost } = useWorkComposition(mockWorkId)
      
      costItems.value = mockComposition.cost_items
      materials.value = mockComposition.materials

      // Cost items: 500
      // Materials: 100 * 0.5 = 50
      // Total: 550
      expect(totalCost.value).toBe(550)
    })

    it('should return 0 for empty composition', () => {
      const { totalCost } = useWorkComposition(mockWorkId)

      expect(totalCost.value).toBe(0)
    })
  })

  describe('helper functions', () => {
    it('should check if cost item has materials', () => {
      const { costItemHasMaterials, materials } = useWorkComposition(mockWorkId)
      materials.value = mockComposition.materials

      expect(costItemHasMaterials(10)).toBe(true)
      expect(costItemHasMaterials(99)).toBe(false)
    })

    it('should calculate material total cost', () => {
      const { calculateMaterialTotal } = useWorkComposition(mockWorkId)

      const material = mockComposition.materials[0]
      const total = calculateMaterialTotal(material as any)

      expect(total).toBe(50) // 100 * 0.5
    })

    it('should return 0 for material without material object', () => {
      const { calculateMaterialTotal } = useWorkComposition(mockWorkId)

      const material = { ...mockComposition.materials[0], material: undefined }
      const total = calculateMaterialTotal(material as any)

      expect(total).toBe(0)
    })
  })
})
