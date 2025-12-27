<template>
  <div class="p-4">
    <h3 class="text-lg font-medium text-gray-900 mb-4">{{ title || 'Example Modal' }}</h3>
    
    <div class="space-y-4">
      <p class="text-gray-600">
        This is an example modal content. Modal ID: <code class="bg-gray-100 px-1 rounded">{{ modalId }}</code>
      </p>
      
      <div v-if="showControls" class="space-y-2">
        <button
          @click="openNestedModal"
          class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Open Nested Modal
        </button>
        
        <button
          @click="openNonModalDialog"
          class="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          Open Non-Modal Dialog
        </button>
      </div>
      
      <div class="flex justify-end space-x-2 pt-4 border-t">
        <button
          @click="$emit('close')"
          class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Cancel
        </button>
        <button
          @click="handleConfirm"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Confirm
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useModal } from '@/composables/useModal'

const props = withDefaults(
  defineProps<{
    title?: string
    modalId?: string
    showControls?: boolean
  }>(),
  {
    showControls: true
  }
)

const emit = defineEmits<{
  close: []
  confirm: []
}>()

const { showModal } = useModal()

const openNestedModal = () => {
  showModal({
    id: `nested-${Date.now()}`,
    component: () => import('./ExampleModalContent.vue'),
    props: {
      title: 'Nested Modal',
      showControls: false
    },
    title: 'Nested Modal',
    size: 'sm'
  })
}

const openNonModalDialog = () => {
  showModal({
    id: `non-modal-${Date.now()}`,
    component: () => import('./ExampleModalContent.vue'),
    props: {
      title: 'Non-Modal Dialog',
      showControls: false
    },
    title: 'Non-Modal Dialog',
    size: 'md',
    modal: false // This makes it non-modal
  })
}

const handleConfirm = () => {
  emit('confirm')
  emit('close')
}
</script>