import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { login, logout, getCurrentUser } from '../auth'
import apiClient from '../client'

// Mock the API client
vi.mock('../client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

describe('auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('should send login request and return response data', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          token_type: 'bearer',
          expires_in: 28800,
          user: {
            id: 1,
            username: 'testuser',
            role: 'admin',
            is_active: true,
          },
        },
      }
      
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)
      
      const result = await login('testuser', 'password123')
      
      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        username: 'testuser',
        password: 'password123',
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('should throw error on failed login', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Invalid credentials'))
      
      await expect(login('testuser', 'wrongpassword')).rejects.toThrow('Invalid credentials')
    })
  })

  describe('logout', () => {
    it('should clear localStorage', () => {
      localStorage.setItem('access_token', 'test-token')
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'test' }))
      
      logout()
      
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })

  describe('getCurrentUser', () => {
    it('should fetch current user info', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        role: 'admin',
        is_active: true,
      }
      
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })
      
      const result = await getCurrentUser()
      
      expect(apiClient.get).toHaveBeenCalledWith('/auth/me')
      expect(result).toEqual(mockUser)
    })

    it('should throw error when request fails', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Unauthorized'))
      
      await expect(getCurrentUser()).rejects.toThrow('Unauthorized')
    })
  })
})
