<template>
  <ListForm
    :is-open="isOpen"
    :title="title"
    search-placeholder="Search by code or name..."
    loading-message="Loading works..."
    empty-message="No works found"
    confirm-button-text="Select Work"
    :items="filteredWorks"
    :loading="loading"
    :error="error"
    :selected-item="selectedItem"
    :show-pagination="true"
    :items-per-page="20"
    :get-item-key="(item) => item.id"
    :get-item-code="(item) => item.code || '-'"
    :get-item-description="(item) => item.name"
    :is-item-disabled="isItemDisabled"
    @close="handleClose"
    @select="handleSelect"
    @retry="loadWorks"
  >
    <template #filters>
      <div class="filter-buttons">
        <button 
          :class="['filter-btn', { active: !showGroupsOnly }]"
          @click="showGroupsOnly = false"
        >
          All Works
        </button>
        <button 
          :class="['filter-btn', { active: showGroupsOnly }]"
          @click="showGroupsOnly = true"
        >
          Groups Only
        </button>
      </div>
    </template>

    <template #item="{ item, highlightText }">
      <div class="work-content" :id="`work-item-${item.id}`" :style="{ paddingLeft: `${(item._level || 0) * 1.5}rem` }">
        <!-- Expand/Collapse Button -->
        <button
          v-if="item._hasChildren"
          class="expand-btn"
          @click="toggleExpand(item.id, $event)"
          :aria-label="item._isExpanded ? 'Collapse' : 'Expand'"
        >
          {{ item._isExpanded ? '▼' : '▶' }}
        </button>
        <div v-else class="expand-spacer"></div>
        
        <div class="item-icon">
          {{ item.is_group ? '📁' : '📄' }}
        </div>
        <div class="item-details">
          <div class="item-header">
            <span class="item-code" v-html="highlightText(item.code || '-')"></span>
            <span v-if="item.is_group" class="badge badge-secondary">Group</span>
            <span v-if="isCircularReference(item.id)" class="badge badge-warning">Circular Ref</span>
            <span v-if="childCounts[item.id]" class="badge badge-info">
              {{ childCounts[item.id] }} children
            </span>
          </div>
          <div class="item-name" v-html="highlightText(item.name)"></div>
          <div v-if="hierarchyPaths[item.id]" class="item-path">
            {{ hierarchyPaths[item.id] }}
          </div>
          <div v-if="!item.is_group" class="item-metadata">
            <span v-if="item.price" class="price-info">{{ formatPrice(item.price) }}</span>
          </div>
        </div>
      </div>
    </template>
  </ListForm>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import ListForm from './ListForm.vue'
import { getWorks } from '@/api/references'
import type { Work } from '@/types/models'

// Extended Work type with hierarchy metadata
interface WorkWithMeta extends Work {
  _level?: number
  _hasChildren?: boolean
  _isExpanded?: boolean
}

interface Props {
  isOpen: boolean
  title?: string
  currentWorkId?: number | null
  groupsOnly?: boolean
  selectedId?: number | null // ID of the work to be selected/highlighted
}

interface Emits {
  (e: 'close'): void
  (e: 'select', work: Work): void
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Select Parent Work',
  currentWorkId: null,
  groupsOnly: false,
  selectedId: null
})

const emit = defineEmits<Emits>()

// State
const works = ref<Work[]>([])
const selectedItem = ref<Work | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const showGroupsOnly = ref(false)
const expandedNodes = ref<Set<number>>(new Set())

// Watch for selectedId changes
watch(() => props.selectedId, (newId) => {
  if (newId && works.value.length > 0) {
    expandToItem(newId)
    const found = works.value.find(w => w.id === newId)
    if (found) {
      selectedItem.value = found
    }
  }
})

function expandToItem(itemId: number) {
  // Find item and its parents
  const item = works.value.find(w => w.id === itemId)
  if (!item) return
  
  let currentParentId = item.parent_id
  while (currentParentId) {
    expandedNodes.value.add(currentParentId)
    const parent = works.value.find(w => w.id === currentParentId)
    currentParentId = parent ? parent.parent_id : null
  }
}

// Computed
const filteredWorks = computed(() => {
  let filtered = works.value

  // Filter by groups if needed
  if (showGroupsOnly.value || props.groupsOnly) {
    filtered = filtered.filter(w => w.is_group)
  }

  // Build hierarchical structure and flatten with visibility
  return buildHierarchicalList(filtered)
})

function buildHierarchicalList(worksList: Work[]): Work[] {
  // First, organize works by parent
  const rootWorks = worksList.filter(w => !w.parent_id)
  const childrenMap = new Map<number, Work[]>()
  
  worksList.forEach(work => {
    if (work.parent_id) {
      if (!childrenMap.has(work.parent_id)) {
        childrenMap.set(work.parent_id, [])
      }
      childrenMap.get(work.parent_id)!.push(work)
    }
  })
  
  // Flatten the tree with proper ordering and visibility
  const result: Work[] = []
  
  function addWorkAndChildren(work: Work, level: number = 0) {
    // Add metadata for rendering
    const workWithMeta = {
      ...work,
      _level: level,
      _hasChildren: childrenMap.has(work.id),
      _isExpanded: expandedNodes.value.has(work.id)
    }
    result.push(workWithMeta as unknown)
    
    // Add children if expanded
    if (expandedNodes.value.has(work.id) && childrenMap.has(work.id)) {
      const children = childrenMap.get(work.id)!
      children.forEach(child => addWorkAndChildren(child, level + 1))
    }
  }
  
  rootWorks.forEach(work => addWorkAndChildren(work))
  
  return result
}

