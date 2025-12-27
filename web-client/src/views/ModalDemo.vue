<template>
  <div class="container mx-auto p-6">
    <h1 class="text-3xl font-bold text-gray-900 mb-8">Modal Service Demo</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Basic Modal -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4">Basic Modal</h2>
        <p class="text-gray-600 mb-4">Standard modal dialog with backdrop</p>
        <button
          @click="openBasicModal"
          class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Open Basic Modal
        </button>
      </div>

      <!-- Non-Modal Dialog -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4">Non-Modal Dialog</h2>
        <p class="text-gray-600 mb-4">Dialog that doesn't block interaction</p>
        <button
          @click="openNonModalDialog"
          class="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          Open Non-Modal
        </button>
      </div>

      <!-- Large Modal -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4">Large Modal</h2>
        <p class="text-gray-600 mb-4">Modal with larger size</p>
        <button
          @click="openLargeModal"
          class="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          Open Large Modal
        </button>
      </div>

      <!-- Stacked Modals -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4">Stacked Modals</h2>
        <p class="text-gray-600 mb-4">Test modal stacking with proper z-index</p>
        <button
          @click="openStackedModal"
          class="w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
        >
          Open Stacked Modal
        </button>
      </div>

      <!-- Multiple Non-Modal -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4">Multiple Non-Modal</h2>
        <p class="text-gray-600 mb-4">Open multiple non-modal dialogs</p>
        <button
          @click="openMultipleNonModal"
          class="w-full px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
        >
          Open Multiple
        </button>
      </div>

      <!-- Control Panel -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4">Control Panel</h2>
        <div class="space-y-2">
          <button
            @click="closeAllModals"
            class="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Close All Modals
          </button>
          <button
            @click="closeTopModal"
            class="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Close Top Modal
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Status -->
    <div class="mt-8 bg-gray-50 p-6 rounded-lg">
      <h2 class="text-xl font-semibold mb-4">Modal Status</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h3 class="font-medium mb-2">Active Modals: {{ modals.size }}</h3>
          <ul class="space-y-1">
            <li
              v-for="[id, modal] in modals"
              :key="id"
              class="text-sm bg-white p-2 rounded border"
            >
              <strong>{{ id }}</strong> - Z-Index: {{ modal.zIndex }} - 
              {{ modal.modal ? 'Modal' : 'Non-Modal' }}
            </li>
          </ul>
        </div>
        <div>
          <h3 class="font-medium mb-2">Modal Stack Order:</h3>
          <ol class="space-y-1">
            <li
              v-for="(id, index) in modalStack"
              :key="id"
              class="text-sm bg-white p-2 rounded border"
            >
              {{ index + 1 }}. {{ id }}
            </li>
          </ol>
        </div>
      </div>
    </div>

    <!-- Modal Container -->
    <ModalContainer />
  </div>
</template>

<script setup lang="ts">
import { useModal } from '@/composables/useModal'
import ModalContainer from '@/components/common/ModalContainer.vue'
import ExampleModalContent from '@/components/common/ExampleModalContent.vue'

const { modals, modalStack, showModal, closeAllModals, closeTopModal } = useModal()

const openBasicModal = () => {
  showModal({
    id: 'basic-modal',
    component: ExampleModalContent,
    props: {
      title: 'Basic Modal',
      modalId: 'basic-modal'
    },
    title: 'Basic Modal',
    size: 'md'
  })
}

const openNonModalDialog = () => {
  showModal({
    id: `non-modal-${Date.now()}`,
    component: ExampleModalContent,
    props: {
      title: 'Non-Modal Dialog',
      modalId: `non-modal-${Date.now()}`,
      showControls: false
    },
    title: 'Non-Modal Dialog',
    size: 'md',
    modal: false
  })
}

const openLargeModal = () => {
  showModal({
    id: 'large-modal',
    component: ExampleModalContent,
    props: {
      title: 'Large Modal',
      modalId: 'large-modal'
    },
    title: 'Large Modal',
    size: 'xl'
  })
}

const openStackedModal = () => {
  showModal({
    id: 'stacked-modal-1',
    component: ExampleModalContent,
    props: {
      title: 'First Stacked Modal',
      modalId: 'stacked-modal-1'
    },
    title: 'First Stacked Modal',
    size: 'lg'
  })
}

const openMultipleNonModal = () => {
  for (let i = 1; i <= 3; i++) {
    showModal({
      id: `multi-non-modal-${i}`,
      component: ExampleModalContent,
      props: {
        title: `Non-Modal ${i}`,
        modalId: `multi-non-modal-${i}`,
        showControls: false
      },
      title: `Non-Modal ${i}`,
      size: 'sm',
      modal: false
    })
  }
}
</script>