import apiClient from './client'
import type { ApiResponse, PaginationParams } from '@/types/api'
import type { Counterparty, Object, Work, Person, Organization, Unit } from '@/types/models'

// Generic reference API functions
async function getReferences<T>(
  referenceType: string,
  params?: PaginationParams
): Promise<ApiResponse<T[]>> {
  const response = await apiClient.get<ApiResponse<T[]>>(`/references/${referenceType}`, {
    params,
  })
  return response.data
}

async function getReference<T>(referenceType: string, id: number): Promise<T> {
  const response = await apiClient.get<{ success: boolean; data: T }>(`/references/${referenceType}/${id}`)
  return response.data.data
}

async function createReference<T>(referenceType: string, data: Partial<T>): Promise<T> {
  const response = await apiClient.post<{ success: boolean; data: T }>(`/references/${referenceType}`, data)
  return response.data.data
}

async function updateReference<T>(
  referenceType: string,
  id: number,
  data: Partial<T>
): Promise<T> {
  const response = await apiClient.put<{ success: boolean; data: T }>(`/references/${referenceType}/${id}`, data)
  return response.data.data
}

async function deleteReference(referenceType: string, id: number): Promise<void> {
  await apiClient.delete(`/references/${referenceType}/${id}`)
}

// Counterparties
export const getCounterparties = (params?: PaginationParams) =>
  getReferences<Counterparty>('counterparties', params)

export const getCounterparty = (id: number) => getReference<Counterparty>('counterparties', id)

export const createCounterparty = (data: Partial<Counterparty>) =>
  createReference<Counterparty>('counterparties', data)

export const updateCounterparty = (id: number, data: Partial<Counterparty>) =>
  updateReference<Counterparty>('counterparties', id, data)

export const deleteCounterparty = (id: number) => deleteReference('counterparties', id)

// Objects
export const getObjects = (params?: PaginationParams) =>
  getReferences<Object>('objects', params)

export const getObject = (id: number) => getReference<Object>('objects', id)

export const createObject = (data: Partial<Object>) => createReference<Object>('objects', data)

export const updateObject = (id: number, data: Partial<Object>) =>
  updateReference<Object>('objects', id, data)

export const deleteObject = (id: number) => deleteReference('objects', id)

// Works
export interface WorksParams extends PaginationParams {
  include_unit_info?: boolean
  hierarchy_mode?: 'flat' | 'tree' | 'breadcrumb'
  parent_id?: number | null
}

export const getWorks = (params?: WorksParams) => getReferences<Work>('works', params)

export const getWork = (id: number) => getReference<Work>('works', id)

export const createWork = (data: Partial<Work>) => createReference<Work>('works', data)

export const updateWork = (id: number, data: Partial<Work>) =>
  updateReference<Work>('works', id, data)

export const deleteWork = (id: number) => deleteReference('works', id)

// Units
export const getUnits = (params?: PaginationParams) => getReferences<Unit>('units', params)

export const getUnit = (id: number) => getReference<Unit>('units', id)

export const createUnit = (data: Partial<Unit>) => createReference<Unit>('units', data)

export const updateUnit = (id: number, data: Partial<Unit>) =>
  updateReference<Unit>('units', id, data)

export const deleteUnit = (id: number) => deleteReference('units', id)

// Persons
export const getPersons = (params?: PaginationParams) => getReferences<Person>('persons', params)

export const getPerson = (id: number) => getReference<Person>('persons', id)

export const createPerson = (data: Partial<Person>) => createReference<Person>('persons', data)

export const updatePerson = (id: number, data: Partial<Person>) =>
  updateReference<Person>('persons', id, data)

export const deletePerson = (id: number) => deleteReference('persons', id)

// Organizations
export const getOrganizations = (params?: PaginationParams) =>
  getReferences<Organization>('organizations', params)

export const getOrganization = (id: number) => getReference<Organization>('organizations', id)

export const createOrganization = (data: Partial<Organization>) =>
  createReference<Organization>('organizations', data)

export const updateOrganization = (id: number, data: Partial<Organization>) =>
  updateReference<Organization>('organizations', id, data)

export const deleteOrganization = (id: number) => deleteReference('organizations', id)

// Bulk Operations
export interface BulkOperationResult {
  success: boolean
  message: string
  processed: number
  errors: string[]
}

async function bulkDeleteReferences(
  referenceType: string,
  ids: number[]
): Promise<BulkOperationResult> {
  const response = await apiClient.post<BulkOperationResult>(
    `/references/${referenceType}/bulk-delete`,
    { ids }
  )
  return response.data
}

