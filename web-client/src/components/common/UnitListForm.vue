<template>
  <ListForm
    :is-open="isOpen"
    :title="title"
    search-placeholder="Search by name..."
    loading-message="Loading units..."
    empty-message="No units found"
    confirm-button-text="Select Unit"
    :items="units || []"
    :loading="loading"
    :error="error"
    :selected-item="selectedItem"
    :show-pagination="false"
    :get-item-key="(item) => item.id"
    :get-item-code="(item) => item.name"
    :get-item-description="(item) => item.description || ''"
    :is-item-disabled="() => false"
    @close="handleClose"
    @select="handleSelect"
    @retry="loadUnits"
  >
    <template #item="{ item, highlightText }">
      <div class="unit-content">
        <div class="item-details">
          <div class="item-name" v-html="highlightText(item.name)"></div>
          <div v-if="item.description" class="item-description" v-html="highlightText(item.description || '')"></div>
        </div>
      </div>
    </template>
  </ListForm>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import ListForm from './ListForm.vue'
import { unitsApi } from '@/api/costs-materials'
import type { Unit } from '@/types/models'

interface Props {
  isOpen: boolean
  title?: string
}

interface Emits {
  (e: 'close'): void
  (e: 'select', unit: Unit): void
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Select Unit'
})

const emit = defineEmits<Emits>()

// State
const units = ref<Unit[]>([])
const selectedItem = ref<Unit | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Watch for dialog open
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && units.value.length === 0) {
    loadUnits()
  }
  if (isOpen) {
    selectedItem.value = null
  }
})

// Methods
async function loadUnits() {
  loading.value = true
  error.value = null
  try {
    units.value = await unitsApi.getAll(false)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load units'
    console.error('Error loading units:', err)
  } finally {
    loading.value = false
  }
}

function handleSelect(item: Unit) {
  emit('select', item)
}

function handleClose() {
  emit('close')
}
</script>

<style scoped>
.unit-content {
  display: flex;
  width: 100%;
}

.item-details {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-weight: 600;
  color: #212529;
  margin-bottom: 0.25rem;
}

.item-description {
  font-size: 0.875rem;
  color: #6c757d;
}
</style>
