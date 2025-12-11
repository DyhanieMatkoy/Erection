<template>
  <div class="space-y-1">
    <label v-if="label" :for="id" class="block text-sm font-medium text-gray-700">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    
    <input
      v-if="type !== 'select' && type !== 'textarea'"
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :min="min"
      :max="max"
      :step="step"
      :class="[
        'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : '',
        disabled ? 'bg-gray-100 cursor-not-allowed' : ''
      ]"
      @input="handleInput"
    />
    
    <textarea
      v-else-if="type === 'textarea'"
      :id="id"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :rows="rows"
      :class="[
        'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : '',
        disabled ? 'bg-gray-100 cursor-not-allowed' : ''
      ]"
      @input="handleTextareaInput"
    ></textarea>
    
    <select
      v-else-if="type === 'select'"
      :id="id"
      :value="modelValue"
      :required="required"
      :disabled="disabled"
      :class="[
        'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : '',
        disabled ? 'bg-gray-100 cursor-not-allowed' : ''
      ]"
      @change="handleSelectChange"
    >
      <option v-if="placeholder" value="">{{ placeholder }}</option>
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-else-if="hint" class="text-sm text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
interface Option {
  value: string | number
  label: string
}

withDefaults(
  defineProps<{
    id?: string
    label?: string
    type?: 'text' | 'number' | 'date' | 'email' | 'password' | 'tel' | 'select' | 'textarea'
    modelValue?: string | number
    placeholder?: string
    required?: boolean
    disabled?: boolean
    error?: string
    hint?: string
    min?: number | string
    max?: number | string
    step?: number | string
    rows?: number
    options?: Option[]
  }>(),
  {
    type: 'text',
    rows: 3,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function handleTextareaInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

function handleSelectChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}
</script>
