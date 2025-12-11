// Authentication types
export interface LoginRequest {
  username: string
  password: string
}

export interface UserInfo {
  id: number
  username: string
  role: string
  is_active: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

// Pagination types
export interface PaginationParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginationInfo {
  page: number
  page_size: number
  total_items?: number
  total?: number
  pages?: number
  total_pages?: number
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  pagination?: PaginationInfo
  message?: string
}

// Error response
export interface ApiError {
  detail: string | { msg: string; type: string }[]
}
