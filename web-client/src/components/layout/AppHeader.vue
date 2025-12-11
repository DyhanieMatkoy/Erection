<template>
  <header class="bg-white shadow-sm sticky top-0 z-50">
    <div class="px-4 py-3 flex items-center justify-between">
      <!-- Mobile menu button -->
      <button
        @click="$emit('toggle-sidebar')"
        class="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
      >
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Logo/Title -->
      <div class="flex items-center">
        <h1 class="text-lg md:text-xl font-semibold text-gray-900">
          Учет строительных работ
        </h1>
      </div>

      <!-- User menu -->
      <div class="flex items-center space-x-4">
        <div class="hidden sm:block text-sm text-gray-700">
          <span class="font-medium">{{ currentUser?.username }}</span>
          <span v-if="isAdmin" class="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
            Администратор
          </span>
        </div>
        
        <button
          @click="handleLogout"
          class="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          title="Выход"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

defineEmits<{
  'toggle-sidebar': []
}>()

const router = useRouter()
const { currentUser, isAdmin, logout } = useAuth()

function handleLogout() {
  logout()
  router.push('/login')
}
</script>
