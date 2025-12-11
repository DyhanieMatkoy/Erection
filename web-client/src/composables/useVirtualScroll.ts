/**
 * Composable for virtual scrolling to handle large lists efficiently
 * Only renders visible items plus a buffer for smooth scrolling
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface VirtualScrollOptions {
  itemHeight: number // Height of each item in pixels
  bufferSize?: number // Number of items to render above/below visible area
  containerHeight?: number // Height of scroll container (auto-detected if not provided)
}

export function useVirtualScroll<T>(
  items: T[],
  options: VirtualScrollOptions
) {
  const { itemHeight, bufferSize = 5, containerHeight: providedHeight } = options

  const scrollTop = ref(0)
  const containerHeight = ref(providedHeight || 400)
  const containerRef = ref<HTMLElement | null>(null)

  // Calculate visible range
  const visibleRange = computed(() => {
    const start = Math.floor(scrollTop.value / itemHeight)
    const visibleCount = Math.ceil(containerHeight.value / itemHeight)
    const end = start + visibleCount

    return {
      start: Math.max(0, start - bufferSize),
      end: Math.min(items.length, end + bufferSize)
    }
  })

  // Get visible items
  const visibleItems = computed(() => {
    const { start, end } = visibleRange.value
    return items.slice(start, end).map((item, index) => ({
      item,
      index: start + index,
      offsetTop: (start + index) * itemHeight
    }))
  })

  // Total height of all items
  const totalHeight = computed(() => items.length * itemHeight)

  // Offset for the visible items container
  const offsetY = computed(() => {
    return visibleRange.value.start * itemHeight
  })

  // Handle scroll event
  function handleScroll(event: Event) {
    const target = event.target as HTMLElement
    scrollTop.value = target.scrollTop
  }

  // Update container height
  function updateContainerHeight() {
    if (containerRef.value) {
      containerHeight.value = containerRef.value.clientHeight
    }
  }

  // Setup
  onMounted(() => {
    if (containerRef.value) {
      containerRef.value.addEventListener('scroll', handleScroll)
      updateContainerHeight()
    }

    window.addEventListener('resize', updateContainerHeight)
  })

  // Cleanup
  onUnmounted(() => {
    if (containerRef.value) {
      containerRef.value.removeEventListener('scroll', handleScroll)
    }
    window.removeEventListener('resize', updateContainerHeight)
  })

  // Watch for items changes
  watch(() => items.length, () => {
    // Reset scroll position when items change significantly
    if (scrollTop.value > totalHeight.value) {
      scrollTop.value = 0
      if (containerRef.value) {
        containerRef.value.scrollTop = 0
      }
    }
  })

  return {
    containerRef,
    visibleItems,
    totalHeight,
    offsetY,
    scrollTop
  }
}
