<template>
  <div>
    <!-- Mobile overlay -->
    <div
      v-if="open"
      class="fixed inset-0 bg-gray-600 bg-opacity-75 z-40 md:hidden"
      @click="$emit('close')"
    ></div>

    <!-- Sidebar -->
    <aside
      :class="[
        'fixed top-0 left-0 z-40 h-screen pt-16 transition-all duration-300 bg-white border-r border-gray-200',
        pinned ? 'w-64' : 'w-64 md:w-16',
        open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      ]"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
    >
    <div class="h-full px-3 pb-4 overflow-y-auto">
      <!-- Pin/Unpin button (desktop only) -->
      <div class="hidden md:flex justify-end pt-2 pb-2 border-b border-gray-200">
        <button
          @click="togglePin"
          class="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          :title="pinned ? 'Открепить меню' : 'Закрепить меню'"
        >
          <svg
            v-if="pinned"
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
          <svg
            v-else
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
        </button>
      </div>
      
      <nav class="space-y-2 mt-4">
        <!-- Dashboard -->
        <RouterLink
          to="/"
          class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100 group"
          active-class="bg-blue-50 text-blue-700"
          @click="$emit('close')"
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
          </svg>
          <span :class="['ml-3 transition-opacity', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Главная</span>
        </RouterLink>

        <!-- References Section -->
        <div class="pt-4">
          <h3 :class="['px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider transition-opacity', showText ? 'opacity-100' : 'md:opacity-0 md:h-0 md:overflow-hidden']">
            Справочники
          </h3>
          <div class="mt-2 space-y-1">
            <RouterLink
              to="/references/counterparties"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Контрагенты' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Контрагенты</span>
            </RouterLink>
            <RouterLink
              to="/references/objects"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Объекты' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Объекты</span>
            </RouterLink>
            <RouterLink
              to="/references/works"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Работы' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Работы</span>
            </RouterLink>
            <RouterLink
              to="/references/persons"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Физические лица' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Физические лица</span>
            </RouterLink>
            <RouterLink
              to="/references/organizations"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Организации' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Организации</span>
            </RouterLink>
          </div>
        </div>

        <!-- Documents Section -->
        <div class="pt-4">
          <h3 :class="['px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider transition-opacity', showText ? 'opacity-100' : 'md:opacity-0 md:h-0 md:overflow-hidden']">
            Документы
          </h3>
          <div class="mt-2 space-y-1">
            <RouterLink
              to="/documents/estimates"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Сметы' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Сметы</span>
            </RouterLink>
            <RouterLink
              to="/documents/daily-reports"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Ежедневные отчеты' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Ежедневные отчеты</span>
            </RouterLink>
            <RouterLink
              to="/documents/timesheets"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Табели' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Табели</span>
            </RouterLink>
          </div>
        </div>

        <!-- Registers Section -->
        <div class="pt-4">
          <h3 :class="['px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider transition-opacity', showText ? 'opacity-100' : 'md:opacity-0 md:h-0 md:overflow-hidden']">
            Регистры
          </h3>
          <div class="mt-2 space-y-1">
            <RouterLink
              to="/registers/work-execution"
              class="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-700"
              @click="$emit('close')"
              :title="!showText ? 'Выполнение работ' : ''"
            >
              <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              <span :class="['ml-3 transition-opacity whitespace-nowrap', showText ? 'opacity-100' : 'md:opacity-0 md:w-0 md:overflow-hidden']">Выполнение работ</span>
            </RouterLink>
          </div>
        </div>
      </nav>
    </div>
  </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  'update:pinned': [value: boolean]
}>()

const pinned = ref(true)
const hovering = ref(false)

// Show text when pinned OR hovering (on desktop)
const showText = computed(() => pinned.value || hovering.value)

onMounted(() => {
  // Load pinned state from localStorage
  const saved = localStorage.getItem('sidebar-pinned')
  if (saved !== null) {
    pinned.value = saved === 'true'
  }
  emit('update:pinned', pinned.value)
})

function togglePin() {
  pinned.value = !pinned.value
  localStorage.setItem('sidebar-pinned', String(pinned.value))
  emit('update:pinned', pinned.value)
}

function onMouseEnter() {
  hovering.value = true
}

function onMouseLeave() {
  hovering.value = false
}
</script>
