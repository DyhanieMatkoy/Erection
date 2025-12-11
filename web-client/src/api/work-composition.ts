/**
 * API client for Work Composition endpoints
 * 
 * This module provides functions for managing work composition,
 * including cost items and materials associated with works.
 */
import apiClient from './client'
import type { WorkComposition, CostItemMaterial } from '@/types/models'

/**
 * Get complete work composition with cost items and materials
 * 
 * @param workId - The ID of the work to retrieve composition for
 * @returns Promise resolving to the complete work composition
 * @throws Error if the work is not found or request fails
 */
export async function getWorkComposition(workId: number): Promise<WorkComposition> {
  try {
    const response = await apiClient.get<WorkComposition>(`/works/${workId}/composition`)
    return response.data
  } catch (error: unknown) {
    const err = error as { response?: { status?: number; data?: { message?: string } } }
    if (err.response?.status === 404) {
      throw new Error(`Work with ID ${workId} not found`)
    }
    throw new Error(err.response?.data?.message || 'Failed to load work composition')
  }
}

/**
 * Add a cost item to a work
 * 
 * Creates a CostItemMaterial association record with material_id = NULL
 * 
 * @param workId - The ID of the work
 * @param costItemId - The ID of the cost item to add
 * @returns Promise resolving to the created association record
 * @throws Error if validation fails or the association already exists
 */
export async function addCostItemToWork(
  workId: number,
  costItemId: number
): Promise<CostItemMaterial> {
  try {
    const response = await apiClient.post<CostItemMaterial>(
      `/works/${workId}/cost-items`,
      { cost_item_id: costItemId }
    )
    return response.data
  } catch (error: unknown) {
    const err = error as { response?: { status?: number; data?: { message?: string } } }
    if (err.response?.status === 409) {
      throw new Error('This cost item is already added to this work')
    }
    if (err.response?.status === 404) {
      throw new Error('Work or cost item not found')
    }
    throw new Error(err.response?.data?.message || 'Failed to add cost item to work')
  }
}

/**
 * Remove a cost item from a work
 * 
 * Deletes all CostItemMaterial records where work_id and cost_item_id match
 * and material_id is NULL. Will fail if the cost item has associated materials.
 * 
 * @param workId - The ID of the work
 * @param costItemId - The ID of the cost item to remove
 * @returns Promise resolving when deletion is complete
 * @throws Error if the cost item has associated materials or deletion fails
 */
export async function removeCostItemFromWork(
  workId: number,
  costItemId: number
): Promise<void> {
  try {
    await apiClient.delete(`/works/${workId}/cost-items/${costItemId}`)
  } catch (error: unknown) {
    const err = error as { response?: { status?: number; data?: { message?: string } } }
    if (err.response?.status === 400) {
      throw new Error(
        'Cannot delete cost item with associated materials. Delete materials first.'
      )
    }
    if (err.response?.status === 404) {
      throw new Error('Work or cost item not found')
    }
    throw new Error(err.response?.data?.message || 'Failed to remove cost item from work')
  }
}

/**
 * Add a material to a work with a specific cost item association
 * 
 * Creates a CostItemMaterial record with work_id, cost_item_id, material_id,
 * and quantity_per_unit.
 * 
 * @param workId - The ID of the work
 * @param data - Material association data
 * @param data.cost_item_id - The cost item to associate the material with
 * @param data.material_id - The ID of the material to add
 * @param data.quantity_per_unit - The quantity of material per unit of work
 * @returns Promise resolving to the created association record
 * @throws Error if validation fails or the association already exists
 */
