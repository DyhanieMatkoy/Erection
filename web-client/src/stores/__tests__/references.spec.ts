import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useReferencesStore } from '../references'
import * as referencesApi from '@/api/references'

// Mock the references API
vi.mock('@/api/references', () => ({
  getCounterparties: vi.fn(),
  getObjects: vi.fn(),
  getWorks: vi.fn(),
  getPersons: vi.fn(),
  getOrganizations: vi.fn(),
}))

describe('useReferencesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have empty arrays initially', () => {
      const store = useReferencesStore()
      
      expect(store.counterparties).toEqual([])
      expect(store.objects).toEqual([])
      expect(store.works).toEqual([])
      expect(store.persons).toEqual([])
      expect(store.organizations).toEqual([])
    })

    it('should have all loading states as false', () => {
      const store = useReferencesStore()
      
      expect(store.loading.counterparties).toBe(false)
      expect(store.loading.objects).toBe(false)
      expect(store.loading.works).toBe(false)
      expect(store.loading.persons).toBe(false)
      expect(store.loading.organizations).toBe(false)
    })
  })

  describe('fetchCounterparties', () => {
    it('should fetch and cache counterparties', async () => {
      const mockData = [
        { id: 1, name: 'Counterparty 1', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
        { id: 2, name: 'Counterparty 2', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
      ]
      
      vi.mocked(referencesApi.getCounterparties).mockResolvedValue({
        success: true,
        data: mockData,
        pagination: { page: 1, page_size: 100, total_items: 2, total_pages: 1 },
      })
      
      const store = useReferencesStore()
      const result = await store.fetchCounterparties()
      
      expect(result).toEqual(mockData)
      expect(store.counterparties).toEqual(mockData)
      expect(referencesApi.getCounterparties).toHaveBeenCalledWith({ page: 1, page_size: 100 })
    })

    it('should return cached data without API call', async () => {
      const mockData = [{ id: 1, name: 'Cached', parent_id: null, is_deleted: false, created_at: "", updated_at: "" }]
      
      vi.mocked(referencesApi.getCounterparties).mockResolvedValue({
        success: true,
        data: mockData,
        pagination: { page: 1, page_size: 1000, total_items: 1, total_pages: 1 },
      })
      
      const store = useReferencesStore()
      await store.fetchCounterparties()
      
      vi.clearAllMocks()
      
      const result = await store.fetchCounterparties()
      
      expect(result).toEqual(mockData)
      expect(referencesApi.getCounterparties).not.toHaveBeenCalled()
    })

    it('should force refresh when force=true', async () => {
      const mockData1 = [{ id: 1, name: 'First', parent_id: null, is_deleted: false, created_at: "", updated_at: "" }]
      const mockData2 = [{ id: 2, name: 'Second', parent_id: null, is_deleted: false, created_at: "", updated_at: "" }]
      
      vi.mocked(referencesApi.getCounterparties)
        .mockResolvedValueOnce({
          success: true,
          data: mockData1,
          pagination: { page: 1, page_size: 1000, total_items: 1, total_pages: 1 },
        })
        .mockResolvedValueOnce({
          success: true,
          data: mockData2,
          pagination: { page: 1, page_size: 1000, total_items: 1, total_pages: 1 },
        })
      
      const store = useReferencesStore()
      await store.fetchCounterparties()
      const result = await store.fetchCounterparties(true)
      
      expect(result).toEqual(mockData2)
      expect(store.counterparties).toEqual(mockData2)
      expect(referencesApi.getCounterparties).toHaveBeenCalledTimes(2)
    })

    it('should set loading state during fetch', async () => {
      let loadingDuringFetch = false
      
      vi.mocked(referencesApi.getCounterparties).mockImplementation(async () => {
        const store = useReferencesStore()
        loadingDuringFetch = store.loading.counterparties
        return {
          success: true,
          data: [],
          pagination: { page: 1, page_size: 1000, total_items: 0, total_pages: 0 },
        }
      })
      
      const store = useReferencesStore()
      await store.fetchCounterparties()
      
      expect(loadingDuringFetch).toBe(true)
      expect(store.loading.counterparties).toBe(false)
    })
  })

  describe('fetchObjects', () => {
    it('should fetch and cache objects', async () => {
      const mockData = [
        { id: 1, name: 'Object 1', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
        { id: 2, name: 'Object 2', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
      ]
      
      vi.mocked(referencesApi.getObjects).mockResolvedValue({
        success: true,
        data: mockData,
        pagination: { page: 1, page_size: 1000, total_items: 2, total_pages: 1 },
      })
      
      const store = useReferencesStore()
      const result = await store.fetchObjects()
      
      expect(result).toEqual(mockData)
      expect(store.objects).toEqual(mockData)
    })
  })

  describe('fetchWorks', () => {
    it('should fetch and cache works', async () => {
      const mockData = [
        { id: 1, name: 'Work 1', unit: 'м2', marked_for_deletion: false },
        { id: 2, name: 'Work 2', unit: 'м3', marked_for_deletion: false },
      ]
      
      vi.mocked(referencesApi.getWorks).mockResolvedValue({
        success: true,
        data: mockData,
        pagination: { page: 1, page_size: 1000, total_items: 2, total_pages: 1 },
      })
      
      const store = useReferencesStore()
      const result = await store.fetchWorks()
      
      expect(result).toEqual(mockData)
      expect(store.works).toEqual(mockData)
    })
  })

  describe('fetchPersons', () => {
    it('should fetch and cache persons', async () => {
      const mockData = [
        { id: 1, name: 'Person 1', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
        { id: 2, name: 'Person 2', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
      ]
      
      vi.mocked(referencesApi.getPersons).mockResolvedValue({
        success: true,
        data: mockData,
        pagination: { page: 1, page_size: 1000, total_items: 2, total_pages: 1 },
      })
      
      const store = useReferencesStore()
      const result = await store.fetchPersons()
      
      expect(result).toEqual(mockData)
      expect(store.persons).toEqual(mockData)
    })
  })

  describe('fetchOrganizations', () => {
    it('should fetch and cache organizations', async () => {
      const mockData = [
        { id: 1, name: 'Organization 1', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
        { id: 2, name: 'Organization 2', parent_id: null, is_deleted: false, created_at: "", updated_at: "" },
      ]
      
      vi.mocked(referencesApi.getOrganizations).mockResolvedValue({
        success: true,
        data: mockData,
        pagination: { page: 1, page_size: 1000, total_items: 2, total_pages: 1 },
      })
      
      const store = useReferencesStore()
      const result = await store.fetchOrganizations()
      
      expect(result).toEqual(mockData)
      expect(store.organizations).toEqual(mockData)
    })
  })

  describe('clearCache', () => {
    it('should clear all cached data', async () => {
      vi.mocked(referencesApi.getCounterparties).mockResolvedValue({
        success: true,
        data: [{ id: 1, name: 'Test', parent_id: null, is_deleted: false, created_at: "", updated_at: "" }],
        pagination: { page: 1, page_size: 1000, total_items: 1, total_pages: 1 },
      })
      
      const store = useReferencesStore()
      await store.fetchCounterparties()
      
      expect(store.counterparties.length).toBeGreaterThan(0)
      
      store.clearCache()
      
      expect(store.counterparties).toEqual([])
      expect(store.objects).toEqual([])
      expect(store.works).toEqual([])
      expect(store.persons).toEqual([])
      expect(store.organizations).toEqual([])
    })
  })
})
