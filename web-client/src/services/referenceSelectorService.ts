/**
 * Reference selector service for handling reference selection dialogs and auto-completion
 * Requirements: 10.1, 10.2, 10.3, 10.4, 11.3, 11.4
 */

import { ref, reactive } from 'vue'
import type { ReferenceValue, ReferenceFieldConfig } from '@/types/table-parts'
import * as referencesApi from '@/api/references'

export interface ReferenceSelectorOptions {
  referenceType: string
  title?: string
  currentValue?: ReferenceValue | null
  allowCreate?: boolean
  allowEdit?: boolean
  hierarchical?: boolean
  parentId?: number | null
  extraFilter?: string
}

export interface AutoCompleteOptions {
  referenceType: string
  query: string
  minLength?: number
  limit?: number
  parentId?: number | null
}

export interface ReferenceSelectorResult {
  selected: boolean
  value?: ReferenceValue
  action?: 'select' | 'create' | 'edit' | 'cancel'
}

export class ReferenceSelectorService {
  private static instance: ReferenceSelectorService
  
  // State for managing open dialogs
  private openDialogs = reactive(new Map<string, any>())
  
  // Auto-complete cache
  private autoCompleteCache = reactive(new Map<string, { 
    data: ReferenceValue[], 
    timestamp: number,
    query: string 
  }>())
  
  private readonly CACHE_DURATION = 30000 // 30 seconds
  
  static getInstance(): ReferenceSelectorService {
    if (!ReferenceSelectorService.instance) {
      ReferenceSelectorService.instance = new ReferenceSelectorService()
    }
    return ReferenceSelectorService.instance
  }
  
  /**
   * Open reference selector dialog
   * Requirements: 10.1, 10.3
   */
  async openSelector(options: ReferenceSelectorOptions): Promise<ReferenceSelectorResult> {
    const dialogId = `${options.referenceType}_${Date.now()}`
    
    try {
      // Check if dialog is already open for this reference type
      const existingDialog = Array.from(this.openDialogs.values())
        .find(d => d.referenceType === options.referenceType)
      
      if (existingDialog) {
        // Focus existing dialog
        existingDialog.focus?.()
        return { selected: false, action: 'cancel' }
      }
      
      // Create and show dialog
      const dialog = await this.createSelectorDialog(options)
      this.openDialogs.set(dialogId, dialog)
      
      // Wait for dialog result
      const result = await dialog.show()
      
      // Clean up
      this.openDialogs.delete(dialogId)
      
      return result
    } catch (error) {
      console.error('Error opening reference selector:', error)
      this.openDialogs.delete(dialogId)
      return { selected: false, action: 'cancel' }
    }
  }
  
  /**
   * Get auto-completion suggestions
   * Requirements: 10.2
   */
  async getAutoComplete(options: AutoCompleteOptions): Promise<ReferenceValue[]> {
    const { referenceType, query, minLength = 3, limit = 10, parentId } = options
    
    // Check minimum length
    if (query.length < minLength) {
      return []
    }
    
    // Check cache
    const cacheKey = `${referenceType}_${query}_${parentId || 'null'}`
    const cached = this.autoCompleteCache.get(cacheKey)
    
    if (cached && (Date.now() - cached.timestamp) < this.CACHE_DURATION) {
      return cached.data.slice(0, limit)
    }
    
    try {
      // Fetch from API
      const results = await this.fetchAutoCompleteData(referenceType, query, parentId, limit)
      
      // Cache results
      this.autoCompleteCache.set(cacheKey, {
        data: results,
        timestamp: Date.now(),
        query
      })
      
      return results
    } catch (error) {
      console.error('Auto-complete fetch failed:', error)
      return []
    }
  }
  
  /**
   * Open reference element for editing
   * Requirements: 11.3
   */
  async openReference(referenceType: string, referenceId: number): Promise<boolean> {
    try {
      // Check if form is already open
      const formId = `${referenceType}_form_${referenceId}`
      const existingForm = this.openDialogs.get(formId)
      
      if (existingForm) {
        existingForm.focus?.()
        return true
      }
      
      // Create and show form
      const form = await this.createReferenceForm(referenceType, referenceId)
      this.openDialogs.set(formId, form)
      
      // Show form
      await form.show()
      
      // Clean up when form closes
      form.onClose(() => {
        this.openDialogs.delete(formId)
      })
      
      return true
    } catch (error) {
      console.error('Error opening reference form:', error)
      return false
    }
  }
  
  /**
   * Fill related fields based on selected reference
   * Requirements: 10.4, 11.4
   */
  async fillRelatedFields(
    referenceType: string, 
    referenceId: number, 
    relatedFields: string[]
  ): Promise<Record<string, any>> {
    if (!relatedFields.length || referenceId <= 0) {
      return {}
    }
    
    try {
      // Fetch reference data with related fields
      const referenceData = await this.fetchReferenceWithRelatedData(referenceType, referenceId)
      
      // Map related fields
      const result: Record<string, any> = {}
      
      for (const fieldName of relatedFields) {
        if (fieldName in referenceData) {
          result[fieldName] = referenceData[fieldName]
        } else {
          // Handle special field mappings
          result[fieldName] = this.mapRelatedField(referenceType, fieldName, referenceData)
        }
      }
      
      return result
    } catch (error) {
      console.error('Error filling related fields:', error)
      return {}
    }
  }
  
