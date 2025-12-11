import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'

/**
 * Composable for authentication logic
 */
export function useAuth() {
  const authStore = useAuthStore()

  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const isAdmin = computed(() => authStore.isAdmin)
  const currentUser = computed(() => authStore.currentUser)

  async function login(username: string, password: string) {
    return await authStore.login(username, password)
  }

  function logout() {
    authStore.logout()
  }

  async function checkAuth() {
    return await authStore.checkAuth()
  }

  return {
    isAuthenticated,
    isAdmin,
    currentUser,
    login,
    logout,
    checkAuth,
  }
}