export async function addMaterialToWork(
  workId: number,
  data: {
    cost_item_id: number
    material_id: number
    quantity_per_unit: number
  }
): Promise<CostItemMaterial> {
  try {
    // Validate quantity
    if (data.quantity_per_unit <= 0) {
      throw new Error('Quantity must be greater than zero')
    }

    const response = await apiClient.post<CostItemMaterial>(
      `/works/${workId}/materials`,
      {
        work_id: workId,
        cost_item_id: data.cost_item_id,
        material_id: data.material_id,
        quantity_per_unit: data.quantity_per_unit
      }
    )
    return response.data
  } catch (error: unknown) {
    const err = error as { response?: { status?: number; data?: { message?: string } } }
    if (err.response?.status === 409) {
      throw new Error('This material is already added to this cost item')
    }
    if (err.response?.status === 404) {
      throw new Error('Work, cost item, or material not found')
    }
    if (err.response?.status === 400) {
      throw new Error(err.response?.data?.message || 'Invalid material data')
    }
    throw new Error(err.response?.data?.message || 'Failed to add material to work')
  }
}

/**
 * Update the quantity of a material in a work
 * 
 * Updates the quantity_per_unit field of a CostItemMaterial record.
 * 
 * @param workId - The ID of the work
 * @param associationId - The ID of the CostItemMaterial association record
 * @param quantityPerUnit - The new quantity per unit value
 * @returns Promise resolving to the updated association record
 * @throws Error if validation fails or the record is not found
 */
export async function updateMaterialQuantity(
  workId: number,
  associationId: number,
  quantityPerUnit: number
): Promise<CostItemMaterial> {
  try {
    // Validate quantity
    if (quantityPerUnit <= 0) {
      throw new Error('Quantity must be greater than zero')
    }

    const response = await apiClient.put<CostItemMaterial>(
      `/works/${workId}/materials/${associationId}`,
      { quantity_per_unit: quantityPerUnit }
    )
    return response.data
  } catch (error: unknown) {
    const err = error as { response?: { status?: number; data?: { message?: string } } }
    if (err.response?.status === 404) {
      throw new Error('Material association not found')
    }
    if (err.response?.status === 400) {
      throw new Error(err.response?.data?.message || 'Invalid quantity value')
    }
    throw new Error(err.response?.data?.message || 'Failed to update material quantity')
  }
}

/**
 * Change the cost item association for a material
 * 
 * Updates the cost_item_id field of a CostItemMaterial record while
 * preserving work_id, material_id, and quantity_per_unit.
 * 
 * @param workId - The ID of the work
 * @param associationId - The ID of the CostItemMaterial association record
 * @param newCostItemId - The ID of the new cost item to associate with
 * @returns Promise resolving to the updated association record
 * @throws Error if validation fails or the record is not found
 */
export async function changeMaterialCostItem(
  workId: number,
  associationId: number,
  newCostItemId: number
): Promise<CostItemMaterial> {
  try {
    const response = await apiClient.put<CostItemMaterial>(
      `/works/${workId}/materials/${associationId}`,
      { cost_item_id: newCostItemId }
    )
    return response.data
  } catch (error: unknown) {
    const err = error as { response?: { status?: number; data?: { message?: string } } }
    if (err.response?.status === 404) {
      throw new Error('Material association or cost item not found')
    }
    if (err.response?.status === 400) {
      throw new Error(err.response?.data?.message || 'Invalid cost item')
    }
    throw new Error(
      err.response?.data?.message || 'Failed to change material cost item association'
    )
  }
}

/**
 * Remove a material from a work
 * 
 * Deletes a CostItemMaterial record by its association ID.
 * 
 * @param workId - The ID of the work
 * @param associationId - The ID of the CostItemMaterial association record to delete
 * @returns Promise resolving when deletion is complete
 * @throws Error if the record is not found or deletion fails
 */
export async function removeMaterialFromWork(
  workId: number,
  associationId: number
): Promise<void> {
  try {
    await apiClient.delete(`/works/${workId}/materials/${associationId}`)
  } catch (error: unknown) {
    const err = error as { response?: { status?: number; data?: { message?: string } } }
    if (err.response?.status === 404) {
      throw new Error('Material association not found')
    }
    throw new Error(err.response?.data?.message || 'Failed to remove material from work')
  }
}

// Export all functions as a namespace for convenience
export const workCompositionApi = {
  getWorkComposition,
  addCostItemToWork,
  removeCostItemFromWork,
  addMaterialToWork,
  updateMaterialQuantity,
  changeMaterialCostItem,
  removeMaterialFromWork
}

export default workCompositionApi
