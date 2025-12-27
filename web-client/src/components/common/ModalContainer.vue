<template>
  <div>
    <!-- Render all active modals -->
    <Modal
      v-for="[id, modal] in modals"
      :key="id"
      :open="modal.isOpen"
      :title="modal.title"
      :size="modal.size"
      :closable="modal.closable"
      :close-on-backdrop="modal.closeOnBackdrop"
      :fullscreen="modal.fullscreen"
      :modal="modal.modal"
      :z-index="modal.zIndex"
      :modal-id="id"
      @close="closeModal(id)"
    >
      <!-- Render the dynamic component -->
      <component
        :is="modal.component"
        v-bind="modal.props"
        @close="closeModal(id)"
      />
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { useModal } from '@/composables/useModal'
import Modal from './Modal.vue'

const { modals, closeModal } = useModal()
</script>