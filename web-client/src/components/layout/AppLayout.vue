<template>
  <div class="min-h-screen bg-gray-100">
    <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />
    
    <div class="flex">
      <AppSidebar 
        :open="sidebarOpen" 
        @close="sidebarOpen = false"
        @update:pinned="sidebarPinned = $event"
      />
      
      <main 
        :class="[
          'flex-1 p-4 md:p-6 lg:p-8 transition-all duration-300',
          sidebarPinned ? 'md:ml-64' : 'md:ml-16'
        ]"
      >
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const sidebarOpen = ref(false)
const sidebarPinned = ref(true)
</script>
