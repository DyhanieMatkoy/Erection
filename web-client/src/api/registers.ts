import apiClient from './client'
import type { ApiResponse } from '@/types/api'
import type { WorkExecutionMovement } from '@/types/models'

export interface WorkExecutionParams {
  period_from?: string
  period_to?: string
  object_id?: number
  estimate_id?: number
  work_id?: number
  group_by?: string
  page?: number
  page_size?: number
}

export async function getWorkExecutionRegister(
  params?: WorkExecutionParams
): Promise<ApiResponse<WorkExecutionMovement[]>> {
  const response = await apiClient.get<ApiResponse<WorkExecutionMovement[]>>(
    '/registers/work-execution',
    { params }
  )
  return response.data
}

export interface WorkExecutionDetailMovement {
  id: number
  period: string
  recorder_type: 'estimate' | 'daily_report'
  recorder_id: number
  line_number: number
  object_id: number
  object_name: string
  estimate_id: number
  estimate_number: string
  work_id: number
  work_name: string
  quantity_income: number
  quantity_expense: number
  sum_income: number
  sum_expense: number
}

export async function getWorkExecutionMovements(
  params: WorkExecutionParams
): Promise<ApiResponse<WorkExecutionDetailMovement[]>> {
  const response = await apiClient.get<ApiResponse<WorkExecutionDetailMovement[]>>(
    '/registers/work-execution/movements',
    { params }
  )
  return response.data
}
