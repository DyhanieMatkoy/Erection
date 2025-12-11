import { describe, it, expect, beforeEach } from 'vitest'
import { useTable } from '../useTable'

describe('useTable', () => {
  it('should initialize with default values', () => {
    const { state, loading, data, pagination } = useTable()
    
    expect(state.value).toEqual({
      page: 1,
      pageSize: 50,
      search: '',
      sortBy: '',
      sortOrder: 'asc',
    })
    expect(loading.value).toBe(false)
    expect(data.value).toEqual([])
    expect(pagination.value).toBeUndefined()
  })

  it('should initialize with custom page size', () => {
    const { state } = useTable(100)
    
    expect(state.value.pageSize).toBe(100)
  })

  it('should update page number', () => {
    const { state, setPage } = useTable()
    
    setPage(3)
    
    expect(state.value.page).toBe(3)
  })

  it('should update search and reset page to 1', () => {
    const { state, setPage, setSearch } = useTable()
    
    setPage(3)
    setSearch('test query')
    
    expect(state.value.search).toBe('test query')
    expect(state.value.page).toBe(1)
  })

  it('should update sort parameters', () => {
    const { state, setSort } = useTable()
    
    setSort('name', 'desc')
    
    expect(state.value.sortBy).toBe('name')
    expect(state.value.sortOrder).toBe('desc')
  })

  it('should reset to initial state', () => {
    const { state, setPage, setSearch, setSort, reset } = useTable(25)
    
    setPage(5)
    setSearch('query')
    setSort('date', 'desc')
    
    reset()
    
    expect(state.value).toEqual({
      page: 1,
      pageSize: 25,
      search: '',
      sortBy: '',
      sortOrder: 'asc',
    })
  })

  it('should compute query params correctly with minimal state', () => {
    const { queryParams } = useTable()
    
    expect(queryParams.value).toEqual({
      page: 1,
      page_size: 50,
    })
  })

  it('should compute query params with search', () => {
    const { queryParams, setSearch } = useTable()
    
    setSearch('test')
    
    expect(queryParams.value).toEqual({
      page: 1,
      page_size: 50,
      search: 'test',
    })
  })

  it('should compute query params with sort', () => {
    const { queryParams, setSort } = useTable()
    
    setSort('name', 'desc')
    
    expect(queryParams.value).toEqual({
      page: 1,
      page_size: 50,
      sort_by: 'name',
      sort_order: 'desc',
    })
  })

  it('should compute query params with all parameters', () => {
    const { queryParams, setPage, setSearch, setSort } = useTable(100)
    
    setSearch('query')
    setSort('date', 'asc')
    setPage(2) // Set page after search to avoid reset
    
    expect(queryParams.value).toEqual({
      page: 2,
      page_size: 100,
      search: 'query',
      sort_by: 'date',
      sort_order: 'asc',
    })
  })
})
