<!--
  Optimized Table Part Component for Large Datasets
  
  Features:
  - Virtual scrolling for 1000+ rows
  - Lazy loading with intelligent prefetching
  - Memory optimization and compression
  - Performance monitoring and alerts
-->
<template>
  <div class="optimized-table-part" ref="containerRef">
    <!-- Performance Monitor (when enabled) -->
    <div v-if="showPerformanceMonitor" class="performance-monitor">
      <div class="monitor-header">
        <h4>Performance Monitor</h4>
        <button @click="showPerformanceMonitor = false" class="close-btn">&times;</button>
      </div>
      <div class="monitor-content">
        <div class="metric">
          <label>Rendered Rows:</label>
          <span>{{ performanceMetrics.renderedRows }} / {{ performanceMetrics.totalRows }}</span>
        </div>
        <div class="metric">
          <label>Memory Usage:</label>
          <span>{{ performanceMetrics.memoryUsage.toFixed(2) }} MB</span>
        </div>
        <div class="metric">
          <label>Render Time:</label>
          <span>{{ performanceMetrics.renderTime.toFixed(2) }} ms</span>
        </div>
        <div class="metric">
          <label>Cache Hit Rate:</label>
          <span>{{ (memoryStats.compressionRatio * 100).toFixed(1) }}%</span>
        </div>
      </div>
    </div>

    <!-- Row Control Panel -->
    <div class="row-control-panel">
      <div class="panel-buttons">
        <button
          v-for="command in visibleCommands"
          :key="command.id"
          :class="['btn', 'btn-sm', getButtonClass(command)]"
          :disabled="!isCommandEnabled(command)"
          :title="command.tooltip"
          @click="executeCommand(command.id)"
        >
          <span class="icon">{{ command.icon }}</span>
          {{ command.name }}
        </button>
      </div>
      
      <!-- Performance toggle -->
      <button
        class="btn btn-sm btn-outline-secondary"
        @click="showPerformanceMonitor = !showPerformanceMonitor"
        title="Toggle Performance Monitor"
      >
        📊
      </button>
    </div>

    <!-- Virtual Table Container -->
    <div 
      class="virtual-table-container"
      :style="{ height: containerHeight + 'px' }"
      @scroll="handleScroll"
    >
      <!-- Loading overlay -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>Loading data...</p>
      </div>

      <!-- Virtual table -->
      <div class="virtual-table-wrapper">
        <!-- Table header -->
        <div class="table-header" :style="{ transform: `translateX(-${scrollLeft}px)` }">
          <div class="header-row">
            <div
              v-for="column in visibleColumnsData"
              :key="column.column.id"
              :class="['header-cell', { sortable: column.column.sortable }]"
              :style="{ 
                width: getColumnWidth(column.column) + 'px',
                left: column.offsetLeft + 'px'
              }"
              @click="column.column.sortable && handleSort(column.column.id)"
            >
              {{ column.column.name }}
              <span v-if="column.column.sortable && sortColumn === column.column.id" class="sort-indicator">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Virtual scroll spacer -->
        <div class="virtual-scroll-spacer" :style="{ height: totalHeight + 'px' }">
          <!-- Virtual content -->
          <div
            class="virtual-scroll-content"
            :style="{ 
              transform: `translate(-${scrollLeft}px, ${rowOffset}px)`,
              height: (visibleRows.length * rowHeight) + 'px'
            }"
          >
            <!-- Table rows -->
            <div
              v-for="row in visibleRows"
              :key="getRowKey(row.item, row.index)"
              :class="['table-row', {
                'row-selected': isRowSelected(row.index),
                'row-loading': isRowLoading(row.index)
              }]"
              :style="{ 
                height: rowHeight + 'px',
                top: (row.index - visibleRowRange.start) * rowHeight + 'px'
              }"
              @click="handleRowClick(row.index, $event)"
            >
              <!-- Table cells -->
              <div
                v-for="column in visibleColumnsData"
                :key="column.column.id"
                :class="['table-cell', getCellClass(column.column, row.item)]"
                :style="{ 
                  width: getColumnWidth(column.column) + 'px',
                  left: column.offsetLeft + 'px'
                }"
                @dblclick="handleCellDoubleClick(row.index, column.column.id)"
              >
                <!-- Cell content -->
                <component
                  :is="getCellComponent(column.column)"
                  :value="getCellValue(row.item, column.column)"
                  :column="column.column"
                  :row="row.item"
                  :editable="column.column.editable && !isRowLoading(row.index)"
                  @update:value="updateCellValue(row.index, column.column.id, $event)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!isLoading && totalCount === 0" class="empty-state">
        <p>{{ emptyMessage }}</p>
      </div>
    </div>

    <!-- Status bar -->
    <div class="status-bar">
      <div class="status-left">
        <span v-if="totalCount !== null">
          Showing {{ visibleRows.length }} of {{ totalCount }} rows
        </span>
        <span v-if="isLoading" class="loading-indicator">
          Loading...
        </span>
      </div>
      <div class="status-right">
        <span class="memory-usage">
          Memory: {{ memoryStats.usedMemoryMB.toFixed(1) }}MB
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useTablePartVirtualization } from '@/composables/useTablePartVirtualization'
import { useTablePartLazyLoading } from '@/composables/useTablePartLazyLoading'
import { createMemoryOptimizer } from '@/services/tablePartMemoryOptimizer'
import type { 
  TableColumn, 
  TablePartCommand, 
  TablePartConfiguration,
  PerformanceMetrics 
} from '@/types/table-parts'

