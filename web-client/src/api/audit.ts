import apiClient from './client'
import type { ApiResponse, PaginationParams } from '@/types/api'

export interface AuditLog {
  id: number
  user_id: number
  username: string
  action: string
  resource_type: string
  resource_id: number
  details: string
  created_at: string
}

export async function getAuditLogs(params?: PaginationParams & {
  resource_type?: string
  resource_id?: number
}): Promise<ApiResponse<AuditLog[]>> {
  const response = await apiClient.get<ApiResponse<AuditLog[]>>('/audit/logs', { params })
  return response.data
}