export const bulkDeleteCounterparties = (ids: number[]) =>
  bulkDeleteReferences('counterparties', ids)

export const bulkDeleteObjects = (ids: number[]) => bulkDeleteReferences('objects', ids)

export const bulkDeleteWorks = (ids: number[]) => bulkDeleteReferences('works', ids)

export const bulkDeletePersons = (ids: number[]) => bulkDeleteReferences('persons', ids)

export const bulkDeleteOrganizations = (ids: number[]) =>
  bulkDeleteReferences('organizations', ids)

// User-Person Linking
export interface LinkUserPersonRequest {
  user_id: number
  person_id?: number | null
}

export interface PersonWithUser extends Person {
  user_id?: number | null
}

export async function linkUserToPerson(
  userId: number,
  personId?: number | null
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(
    '/references/persons/link-user',
    { user_id: userId, person_id: personId }
  )
  return response.data
}

export async function getPersonsAvailableForUser(
  userId: number
): Promise<PersonWithUser[]> {
  const response = await apiClient.get<{ success: boolean; data: PersonWithUser[] }>(
    `/references/persons/available-for-user/${userId}`
  )
  return response.data.data
}

// CSV Import for Works
export interface ImportWorksResult {
  success: boolean
  message: string
  added: number
  skipped: number
  errors: string[]
}

export async function importWorksFromCSV(
  file: File,
  parentId?: number | null,
  skipExisting: boolean = true,
  deleteMode: boolean = false
): Promise<ImportWorksResult> {
  const formData = new FormData()
  formData.append('file', file)
  
  const params = new URLSearchParams()
  if (parentId !== null && parentId !== undefined) {
    params.append('parent_id', parentId.toString())
  }
  params.append('skip_existing', skipExisting.toString())
  params.append('delete_mode', deleteMode.toString())
  
  const response = await apiClient.post<ImportWorksResult>(
    `/references/works/import-csv?${params.toString()}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

// Bulk Move Works
export async function bulkMoveWorks(
  workIds: number[],
  newParentId?: number | null
): Promise<BulkOperationResult> {
  const response = await apiClient.post<BulkOperationResult>(
    '/references/works/bulk-move',
    { work_ids: workIds, new_parent_id: newParentId }
  )
  return response.data
}

// Permanent Delete Marked Items
async function permanentDeleteMarked(
  referenceType: string
): Promise<BulkOperationResult> {
  const response = await apiClient.delete<BulkOperationResult>(
    `/references/${referenceType}/permanent-delete-marked`
  )
  return response.data
}

export const permanentDeleteMarkedCounterparties = () =>
  permanentDeleteMarked('counterparties')

export const permanentDeleteMarkedObjects = () => permanentDeleteMarked('objects')

export const permanentDeleteMarkedWorks = () => permanentDeleteMarked('works')

export const permanentDeleteMarkedPersons = () => permanentDeleteMarked('persons')

export const permanentDeleteMarkedOrganizations = () =>
  permanentDeleteMarked('organizations')

// ============================================================================
// Work Unit Migration API
// ============================================================================

export interface MigrationStatus {
  total_works: number
  migrated_count: number
  pending_count: number
  manual_review_count: number
  matched_count: number
  completion_percentage: number
  total_entries: number
  status_breakdown: Record<string, number>
}

export interface MigrationEntry {
  work_id: number
  legacy_unit: string
  matched_unit_id?: number | null
  confidence_score?: number
  manual_review_reason?: string
  migration_status: string
  work_name: string
  matched_unit_name?: string | null
}

export interface StartMigrationRequest {
  auto_apply_threshold?: number
  batch_size?: number
}

export interface ManualReviewRequest {
  work_id: number
  unit_id?: number | null
  action: 'approve' | 'reject' | 'assign'
}

export async function getMigrationStatus(): Promise<MigrationStatus> {
  const response = await apiClient.get<{ success: boolean; data: MigrationStatus }>('/references/works/migration-status')
  return response.data.data
}

export async function startMigration(request: StartMigrationRequest): Promise<{ success: boolean; message: string; data: any }> {
  const response = await apiClient.post<{ success: boolean; message: string; data: any }>('/references/works/migrate-units', request)
  return response.data
}

export async function getPendingMigrations(limit: number = 50): Promise<MigrationEntry[]> {
  const response = await apiClient.get<{ success: boolean; data: MigrationEntry[] }>(`/references/works/migration-pending?limit=${limit}`)
  return response.data.data
}

export async function reviewMigration(request: ManualReviewRequest): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>('/references/works/migration-review', request)
  return response.data
}
