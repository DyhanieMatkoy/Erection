import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import type { UserInfo } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<UserInfo | null>(null)
  const token = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isManager = computed(() => user.value?.role === 'manager')
  const isForeman = computed(() => user.value?.role === 'foreman')
  const currentUser = computed(() => user.value)

  const canCreateGeneralEstimate = computed(() => {
    return isAdmin.value || isManager.value
  })

  const canCreatePlanEstimate = computed(() => {
    return isAdmin.value || isManager.value || isForeman.value
  })

  const canModifyHierarchy = computed(() => {
    return isAdmin.value || isManager.value
  })

  // Actions
  async function login(username: string, password: string) {
    try {
      const response = await authApi.login(username, password)
      
      // Store token and user info
      token.value = response.access_token
      user.value = response.user
      
      // Persist to localStorage
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      
      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  function logout() {
    // Clear state
    token.value = null
    user.value = null
    
    // Clear localStorage
    authApi.logout()
  }

  async function checkAuth() {
    // Try to restore from localStorage
    const storedToken = localStorage.getItem('access_token')
    const storedUser = localStorage.getItem('user')
    
    if (!storedToken || !storedUser) {
      return false
    }

    // Check if token is expired
    try {
      const tokenParts = storedToken.split('.')
      if (tokenParts.length !== 3 || !tokenParts[1]) {
        logout()
        return false
      }
      const payload = JSON.parse(atob(tokenParts[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      
      if (Date.now() >= exp) {
        // Token expired
        logout()
        return false
      }

      // Verify token with backend
      const userInfo = await authApi.getCurrentUser()
      
      // Restore state
      token.value = storedToken
      user.value = userInfo
      
      return true
    } catch (error) {
      console.error('Auth check failed:', error)
      logout()
      return false
    }
  }

  return {
    // State
    user,
    token,
    // Getters
    isAuthenticated,
    isAdmin,
    isManager,
    isForeman,
    currentUser,
    canCreateGeneralEstimate,
    canCreatePlanEstimate,
    canModifyHierarchy,
    // Actions
    login,
    logout,
    checkAuth,
  }
})
