import { ref, computed } from 'vue'
import { workSpecificationApi } from '@/api/work-specifications'
import type { 
  WorkSpecification, 
  WorkSpecificationCreate, 
  WorkSpecificationUpdate,
  WorkSpecificationSummary,
  ComponentType
} from '@/types/models'

export function useWorkSpecification(workId: number) {
  const specifications = ref<WorkSpecification[]>([])
  const summary = ref<WorkSpecificationSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const totalCost = computed(() => summary.value?.total_cost || 0)
  
  const totalsByType = computed(() => summary.value?.totals_by_type || {
    Material: 0,
    Labor: 0,
    Equipment: 0,
    Other: 0
  })

  async function loadSpecifications() {
    loading.value = true
    error.value = null
    try {
      const data = await workSpecificationApi.getByWorkId(workId)
      summary.value = data
      specifications.value = data.specifications
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load specifications'
      console.error('Error loading specifications:', err)
    } finally {
      loading.value = false
    }
  }

  async function addSpecification(data: WorkSpecificationCreate) {
    loading.value = true
    error.value = null
    try {
      const newSpec = await workSpecificationApi.create(workId, data)
      await loadSpecifications() // Reload to update summary
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to add specification'
      return false
    } finally {
      loading.value = false
    }
  }

  async function updateSpecification(specId: number, data: WorkSpecificationUpdate) {
    loading.value = true
    error.value = null
    try {
      await workSpecificationApi.update(workId, specId, data)
      await loadSpecifications() // Reload to update summary and list
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update specification'
      return false
    } finally {
      loading.value = false
    }
  }

  async function removeSpecification(specId: number) {
    loading.value = true
    error.value = null
    try {
      await workSpecificationApi.delete(workId, specId)
      specifications.value = specifications.value.filter(s => s.id !== specId)
      await loadSpecifications() // Reload to update summary
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to remove specification'
      return false
    } finally {
      loading.value = false
    }
  }

  async function copyFromWork(sourceWorkId: number) {
    loading.value = true
    error.value = null
    try {
      const data = await workSpecificationApi.copyFromWork(workId, sourceWorkId)
      summary.value = data
      specifications.value = data.specifications
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to copy specifications'
      return false
    } finally {
      loading.value = false
    }
  }

  async function importFromExcel(file: File) {
    loading.value = true
    error.value = null
    try {
      const data = await workSpecificationApi.importFromExcel(workId, file)
      summary.value = data
      specifications.value = data.specifications
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to import specifications'
      return false
    } finally {
      loading.value = false
    }
  }

  async function exportToExcel() {
    loading.value = true
    error.value = null
    try {
      const blob = await workSpecificationApi.exportToExcel(workId)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `specifications_${workId}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to export specifications'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    specifications,
    summary,
    loading,
    error,
    totalCost,
    totalsByType,
    loadSpecifications,
    addSpecification,
    updateSpecification,
    removeSpecification,
    copyFromWork,
    importFromExcel,
    exportToExcel
  }
}