  /**
   * Clear auto-complete cache
   */
  clearAutoCompleteCache(referenceType?: string) {
    if (referenceType) {
      // Clear cache for specific reference type
      for (const [key] of this.autoCompleteCache) {
        if (key.startsWith(`${referenceType}_`)) {
          this.autoCompleteCache.delete(key)
        }
      }
    } else {
      // Clear all cache
      this.autoCompleteCache.clear()
    }
  }
  
  /**
   * Get list of open dialogs
   */
  getOpenDialogs(): string[] {
    return Array.from(this.openDialogs.keys())
  }
  
  /**
   * Close all open dialogs
   */
  closeAllDialogs() {
    for (const [id, dialog] of this.openDialogs) {
      dialog.close?.()
      this.openDialogs.delete(id)
    }
  }
  
  // Private methods
  
  private async createSelectorDialog(options: ReferenceSelectorOptions): Promise<any> {
    // This would create the actual dialog component
    // For now, return a mock dialog
    return {
      referenceType: options.referenceType,
      show: async (): Promise<ReferenceSelectorResult> => {
        // Mock implementation - in real app this would show a Vue dialog
        return new Promise((resolve) => {
          setTimeout(() => {
            // Simulate user selection
            const mockResult: ReferenceValue = {
              id: Math.floor(Math.random() * 1000) + 1,
              name: `Selected ${options.referenceType} ${Math.floor(Math.random() * 100)}`,
              code: `CODE${Math.floor(Math.random() * 1000)}`
            }
            
            resolve({
              selected: true,
              value: mockResult,
              action: 'select'
            })
          }, 500)
        })
      },
      focus: () => {
        console.log('Focusing dialog')
      },
      close: () => {
        console.log('Closing dialog')
      }
    }
  }
  
  private async createReferenceForm(referenceType: string, referenceId: number): Promise<any> {
    // This would create the actual form component
    return {
      show: async () => {
        console.log(`Opening ${referenceType} form for ID ${referenceId}`)
        return true
      },
      focus: () => {
        console.log('Focusing form')
      },
      onClose: (callback: () => void) => {
        // Mock - would call callback when form closes
        setTimeout(callback, 1000)
      }
    }
  }
  
  private async fetchAutoCompleteData(
    referenceType: string, 
    query: string, 
    parentId?: number | null,
    limit: number = 10
  ): Promise<ReferenceValue[]> {
    const params: any = {
      search: query,
      limit,
      include_unit_info: referenceType === 'works'
    }
    
    if (parentId !== null && parentId !== undefined) {
      params.parent_id = parentId
    }
    
    try {
      let response: any
      
      switch (referenceType) {
        case 'works':
          response = await referencesApi.getWorks(params)
          break
        case 'counterparties':
          response = await referencesApi.getCounterparties(params)
          break
        case 'objects':
          response = await referencesApi.getObjects(params)
          break
        case 'persons':
          response = await referencesApi.getPersons(params)
          break
        case 'organizations':
          response = await referencesApi.getOrganizations(params)
          break
        case 'units':
          response = await referencesApi.getUnits(params)
          break
        default:
          throw new Error(`Unsupported reference type: ${referenceType}`)
      }
      
      // Convert API response to ReferenceValue format
      return response.data.map((item: any) => ({
        id: item.id,
        name: item.name || item.full_name || `${referenceType} ${item.id}`,
        code: item.code || item.number || undefined,
        additionalData: item
      }))
    } catch (error) {
      console.error(`Failed to fetch auto-complete for ${referenceType}:`, error)
      return []
    }
  }
  
  private async fetchReferenceWithRelatedData(
    referenceType: string, 
    referenceId: number
  ): Promise<any> {
    try {
      switch (referenceType) {
        case 'works':
          return await referencesApi.getWork(referenceId)
        case 'counterparties':
          return await referencesApi.getCounterparty(referenceId)
        case 'objects':
          return await referencesApi.getObject(referenceId)
        case 'persons':
          return await referencesApi.getPerson(referenceId)
        case 'organizations':
          return await referencesApi.getOrganization(referenceId)
        case 'units':
          return await referencesApi.getUnit(referenceId)
        default:
          throw new Error(`Unsupported reference type: ${referenceType}`)
      }
    } catch (error) {
      console.error(`Failed to fetch reference data for ${referenceType} ID ${referenceId}:`, error)
      return {}
    }
  }
  
  private mapRelatedField(referenceType: string, fieldName: string, referenceData: any): any {
    // Handle special field mappings based on reference type
    switch (referenceType) {
      case 'works':
        if (fieldName === 'unit' || fieldName === 'unit_name') {
          return referenceData.unit?.name || ''
        }
        if (fieldName === 'unit_id') {
          return referenceData.unit?.id || null
        }
        if (fieldName === 'price') {
          return referenceData.price || 0
        }
        break
        
      case 'counterparties':
        if (fieldName === 'organization' || fieldName === 'organization_name') {
          return referenceData.organization?.name || ''
        }
        if (fieldName === 'organization_id') {
          return referenceData.organization?.id || null
        }
        break
        
      default:
        break
    }
    
    return null
  }
}

// Export singleton instance
export const referenceSelectorService = ReferenceSelectorService.getInstance()

// Export composable for Vue components
export function useReferenceSelector() {
  const service = ReferenceSelectorService.getInstance()
  
  return {
    openSelector: service.openSelector.bind(service),
    getAutoComplete: service.getAutoComplete.bind(service),
    openReference: service.openReference.bind(service),
    fillRelatedFields: service.fillRelatedFields.bind(service),
    clearCache: service.clearAutoCompleteCache.bind(service),
    closeAllDialogs: service.closeAllDialogs.bind(service)
  }
}