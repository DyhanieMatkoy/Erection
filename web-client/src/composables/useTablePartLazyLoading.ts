/**
 * Composable for lazy loading table part data
 * Implements progressive data loading for large datasets
 */
import { ref, computed, watch } from 'vue'
import { debounce } from '@/utils/debounce'

interface LazyLoadingOptions {
  pageSize: number
  preloadPages?: number
  loadingDelay?: number
  cacheSize?: number
  enablePrefetch?: boolean
}

interface DataPage<T> {
  pageNumber: number
  data: T[]
  isLoading: boolean
  isLoaded: boolean
  error?: string
  timestamp: number
}

interface LoadingState {
  isLoading: boolean
  hasMore: boolean
  error?: string
  totalCount?: number
}

export function useTablePartLazyLoading<T>(
  loadDataFn: (page: number, pageSize: number) => Promise<{ data: T[], totalCount: number }>,
  options: LazyLoadingOptions
) {
  const {
    pageSize,
    preloadPages = 2,
    loadingDelay = 100,
    cacheSize = 10,
    enablePrefetch = true
  } = options

  // State
  const pages = ref(new Map<number, DataPage<T>>())
  const loadingState = ref<LoadingState>({
    isLoading: false,
    hasMore: true,
    totalCount: undefined
  })
  const currentPage = ref(0)
  const loadedPageCount = ref(0)

  // Performance metrics
  const loadingMetrics = ref({
    totalLoadTime: 0,
    averageLoadTime: 0,
    cacheHitRate: 0,
    totalRequests: 0,
    cacheHits: 0,
    memoryUsage: 0
  })

  // Computed properties
  const allData = computed(() => {
    const result: T[] = []
    const sortedPages = Array.from(pages.value.entries())
      .sort(([a], [b]) => a - b)
    
    for (const [, page] of sortedPages) {
      if (page.isLoaded && page.data) {
        result.push(...page.data)
      }
    }
    
    return result
  })

  const isLoading = computed(() => loadingState.value.isLoading)
  const hasMore = computed(() => loadingState.value.hasMore)
  const totalCount = computed(() => loadingState.value.totalCount)

  // Memory usage estimation
  const estimatedMemoryUsage = computed(() => {
    let totalItems = 0
    pages.value.forEach(page => {
      if (page.isLoaded) {
        totalItems += page.data.length
      }
    })
    
    // Rough estimate: 1KB per item
    const memoryMB = (totalItems * 1) / 1024
    loadingMetrics.value.memoryUsage = memoryMB
    return memoryMB
  })

  // Load a specific page
  async function loadPage(pageNumber: number): Promise<void> {
    // Check if page is already loaded or loading
    const existingPage = pages.value.get(pageNumber)
    if (existingPage && (existingPage.isLoaded || existingPage.isLoading)) {
      if (existingPage.isLoaded) {
        loadingMetrics.value.cacheHits++
        updateCacheHitRate()
      }
      return
    }

    // Create loading page entry
    const loadingPage: DataPage<T> = {
      pageNumber,
      data: [],
      isLoading: true,
      isLoaded: false,
      timestamp: Date.now()
    }
    
    pages.value.set(pageNumber, loadingPage)
    loadingState.value.isLoading = true
    loadingMetrics.value.totalRequests++

    try {
      const startTime = performance.now()
      
      const result = await loadDataFn(pageNumber, pageSize)
      
      const loadTime = performance.now() - startTime
      updateLoadingMetrics(loadTime)

      // Update page with loaded data
      const loadedPage: DataPage<T> = {
        pageNumber,
        data: result.data,
        isLoading: false,
        isLoaded: true,
        timestamp: Date.now()
      }
      
      pages.value.set(pageNumber, loadedPage)
      loadedPageCount.value++

      // Update total count and hasMore flag
      if (result.totalCount !== undefined) {
        loadingState.value.totalCount = result.totalCount
        const totalPages = Math.ceil(result.totalCount / pageSize)
        loadingState.value.hasMore = pageNumber < totalPages - 1
      }

      // Cleanup old pages if cache is full
      cleanupCache()

      // Prefetch next pages if enabled
      if (enablePrefetch && result.data.length === pageSize) {
        debouncedPrefetch(pageNumber + 1)
      }

    } catch (error) {
      console.error(`Failed to load page ${pageNumber}:`, error)
      
      const errorPage: DataPage<T> = {
        pageNumber,
        data: [],
        isLoading: false,
        isLoaded: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      }
      
      pages.value.set(pageNumber, errorPage)
      loadingState.value.error = errorPage.error
    } finally {
      loadingState.value.isLoading = false
    }
  }

  // Load multiple pages
  async function loadPages(startPage: number, endPage: number): Promise<void> {
    const loadPromises: Promise<void>[] = []
    
    for (let page = startPage; page <= endPage; page++) {
      loadPromises.push(loadPage(page))
    }
    
    await Promise.all(loadPromises)
  }

  // Load data for visible range
  async function loadVisibleRange(startIndex: number, endIndex: number): Promise<void> {
    const startPage = Math.floor(startIndex / pageSize)
    const endPage = Math.floor(endIndex / pageSize)
    
    // Load current visible pages
    await loadPages(startPage, endPage)
    
    // Preload adjacent pages if enabled
    if (enablePrefetch) {
      const preloadStart = Math.max(0, startPage - preloadPages)
      const preloadEnd = endPage + preloadPages
      
      // Don't await preload to avoid blocking
      loadPages(preloadStart, preloadEnd).catch(error => {
        console.warn('Preload failed:', error)
      })
    }
  }

  // Debounced prefetch function
  const debouncedPrefetch = debounce((pageNumber: number) => {
    if (loadingState.value.hasMore) {
      loadPage(pageNumber).catch(error => {
        console.warn('Prefetch failed:', error)
      })
    }
  }, loadingDelay)

  // Get data for specific range
  function getDataRange(startIndex: number, endIndex: number): T[] {
    const result: T[] = []
    const startPage = Math.floor(startIndex / pageSize)
    const endPage = Math.floor(endIndex / pageSize)
    
    for (let pageNum = startPage; pageNum <= endPage; pageNum++) {
      const page = pages.value.get(pageNum)
      if (page && page.isLoaded) {
        const pageStartIndex = pageNum * pageSize
        const pageEndIndex = pageStartIndex + page.data.length
        
        // Calculate intersection with requested range
        const rangeStart = Math.max(startIndex, pageStartIndex)
        const rangeEnd = Math.min(endIndex, pageEndIndex)
        
        if (rangeStart < rangeEnd) {
          const localStart = rangeStart - pageStartIndex
          const localEnd = rangeEnd - pageStartIndex
          result.push(...page.data.slice(localStart, localEnd))
        }
      }
    }
    
    return result
  }

  // Check if range is loaded
  function isRangeLoaded(startIndex: number, endIndex: number): boolean {
    const startPage = Math.floor(startIndex / pageSize)
    const endPage = Math.floor(endIndex / pageSize)
    
    for (let pageNum = startPage; pageNum <= endPage; pageNum++) {
      const page = pages.value.get(pageNum)
      if (!page || !page.isLoaded) {
        return false
      }
    }
    
    return true
  }

  // Cleanup old pages to manage memory
  function cleanupCache(): void {
    if (pages.value.size <= cacheSize) {
      return
    }
    
    // Sort pages by timestamp (oldest first)
    const sortedPages = Array.from(pages.value.entries())
      .sort(([, a], [, b]) => a.timestamp - b.timestamp)
    
    // Remove oldest pages
    const pagesToRemove = sortedPages.slice(0, pages.value.size - cacheSize)
    pagesToRemove.forEach(([pageNumber]) => {
      pages.value.delete(pageNumber)
    })
  }

  // Update loading metrics
  function updateLoadingMetrics(loadTime: number): void {
    loadingMetrics.value.totalLoadTime += loadTime
    loadingMetrics.value.averageLoadTime = 
      loadingMetrics.value.totalLoadTime / loadingMetrics.value.totalRequests
  }

  // Update cache hit rate
  function updateCacheHitRate(): void {
    loadingMetrics.value.cacheHitRate = 
      loadingMetrics.value.cacheHits / loadingMetrics.value.totalRequests
  }

  // Reset all data
  function reset(): void {
    pages.value.clear()
    loadingState.value = {
      isLoading: false,
      hasMore: true,
      totalCount: undefined
    }
    currentPage.value = 0
    loadedPageCount.value = 0
    
    // Reset metrics
    loadingMetrics.value = {
      totalLoadTime: 0,
      averageLoadTime: 0,
      cacheHitRate: 0,
      totalRequests: 0,
      cacheHits: 0,
      memoryUsage: 0
    }
  }

  // Refresh specific page
  async function refreshPage(pageNumber: number): Promise<void> {
    pages.value.delete(pageNumber)
    await loadPage(pageNumber)
  }

  // Refresh all loaded pages
  async function refreshAll(): Promise<void> {
    const loadedPages = Array.from(pages.value.keys())
    pages.value.clear()
    
    for (const pageNumber of loadedPages) {
      await loadPage(pageNumber)
    }
  }

  return {
    // Data
    allData,
    pages: computed(() => pages.value),
    
    // State
    isLoading,
    hasMore,
    totalCount,
    loadingMetrics: computed(() => loadingMetrics.value),
    estimatedMemoryUsage,
    
    // Methods
    loadPage,
    loadPages,
    loadVisibleRange,
    getDataRange,
    isRangeLoaded,
    reset,
    refreshPage,
    refreshAll,
    
    // Cleanup
    cleanupCache
  }
}