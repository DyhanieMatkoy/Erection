<template>
  <div class="compact-reference-field" :class="{ 'has-value': hasValue, 'disabled': disabled }">
    <input
      ref="inputRef"
      type="text"
      class="reference-input"
      :value="displayValue"
      :placeholder="placeholder"
      :disabled="disabled"
      readonly
      @focus="onFocus"
      @blur="onBlur"
      @keydown="onKeyDown"
    />
    
    <div class="compact-buttons">
      <button
        v-if="hasValue && allowEdit"
        class="compact-button open-button"
        type="button"
        :disabled="disabled"
        @click="openReference"
        :title="openTooltip"
      >
        o
      </button>
      
      <button
        class="compact-button selector-button"
        type="button"
        :disabled="disabled"
        @click="selectReference"
        :title="selectorTooltip"
      >
        ▼
      </button>
    </div>
    
    <!-- Auto-completion dropdown -->
    <div
      v-if="showAutoComplete && autoCompleteItems.length > 0"
      class="autocomplete-dropdown"
    >
      <div
        v-for="(item, index) in autoCompleteItems"
        :key="item.id"
        class="autocomplete-item"
        :class="{ 'selected': index === selectedAutoCompleteIndex }"
        @click="selectAutoCompleteItem(item)"
        @mouseenter="selectedAutoCompleteIndex = index"
      >
        <span class="item-name">{{ item.name }}</span>
        <span v-if="item.code" class="item-code">{{ item.code }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { ReferenceValue, ReferenceFieldConfig } from '@/types/table-parts'
import { referenceSelectorService } from '@/services/referenceSelectorService'

// Props
interface Props {
  modelValue?: ReferenceValue | null
  referenceType: string
  placeholder?: string
  disabled?: boolean
  allowEdit?: boolean
  allowCreate?: boolean
  relatedFields?: string[]
  autoComplete?: boolean
  minSearchLength?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Не выбрано',
  disabled: false,
  allowEdit: true,
  allowCreate: false,
  relatedFields: () => [],
  autoComplete: true,
  minSearchLength: 3
})

// Emits
interface Emits {
  (e: 'update:modelValue', value: ReferenceValue | null): void
  (e: 'open-reference', value: ReferenceValue): void
  (e: 'select-reference', referenceType: string, currentValue?: ReferenceValue | null): void
  (e: 'fill-related-fields', referenceValue: ReferenceValue, relatedFields: string[]): void
}

const emit = defineEmits<Emits>()

// Refs
const inputRef = ref<HTMLInputElement>()
const showAutoComplete = ref(false)
const autoCompleteItems = ref<ReferenceValue[]>([])
const selectedAutoCompleteIndex = ref(-1)
const searchQuery = ref('')
const isLoading = ref(false)

// Computed
const hasValue = computed(() => props.modelValue && props.modelValue.id > 0)

const displayValue = computed(() => {
  if (props.modelValue && props.modelValue.name) {
    return props.modelValue.name
  }
  return ''
})

const openTooltip = computed(() => 'Открыть элемент (F4)')
const selectorTooltip = computed(() => 'Выбрать из списка (Enter)')

// Methods
function onFocus() {
  if (props.autoComplete && !props.disabled) {
    // Could implement focus-based auto-complete here
  }
}

function onBlur() {
  // Hide auto-complete after a delay to allow clicking on items
  setTimeout(() => {
    showAutoComplete.value = false
    selectedAutoCompleteIndex.value = -1
  }, 200)
}

function onKeyDown(event: KeyboardEvent) {
  switch (event.key) {
    case 'F4':
      event.preventDefault()
      if (hasValue.value && props.allowEdit) {
        openReference()
      } else {
        selectReference()
      }
      break
    
    case 'Enter':
      event.preventDefault()
      if (showAutoComplete.value && selectedAutoCompleteIndex.value >= 0) {
        selectAutoCompleteItem(autoCompleteItems.value[selectedAutoCompleteIndex.value])
      } else {
        selectReference()
      }
      break
    
    case 'ArrowDown':
      if (showAutoComplete.value) {
        event.preventDefault()
        selectedAutoCompleteIndex.value = Math.min(
          selectedAutoCompleteIndex.value + 1,
          autoCompleteItems.value.length - 1
        )
      }
      break
    
    case 'ArrowUp':
      if (showAutoComplete.value) {
        event.preventDefault()
        selectedAutoCompleteIndex.value = Math.max(selectedAutoCompleteIndex.value - 1, 0)
      }
      break
    
    case 'Escape':
      if (showAutoComplete.value) {
        event.preventDefault()
        showAutoComplete.value = false
        selectedAutoCompleteIndex.value = -1
      }
      break
  }
}

