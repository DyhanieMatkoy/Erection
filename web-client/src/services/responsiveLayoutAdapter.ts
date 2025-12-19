/**
 * Responsive Layout Adapter
 *
 * Handles window size-based layout adjustments and dynamic layout changes.
 * Implements requirement 12.5 for document table parts.
 */

import { ref, computed, onUnmounted, type Ref } from 'vue'
import type { FormField, LayoutConfiguration } from './formLayoutManager'
import { FormLayoutManager } from './formLayoutManager'

export interface WindowSize {
  width: number
  height: number
}

export interface ResponsiveLayoutRules {
  minWidthForTwoColumns: number
  fieldWidthRatios: Record<string, number>
  breakpoints: Record<string, number>
}

export class ResponsiveLayoutAdapter {
  private rules: ResponsiveLayoutRules
  private layoutManager: FormLayoutManager
  private currentWindowSize: WindowSize | null = null
  private currentLayoutType: 'single_column' | 'two_column' = 'single_column'
  private fields: FormField[] = []
  private resizeTimeout: number | null = null
  private readonly resizeDebounceMs = 150

  // Reactive properties
  public windowSize: Ref<WindowSize | null> = ref(null)
  public layoutType: Ref<'single_column' | 'two_column'> = ref('single_column')
  public breakpoint: Ref<string> = ref('desktop')

  constructor() {
    this.rules = {
      minWidthForTwoColumns: 800,
      fieldWidthRatios: {
        short: 0.3,
        medium: 0.5,
        long: 1.0,
        reference: 0.4
      },
      breakpoints: {
        mobile: 480,
        tablet: 768,
        desktop: 1024,
        wide: 1440
      }
    }

    this.layoutManager = new FormLayoutManager()

    // Set up window resize listener
    this.setupResizeListener()
  }

  private resizeHandler: (() => void) | null = null

  private setupResizeListener(): void {
    this.resizeHandler = () => {
      this.handleWindowResize({
        width: window.innerWidth,
        height: window.innerHeight
      })
    }

    window.addEventListener('resize', this.resizeHandler)
    
    // Initial size
    this.resizeHandler()
  }

  cleanup(): void {
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler)
    }
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout)
    }
  }

  setFields(fields: FormField[]): void {
    this.fields = fields
  }

  handleWindowResize(newSize: WindowSize): void {
    this.currentWindowSize = newSize
    this.windowSize.value = newSize

    // Update breakpoint
    this.breakpoint.value = this.getCurrentBreakpoint()

    // Debounce resize events
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout)
    }

    this.resizeTimeout = window.setTimeout(() => {
      this.handleResizeTimeout()
    }, this.resizeDebounceMs)
  }

  private handleResizeTimeout(): void {
    if (!this.currentWindowSize || !this.fields) {
      return
    }

    // Determine optimal layout
    const shouldUseTwoColumns = this.shouldUseTwoColumns(
      this.currentWindowSize,
      this.fields.filter((f) => this.layoutManager.isShortField(f)).length
    )

    const newLayoutType: 'single_column' | 'two_column' = shouldUseTwoColumns
      ? 'two_column'
      : 'single_column'

    // Update layout type if changed
    if (newLayoutType !== this.currentLayoutType) {
      this.currentLayoutType = newLayoutType
      this.layoutType.value = newLayoutType
    }
  }

  shouldUseTwoColumns(windowSize: WindowSize, fieldCount: number): boolean {
    return windowSize.width >= this.rules.minWidthForTwoColumns && fieldCount >= 6
  }

  adaptToWindowSize(layout: LayoutConfiguration, windowSize: WindowSize): LayoutConfiguration {
    const adaptedLayout: LayoutConfiguration = {
      leftColumn: [],
      rightColumn: [],
      fullWidthFields: [...layout.fullWidthFields],
      columnRatio: this.getColumnRatio(windowSize)
    }

    // Redistribute fields based on new ratio
    const allShortFields = [...layout.leftColumn, ...layout.rightColumn]
    if (allShortFields.length > 0) {
      const splitPoint = Math.floor(allShortFields.length * adaptedLayout.columnRatio)
      adaptedLayout.leftColumn = allShortFields.slice(0, splitPoint)
      adaptedLayout.rightColumn = allShortFields.slice(splitPoint)
    }

    return adaptedLayout
  }

  getColumnRatio(windowSize: WindowSize): number {
    if (windowSize.width < this.rules.breakpoints.tablet) {
      return 0.5 // Equal columns on small screens
    } else if (windowSize.width < this.rules.breakpoints.desktop) {
      return 0.45 // Slightly favor right column
    } else {
      return 0.4 // More space for right column on large screens
    }
  }

  getCurrentBreakpoint(): string {
    if (!this.currentWindowSize) {
      return 'desktop'
    }

    const width = this.currentWindowSize.width

    if (width < this.rules.breakpoints.mobile) {
      return 'mobile'
    } else if (width < this.rules.breakpoints.tablet) {
      return 'tablet'
    } else if (width < this.rules.breakpoints.wide) {
      return 'desktop'
    } else {
      return 'wide'
    }
  }

  shouldForceSingleColumn(): boolean {
    if (!this.currentWindowSize) {
      return false
    }

    return this.currentWindowSize.width < this.rules.minWidthForTwoColumns
  }

  getFieldWidthForBreakpoint(fieldType: string): number {
    const breakpoint = this.getCurrentBreakpoint()
    const baseRatio = this.rules.fieldWidthRatios[fieldType] || 0.5

    // Adjust based on breakpoint
    if (breakpoint === 'mobile') {
      return Math.min(baseRatio * 1.2, 1.0) // Wider fields on mobile
    } else if (breakpoint === 'tablet') {
      return baseRatio
    } else {
      return baseRatio * 0.9 // Slightly narrower on desktop
    }
  }
}

/**
 * Vue composable for responsive form layout
 */
export function useResponsiveFormLayout(fields: Ref<FormField[]>) {
  const adapter = new ResponsiveLayoutAdapter()
  const layoutManager = new FormLayoutManager()

  // Cleanup on unmount
  onUnmounted(() => {
    adapter.cleanup()
  })

  // Reactive layout configuration
  const layoutConfig = computed(() => {
    if (!fields.value.length) {
      return null
    }

    adapter.setFields(fields.value)
    const analysis = layoutManager.analyzeFields(fields.value)

    if (analysis.recommendedLayout === 'two_column' && !adapter.shouldForceSingleColumn()) {
      const config = layoutManager.createTwoColumnLayout(fields.value)
      return adapter.windowSize.value ? adapter.adaptToWindowSize(config, adapter.windowSize.value) : config
    }

    return null
  })

  // CSS classes for responsive behavior
  const containerClasses = computed(() => {
    const classes = ['form-container']
    
    if (adapter.layoutType.value === 'two_column') {
      classes.push('form-container--two-column')
    } else {
      classes.push('form-container--single-column')
    }

    classes.push(`form-container--${adapter.breakpoint.value}`)
    
    return classes
  })

  return {
    layoutConfig,
    layoutType: adapter.layoutType,
    windowSize: adapter.windowSize,
    breakpoint: adapter.breakpoint,
    containerClasses,
    shouldUseTwoColumns: (fieldCount: number) => {
      return adapter.windowSize.value
        ? adapter.shouldUseTwoColumns(adapter.windowSize.value, fieldCount)
        : false
    },
    getFieldWidthForBreakpoint: adapter.getFieldWidthForBreakpoint.bind(adapter)
  }
}