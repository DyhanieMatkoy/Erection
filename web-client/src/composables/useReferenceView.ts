import { ref, computed } from 'vue'
import { useTable } from './useTable'
import { useReferencesStore } from '@/stores/references'

interface ReferenceItem {
  id?: number
  name?: string
  full_name?: string
  parent_id: number | null
  is_deleted: boolean
  unit?: string
}

interface ReferenceApi<T> {
  getAll: (params?: unknown) => Promise<{ data: T[]; pagination?: unknown }>
  create: (data: Partial<T>) => Promise<T>
  update: (id: number, data: Partial<T>) => Promise<T>
  delete: (id: number) => Promise<void>
}

export function useReferenceView<T extends ReferenceItem>(
  api: ReferenceApi<T>,
  cacheUpdater?: () => Promise<void>
) {
  const referencesStore = useReferencesStore()
  const table = useTable()

  const modalOpen = ref(false)
  const editingItem = ref<T | null>(null)
  const formData = ref<Partial<T>>({
    name: '',
    parent_id: null,
  } as Partial<T>)
  const errors = ref<Record<string, string>>({})
  const submitError = ref('')
  const submitting = ref(false)

  const parentItems = computed(() => {
    return table.data.value
      .filter((item: any) => !item.is_deleted && item.id !== editingItem.value?.id)
      .map((item: any) => ({
        id: item.id,
        name: item.name || item.full_name,
      }))
  })

  function getParentName(parentId: number): string {
    const parent = table.data.value.find((item: any) => item.id === parentId)
    return (parent as any)?.name || (parent as any)?.full_name || ''
  }

  async function loadData() {
    table.loading.value = true
    try {
      const response = await api.getAll(table.queryParams.value)
      table.data.value = response.data as unknown[]
      table.pagination.value = response.pagination as any
      
      // Update cache if provided
      if (cacheUpdater) {
        await cacheUpdater()
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      table.loading.value = false
    }
  }

  function handlePageChange(page: number) {
    table.setPage(page)
    loadData()
  }

  function handleSearch(query: string) {
    table.setSearch(query)
    loadData()
  }

  function handleSort(sortBy: string, sortOrder: 'asc' | 'desc') {
    table.setSort(sortBy, sortOrder)
    loadData()
  }

  function handleCreate() {
    editingItem.value = null
    formData.value = {
      name: '',
      full_name: '',
      parent_id: null,
    } as Partial<T>
    errors.value = {}
    submitError.value = ''
    modalOpen.value = true
  }

  function handleEdit(item: T) {
    editingItem.value = item
    formData.value = { ...item }
    errors.value = {}
    submitError.value = ''
    modalOpen.value = true
  }

  async function handleSubmit() {
    // Validate
    errors.value = {}
    const nameField = (formData.value as any).full_name !== undefined ? 'full_name' : 'name'
    const nameValue = (formData.value as any)[nameField]
    
    if (!nameValue?.trim()) {
      errors.value[nameField] = 'Обязательное поле'
      return
    }

    submitting.value = true
    submitError.value = ''

    try {
      if (editingItem.value?.id) {
        await api.update(editingItem.value.id, formData.value)
      } else {
        await api.create(formData.value)
      }
      
      modalOpen.value = false
      await loadData()
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { detail?: string } } }
      submitError.value = apiError.response?.data?.detail || 'Ошибка при сохранении'
    } finally {
      submitting.value = false
    }
  }

  async function handleDelete(item: T) {
    const itemName = (item as any).name || (item as any).full_name || 'элемент'
    if (!confirm(`Удалить "${itemName}"?`)) {
      return
    }

    try {
      await api.delete(item.id!)
      await loadData()
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { detail?: string } } }
      alert(apiError.response?.data?.detail || 'Ошибка при удалении')
    }
  }

  function handleCloseModal() {
    modalOpen.value = false
    editingItem.value = null
  }

  return {
    table,
    modalOpen,
    editingItem,
    formData,
    errors,
    submitError,
    submitting,
    parentItems,
    getParentName,
    loadData,
    handlePageChange,
    handleSearch,
    handleSort,
    handleCreate,
    handleEdit,
    handleSubmit,
    handleDelete,
    handleCloseModal,
  }
}
