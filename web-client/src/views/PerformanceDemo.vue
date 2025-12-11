<!--
  Performance Optimization Demo
  Demonstrates the various performance optimizations implemented
-->
<template>
  <div class="performance-demo">
    <h1>Performance Optimization Demo</h1>
    
    <div class="demo-section">
      <h2>1. Debouncing Demo</h2>
      <p>Type quickly - notice the search only executes after you stop typing (300ms delay)</p>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Type to search..."
        class="demo-input"
        @input="handleDebouncedSearch"
      />
      <div class="demo-output">
        <p>Search executed: {{ searchExecutionCount }} times</p>
        <p>Last search: {{ lastSearch || 'None' }}</p>
        <p class="hint">Without debouncing, this would execute {{ searchQuery.length }} times!</p>
      </div>
    </div>

    <div class="demo-section">
      <h2>2. Virtual Scrolling Demo</h2>
      <p>Scroll through 10,000 items smoothly - only ~20 items are rendered at a time</p>
      <div class="demo-controls">
        <button @click="generateLargeList(100)" class="btn btn-sm">100 items</button>
        <button @click="generateLargeList(1000)" class="btn btn-sm">1,000 items</button>
        <button @click="generateLargeList(10000)" class="btn btn-sm">10,000 items</button>
      </div>
      <div class="demo-output">
        <p>Total items: {{ largeList.length }}</p>
        <p>Rendered items: ~20 (virtual scrolling)</p>
        <p>Memory usage: Constant (regardless of list size)</p>
      </div>
      <div class="virtual-scroll-demo" ref="scrollContainer">
        <div class="virtual-scroll-spacer" :style="{ height: totalHeight + 'px' }">
          <div class="virtual-scroll-content" :style="{ transform: `translateY(${offsetY}px)` }">
            <div
              v-for="{ item, index } in visibleItems"
              :key="index"
              class="virtual-item"
              :style="{ height: itemHeight + 'px' }"
            >
              Item #{{ index + 1 }}: {{ item.name }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="demo-section">
      <h2>3. Caching Demo</h2>
      <p>Click "Load Data" multiple times - notice instant loading after first fetch</p>
      <div class="demo-controls">
        <button @click="loadCachedData" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Loading...' : 'Load Data' }}
        </button>
        <button @click="clearCache" class="btn btn-secondary">Clear Cache</button>
      </div>
      <div class="demo-output">
        <p>Load count: {{ loadCount }}</p>
        <p>Cache hits: {{ cacheHits }}</p>
        <p>Cache misses: {{ cacheMisses }}</p>
        <p>Cache hit rate: {{ cacheHitRate }}%</p>
        <p v-if="lastLoadTime" class="success">
          Last load time: {{ lastLoadTime }}ms
          {{ lastLoadTime < 50 ? '(cached!)' : '(from API)' }}
        </p>
      </div>
    </div>

    <div class="demo-section">
      <h2>4. Loading Skeleton Demo</h2>
      <p>Click to see different skeleton types</p>
      <div class="demo-controls">
        <button @click="showSkeleton('table')" class="btn btn-sm">Table</button>
        <button @click="showSkeleton('form')" class="btn btn-sm">Form</button>
        <button @click="showSkeleton('card')" class="btn btn-sm">Card</button>
        <button @click="showSkeleton('list')" class="btn btn-sm">List</button>
      </div>
      <div class="demo-output">
        <LoadingSkeleton
          v-if="showingSkeletonType"
          :type="showingSkeletonType"
          :rows="3"
          :columns="4"
        />
        <p v-else class="hint">Click a button to see skeleton</p>
      </div>
    </div>

    <div class="demo-section">
      <h2>5. Performance Monitoring Demo</h2>
      <p>Click to measure execution time of operations</p>
      <div class="demo-controls">
        <button @click="measureSync" class="btn btn-primary">Measure Sync Operation</button>
        <button @click="measureAsync" class="btn btn-primary">Measure Async Operation</button>
      </div>
      <div class="demo-output">
        <div v-if="performanceLogs.length > 0" class="performance-logs">
          <p v-for="(log, index) in performanceLogs" :key="index" class="log-entry">
            {{ log }}
          </p>
        </div>
        <p v-else class="hint">Click a button to see measurements</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { debounce } from '@/utils/debounce'
import { useCache } from '@/composables/useCache'
import { useVirtualScroll } from '@/composables/useVirtualScroll'
import { measureTime, measureTimeAsync } from '@/utils/performance'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

// Debouncing Demo
const searchQuery = ref('')
const searchExecutionCount = ref(0)
const lastSearch = ref('')

