import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'
import * as authApi from '@/api/auth'

// Mock the auth API
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
}))

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have null user and token initially', () => {
      const store = useAuthStore()
      
      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isAdmin).toBe(false)
      expect(store.currentUser).toBeNull()
    })
  })

  describe('login', () => {
    it('should successfully login and store credentials', async () => {
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
      
      const store = useAuthStore()
      const result = await store.login('testuser', 'password123')
      
      expect(result).toBe(true)
      expect(store.token).toBe('test-token')
      expect(store.user).toEqual(mockResponse.user)
      expect(store.isAuthenticated).toBe(true)
      expect(store.isAdmin).toBe(true)
      expect(localStorage.getItem('access_token')).toBe('test-token')
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockResponse.user))
    })

    it('should handle login failure', async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))
      
      const store = useAuthStore()
      
      await expect(store.login('testuser', 'wrongpassword')).rejects.toThrow('Invalid credentials')
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('logout', () => {
    it('should clear user data and localStorage', async () => {
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
      
      const store = useAuthStore()
      await store.login('testuser', 'password123')
      
      store.logout()
      
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(authApi.logout).toHaveBeenCalled()
    })
  })

  describe('checkAuth', () => {
    it('should return false when no token in localStorage', async () => {
      const store = useAuthStore()
      const result = await store.checkAuth()
      
      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })

    it('should return false when token is malformed', async () => {
      localStorage.setItem('access_token', 'invalid-token')
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'test', role: 'user', is_active: true }))
      
      const store = useAuthStore()
      const result = await store.checkAuth()
      
      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })

    it('should return false when token is expired', async () => {
      const expiredToken = createMockToken({ exp: Math.floor(Date.now() / 1000) - 3600 })
      localStorage.setItem('access_token', expiredToken)
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'test', role: 'user', is_active: true }))
      
      const store = useAuthStore()
      const result = await store.checkAuth()
      
      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      // Token should be cleared after logout is called
      expect(store.token).toBeNull()
    })

    it('should restore auth state when token is valid', async () => {
      const validToken = createMockToken({ exp: Math.floor(Date.now() / 1000) + 3600 })
      const mockUser = { id: 1, username: 'testuser', role: 'admin', is_active: true }
      
      localStorage.setItem('access_token', validToken)
      localStorage.setItem('user', JSON.stringify(mockUser))
      
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)
      
      const store = useAuthStore()
      const result = await store.checkAuth()
      
      expect(result).toBe(true)
      expect(store.token).toBe(validToken)
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
      expect(authApi.getCurrentUser).toHaveBeenCalled()
    })

    it('should logout when backend verification fails', async () => {
      const validToken = createMockToken({ exp: Math.floor(Date.now() / 1000) + 3600 })
      localStorage.setItem('access_token', validToken)
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'test', role: 'user', is_active: true }))
      
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Unauthorized'))
      
      const store = useAuthStore()
      const result = await store.checkAuth()
      
      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      // Token should be cleared after logout is called
      expect(store.token).toBeNull()
    })
  })

  describe('computed properties', () => {
    it('should compute isAdmin correctly for admin user', async () => {
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
      
      const store = useAuthStore()
      await store.login('admin', 'password')
      
      expect(store.isAdmin).toBe(true)
    })

    it('should compute isAdmin correctly for regular user', async () => {
      const mockResponse = {
        access_token: 'test-token',
        token_type: 'bearer',
        expires_in: 28800,
        user: {
          id: 2,
          username: 'user',
          role: 'user',
          is_active: true,
        },
      }
      
      vi.mocked(authApi.login).mockResolvedValue(mockResponse)
      
      const store = useAuthStore()
      await store.login('user', 'password')
      
      expect(store.isAdmin).toBe(false)
    })
  })
})

// Helper function to create mock JWT tokens
function createMockToken(payload: any): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = btoa(JSON.stringify(payload))
  const signature = 'mock-signature'
  return `${header}.${body}.${signature}`
}
