<template>
  <button
    :class="[
      'inline-flex items-center px-3 py-2 border text-sm font-medium rounded-md transition-colors',
      variantClasses,
      sizeClasses,
      disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
    ]"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <span v-if="icon" v-html="iconHtml" class="flex-shrink-0" :class="{ 'mr-2': !!$slots.default }"></span>
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getIcon, type IconProps, ICON_NAMES } from '@/utils/icons'

interface Props {
  icon?: keyof typeof ICON_NAMES | string
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'secondary',
  size: 'md',
  disabled: false
})

defineEmits<{
  click: []
}>()

const iconHtml = computed(() => {
  if (!props.icon) return ''
  
  const iconProps: IconProps = {
    class: props.size === 'sm' ? 'h-4 w-4' : props.size === 'lg' ? 'h-6 w-6' : 'h-5 w-5'
  }
  
  // Check if it's a standard icon name
  const iconName = props.icon as keyof typeof ICON_NAMES
  if (iconName in ICON_NAMES) {
    return getIcon(ICON_NAMES[iconName], iconProps)
  }
  
  // Fallback to direct icon name
  return getIcon(props.icon as any, iconProps)
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'border-transparent text-white bg-blue-600 hover:bg-blue-700'
    case 'success':
      return 'border-transparent text-white bg-green-600 hover:bg-green-700'
    case 'warning':
      return 'border-transparent text-white bg-yellow-600 hover:bg-yellow-700'
    case 'danger':
      return 'border-transparent text-white bg-red-600 hover:bg-red-700'
    case 'secondary':
    default:
      return 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-2 py-1 text-xs'
    case 'lg':
      return 'px-4 py-3 text-base'
    case 'md':
    default:
      return 'px-3 py-2 text-sm'
  }
})
</script>