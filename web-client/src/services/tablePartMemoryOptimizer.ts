/**
 * Table Part Memory Optimizer
 * Manages memory usage for large table datasets
 */

interface MemoryOptimizationOptions {
  maxMemoryMB: number
  cleanupThreshold: number
  compressionEnabled: boolean
  cacheStrategy: 'lru' | 'lfu' | 'fifo'
  monitoringInterval: number
}

interface MemoryStats {
  usedMemoryMB: number
  maxMemoryMB: number
  cacheSize: number
  compressionRatio: number
  cleanupCount: number
  lastCleanup: Date
}

interface CacheEntry<T> {
  key: string
  data: T
  compressed?: Uint8Array
  size: number
  accessCount: number
  lastAccessed: Date
  created: Date
}

export class TablePartMemoryOptimizer<T = any> {
  private cache = new Map<string, CacheEntry<T>>()
  private options: MemoryOptimizationOptions
  private stats: MemoryStats
  private monitoringTimer?: number
  private compressionWorker?: Worker

  constructor(options: Partial<MemoryOptimizationOptions> = {}) {
    this.options = {
      maxMemoryMB: 100,
      cleanupThreshold: 0.8,
      compressionEnabled: true,
      cacheStrategy: 'lru',
      monitoringInterval: 5000,
      ...options
    }

    this.stats = {
      usedMemoryMB: 0,
      maxMemoryMB: this.options.maxMemoryMB,
      cacheSize: 0,
      compressionRatio: 0,
      cleanupCount: 0,
      lastCleanup: new Date()
    }

    this.startMonitoring()
    this.initializeCompression()
  }

  /**
   * Store data in optimized cache
   */
  async store(key: string, data: T): Promise<void> {
    const size = this.estimateSize(data)
    
    // Check if we need cleanup before storing
    if (this.shouldCleanup(size)) {
      await this.cleanup()
    }

    const entry: CacheEntry<T> = {
      key,
      data,
      size,
      accessCount: 1,
      lastAccessed: new Date(),
      created: new Date()
    }

    // Compress if enabled and data is large enough
    if (this.options.compressionEnabled && size > 10240) { // 10KB threshold
      try {
        entry.compressed = await this.compress(data)
        entry.size = entry.compressed.length
        // Clear original data to save memory
        entry.data = null as any
      } catch (error) {
        console.warn('Compression failed, storing uncompressed:', error)
      }
    }

    this.cache.set(key, entry)
    this.updateStats()
  }

  /**
   * Retrieve data from cache
   */
  async get(key: string): Promise<T | null> {
    const entry = this.cache.get(key)
    if (!entry) {
      return null
    }

    // Update access statistics
    entry.accessCount++
    entry.lastAccessed = new Date()

    // Decompress if needed
    if (entry.compressed && !entry.data) {
      try {
        entry.data = await this.decompress(entry.compressed)
      } catch (error) {
        console.error('Decompression failed:', error)
        this.cache.delete(key)
        return null
      }
    }

    return entry.data
  }

  /**
   * Check if key exists in cache
   */
  has(key: string): boolean {
    return this.cache.has(key)
  }

  /**
   * Remove entry from cache
   */
  delete(key: string): boolean {
    const deleted = this.cache.delete(key)
    if (deleted) {
      this.updateStats()
    }
    return deleted
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear()
    this.updateStats()
  }

  /**
   * Get current memory statistics
   */
  getStats(): MemoryStats {
    return { ...this.stats }
  }

  /**
   * Force cleanup of cache
   */
  async cleanup(): Promise<void> {
    const targetSize = this.options.maxMemoryMB * this.options.cleanupThreshold
    const currentSize = this.stats.usedMemoryMB

    if (currentSize <= targetSize) {
      return
    }

    const entries = Array.from(this.cache.entries())
    let removedSize = 0
    let removedCount = 0

    // Sort entries based on cache strategy
    const sortedEntries = this.sortEntriesForCleanup(entries)

    // Remove entries until we're under the target size
    for (const [key, entry] of sortedEntries) {
      if (currentSize - removedSize <= targetSize) {
        break
      }

      removedSize += entry.size / (1024 * 1024) // Convert to MB
      removedCount++
      this.cache.delete(key)
    }

    this.stats.cleanupCount++
    this.stats.lastCleanup = new Date()
    this.updateStats()

    console.log(`Memory cleanup: removed ${removedCount} entries, freed ${removedSize.toFixed(2)}MB`)
  }

  /**
   * Optimize memory usage by compressing uncompressed entries
   */
  async optimizeMemory(): Promise<void> {
    if (!this.options.compressionEnabled) {
      return
    }

    const entries = Array.from(this.cache.values())
    let optimizedCount = 0
    let savedMemory = 0

    for (const entry of entries) {
      if (!entry.compressed && entry.data && entry.size > 10240) {
        try {
          const originalSize = entry.size
          entry.compressed = await this.compress(entry.data)
          entry.size = entry.compressed.length
          entry.data = null as any

          savedMemory += (originalSize - entry.size) / (1024 * 1024)
          optimizedCount++
        } catch (error) {
          console.warn('Failed to compress entry:', error)
        }
      }
    }

    this.updateStats()

    if (optimizedCount > 0) {
      console.log(`Memory optimization: compressed ${optimizedCount} entries, saved ${savedMemory.toFixed(2)}MB`)
    }
  }

