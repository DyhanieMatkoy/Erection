<template>
  <div class="relative">
    <label v-if="label" class="block text-sm font-medium text-gray-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    
    <button
      type="button"
      :disabled="disabled"
      :class="[
        'relative w-full cursor-pointer rounded-md border bg-white py-2 pl-3 pr-10 text-left shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm',
        error ? 'border-red-300' : 'border-gray-300',
        disabled ? 'bg-gray-100 cursor-not-allowed' : ''
      ]"
      @click="open = !open"
    >
      <span v-if="selectedItem" class="block truncate">{{ selectedItem[displayKey] }}</span>
      <span v-else class="block truncate text-gray-400">{{ placeholder }}</span>
      <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
        <svg class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a.75.75 0 01.55.24l3.25 3.5a.75.75 0 11-1.1 1.02L10 4.852 7.3 7.76a.75.75 0 01-1.1-1.02l3.25-3.5A.75.75 0 0110 3zm-3.76 9.2a.75.75 0 011.06.04l2.7 2.908 2.7-2.908a.75.75 0 111.1 1.02l-3.25 3.5a.75.75 0 01-1.1 0l-3.25-3.5a.75.75 0 01.04-1.06z" clip-rule="evenodd" />
        </svg>
      </span>
    </button>

    <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>

    <!-- Dropdown -->
    <Transition
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
      >
        <!-- Search -->
        <div class="sticky top-0 bg-white px-2 py-2 border-b border-gray-200">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск..."
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            @click.stop
          />
        </div>

        <!-- Clear option (if not required) -->
        <div v-if="!required && modelValue">
          <div
            class="relative cursor-pointer select-none py-2 pl-3 pr-9 hover:bg-gray-100 text-gray-500 border-b border-gray-200"
            @click="clearSelection"
          >
            <span class="block truncate italic">Очистить выбор</span>
          </div>
        </div>

        <!-- Items -->
        <div v-if="filteredItems.length > 0">
          <div
            v-for="item in filteredItems"
            :key="String(item[valueKey])"
            :class="[
              'relative cursor-pointer select-none py-2 pl-3 pr-9 hover:bg-gray-100',
              modelValue === item[valueKey] ? 'bg-blue-50 text-blue-900' : 'text-gray-900'
            ]"
            @click="selectItem(item)"
          >
            <span :class="['block truncate', modelValue === item[valueKey] ? 'font-semibold' : 'font-normal']">
              {{ item[displayKey] }}
            </span>
            <span
              v-if="modelValue === item[valueKey]"
              class="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600"
            >
              <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
              </svg>
            </span>
          </div>
        </div>
        <div v-else class="py-2 px-3 text-sm text-gray-500">
          Ничего не найдено
        </div>
      </div>
    </Transition>

    <!-- Backdrop to close dropdown -->
    <div
      v-if="open"
      class="fixed inset-0 z-0"
      @click="open = false"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

 
export interface PickerItem {
      [key: string]: any
      id: number | string
    }

const props = withDefaults(
  defineProps<{
    label?: string
    modelValue?: number | string | null
    items: PickerItem[]
    valueKey?: string
    displayKey?: string
    placeholder?: string
    required?: boolean
    disabled?: boolean
    error?: string
  }>(),
  {
    valueKey: 'id',
    displayKey: 'name',
    placeholder: 'Выберите...',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: number | string | null]
}>()

const open = ref(false)
const searchQuery = ref('')

const selectedItem = computed(() => {
  return props.items.find(item => item[props.valueKey] === props.modelValue)
})

const filteredItems = computed(() => {
  if (!searchQuery.value) {
    return props.items
  }
  
  const query = searchQuery.value.toLowerCase()
  return props.items.filter(item => {
    const displayValue = item[props.displayKey]
    return typeof displayValue === 'string' && displayValue.toLowerCase().includes(query)
  })
})

function selectItem(item: PickerItem) {
  emit('update:modelValue', item[props.valueKey] as number | string)
  open.value = false
  searchQuery.value = ''
}

function clearSelection() {
  emit('update:modelValue', null)
  open.value = false
  searchQuery.value = ''
}

watch(open, (newValue) => {
  if (!newValue) {
    searchQuery.value = ''
  }
})
</script>