// Props
interface Props<T> {
  configuration: TablePartConfiguration
  columns: TableColumn[]
  loadDataFn: (page: number, pageSize: number) => Promise<{ data: T[], totalCount: number }>
  emptyMessage?: string
  rowHeight?: number
  containerHeight?: number
  getRowKey?: (row: T, index: number) => string | number
  isRowSelected?: (index: number) => boolean
}

const props = withDefaults(defineProps<Props<T>>(), {
  emptyMessage: 'No data available',
  rowHeight: 40,
  containerHeight: 400,
  getRowKey: (row: any, index: number) => index,
  isRowSelected: () => false
})

// Emits
interface Emits<T> {
  (e: 'row-selection-changed', selectedRows: number[]): void
  (e: 'cell-value-changed', row: number, column: string, value: any): void
  (e: 'command-executed', commandId: string, context: any): void
  (e: 'performance-alert', metric: string, value: number): void
}

const emit = defineEmits<Emits<T>>()

// Refs
const containerRef = ref<HTMLElement | null>(null)
const showPerformanceMonitor = ref(false)
const selectedRows = ref<number[]>([])
const sortColumn = ref<string | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')
const scrollLeft = ref(0)

// Memory optimizer
const memoryOptimizer = createMemoryOptimizer<T[]>({
  maxMemoryMB: 50,
  cleanupThreshold: 0.8,
  compressionEnabled: true,
  cacheStrategy: 'lru'
})

// Lazy loading
const {
  allData,
  isLoading,
  totalCount,
  loadVisibleRange,
  isRangeLoaded,
  loadingMetrics,
  estimatedMemoryUsage
} = useTablePartLazyLoading(props.loadDataFn, {
  pageSize: 100,
  preloadPages: 2,
  cacheSize: 10,
  enablePrefetch: true
})

// Virtualization
const {
  visibleRows,
  visibleColumnsData,
  totalHeight,
  rowOffset,
  performanceMetrics,
  scrollToRow,
  updateContainerDimensions
} = useTablePartVirtualization(allData.value, props.columns, {
  rowHeight: props.rowHeight,
  bufferSize: 10,
  containerHeight: props.containerHeight,
  enableColumnVirtualization: props.columns.length > 20
})

// Computed
const visibleRowRange = computed(() => {
  if (visibleRows.value.length === 0) {
    return { start: 0, end: 0 }
  }
  return {
    start: visibleRows.value[0].index,
    end: visibleRows.value[visibleRows.value.length - 1].index
  }
})

const visibleCommands = computed(() => {
  return props.configuration.availableCommands.filter(cmd => 
    props.configuration.visibleCommands.includes(cmd.id)
  )
})

const memoryStats = computed(() => memoryOptimizer.getStats())

// Methods
function handleScroll(event: Event) {
  const target = event.target as HTMLElement
  scrollLeft.value = target.scrollLeft
  
  // Load data for visible range
  const range = visibleRowRange.value
  if (range.start !== range.end) {
    loadVisibleRange(range.start, range.end + 20) // Load a bit ahead
  }
}

function handleRowClick(index: number, event: MouseEvent) {
  if (event.ctrlKey) {
    // Multi-select
    const idx = selectedRows.value.indexOf(index)
    if (idx > -1) {
      selectedRows.value.splice(idx, 1)
    } else {
      selectedRows.value.push(index)
    }
  } else {
    // Single select
    selectedRows.value = [index]
  }
  
  emit('row-selection-changed', selectedRows.value)
}

function handleCellDoubleClick(rowIndex: number, columnId: string) {
  const column = props.columns.find(col => col.id === columnId)
  if (column?.editable) {
    // Start editing
    console.log('Start editing cell:', rowIndex, columnId)
  }
}

function handleSort(columnId: string) {
  if (sortColumn.value === columnId) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = columnId
    sortDirection.value = 'asc'
  }
  
  // Trigger data reload with sorting
  // This would need to be implemented based on your data loading strategy
}

function executeCommand(commandId: string) {
  const context = {
    selectedRows: selectedRows.value,
    totalRows: totalCount.value || 0,
    visibleRange: visibleRowRange.value
  }
  
  emit('command-executed', commandId, context)
}

function isCommandEnabled(command: TablePartCommand): boolean {
  switch (command.id) {
    case 'delete_row':
    case 'move_up':
    case 'move_down':
      return selectedRows.value.length > 0
    case 'export_data':
      return (totalCount.value || 0) > 0
    default:
      return true
  }
}

