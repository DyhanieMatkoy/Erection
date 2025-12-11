import { ref } from 'vue'
import * as documentsApi from '@/api/documents'

export function usePrint() {
  const loading = ref(false)
  const error = ref('')

  async function printEstimate(
    id: number,
    format: 'pdf' | 'excel',
    action: 'download' | 'open',
    filename: string
  ) {
    loading.value = true
    error.value = ''

    try {
      const blob = await documentsApi.printEstimate(id, format)
      handleBlob(blob, format, action, filename)
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } }
      error.value = apiError.response?.data?.detail || 'Ошибка при печати'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function printDailyReport(
    id: number,
    format: 'pdf' | 'excel',
    action: 'download' | 'open',
    filename: string
  ) {
    loading.value = true
    error.value = ''

    try {
      const blob = await documentsApi.printDailyReport(id, format)
      handleBlob(blob, format, action, filename)
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } }
      error.value = apiError.response?.data?.detail || 'Ошибка при печати'
      throw err
    } finally {
      loading.value = false
    }
  }

  function handleBlob(blob: Blob, format: 'pdf' | 'excel', action: 'download' | 'open', filename: string) {
    const url = window.URL.createObjectURL(blob)
    
    if (action === 'open' && format === 'pdf') {
      // Open PDF in new tab
      window.open(url, '_blank')
    } else {
      // Download file
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}.${format === 'pdf' ? 'pdf' : 'xlsx'}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    // Clean up
    setTimeout(() => window.URL.revokeObjectURL(url), 100)
  }

  async function printTimesheet(
    id: number,
    format: 'pdf' | 'excel',
    action: 'download' | 'open',
    filename: string
  ) {
    loading.value = true
    error.value = ''

    try {
      const blob = await documentsApi.printTimesheet(id, format)
      handleBlob(blob, format, action, filename)
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } }
      error.value = apiError.response?.data?.detail || 'Ошибка при печати'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    printEstimate,
    printDailyReport,
    printTimesheet,
  }
}
