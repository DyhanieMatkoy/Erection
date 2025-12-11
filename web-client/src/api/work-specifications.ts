import apiClient from './client'
import type { 
  WorkSpecification, 
  WorkSpecificationCreate, 
  WorkSpecificationUpdate,
  WorkSpecificationSummary 
} from '@/types/models'

const BASE_URL = '/works'

export const workSpecificationApi = {
  // Get all specifications for a work
  getByWorkId(workId: number): Promise<WorkSpecificationSummary> {
    return apiClient.get(`${BASE_URL}/${workId}/specifications`).then(res => res.data)
  },

  // Create a new specification entry
  create(workId: number, data: WorkSpecificationCreate): Promise<WorkSpecification> {
    return apiClient.post(`${BASE_URL}/${workId}/specifications`, data).then(res => res.data)
  },

  // Update a specification entry
  update(workId: number, specId: number, data: WorkSpecificationUpdate): Promise<WorkSpecification> {
    return apiClient.put(`${BASE_URL}/${workId}/specifications/${specId}`, data).then(res => res.data)
  },

  // Delete a specification entry
  delete(workId: number, specId: number): Promise<void> {
    return apiClient.delete(`${BASE_URL}/${workId}/specifications/${specId}`).then(res => res.data)
  },

  // Copy specifications from another work
  copyFromWork(targetWorkId: number, sourceWorkId: number): Promise<WorkSpecificationSummary> {
    return apiClient.post(`${BASE_URL}/${targetWorkId}/specifications/copy-from/${sourceWorkId}`).then(res => res.data)
  },
  
  // Import from Excel (multipart/form-data)
  importFromExcel(workId: number, file: File): Promise<WorkSpecificationSummary> {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiClient.post(`${BASE_URL}/${workId}/specifications/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then(res => res.data)
  },
  
  // Export to Excel (blob)
  exportToExcel(workId: number): Promise<Blob> {
    return apiClient.get(`${BASE_URL}/${workId}/specifications/export`, {
      responseType: 'blob'
    }).then(res => res.data)
  }
}
