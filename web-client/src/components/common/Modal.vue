<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="handleBackdropClick"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>

        <!-- Modal container -->
        <div class="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
          <Transition
            enter-active-class="transition ease-out duration-200"
            enter-from-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enter-to-class="opacity-100 translate-y-0 sm:scale-100"
            leave-active-class="transition ease-in duration-150"
            leave-from-class="opacity-100 translate-y-0 sm:scale-100"
            leave-to-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <div
              v-if="open"
              :class="[
                'relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all',
                'w-full',
                size === 'sm' ? 'sm:max-w-sm' : '',
                size === 'md' ? 'sm:max-w-lg' : '',
                size === 'lg' ? 'sm:max-w-2xl' : '',
                size === 'xl' ? 'sm:max-w-4xl' : '',
                size === 'full' ? 'sm:max-w-7xl' : '',
                fullscreen ? 'h-screen sm:h-auto' : ''
              ]"
            >
              <!-- Header -->
              <div v-if="$slots.header || title" class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4 border-b border-gray-200">
                <div class="flex items-center justify-between">
                  <slot name="header">
                    <h3 class="text-lg font-medium leading-6 text-gray-900">{{ title }}</h3>
                  </slot>
                  <button
                    v-if="closable"
                    @click="handleClose"
                    class="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <span class="sr-only">Закрыть</span>
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Body -->
              <div class="bg-white px-4 pt-5 pb-4 sm:p-6">
                <slot></slot>
              </div>

              <!-- Footer -->
              <div v-if="$slots.footer" class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 border-t border-gray-200">
                <slot name="footer"></slot>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
    closable?: boolean
    closeOnBackdrop?: boolean
    fullscreen?: boolean
  }>(),
  {
    size: 'md',
    closable: true,
    closeOnBackdrop: true,
    fullscreen: false,
  }
)

const emit = defineEmits<{
  close: []
}>()

function handleClose() {
  emit('close')
}

function handleBackdropClick() {
  if (props.closeOnBackdrop) {
    handleClose()
  }
}

function handleEscape(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open && props.closable) {
    handleClose()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})
</script>
