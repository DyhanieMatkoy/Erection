import apiClient from './client'
import type { ApiResponse, PaginationParams } from '@/types/api'
import type { Estimate, DailyReport, Timesheet, TimesheetLine } from '@/types/models'

// Estimates
export async function getEstimates(params?: PaginationParams): Promise<ApiResponse<Estimate[]>> {
  const response = await apiClient.get<ApiResponse<Estimate[]>>('/documents/estimates', { params })
  return response.data
}

export async function getEstimate(id: number): Promise<Estimate> {
  const response = await apiClient.get<{ success: boolean; data: Estimate }>(`/documents/estimates/${id}`)
  return response.data.data
}

export async function createEstimate(data: Partial<Estimate>): Promise<Estimate> {
  const response = await apiClient.post<{ success: boolean; data: Estimate }>('/documents/estimates', data)
  return response.data.data
}

export async function updateEstimate(id: number, data: Partial<Estimate>): Promise<Estimate> {
  const response = await apiClient.put<{ success: boolean; data: Estimate }>(`/documents/estimates/${id}`, data)
  return response.data.data
}

export async function deleteEstimate(id: number): Promise<void> {
  await apiClient.delete(`/documents/estimates/${id}`)
}

export async function postEstimate(id: number): Promise<Estimate> {
  const response = await apiClient.post<{ success: boolean; data: Estimate }>(`/documents/estimates/${id}/post`)
  return response.data.data
}

export async function unpostEstimate(id: number): Promise<Estimate> {
  const response = await apiClient.post<{ success: boolean; data: Estimate }>(`/documents/estimates/${id}/unpost`)
  return response.data.data
}

export async function importEstimateFromExcel(file: File): Promise<Estimate> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await apiClient.post<{ success: boolean; data: Estimate; message: string }>(
    '/documents/estimates/import-excel',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data.data
}

// Daily Reports
export async function getDailyReports(
  params?: PaginationParams
): Promise<ApiResponse<DailyReport[]>> {
  const response = await apiClient.get<ApiResponse<DailyReport[]>>('/documents/daily-reports', {
    params,
  })
  return response.data
}

export async function getDailyReport(id: number): Promise<DailyReport> {
  const response = await apiClient.get<{ success: boolean; data: DailyReport }>(`/documents/daily-reports/${id}`)
  return response.data.data
}

export async function createDailyReport(data: Partial<DailyReport>): Promise<DailyReport> {
  const response = await apiClient.post<{ success: boolean; data: DailyReport }>('/documents/daily-reports', data)
  return response.data.data
}

export async function updateDailyReport(
  id: number,
  data: Partial<DailyReport>
): Promise<DailyReport> {
  const response = await apiClient.put<{ success: boolean; data: DailyReport }>(`/documents/daily-reports/${id}`, data)
  return response.data.data
}

export async function deleteDailyReport(id: number): Promise<void> {
  await apiClient.delete(`/documents/daily-reports/${id}`)
}

export async function postDailyReport(id: number): Promise<DailyReport> {
  const response = await apiClient.post<{ success: boolean; data: DailyReport }>(`/documents/daily-reports/${id}/post`)
  return response.data.data
}

export async function unpostDailyReport(id: number): Promise<DailyReport> {
  const response = await apiClient.post<{ success: boolean; data: DailyReport }>(`/documents/daily-reports/${id}/unpost`)
  return response.data.data
}

export async function importDailyReportFromExcel(file: File): Promise<DailyReport> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await apiClient.post<{ success: boolean; data: DailyReport; message: string }>(
    '/documents/daily-reports/import-excel',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data.data
}

// Timesheets
export async function getTimesheets(params?: PaginationParams): Promise<ApiResponse<Timesheet[]>> {
  const response = await apiClient.get<ApiResponse<Timesheet[]>>('/documents/timesheets', {
    params,
  })
  return response.data
}

export async function getTimesheet(id: number): Promise<Timesheet> {
  const response = await apiClient.get<{ success: boolean; data: Timesheet }>(
    `/documents/timesheets/${id}`
  )
  return response.data.data
}

export async function createTimesheet(data: Partial<Timesheet>): Promise<Timesheet> {
  const response = await apiClient.post<{ success: boolean; data: Timesheet }>(
    '/documents/timesheets',
    data
  )
  return response.data.data
}

export async function updateTimesheet(id: number, data: Partial<Timesheet>): Promise<Timesheet> {
  const response = await apiClient.put<{ success: boolean; data: Timesheet }>(
    `/documents/timesheets/${id}`,
    data
  )
  return response.data.data
}

export async function deleteTimesheet(id: number): Promise<void> {
  await apiClient.delete(`/documents/timesheets/${id}`)
}

export async function postTimesheet(id: number): Promise<Timesheet> {
  const response = await apiClient.post<{ success: boolean; data: Timesheet }>(
    `/documents/timesheets/${id}/post`
  )
  return response.data.data
}

export async function unpostTimesheet(id: number): Promise<Timesheet> {
  const response = await apiClient.post<{ success: boolean; data: Timesheet }>(
    `/documents/timesheets/${id}/unpost`
  )
  return response.data.data
}

export async function autofillTimesheet(
  object_id: number,
  estimate_id: number,
  month_year: string
): Promise<{ lines: TimesheetLine[] }> {
  const response = await apiClient.post<{ lines: TimesheetLine[] }>(
    '/documents/timesheets/autofill',
    null,
    {
      params: { object_id, estimate_id, month_year },
    }
  )
  return response.data
}

// Print Forms
export async function printEstimate(id: number, format: 'pdf' | 'excel'): Promise<Blob> {
  const response = await apiClient.get(`/documents/estimates/${id}/print`, {
    params: { format },
    responseType: 'blob',
  })
  return response.data
}

export async function printDailyReport(id: number, format: 'pdf' | 'excel'): Promise<Blob> {
  const response = await apiClient.get(`/documents/daily-reports/${id}/print`, {
    params: { format },
    responseType: 'blob',
  })
  return response.data
}

export async function printTimesheet(id: number, format: 'pdf' | 'excel'): Promise<Blob> {
  const response = await apiClient.get(`/documents/timesheets/${id}/print`, {
    params: { format },
    responseType: 'blob',
  })
  return response.data
}

// Bulk Operations
interface BulkOperationResponse {
  success: boolean
  deleted_count?: number
  posted_count?: number
  unposted_count?: number
  errors: string[]
  message: string
}

export async function bulkDeleteEstimates(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/estimates/bulk-delete', { ids })
  return response.data
}

export async function bulkPostEstimates(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/estimates/bulk-post', { ids })
  return response.data
}

export async function bulkUnpostEstimates(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/estimates/bulk-unpost', { ids })
  return response.data
}

export async function bulkDeleteDailyReports(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/daily-reports/bulk-delete', { ids })
  return response.data
}

export async function bulkPostDailyReports(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/daily-reports/bulk-post', { ids })
  return response.data
}

export async function bulkUnpostDailyReports(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/daily-reports/bulk-unpost', { ids })
  return response.data
}

export async function bulkDeleteTimesheets(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/timesheets/bulk-delete', { ids })
  return response.data
}

export async function bulkPostTimesheets(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/timesheets/bulk-post', { ids })
  return response.data
}

export async function bulkUnpostTimesheets(ids: number[]): Promise<BulkOperationResponse> {
  const response = await apiClient.post<BulkOperationResponse>('/documents/timesheets/bulk-unpost', { ids })
  return response.data
}
