import apiClient from './client'
import type { LoginRequest, LoginResponse, UserInfo } from '@/types/api'

/**
 * Authenticate user with username and password
 */
export async function login(username: string, password: string): Promise<LoginResponse> {
  const request: LoginRequest = { username, password }
  const response = await apiClient.post<LoginResponse>('/auth/login', request)
  return response.data
}

/**
 * Logout user (client-side only - clear token)
 */
export function logout(): void {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

/**
 * Get current user information
 */
export async function getCurrentUser(): Promise<UserInfo> {
  const response = await apiClient.get<UserInfo>('/auth/me')
  return response.data
}