const hierarchyPaths = computed(() => {
  const paths: Record<number, string> = {}
  
  works.value.forEach(work => {
    if (work.parent_id) {
      paths[work.id] = buildHierarchyPath(work.id)
    }
  })
  
  return paths
})

const childCounts = computed(() => {
  const counts: Record<number, number> = {}
  
  works.value.forEach(work => {
    if (work.parent_id) {
      counts[work.parent_id] = (counts[work.parent_id] || 0) + 1
    }
  })
  
  return counts
})

// Watch for dialog open
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && works.value.length === 0) {
    loadWorks()
  }
  if (isOpen) {
    selectedItem.value = null
    showGroupsOnly.value = props.groupsOnly
    
    if (props.selectedId) {
      // If we have a selected ID, try to find and select it
      // Wait for data load if needed
      if (works.value.length > 0) {
        expandToItem(props.selectedId)
        const found = works.value.find(w => w.id === props.selectedId)
        if (found) {
          selectedItem.value = found
          
          // Scroll to item after render
          nextTick(() => {
             const el = document.getElementById(`work-item-${props.selectedId}`)
             if (el) el.scrollIntoView({ block: 'center' })
          })
        }
      }
    } else {
      // Default behavior: Expand all root nodes
      expandedNodes.value.clear()
      works.value.filter(w => !w.parent_id).forEach(w => {
        expandedNodes.value.add(w.id)
      })
    }
  }
})

// Methods
async function loadWorks() {
  loading.value = true
  error.value = null
  try {
    const response = await getWorks()
    works.value = response.data || []
    
    // Handle initial selection if provided
    if (props.selectedId && props.isOpen) {
       expandToItem(props.selectedId)
       const found = works.value.find(w => w.id === props.selectedId)
       if (found) {
         selectedItem.value = found
          nextTick(() => {
             const el = document.getElementById(`work-item-${props.selectedId}`)
             if (el) el.scrollIntoView({ block: 'center' })
          })
       }
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load works'
    console.error('Error loading works:', err)
  } finally {
    loading.value = false
  }
}

function buildHierarchyPath(workId: number, visited = new Set<number>()): string {
  // Prevent infinite loops
  if (visited.has(workId)) {
    return '[Circular]'
  }
  
  const work = works.value.find(w => w.id === workId)
  if (!work) return ''
  
  if (!work.parent_id) {
    return work.name
  }
  
  visited.add(workId)
  const parentPath = buildHierarchyPath(work.parent_id, visited)
  return parentPath ? `${parentPath} > ${work.name}` : work.name
}

function isCircularReference(workId: number): boolean {
  if (!props.currentWorkId) return false
  
  // Check if selecting this work would create a circular reference
  return isDescendant(props.currentWorkId, workId)
}

function isDescendant(ancestorId: number, descendantId: number, visited = new Set<number>()): boolean {
  if (ancestorId === descendantId) return true
  if (visited.has(descendantId)) return false
  
  visited.add(descendantId)
  
  const descendant = works.value.find(w => w.id === descendantId)
  if (!descendant || !descendant.parent_id) return false
  
  return isDescendant(ancestorId, descendant.parent_id, visited)
}

function isItemDisabled(item: Work): boolean {
  // Disable if it's the current work itself
  if (props.currentWorkId && item.id === props.currentWorkId) {
    return true
  }
  
  // Disable if selecting it would create a circular reference
  if (isCircularReference(item.id)) {
    return true
  }
  
  // Disable non-groups if groupsOnly is true
  if (props.groupsOnly && !item.is_group) {
    return true
  }
  
  return false
}

function handleSelect(item: Work) {
  emit('select', item)
}

function handleClose() {
  emit('close')
}

function formatPrice(price: number | undefined): string {
  if (price === undefined || price === null) return '-'
  return price.toFixed(2)
}

function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(2)
}

function toggleExpand(workId: number, event: Event) {
  event.stopPropagation()
  if (expandedNodes.value.has(workId)) {
    expandedNodes.value.delete(workId)
  } else {
    expandedNodes.value.add(workId)
  }
}
</script>

<style scoped>
.filter-buttons {
  display: flex;
  gap: 0.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ced4da;
  background-color: white;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.filter-btn:hover {
  background-color: #f8f9fa;
}

.filter-btn.active {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.work-content {
  display: flex;
  gap: 0.5rem;
  width: 100%;
  align-items: flex-start;
}

.expand-btn {
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.75rem;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: color 0.2s;
}

.expand-btn:hover {
  color: #007bff;
}

.expand-spacer {
  width: 1.5rem;
  flex-shrink: 0;
}

.item-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.item-details {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  flex-wrap: wrap;
}

.item-code {
  font-weight: 600;
  color: #495057;
}

.item-name {
  color: #212529;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.item-path {
  font-size: 0.75rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
  font-style: italic;
}

.item-metadata {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #6c757d;
}

.price-info {
  font-weight: 600;
  color: #28a745;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.25rem;
}

.badge-info {
  background-color: #17a2b8;
  color: white;
}

.badge-secondary {
  background-color: #6c757d;
  color: white;
}

.badge-warning {
  background-color: #ffc107;
  color: #212529;
}
</style>
