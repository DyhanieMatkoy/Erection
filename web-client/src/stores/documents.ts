import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Estimate, DailyReport } from '@/types/models'

export const useDocumentsStore = defineStore('documents', () => {
  // Current editing documents
  const currentEstimate = ref<Estimate | null>(null)
  const currentDailyReport = ref<DailyReport | null>(null)

  // Loading states
  const loading = ref({
    estimate: false,
    dailyReport: false,
  })

  function setCurrentEstimate(estimate: Estimate | null) {
    currentEstimate.value = estimate
  }

  function setCurrentDailyReport(report: DailyReport | null) {
    currentDailyReport.value = report
  }

  function clearCurrent() {
    currentEstimate.value = null
    currentDailyReport.value = null
  }

  return {
    // State
    currentEstimate,
    currentDailyReport,
    loading,
    // Actions
    setCurrentEstimate,
    setCurrentDailyReport,
    clearCurrent,
  }
})