function getButtonClass(command: TablePartCommand): string {
  switch (command.id) {
    case 'add_row':
      return 'btn-primary'
    case 'delete_row':
      return 'btn-danger'
    default:
      return 'btn-secondary'
  }
}

function isRowLoading(index: number): boolean {
  // Check if the row's data is still loading
  return !isRangeLoaded(index, index + 1)
}

function getCellComponent(column: TableColumn): string {
  // Return appropriate cell component based on column type
  switch (column.type) {
    case 'reference':
      return 'CompactReferenceField'
    case 'number':
    case 'currency':
      return 'NumberCell'
    case 'date':
      return 'DateCell'
    default:
      return 'TextCell'
  }
}

function getCellValue(row: T, column: TableColumn): any {
  return (row as any)[column.id]
}

function getCellClass(column: TableColumn, row: T): string {
  const classes = []
  
  if (column.type === 'number' || column.type === 'currency') {
    classes.push('text-right')
  }
  
  if (column.editable) {
    classes.push('editable')
  }
  
  return classes.join(' ')
}

function getColumnWidth(column: TableColumn): number {
  return parseInt(column.width || '150')
}

function updateCellValue(rowIndex: number, columnId: string, value: any) {
  emit('cell-value-changed', rowIndex, columnId, value)
}

// Performance monitoring
watch(performanceMetrics, (metrics) => {
  // Alert on performance issues
  if (metrics.renderTime > 16) {
    emit('performance-alert', 'renderTime', metrics.renderTime)
  }
  
  if (metrics.memoryUsage > 100) {
    emit('performance-alert', 'memoryUsage', metrics.memoryUsage)
  }
}, { deep: true })

// Memory optimization
watch(estimatedMemoryUsage, (usage) => {
  if (usage > 50) { // 50MB threshold
    memoryOptimizer.optimizeMemory().catch(error => {
      console.error('Memory optimization failed:', error)
    })
  }
})

// Lifecycle
onMounted(() => {
  updateContainerDimensions()
  
  // Load initial data
  loadVisibleRange(0, Math.ceil(props.containerHeight / props.rowHeight) + 10)
})

onUnmounted(() => {
  memoryOptimizer.destroy()
})

// Expose methods for parent components
defineExpose({
  scrollToRow,
  showPerformanceMonitor: () => { showPerformanceMonitor.value = true },
  hidePerformanceMonitor: () => { showPerformanceMonitor.value = false },
  getPerformanceMetrics: () => performanceMetrics.value,
  getMemoryStats: () => memoryStats.value,
  refreshData: () => {
    // Implement data refresh
  }
})
</script>

<style scoped>
.optimized-table-part {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.performance-monitor {
  position: absolute;
  top: 10px;
  right: 10px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 1000;
  min-width: 200px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.monitor-header h4 {
  margin: 0;
  font-size: 14px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
}

.monitor-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.metric label {
  font-weight: 500;
}

.row-control-panel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  flex-shrink: 0;
}

.panel-buttons {
  display: flex;
  gap: 4px;
}

.virtual-table-container {
  flex: 1;
  overflow: auto;
  position: relative;
  border: 1px solid #dee2e6;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.virtual-table-wrapper {
  position: relative;
  width: 100%;
}

.table-header {
  position: sticky;
  top: 0;
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  z-index: 10;
}

.header-row {
  position: relative;
  height: 40px;
  display: flex;
}

.header-cell {
  position: absolute;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 8px;
  font-weight: 600;
  border-right: 1px solid #dee2e6;
  background: #f8f9fa;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-cell.sortable {
  cursor: pointer;
  user-select: none;
}

.header-cell.sortable:hover {
  background: #e9ecef;
}

.sort-indicator {
  margin-left: 4px;
  font-size: 12px;
}

.virtual-scroll-spacer {
  position: relative;
  width: 100%;
}

.virtual-scroll-content {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
}

.table-row {
  position: absolute;
  width: 100%;
  display: flex;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
  transition: background-color 0.1s;
}

.table-row:hover {
  background: #f8f9fa;
}

.table-row.row-selected {
  background: #e7f3ff;
}

.table-row.row-loading {
  opacity: 0.6;
}

.table-cell {
  position: absolute;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 8px;
  border-right: 1px solid #dee2e6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table-cell.text-right {
  justify-content: flex-end;
}

.table-cell.editable {
  cursor: text;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #6c757d;
  font-style: italic;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
  font-size: 12px;
  color: #6c757d;
  flex-shrink: 0;
}

.loading-indicator {
  color: #007bff;
  font-weight: 500;
}

.memory-usage {
  font-family: monospace;
}

/* Button styles */
.btn {
  padding: 4px 8px;
  font-size: 12px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

.btn-outline-secondary {
  background: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background: #6c757d;
  color: white;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.icon {
  font-size: 14px;
}
</style>