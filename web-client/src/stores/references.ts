import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Counterparty, Object, Work, Person, Organization, Unit } from '@/types/models'
import * as referencesApi from '@/api/references'

export const useReferencesStore = defineStore('references', () => {
  // Cache for reference data
  const counterparties = ref<Counterparty[]>([])
  const objects = ref<Object[]>([])
  const works = ref<Work[]>([])
  const persons = ref<Person[]>([])
  const organizations = ref<Organization[]>([])
  const units = ref<Unit[]>([])

  // Loading states
  const loading = ref({
    counterparties: false,
    objects: false,
    works: false,
    persons: false,
    organizations: false,
    units: false,
  })

  // Fetch counterparties
  async function fetchCounterparties(force = false) {
    if (counterparties.value.length > 0 && !force) {
      return counterparties.value
    }

    loading.value.counterparties = true
    try {
      // Load all counterparties with pagination
      const allData = []
      let page = 1
      let hasMore = true
      
      while (hasMore) {
        const response = await referencesApi.getCounterparties({ page, page_size: 100 })
        allData.push(...response.data)
        hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
        page++
      }
      
      counterparties.value = allData
      return allData
    } finally {
      loading.value.counterparties = false
    }
  }

  // Fetch objects
  async function fetchObjects(force = false) {
    if (objects.value.length > 0 && !force) {
      return objects.value
    }

    loading.value.objects = true
    try {
      // Load all objects with pagination
      const allData = []
      let page = 1
      let hasMore = true
      
      while (hasMore) {
        const response = await referencesApi.getObjects({ page, page_size: 100 })
        allData.push(...response.data)
        hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
        page++
      }
      
      objects.value = allData
      return allData
    } finally {
      loading.value.objects = false
    }
  }

  // Fetch works
  async function fetchWorks(force = false) {
    if (works.value.length > 0 && !force) {
      return works.value
    }

    loading.value.works = true
    try {
      // Load all works in a single request (limit increased on backend)
      const response = await referencesApi.getWorks({ page: 1, page_size: 10000 })
      works.value = response.data
      return works.value
    } finally {
      loading.value.works = false
    }
  }

  // Fetch units
  async function fetchUnits(force = false) {
    if (units.value.length > 0 && !force) {
      return units.value
    }

    loading.value.units = true
    try {
      // Load all units in a single request
      const response = await referencesApi.getUnits({ page: 1, page_size: 1000 })
      units.value = response.data
      return units.value
    } finally {
      loading.value.units = false
    }
  }

  // Fetch persons
  async function fetchPersons(force = false) {
    if (persons.value.length > 0 && !force) {
      return persons.value
    }

    loading.value.persons = true
    try {
      // Load all persons with pagination
      const allData = []
      let page = 1
      let hasMore = true
      
      while (hasMore) {
        const response = await referencesApi.getPersons({ page, page_size: 100 })
        allData.push(...response.data)
        hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
        page++
      }
      
      persons.value = allData
      return allData
    } finally {
      loading.value.persons = false
    }
  }

  // Fetch organizations
  async function fetchOrganizations(force = false) {
    if (organizations.value.length > 0 && !force) {
      return organizations.value
    }

    loading.value.organizations = true
    try {
      // Load all organizations with pagination
      const allData = []
      let page = 1
      let hasMore = true
      
      while (hasMore) {
        const response = await referencesApi.getOrganizations({ page, page_size: 100 })
        allData.push(...response.data)
        hasMore = !!(response.pagination && response.pagination.total_pages && page < response.pagination.total_pages)
        page++
      }
      
      organizations.value = allData
      return allData
    } finally {
      loading.value.organizations = false
    }
  }

  // Clear cache
  function clearCache() {
    counterparties.value = []
    objects.value = []
    works.value = []
    persons.value = []
    organizations.value = []
    units.value = []
  }

  return {
    // State
    counterparties,
    objects,
    works,
    persons,
    organizations,
    units,
    loading,
    // Actions
    fetchCounterparties,
    fetchObjects,
    fetchWorks,
    fetchUnits,
    fetchPersons,
    fetchOrganizations,
    clearCache,
  }
})
