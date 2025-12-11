/**
 * Performance monitoring utilities
 * Helps track and optimize component performance
 */

/**
 * Measure execution time of a function
 */
export function measureTime<T>(
  fn: () => T,
  label: string = 'Operation'
): T {
  const start = performance.now()
  const result = fn()
  const end = performance.now()
  
  if (import.meta.env.DEV) {
    console.log(`[Performance] ${label}: ${(end - start).toFixed(2)}ms`)
  }
  
  return result
}

/**
 * Measure async execution time
 */
export async function measureTimeAsync<T>(
  fn: () => Promise<T>,
  label: string = 'Async Operation'
): Promise<T> {
  const start = performance.now()
  const result = await fn()
  const end = performance.now()
  
  if (import.meta.env.DEV) {
    console.log(`[Performance] ${label}: ${(end - start).toFixed(2)}ms`)
  }
  
  return result
}

/**
 * Create a performance marker
 */
export function mark(name: string): void {
  if (import.meta.env.DEV && performance.mark) {
    performance.mark(name)
  }
}

/**
 * Measure between two markers
 */
export function measure(
  name: string,
  startMark: string,
  endMark: string
): void {
  if (import.meta.env.DEV && performance.measure) {
    try {
      performance.measure(name, startMark, endMark)
      const measure = performance.getEntriesByName(name)[0]
      console.log(`[Performance] ${name}: ${measure.duration.toFixed(2)}ms`)
    } catch (e) {
      console.warn(`Failed to measure ${name}:`, e)
    }
  }
}

/**
 * Log component render time
 */
export function logRenderTime(componentName: string, duration: number): void {
  if (import.meta.env.DEV) {
    if (duration > 16) { // More than one frame (60fps)
      console.warn(
        `[Performance Warning] ${componentName} render took ${duration.toFixed(2)}ms (> 16ms)`
      )
    } else {
      console.log(
        `[Performance] ${componentName} render: ${duration.toFixed(2)}ms`
      )
    }
  }
}

/**
 * Batch updates to reduce re-renders
 */
export function batchUpdates<T>(updates: Array<() => void>): void {
  // Use requestAnimationFrame to batch updates
  requestAnimationFrame(() => {
    updates.forEach(update => update())
  })
}

/**
 * Lazy load component with loading state
 */
export function lazyLoadComponent(
  loader: () => Promise<any>,
  loadingComponent?: any,
  errorComponent?: any,
  delay: number = 200
) {
  return {
    component: loader,
    loading: loadingComponent,
    error: errorComponent,
    delay
  }
}
