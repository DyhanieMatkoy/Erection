/**
 * Tests for table part performance optimization features
 * Tests virtual scrolling, lazy loading, and memory optimization
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ref } from 'vue'
import { useTablePartVirtualization } from '@/composables/useTablePartVirtualization'
import { useTablePartLazyLoading } from '@/composables/useTablePartLazyLoading'
import { createMemoryOptimizer } from '@/services/tablePartMemoryOptimizer'
import type { TableColumn } from '@/types/table-parts'

// Mock data generators
const generateLargeDataset = (count: number) => {
  return Array.from({ length: count }, (_, index) => ({
    id: index,
    name: `Item ${index}`,
    description: `Description for item ${index}`.repeat(10),
    value: index * 100,
    category: `Category ${index % 10}`
  }))
}

const generateColumns = (): TableColumn[] => [
  { id: 'id', name: 'ID', type: 'number', width: '80px' },
  { id: 'name', name: 'Name', type: 'text', width: '200px' },
  { id: 'description', name: 'Description', type: 'text', width: '300px' },
  { id: 'value', name: 'Value', type: 'currency', width: '120px' },
  { id: 'category', name: 'Category', type: 'text', width: '150px' }
]

describe('Table Part Virtualization', () => {
  let mockData: any[]
  let columns: TableColumn[]

  beforeEach(() => {
    mockData = generateLargeDataset(10000)
    columns = generateColumns()
  })

  it('should create virtualization composable', () => {
    const { visibleRows, totalHeight, performanceMetrics } = useTablePartVirtualization(
      mockData,
      columns,
      {
        rowHeight: 40,
        bufferSize: 10,
        containerHeight: 400
      }
    )

    expect(visibleRows).toBeDefined()
    expect(totalHeight).toBeDefined()
    expect(performanceMetrics).toBeDefined()
  })

  it('should calculate correct total height for large dataset', () => {
    const { totalHeight } = useTablePartVirtualization(
      mockData,
      columns,
      {
        rowHeight: 40,
        bufferSize: 10,
        containerHeight: 400
      }
    )

    expect(totalHeight.value).toBe(10000 * 40) // 10,000 rows * 40px height
  })

  it('should render only visible rows plus buffer', () => {
    const { visibleRows } = useTablePartVirtualization(
      mockData,
      columns,
      {
        rowHeight: 40,
        bufferSize: 5,
        containerHeight: 400
      }
    )

    // Should render visible rows (400px / 40px = 10) plus buffer (5 * 2 = 10)
    // Total should be around 20 rows
    expect(visibleRows.value.length).toBeLessThanOrEqual(25)
    expect(visibleRows.value.length).toBeGreaterThan(0)
  })

  it('should track performance metrics', () => {
    const { performanceMetrics } = useTablePartVirtualization(
      mockData,
      columns,
      {
        rowHeight: 40,
        bufferSize: 10,
        containerHeight: 400
      }
    )

    expect(performanceMetrics.value.totalRows).toBe(10000)
    expect(performanceMetrics.value.renderedRows).toBeGreaterThan(0)
    expect(performanceMetrics.value.virtualizationRatio.rows).toBeLessThan(1)
  })

  it('should handle column virtualization for wide tables', () => {
    const manyColumns = Array.from({ length: 50 }, (_, i) => ({
      id: `col_${i}`,
      name: `Column ${i}`,
      type: 'text' as const,
      width: '150px'
    }))

    const { visibleColumnsData, performanceMetrics } = useTablePartVirtualization(
      mockData.slice(0, 100), // Smaller dataset for this test
      manyColumns,
      {
        rowHeight: 40,
        bufferSize: 5,
        containerHeight: 400,
        enableColumnVirtualization: true,
        columnWidth: 150,
        visibleColumns: 10
      }
    )

    expect(visibleColumnsData.value.length).toBeLessThanOrEqual(15) // 10 visible + buffer
    expect(performanceMetrics.value.renderedColumns).toBeLessThan(50)
  })

  it('should optimize for data changes', () => {
    const data = ref(generateLargeDataset(1000))
    
    const { visibleRows, performanceMetrics } = useTablePartVirtualization(
      data.value,
      columns,
      {
        rowHeight: 40,
        bufferSize: 10,
        containerHeight: 400
      }
    )

    const initialRenderedRows = performanceMetrics.value.renderedRows

    // Change data significantly
    data.value = generateLargeDataset(5000)

    // Should handle the change efficiently
    expect(performanceMetrics.value.totalRows).toBe(5000)
    expect(visibleRows.value.length).toBeGreaterThan(0)
  })
})

describe('Table Part Lazy Loading', () => {
  let mockLoadFunction: vi.MockedFunction<any>

  beforeEach(() => {
    mockLoadFunction = vi.fn().mockImplementation(async (page: number, pageSize: number) => {
      const startIndex = page * pageSize
      const data = generateLargeDataset(pageSize).map((item, index) => ({
        ...item,
        id: startIndex + index
      }))
      
      return {
        data,
        totalCount: 50000 // Simulate 50,000 total items
      }
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should create lazy loading composable', () => {
    const { allData, isLoading, totalCount, loadVisibleRange } = useTablePartLazyLoading(
      mockLoadFunction,
      {
        pageSize: 100,
        preloadPages: 2,
        cacheSize: 10
      }
    )

    expect(allData).toBeDefined()
    expect(isLoading).toBeDefined()
    expect(totalCount).toBeDefined()
    expect(loadVisibleRange).toBeDefined()
  })

  it('should load data on demand', async () => {
    const { loadVisibleRange, isLoading, allData } = useTablePartLazyLoading(
      mockLoadFunction,
      {
        pageSize: 100,
        preloadPages: 1,
        cacheSize: 5
      }
    )

    expect(isLoading.value).toBe(false)
    expect(allData.value.length).toBe(0)

    // Load first page
    await loadVisibleRange(0, 50)

    expect(mockLoadFunction).toHaveBeenCalledWith(0, 100)
    expect(allData.value.length).toBeGreaterThan(0)
  })

  it('should implement caching to avoid redundant requests', async () => {
    const { loadVisibleRange } = useTablePartLazyLoading(
      mockLoadFunction,
      {
        pageSize: 100,
        preloadPages: 1,
        cacheSize: 5
      }
    )

    // Load same range twice
    await loadVisibleRange(0, 50)
    await loadVisibleRange(0, 50)

    // Should only call load function once due to caching
    expect(mockLoadFunction).toHaveBeenCalledTimes(1)
  })

  it('should preload adjacent pages', async () => {
    const { loadVisibleRange } = useTablePartLazyLoading(
      mockLoadFunction,
      {
        pageSize: 100,
        preloadPages: 2,
        cacheSize: 10,
        enablePrefetch: true
      }
    )

    await loadVisibleRange(200, 250) // Page 2

    // Should load current page and preload adjacent pages
    // Allow some time for prefetch
    await new Promise(resolve => setTimeout(resolve, 150))

    expect(mockLoadFunction).toHaveBeenCalledWith(2, 100) // Current page
    // May also call pages 0, 1, 3, 4 for prefetch
  })

  it('should track loading metrics', async () => {
    const { loadVisibleRange, loadingMetrics } = useTablePartLazyLoading(
      mockLoadFunction,
      {
        pageSize: 100,
        preloadPages: 1,
        cacheSize: 5
      }
    )

    await loadVisibleRange(0, 50)

    expect(loadingMetrics.value.totalRequests).toBeGreaterThan(0)
    expect(loadingMetrics.value.averageLoadTime).toBeGreaterThan(0)
  })

  it('should handle loading errors gracefully', async () => {
    const errorLoadFunction = vi.fn().mockRejectedValue(new Error('Network error'))

    const { loadVisibleRange, isLoading } = useTablePartLazyLoading(
      errorLoadFunction,
      {
        pageSize: 100,
        preloadPages: 1,
        cacheSize: 5
      }
    )

    await loadVisibleRange(0, 50)

    expect(isLoading.value).toBe(false)
    // Should handle error without crashing
  })

  it('should manage memory by cleaning up old pages', async () => {
    const { loadVisibleRange, pages } = useTablePartLazyLoading(
      mockLoadFunction,
      {
        pageSize: 100,
        preloadPages: 0,
        cacheSize: 3 // Small cache for testing
      }
    )

    // Load more pages than cache size
    for (let i = 0; i < 5; i++) {
      await loadVisibleRange(i * 100, (i * 100) + 50)
    }

    // Should not exceed cache size
    expect(pages.value.size).toBeLessThanOrEqual(3)
  })
})

describe('Memory Optimizer', () => {
  let memoryOptimizer: any

  beforeEach(() => {
    memoryOptimizer = createMemoryOptimizer({
      maxMemoryMB: 10, // Small limit for testing
      cleanupThreshold: 0.8,
      compressionEnabled: true,
      cacheStrategy: 'lru'
    })
  })

  afterEach(() => {
    memoryOptimizer.destroy()
  })

  it('should create memory optimizer', () => {
    expect(memoryOptimizer).toBeDefined()
    expect(memoryOptimizer.getStats().maxMemoryMB).toBe(10)
  })

  it('should store and retrieve data', async () => {
    const testData = { items: generateLargeDataset(100) }

    await memoryOptimizer.store('test_key', testData)
    const retrieved = await memoryOptimizer.get('test_key')

    expect(retrieved).toEqual(testData)
    expect(memoryOptimizer.has('test_key')).toBe(true)
  })

  it('should compress large data automatically', async () => {
    const largeData = {
      items: generateLargeDataset(1000),
      description: 'x'.repeat(10000)
    }

    await memoryOptimizer.store('large_data', largeData)
    const stats = memoryOptimizer.getStats()

    expect(stats.compressionRatio).toBeGreaterThan(0)
  })

  it('should perform cleanup when memory limit is exceeded', async () => {
    // Store many large items to exceed memory limit
    for (let i = 0; i < 20; i++) {
      const largeData = {
        id: i,
        data: 'x'.repeat(100000), // 100KB per item
        items: generateLargeDataset(50)
      }
      await memoryOptimizer.store(`item_${i}`, largeData)
    }

    const stats = memoryOptimizer.getStats()
    expect(stats.cleanupCount).toBeGreaterThan(0)
    expect(stats.usedMemoryMB).toBeLessThanOrEqual(10)
  })

  it('should implement LRU eviction strategy', async () => {
    // Store items
    for (let i = 0; i < 5; i++) {
      await memoryOptimizer.store(`item_${i}`, { data: 'x'.repeat(50000) })
    }

    // Access some items to make them recently used
    await memoryOptimizer.get('item_0')
    await memoryOptimizer.get('item_2')

    // Store more items to trigger cleanup
    for (let i = 5; i < 15; i++) {
      await memoryOptimizer.store(`item_${i}`, { data: 'x'.repeat(50000) })
    }

    // Recently accessed items should still be in cache
    expect(memoryOptimizer.has('item_0')).toBe(true)
    expect(memoryOptimizer.has('item_2')).toBe(true)
  })

  it('should optimize memory by compressing existing entries', async () => {
    // Temporarily disable compression
    memoryOptimizer.options.compressionEnabled = false

    // Store uncompressed data
    for (let i = 0; i < 5; i++) {
      await memoryOptimizer.store(`item_${i}`, {
        data: 'x'.repeat(20000),
        items: generateLargeDataset(100)
      })
    }

    // Re-enable compression and optimize
    memoryOptimizer.options.compressionEnabled = true
    await memoryOptimizer.optimizeMemory()

    const stats = memoryOptimizer.getStats()
    expect(stats.compressionRatio).toBeGreaterThan(0)
  })

  it('should preload data with memory-aware batching', async () => {
    const loadFn = vi.fn().mockImplementation(async (key: string) => ({
      key,
      data: generateLargeDataset(50)
    }))

    const keys = Array.from({ length: 10 }, (_, i) => `preload_${i}`)

    await memoryOptimizer.preloadData(keys, loadFn, 3)

    // Should have loaded all keys
    for (const key of keys) {
      expect(memoryOptimizer.has(key)).toBe(true)
    }

    expect(loadFn).toHaveBeenCalledTimes(10)
  })

  it('should track memory statistics', async () => {
    // Store some data
    for (let i = 0; i < 3; i++) {
      await memoryOptimizer.store(`item_${i}`, {
        data: 'x'.repeat(10000),
        items: generateLargeDataset(20)
      })
    }

    const stats = memoryOptimizer.getStats()

    expect(stats.cacheSize).toBe(3)
    expect(stats.usedMemoryMB).toBeGreaterThan(0)
    expect(stats.usedMemoryMB).toBeLessThanOrEqual(stats.maxMemoryMB)
  })
})

describe('Performance Integration', () => {
  it('should handle large dataset efficiently', async () => {
    const largeDataset = generateLargeDataset(50000)
    const columns = generateColumns()

    const startTime = performance.now()

    // Create virtualization for large dataset
    const { visibleRows, performanceMetrics } = useTablePartVirtualization(
      largeDataset,
      columns,
      {
        rowHeight: 40,
        bufferSize: 10,
        containerHeight: 600
      }
    )

    const setupTime = performance.now() - startTime

    // Setup should be fast even for large dataset
    expect(setupTime).toBeLessThan(100) // Less than 100ms

    // Should only render a small fraction of total rows
    const virtualizationRatio = performanceMetrics.value.virtualizationRatio.rows
    expect(virtualizationRatio).toBeLessThan(0.01) // Less than 1% of rows rendered

    // Memory usage should be reasonable
    expect(performanceMetrics.value.memoryUsage).toBeLessThan(50) // Less than 50MB
  })

  it('should integrate virtualization with lazy loading', async () => {
    const mockLoadFunction = vi.fn().mockImplementation(async (page: number, pageSize: number) => {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 10))
      
      const startIndex = page * pageSize
      const data = generateLargeDataset(pageSize).map((item, index) => ({
        ...item,
        id: startIndex + index
      }))
      
      return { data, totalCount: 100000 }
    })

    const { allData, loadVisibleRange, isLoading } = useTablePartLazyLoading(
      mockLoadFunction,
      {
        pageSize: 200,
        preloadPages: 2,
        cacheSize: 10
      }
    )

    // Load initial visible range
    await loadVisibleRange(0, 100)

    expect(allData.value.length).toBeGreaterThan(0)
    expect(isLoading.value).toBe(false)

    // Create virtualization with loaded data
    const { visibleRows, performanceMetrics } = useTablePartVirtualization(
      allData.value,
      generateColumns(),
      {
        rowHeight: 40,
        bufferSize: 10,
        containerHeight: 600
      }
    )

    expect(visibleRows.value.length).toBeGreaterThan(0)
    expect(performanceMetrics.value.renderedRows).toBeLessThan(allData.value.length)
  })

  it('should maintain performance with frequent updates', async () => {
    const data = ref(generateLargeDataset(1000))
    const columns = generateColumns()

    const { visibleRows, performanceMetrics } = useTablePartVirtualization(
      data.value,
      columns,
      {
        rowHeight: 40,
        bufferSize: 5,
        containerHeight: 400
      }
    )

    const renderTimes: number[] = []

    // Simulate frequent data updates
    for (let i = 0; i < 10; i++) {
      const startTime = performance.now()
      
      // Update data
      data.value = generateLargeDataset(1000 + i * 100)
      
      // Wait for reactivity
      await new Promise(resolve => setTimeout(resolve, 1))
      
      const renderTime = performance.now() - startTime
      renderTimes.push(renderTime)
    }

    // All render times should be reasonable
    const avgRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length
    expect(avgRenderTime).toBeLessThan(50) // Less than 50ms average

    // Performance should remain consistent
    const maxRenderTime = Math.max(...renderTimes)
    expect(maxRenderTime).toBeLessThan(100) // No render should take more than 100ms
  })
})