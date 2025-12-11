/**
 * API client for Costs and Materials endpoints
 */
import apiClient from './client'
import type {
  Unit,
  CostItem,
  Material,
  CostItemMaterial,
  WorkComposition
} from '@/types/models'

// ============================================================================
// Units API
// ============================================================================

export const unitsApi = {
  /**
   * Get all units
   */
  async getAll(includeDeleted = false): Promise<Unit[]> {
    const response = await apiClient.get<Unit[]>('/units', {
      params: { include_deleted: includeDeleted }
    })
    return response.data
  },

  /**
   * Get unit by ID
   */
  async getById(id: number): Promise<Unit> {
    const response = await apiClient.get<Unit>(`/units/${id}`)
    return response.data
  },

  /**
   * Create new unit
   */
  async create(data: Omit<Unit, 'id' | 'marked_for_deletion' | 'created_at' | 'modified_at'>): Promise<Unit> {
    const response = await apiClient.post<Unit>('/units', data)
    return response.data
  },

  /**
   * Update unit
   */
  async update(id: number, data: Partial<Unit>): Promise<Unit> {
    const response = await apiClient.put<Unit>(`/units/${id}`, data)
    return response.data
  },

  /**
   * Delete unit
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/units/${id}`)
  }
}

// ============================================================================
// Cost Items API
// ============================================================================

export const costItemsApi = {
  /**
   * Get all cost items
   */
  async getAll(includeDeleted = false): Promise<CostItem[]> {
    const response = await apiClient.get<CostItem[]>('/cost-items', {
      params: { include_deleted: includeDeleted }
    })
    return response.data
  },

  /**
   * Get cost item by ID
   */
  async getById(id: number): Promise<CostItem> {
    const response = await apiClient.get<CostItem>(`/cost-items/${id}`)
    return response.data
  },

  /**
   * Create new cost item
   */
  async create(data: Omit<CostItem, 'id' | 'marked_for_deletion' | 'created_at' | 'modified_at'>): Promise<CostItem> {
    const response = await apiClient.post<CostItem>('/cost-items', data)
    return response.data
  },

  /**
   * Update cost item
   */
  async update(id: number, data: Partial<CostItem>): Promise<CostItem> {
    const response = await apiClient.put<CostItem>(`/cost-items/${id}`, data)
    return response.data
  },

  /**
   * Delete cost item
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/cost-items/${id}`)
  }
}

// ============================================================================
// Materials API
// ============================================================================

export const materialsApi = {
  /**
   * Get all materials
   */
  async getAll(includeDeleted = false): Promise<Material[]> {
    const response = await apiClient.get<Material[]>('/materials', {
      params: { include_deleted: includeDeleted }
    })
    return response.data
  },

  /**
   * Get material by ID
   */
  async getById(id: number): Promise<Material> {
    const response = await apiClient.get<Material>(`/materials/${id}`)
    return response.data
  },

  /**
   * Create new material
   */
  async create(data: Omit<Material, 'id' | 'marked_for_deletion' | 'created_at' | 'modified_at'>): Promise<Material> {
    const response = await apiClient.post<Material>('/materials', data)
    return response.data
  },

  /**
   * Update material
   */
  async update(id: number, data: Partial<Material>): Promise<Material> {
    const response = await apiClient.put<Material>(`/materials/${id}`, data)
    return response.data
  },

  /**
   * Delete material
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/materials/${id}`)
  }
}

// ============================================================================
// Work Composition API
// ============================================================================

export const workCompositionApi = {
  /**
   * Get complete work composition with cost items and materials
   */
  async getComposition(workId: number): Promise<WorkComposition> {
    const response = await apiClient.get<WorkComposition>(`/works/${workId}/composition`)
    return response.data
  },

  /**
   * Add cost item to work
   */
  async addCostItem(workId: number, costItemId: number): Promise<CostItemMaterial> {
    const response = await apiClient.post<CostItemMaterial>(
      `/works/${workId}/cost-items`,
      { cost_item_id: costItemId }
    )
    return response.data
  },

  /**
   * Add material to work
   */
  async addMaterial(
    workId: number,
    data: {
      cost_item_id: number
      material_id: number
      quantity_per_unit: number
    }
  ): Promise<CostItemMaterial> {
    const response = await apiClient.post<CostItemMaterial>(
      `/works/${workId}/materials`,
      { ...data, work_id: workId }
    )
    return response.data
  },

  /**
   * Update material quantity
   */
  async updateMaterialQuantity(
    workId: number,
    associationId: number,
    quantityPerUnit: number
  ): Promise<CostItemMaterial> {
    const response = await apiClient.put<CostItemMaterial>(
      `/works/${workId}/materials/${associationId}`,
      { quantity_per_unit: quantityPerUnit }
    )
    return response.data
  },

  /**
   * Change material cost item association
   */
  async changeMaterialCostItem(
    workId: number,
    associationId: number,
    newCostItemId: number
  ): Promise<CostItemMaterial> {
    const response = await apiClient.put<CostItemMaterial>(
      `/works/${workId}/materials/${associationId}`,
      { cost_item_id: newCostItemId }
    )
    return response.data
  },

  /**
   * Remove cost item from work
   */
  async removeCostItem(workId: number, costItemId: number): Promise<void> {
    await apiClient.delete(`/works/${workId}/cost-items/${costItemId}`)
  },

  /**
   * Remove material from work
   */
  async removeMaterial(workId: number, associationId: number): Promise<void> {
    await apiClient.delete(`/works/${workId}/materials/${associationId}`)
  }
}
