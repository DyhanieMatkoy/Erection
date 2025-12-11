import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentsStore } from '../documents'
import type { Estimate, DailyReport } from '@/types/models'

describe('useDocumentsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('initial state', () => {
    it('should have null documents initially', () => {
      const store = useDocumentsStore()
      
      expect(store.currentEstimate).toBeNull()
      expect(store.currentDailyReport).toBeNull()
    })

    it('should have all loading states as false', () => {
      const store = useDocumentsStore()
      
      expect(store.loading.estimate).toBe(false)
      expect(store.loading.dailyReport).toBe(false)
    })
  })

  describe('setCurrentEstimate', () => {
    it('should set current estimate', () => {
      const store = useDocumentsStore()
      const mockEstimate: Estimate = {
        id: 1,
        number: 'EST-001',
        date: '2024-01-01',
        total_sum: 100000,
        total_labor: 500,
        is_posted: false,
        created_at: '2024-01-01T00:00:00',
        lines: [],
      }
      
      store.setCurrentEstimate(mockEstimate)
      
      expect(store.currentEstimate).toEqual(mockEstimate)
    })

    it('should clear current estimate when set to null', () => {
      const store = useDocumentsStore()
      const mockEstimate: Estimate = {
        id: 1,
        number: 'EST-001',
        date: '2024-01-01',
        total_sum: 100000,
        total_labor: 500,
        is_posted: false,
        created_at: '2024-01-01T00:00:00',
        lines: [],
      }
      
      store.setCurrentEstimate(mockEstimate)
      store.setCurrentEstimate(null)
      
      expect(store.currentEstimate).toBeNull()
    })
  })

  describe('setCurrentDailyReport', () => {
    it('should set current daily report', () => {
      const store = useDocumentsStore()
      const mockReport: DailyReport = {
        id: 1,
        date: '2024-01-01',
        estimate_id: 1,
        foreman_id: 1,
        is_posted: false,
        created_at: '2024-01-01T00:00:00',
        lines: [],
      }
      
      store.setCurrentDailyReport(mockReport)
      
      expect(store.currentDailyReport).toEqual(mockReport)
    })

    it('should clear current daily report when set to null', () => {
      const store = useDocumentsStore()
      const mockReport: DailyReport = {
        id: 1,
        date: '2024-01-01',
        estimate_id: 1,
        foreman_id: 1,
        is_posted: false,
        created_at: '2024-01-01T00:00:00',
        lines: [],
      }
      
      store.setCurrentDailyReport(mockReport)
      store.setCurrentDailyReport(null)
      
      expect(store.currentDailyReport).toBeNull()
    })
  })

  describe('clearCurrent', () => {
    it('should clear both current documents', () => {
      const store = useDocumentsStore()
      const mockEstimate: Estimate = {
        id: 1,
        number: 'EST-001',
        date: '2024-01-01',
        total_sum: 100000,
        total_labor: 500,
        is_posted: false,
        created_at: '2024-01-01T00:00:00',
        lines: [],
      }
      const mockReport: DailyReport = {
        id: 1,
        date: '2024-01-01',
        estimate_id: 1,
        foreman_id: 1,
        is_posted: false,
        created_at: '2024-01-01T00:00:00',
        lines: [],
      }
      
      store.setCurrentEstimate(mockEstimate)
      store.setCurrentDailyReport(mockReport)
      
      store.clearCurrent()
      
      expect(store.currentEstimate).toBeNull()
      expect(store.currentDailyReport).toBeNull()
    })
  })
})