const debouncedSearch = debounce((query: string) => {
  searchExecutionCount.value++
  lastSearch.value = query
}, 300)

function handleDebouncedSearch() {
  debouncedSearch(searchQuery.value)
}

// Virtual Scrolling Demo
const largeList = ref<Array<{ id: number; name: string }>>([])
const itemHeight = 50
const scrollContainer = ref<HTMLElement | null>(null)

function generateLargeList(count: number) {
  largeList.value = Array.from({ length: count }, (_, i) => ({
    id: i,
    name: `Item ${i + 1}`
  }))
}

const { visibleItems, totalHeight, offsetY } = useVirtualScroll(largeList.value, {
  itemHeight,
  bufferSize: 5,
  containerHeight: 300
})

// Caching Demo
const cache = useCache<any>('demo')
const loading = ref(false)
const loadCount = ref(0)
const cacheHits = ref(0)
const cacheMisses = ref(0)
const lastLoadTime = ref<number | null>(null)

const cacheHitRate = computed(() => {
  if (loadCount.value === 0) return 0
  return Math.round((cacheHits.value / loadCount.value) * 100)
})

async function loadCachedData() {
  loading.value = true
  loadCount.value++
  
  const start = performance.now()
  
  const data = await cache.getOrFetch('demo-data', async () => {
    // Simulate API call
    cacheMisses.value++
    await new Promise(resolve => setTimeout(resolve, 1000))
    return { data: 'Sample data', timestamp: Date.now() }
  })
  
  const end = performance.now()
  lastLoadTime.value = Math.round(end - start)
  
  if (lastLoadTime.value < 50) {
    cacheHits.value++
  }
  
  loading.value = false
}

function clearCache() {
  cache.clear('demo-data')
  cacheHits.value = 0
  cacheMisses.value = 0
  loadCount.value = 0
  lastLoadTime.value = null
}

// Loading Skeleton Demo
const showingSkeletonType = ref<'table' | 'form' | 'card' | 'list' | null>(null)

function showSkeleton(type: 'table' | 'form' | 'card' | 'list') {
  showingSkeletonType.value = type
  setTimeout(() => {
    showingSkeletonType.value = null
  }, 3000)
}

// Performance Monitoring Demo
const performanceLogs = ref<string[]>([])

function measureSync() {
  const result = measureTime(() => {
    // Simulate expensive operation
    let sum = 0
    for (let i = 0; i < 1000000; i++) {
      sum += i
    }
    return sum
  }, 'Expensive Calculation')
  
  performanceLogs.value.unshift(`Sync operation completed in ${result}ms`)
  if (performanceLogs.value.length > 5) {
    performanceLogs.value.pop()
  }
}

async function measureAsync() {
  const start = performance.now()
  await measureTimeAsync(async () => {
    await new Promise(resolve => setTimeout(resolve, 500))
  }, 'Async Operation')
  const duration = Math.round(performance.now() - start)
  
  performanceLogs.value.unshift(`Async operation completed in ${duration}ms`)
  if (performanceLogs.value.length > 5) {
    performanceLogs.value.pop()
  }
}

// Initialize
generateLargeList(1000)
</script>

<style scoped>
.performance-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.demo-section {
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.demo-section h2 {
  color: #007bff;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.demo-section > p {
  color: #6c757d;
  margin-bottom: 1rem;
}

.demo-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.demo-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.demo-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.demo-output {
  background: #f8f9fa;
  border-radius: 0.25rem;
  padding: 1rem;
  margin-top: 1rem;
}

.demo-output p {
  margin: 0.5rem 0;
  color: #495057;
}

.hint {
  color: #6c757d;
  font-style: italic;
  font-size: 0.875rem;
}

.success {
  color: #28a745;
  font-weight: 600;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

/* Virtual Scrolling Demo */
.virtual-scroll-demo {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  margin-top: 1rem;
  position: relative;
}

.virtual-scroll-spacer {
  position: relative;
  width: 100%;
}

.virtual-scroll-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  will-change: transform;
}

.virtual-item {
  display: flex;
  align-items: center;
  padding: 0 1rem;
  border-bottom: 1px solid #dee2e6;
  box-sizing: border-box;
}

.virtual-item:hover {
  background-color: #f8f9fa;
}

/* Performance Logs */
.performance-logs {
  max-height: 200px;
  overflow-y: auto;
}

.log-entry {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  padding: 0.5rem;
  background: white;
  border-left: 3px solid #007bff;
  margin: 0.5rem 0;
}
</style>