async function openReference() {
  if (hasValue.value && props.allowEdit && !props.disabled) {
    try {
      await referenceSelectorService.openReference(props.referenceType, props.modelValue!.id)
    } catch (error) {
      console.error('Failed to open reference:', error)
    }
    
    // Also emit the original event for backward compatibility
    emit('open-reference', props.modelValue!)
  }
}

async function selectReference() {
  if (!props.disabled) {
    try {
      const result = await referenceSelectorService.openSelector({
        referenceType: props.referenceType,
        currentValue: props.modelValue,
        allowCreate: props.allowCreate,
        allowEdit: props.allowEdit
      })
      
      if (result.selected && result.value) {
        emit('update:modelValue', result.value)
        
        // Fill related fields if configured
        if (props.relatedFields.length > 0) {
          const relatedData = await referenceSelectorService.fillRelatedFields(
            props.referenceType,
            result.value.id,
            props.relatedFields
          )
          emit('fill-related-fields', result.value, props.relatedFields)
        }
      }
    } catch (error) {
      console.error('Reference selection failed:', error)
    }
    
    // Also emit the original event for backward compatibility
    emit('select-reference', props.referenceType, props.modelValue)
  }
}

function selectAutoCompleteItem(item: ReferenceValue) {
  emit('update:modelValue', item)
  showAutoComplete.value = false
  selectedAutoCompleteIndex.value = -1
  
  // Fill related fields if configured
  if (props.relatedFields.length > 0) {
    emit('fill-related-fields', item, props.relatedFields)
  }
}

async function searchAutoComplete(query: string) {
  if (query.length < props.minSearchLength) {
    autoCompleteItems.value = []
    showAutoComplete.value = false
    return
  }
  
  isLoading.value = true
  
  try {
    const results = await referenceSelectorService.getAutoComplete({
      referenceType: props.referenceType,
      query,
      minLength: props.minSearchLength,
      limit: 10
    })
    
    autoCompleteItems.value = results
    showAutoComplete.value = results.length > 0
    selectedAutoCompleteIndex.value = results.length > 0 ? 0 : -1
  } catch (error) {
    console.error('Auto-complete search failed:', error)
    autoCompleteItems.value = []
    showAutoComplete.value = false
  } finally {
    isLoading.value = false
  }
}

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  if (!newValue) {
    searchQuery.value = ''
  }
})

// Focus method for external use
function focus() {
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// Expose methods
defineExpose({
  focus
})
</script>

<style scoped>
.compact-reference-field {
  position: relative;
  display: inline-block;
  width: 100%;
}

.reference-input {
  width: 100%;
  padding: 6px 60px 6px 8px; /* Space for buttons on right */
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  background-color: #fff;
  cursor: pointer;
}

.reference-input:focus {
  outline: none;
  border-color: #0056b3;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.reference-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.compact-buttons {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  gap: 2px;
}

.compact-button {
  width: 24px;
  height: 24px;
  border: 1px solid #999;
  background: #f5f5f5;
  border-radius: 2px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}

.compact-button:hover:not(:disabled) {
  background: #e9ecef;
  border-color: #666;
}

.compact-button:active:not(:disabled) {
  background: #dee2e6;
  border-color: #333;
}

.compact-button:disabled {
  background: #f8f9fa;
  border-color: #dee2e6;
  color: #6c757d;
  cursor: not-allowed;
}

.open-button {
  font-weight: bold;
}

.selector-button {
  font-size: 10px;
}

.has-value .reference-input {
  color: #212529;
}

.disabled {
  opacity: 0.6;
}

/* Auto-complete dropdown */
.autocomplete-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ccc;
  border-top: none;
  border-radius: 0 0 4px 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
}

.autocomplete-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.autocomplete-item:hover,
.autocomplete-item.selected {
  background-color: #f8f9fa;
}

.autocomplete-item.selected {
  background-color: #e3f2fd;
}

.item-name {
  flex: 1;
  font-weight: 500;
}

.item-code {
  font-size: 12px;
  color: #6c757d;
  margin-left: 8px;
}
</style>