  /**
   * Preload data with memory-aware batching
   */
  async preloadData(
    keys: string[],
    loadFn: (key: string) => Promise<T>,
    batchSize: number = 10
  ): Promise<void> {
    const batches = this.createBatches(keys, batchSize)

    for (const batch of batches) {
      // Check memory before each batch
      if (this.shouldCleanup()) {
        await this.cleanup()
      }

      // Load batch in parallel
      const loadPromises = batch
        .filter(key => !this.has(key))
        .map(async key => {
          try {
            const data = await loadFn(key)
            await this.store(key, data)
          } catch (error) {
            console.error(`Failed to preload ${key}:`, error)
          }
        })

      await Promise.all(loadPromises)

      // Small delay between batches to prevent blocking
      await new Promise(resolve => setTimeout(resolve, 10))
    }
  }

  /**
   * Destroy optimizer and cleanup resources
   */
  destroy(): void {
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer)
    }

    if (this.compressionWorker) {
      this.compressionWorker.terminate()
    }

    this.clear()
  }

  // Private methods

  private startMonitoring(): void {
    this.monitoringTimer = window.setInterval(() => {
      this.updateStats()
      
      // Auto-cleanup if threshold exceeded
      if (this.shouldCleanup()) {
        this.cleanup().catch(error => {
          console.error('Auto-cleanup failed:', error)
        })
      }
    }, this.options.monitoringInterval)
  }

  private initializeCompression(): void {
    if (this.options.compressionEnabled && typeof Worker !== 'undefined') {
      try {
        // Create compression worker for background processing
        const workerCode = `
          self.onmessage = function(e) {
            const { action, data, id } = e.data
            
            try {
              if (action === 'compress') {
                const compressed = new TextEncoder().encode(JSON.stringify(data))
                self.postMessage({ id, result: compressed })
              } else if (action === 'decompress') {
                const decompressed = JSON.parse(new TextDecoder().decode(data))
                self.postMessage({ id, result: decompressed })
              }
            } catch (error) {
              self.postMessage({ id, error: error.message })
            }
          }
        `
        
        const blob = new Blob([workerCode], { type: 'application/javascript' })
        this.compressionWorker = new Worker(URL.createObjectURL(blob))
      } catch (error) {
        console.warn('Failed to create compression worker:', error)
      }
    }
  }

  private async compress(data: T): Promise<Uint8Array> {
    if (this.compressionWorker) {
      return new Promise((resolve, reject) => {
        const id = Math.random().toString(36)
        
        const handler = (e: MessageEvent) => {
          if (e.data.id === id) {
            this.compressionWorker!.removeEventListener('message', handler)
            if (e.data.error) {
              reject(new Error(e.data.error))
            } else {
              resolve(e.data.result)
            }
          }
        }
        
        this.compressionWorker.addEventListener('message', handler)
        this.compressionWorker.postMessage({ action: 'compress', data, id })
      })
    } else {
      // Fallback to synchronous compression
      return new TextEncoder().encode(JSON.stringify(data))
    }
  }

  private async decompress(compressed: Uint8Array): Promise<T> {
    if (this.compressionWorker) {
      return new Promise((resolve, reject) => {
        const id = Math.random().toString(36)
        
        const handler = (e: MessageEvent) => {
          if (e.data.id === id) {
            this.compressionWorker!.removeEventListener('message', handler)
            if (e.data.error) {
              reject(new Error(e.data.error))
            } else {
              resolve(e.data.result)
            }
          }
        }
        
        this.compressionWorker.addEventListener('message', handler)
        this.compressionWorker.postMessage({ action: 'decompress', data: compressed, id })
      })
    } else {
      // Fallback to synchronous decompression
      return JSON.parse(new TextDecoder().decode(compressed))
    }
  }

  private estimateSize(data: T): number {
    // Rough estimation of object size in bytes
    const jsonString = JSON.stringify(data)
    return new Blob([jsonString]).size
  }

  private shouldCleanup(additionalSize: number = 0): boolean {
    const projectedSize = this.stats.usedMemoryMB + (additionalSize / (1024 * 1024))
    return projectedSize > (this.options.maxMemoryMB * this.options.cleanupThreshold)
  }

  private sortEntriesForCleanup(entries: [string, CacheEntry<T>][]): [string, CacheEntry<T>][] {
    switch (this.options.cacheStrategy) {
      case 'lru':
        return entries.sort(([, a], [, b]) => 
          a.lastAccessed.getTime() - b.lastAccessed.getTime()
        )
      
      case 'lfu':
        return entries.sort(([, a], [, b]) => 
          a.accessCount - b.accessCount
        )
      
      case 'fifo':
        return entries.sort(([, a], [, b]) => 
          a.created.getTime() - b.created.getTime()
        )
      
      default:
        return entries
    }
  }

  private updateStats(): void {
    let totalSize = 0
    let compressedSize = 0
    let uncompressedSize = 0

    for (const entry of this.cache.values()) {
      totalSize += entry.size
      
      if (entry.compressed) {
        compressedSize += entry.size
        // Estimate original size for compression ratio
        uncompressedSize += entry.size * 2 // Rough estimate
      } else {
        uncompressedSize += entry.size
      }
    }

    this.stats.usedMemoryMB = totalSize / (1024 * 1024)
    this.stats.cacheSize = this.cache.size
    this.stats.compressionRatio = uncompressedSize > 0 ? compressedSize / uncompressedSize : 0
  }

  private createBatches<U>(items: U[], batchSize: number): U[][] {
    const batches: U[][] = []
    for (let i = 0; i < items.length; i += batchSize) {
      batches.push(items.slice(i, i + batchSize))
    }
    return batches
  }
}

/**
 * Factory function to create a memory optimizer
 */
export function createMemoryOptimizer<T>(
  options?: Partial<MemoryOptimizationOptions>
): TablePartMemoryOptimizer<T> {
  return new TablePartMemoryOptimizer<T>(options)
}