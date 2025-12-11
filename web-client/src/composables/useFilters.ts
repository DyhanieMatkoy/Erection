import { ref, computed, type Ref } from 'vue'

export interface FilterValue {
  [key: string]: any
}

export function useFilters<T extends FilterValue>(initialFilters: T = {} as T) {
  const filters = ref({ ...initialFilters } as T) as Ref<T>
  const appliedFilters = ref({ ...initialFilters } as T) as Ref<T>

  const hasActiveFilters = computed(() => {
    return Object.values(appliedFilters.value).some(value => {
      if (value === null || value === undefined || value === '') return false
      if (Array.isArray(value)) return value.length > 0
      return true
    })
  })

  const filterCount = computed(() => {
    return Object.values(appliedFilters.value).filter(value => {
      if (value === null || value === undefined || value === '') return false
      if (Array.isArray(value)) return value.length > 0
      return true
    }).length
  })

  function setFilter(key: keyof T, value: any) {
    filters.value = {
      ...filters.value,
      [key]: value
    }
  }

  function clearFilter(key: keyof T) {
    filters.value = {
      ...filters.value,
      [key]: initialFilters[key]
    }
  }

  function clearAllFilters() {
    filters.value = { ...initialFilters } as T
    appliedFilters.value = { ...initialFilters } as T
  }

  function applyFilters() {
    appliedFilters.value = { ...filters.value }
  }

  function resetFilters() {
    filters.value = { ...appliedFilters.value }
  }

  function getQueryParams(): Record<string, any> {
    const params: Record<string, any> = {}
    
    Object.entries(appliedFilters.value).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value) && value.length > 0) {
          params[key] = value
        } else if (!Array.isArray(value)) {
          params[key] = value
        }
      }
    })
    
    return params
  }

  return {
    filters,
    appliedFilters,
    hasActiveFilters,
    filterCount,
    setFilter,
    clearFilter,
    clearAllFilters,
    applyFilters,
    resetFilters,
    getQueryParams
  }
}
