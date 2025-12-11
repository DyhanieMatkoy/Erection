import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuth } from '../useAuth'
import * as authApi from '@/api/auth'

// Mock the auth API
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
}))

describe('useAuth', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should expose isAuthenticated computed property', async () => {
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 28800,
      user: {
        id: 1,
        username: 'testuser',
        role: 'admin',
        is_active: true,
      },
    }
    
    vi.mocked(authApi.login).mockResolvedValue(mockResponse)
    
    const { isAuthenticated, login } = useAuth()
    expect(isAuthenticated.value).toBe(false)
    
    await login('testuser', 'password')
    expect(isAuthenticated.value).toBe(true)
  })

  it('should expose isAdmin computed property', async () => {
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 28800,
      user: {
        id: 1,
        username: 'admin',
        role: 'admin',
        is_active: true,
      },
    }
    
    vi.mocked(authApi.login).mockResolvedValue(mockResponse)
    
    const { isAdmin, login } = useAuth()
    expect(isAdmin.value).toBe(false)
    
    await login('admin', 'password')
    expect(isAdmin.value).toBe(true)
  })

  it('should expose currentUser computed property', async () => {
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 28800,
      user: {
        id: 1,
        username: 'testuser',
        role: 'user',
        is_active: true,
      },
    }
    
    vi.mocked(authApi.login).mockResolvedValue(mockResponse)
    
    const { currentUser, login } = useAuth()
    expect(currentUser.value).toBeNull()
    
    await login('testuser', 'password')
    expect(currentUser.value).toEqual(mockResponse.user)
  })

  it('should call login and return result', async () => {
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 28800,
      user: {
        id: 1,
        username: 'testuser',
        role: 'user',
        is_active: true,
      },
    }
    
    vi.mocked(authApi.login).mockResolvedValue(mockResponse)
    
    const { login } = useAuth()
    const result = await login('testuser', 'password123')
    
    expect(authApi.login).toHaveBeenCalledWith('testuser', 'password123')
    expect(result).toBe(true)
  })

  it('should call logout', () => {
    const { logout } = useAuth()
    
    logout()
    
    expect(authApi.logout).toHaveBeenCalled()
  })

  it('should call checkAuth and return result', async () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      role: 'user',
      is_active: true,
    }
    
    const validToken = createMockToken({ exp: Math.floor(Date.now() / 1000) + 3600 })
    localStorage.setItem('access_token', validToken)
    localStorage.setItem('user', JSON.stringify(mockUser))
    
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)
    
    const { checkAuth } = useAuth()
    const result = await checkAuth()
    
    expect(result).toBe(true)
  })
})

// Helper function to create mock JWT tokens
function createMockToken(payload: any): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = btoa(JSON.stringify(payload))
  const signature = 'mock-signature'
  return `${header}.${body}.${signature}`
}
