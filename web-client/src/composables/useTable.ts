import { ref, computed } from 'vue'
import type { PaginationInfo } from '@/types/api'

export interface TableState {
  page: number
  pageSize: number
  search: string
  sortBy: string
  sortOrder: 'asc' | 'desc'
}

export function useTable(initialPageSize = 50) {
  const state = ref<TableState>({
    page: 1,
    pageSize: initialPageSize,
    search: '',
    sortBy: '',
    sortOrder: 'asc',
  })

  const loading = ref(false)
  const data = ref<any[]>([])
  const pagination = ref<PaginationInfo | undefined>()

  function setPage(page: number) {
    state.value.page = page
  }

  function setSearch(search: string) {
    state.value.search = search
    state.value.page = 1 // Reset to first page on search
  }

  function setSort(sortBy: string, sortOrder: 'asc' | 'desc') {
    state.value.sortBy = sortBy
    state.value.sortOrder = sortOrder
  }

  function reset() {
    state.value = {
      page: 1,
      pageSize: initialPageSize,
      search: '',
      sortBy: '',
      sortOrder: 'asc',
    }
  }

  const queryParams = computed(() => {
    const params: Record<string, any> = {
      page: state.value.page,
      page_size: state.value.pageSize,
    }

    if (state.value.search) {
      params.search = state.value.search
    }

    if (state.value.sortBy) {
      params.sort_by = state.value.sortBy
      params.sort_order = state.value.sortOrder
    }

    return params
  })

  return {
    state,
    loading,
    data,
    pagination,
    queryParams,
    setPage,
    setSearch,
    setSort,
    reset,
  }
}
