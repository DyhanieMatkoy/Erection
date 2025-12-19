/**
 * Composable for table part virtualization to handle large datasets efficiently
 * Extends the basic virtual scroll with table-specific optimizations
 */
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import type { TableColumn } from '@/types/table-parts'

interface VirtualTableOptions {
  rowHeight: number
  bufferSize?: number
  containerHeight?: number
  enableColumnVirtualization?: boolean
  columnWidth?: number
  visibleColumns?: number
}

interface VirtualTableRow<T> {
  item: T
  index: number
  offsetTop: number
  isVisible: boolean
}

interface VirtualTableColumn {
  column: TableColumn
  index: number
  offsetLeft: number
  isVisible: boolean
}

export function useTablePartVirtualization<T>(
  data: T[],
  columns: TableColumn[],
  options: VirtualTableOptions
) {
  const {
    rowHeight,
    bufferSize = 10,
    containerHeight: providedHeight = 400,
    enableColumnVirtualization = false,
    columnWidth = 150,
    visibleColumns = 10
  } = options

  // Refs for scroll positions
  const scrollTop = ref(0)
  const scrollLeft = ref(0)
  const containerHeight = ref(providedHeight)
  const containerWidth = ref(800)
  const containerRef = ref<HTMLElement | null>(null)

  // Performance monitoring
  const renderTime = ref(0)
  const memoryUsage = ref(0)
  const renderedRowCount = ref(0)
  const renderedColumnCount = ref(0)

  // Calculate visible row range
  const visibleRowRange = computed(() => {
    const start = Math.floor(scrollTop.value / rowHeight)
    const visibleCount = Math.ceil(containerHeight.value / rowHeight)
    const end = start + visibleCount

    return {
      start: Math.max(0, start - bufferSize),
      end: Math.min(data.length, end + bufferSize)
    }
  })

  // Calculate visible column range (if column virtualization is enabled)
  const visibleColumnRange = computed(() => {
    if (!enableColumnVirtualization) {
      return {
        start: 0,
        end: columns.length
      }
    }

    const start = Math.floor(scrollLeft.value / columnWidth)
    const end = start + visibleColumns

    return {
      start: Math.max(0, start - 2), // Small buffer for columns
      end: Math.min(columns.length, end + 2)
    }
  })

  // Get visible rows with performance tracking
  const visibleRows = computed(() => {
    const startTime = performance.now()
    
    const { start, end } = visibleRowRange.value
    const rows: VirtualTableRow<T>[] = []

    for (let i = start; i < end; i++) {
      if (data[i]) {
        rows.push({
          item: data[i],
          index: i,
          offsetTop: i * rowHeight,
          isVisible: true
        })
      }
    }

    renderedRowCount.value = rows.length
    renderTime.value = performance.now() - startTime
    
    return rows
  })

  // Get visible columns
  const visibleColumnsData = computed(() => {
    const { start, end } = visibleColumnRange.value
    const cols: VirtualTableColumn[] = []

    for (let i = start; i < end; i++) {
      if (columns[i]) {
        cols.push({
          column: columns[i],
          index: i,
          offsetLeft: i * columnWidth,
          isVisible: true
        })
      }
    }

    renderedColumnCount.value = cols.length
    return cols
  })

  // Total dimensions
  const totalHeight = computed(() => data.length * rowHeight)
  const totalWidth = computed(() => columns.length * columnWidth)

  // Offsets for positioning
  const rowOffset = computed(() => visibleRowRange.value.start * rowHeight)
  const columnOffset = computed(() => 
    enableColumnVirtualization ? visibleColumnRange.value.start * columnWidth : 0
  )

  // Memory usage estimation
  const estimatedMemoryUsage = computed(() => {
    const rowSize = 0.5 // KB per row (rough estimate)
    const columnSize = 0.1 // KB per column
    const totalRows = renderedRowCount.value
    const totalCols = renderedColumnCount.value
    
    return (totalRows * rowSize + totalCols * columnSize) / 1024 // Convert to MB
  })

  // Performance metrics
  const performanceMetrics = computed(() => ({
    renderTime: renderTime.value,
    memoryUsage: estimatedMemoryUsage.value,
    renderedRows: renderedRowCount.value,
    renderedColumns: renderedColumnCount.value,
    totalRows: data.length,
    totalColumns: columns.length,
    virtualizationRatio: {
      rows: data.length > 0 ? renderedRowCount.value / data.length : 0,
      columns: columns.length > 0 ? renderedColumnCount.value / columns.length : 0
    }
  }))

  // Scroll handlers
  function handleScroll(event: Event) {
    const target = event.target as HTMLElement
    scrollTop.value = target.scrollTop
    scrollLeft.value = target.scrollLeft
  }

  // Update container dimensions
  function updateContainerDimensions() {
    if (containerRef.value) {
      containerHeight.value = containerRef.value.clientHeight
      containerWidth.value = containerRef.value.clientWidth
    }
  }

  // Scroll to specific row
  function scrollToRow(rowIndex: number, behavior: ScrollBehavior = 'smooth') {
    if (containerRef.value && rowIndex >= 0 && rowIndex < data.length) {
      const targetScrollTop = rowIndex * rowHeight
      containerRef.value.scrollTo({
        top: targetScrollTop,
        behavior
      })
    }
  }

  // Scroll to specific column
  function scrollToColumn(columnIndex: number, behavior: ScrollBehavior = 'smooth') {
    if (containerRef.value && enableColumnVirtualization && 
        columnIndex >= 0 && columnIndex < columns.length) {
      const targetScrollLeft = columnIndex * columnWidth
      containerRef.value.scrollTo({
        left: targetScrollLeft,
        behavior
      })
    }
  }

  // Get row at position
  function getRowAtPosition(y: number): number {
    return Math.floor(y / rowHeight)
  }

  // Get column at position
  function getColumnAtPosition(x: number): number {
    return Math.floor(x / columnWidth)
  }

  // Optimize for large dataset changes
  function optimizeForDataChange(newDataLength: number) {
    // Reset scroll if data changed significantly
    if (Math.abs(newDataLength - data.length) > data.length * 0.5) {
      if (containerRef.value) {
        containerRef.value.scrollTop = 0
        containerRef.value.scrollLeft = 0
      }
      scrollTop.value = 0
      scrollLeft.value = 0
    }
  }

  // Setup and cleanup
  onMounted(() => {
    if (containerRef.value) {
      containerRef.value.addEventListener('scroll', handleScroll, { passive: true })
      updateContainerDimensions()
    }

    window.addEventListener('resize', updateContainerDimensions)
  })

  onUnmounted(() => {
    if (containerRef.value) {
      containerRef.value.removeEventListener('scroll', handleScroll)
    }
    window.removeEventListener('resize', updateContainerDimensions)
  })

  // Watch for data changes
  watch(() => data.length, (newLength, oldLength) => {
    if (oldLength !== undefined) {
      optimizeForDataChange(newLength)
    }
  })

  // Watch for performance issues
  watch(renderTime, (time) => {
    if (time > 16) { // More than one frame at 60fps
      console.warn(`[Table Virtualization] Slow render detected: ${time.toFixed(2)}ms`)
    }
  })

  return {
    // Refs
    containerRef,
    
    // Computed data
    visibleRows,
    visibleColumnsData,
    totalHeight,
    totalWidth,
    rowOffset,
    columnOffset,
    
    // Performance metrics
    performanceMetrics,
    
    // Methods
    scrollToRow,
    scrollToColumn,
    getRowAtPosition,
    getColumnAtPosition,
    updateContainerDimensions,
    
    // State
    scrollTop,
    scrollLeft
  }
}