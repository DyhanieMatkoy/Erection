/**
 * Composable for caching frequently accessed data
 * Reduces API calls and improves performance
 */
import { ref, computed } from 'vue'

interface CacheEntry<T> {
  data: T
  timestamp: number
}

interface CacheOptions {
  ttl?: number // Time to live in milliseconds (default: 5 minutes)
}

const DEFAULT_TTL = 5 * 60 * 1000 // 5 minutes

export function useCache<T>(key: string, options: CacheOptions = {}) {
  const ttl = options.ttl || DEFAULT_TTL
  const cache = ref<Map<string, CacheEntry<T>>>(new Map())

  /**
   * Get cached data if available and not expired
   */
  function get(cacheKey: string): T | null {
    const entry = cache.value.get(cacheKey)
    
    if (!entry) {
      return null
    }

    const now = Date.now()
    const isExpired = now - entry.timestamp > ttl

    if (isExpired) {
      cache.value.delete(cacheKey)
      return null
    }

    return entry.data
  }

  /**
   * Set cached data
   */
  function set(cacheKey: string, data: T): void {
    cache.value.set(cacheKey, {
      data,
      timestamp: Date.now()
    })
  }

  /**
   * Check if cache has valid entry
   */
  function has(cacheKey: string): boolean {
    return get(cacheKey) !== null
  }

  /**
   * Clear specific cache entry
   */
  function clear(cacheKey: string): void {
    cache.value.delete(cacheKey)
  }

  /**
   * Clear all cache entries
   */
  function clearAll(): void {
    cache.value.clear()
  }

  /**
   * Get or fetch data with caching
   */
  async function getOrFetch(
    cacheKey: string,
    fetchFn: () => Promise<T>
  ): Promise<T> {
    const cached = get(cacheKey)
    
    if (cached !== null) {
      return cached
    }

    const data = await fetchFn()
    set(cacheKey, data)
    return data
  }

  return {
    get,
    set,
    has,
    clear,
    clearAll,
    getOrFetch
  }
}

/**
 * Global cache for reference data (units, works, etc.)
 */
export function useReferenceCache() {
  const unitsCache = useCache<any[]>('units', { ttl: 10 * 60 * 1000 }) // 10 minutes
  const worksCache = useCache<any[]>('works', { ttl: 5 * 60 * 1000 }) // 5 minutes
  const costItemsCache = useCache<any[]>('cost-items', { ttl: 5 * 60 * 1000 })
  const materialsCache = useCache<any[]>('materials', { ttl: 5 * 60 * 1000 })

  return {
    units: unitsCache,
    works: worksCache,
    costItems: costItemsCache,
    materials: materialsCache
  }
}
