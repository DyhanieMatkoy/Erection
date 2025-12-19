<template>
  <div class="migration-demo">
    <div class="demo-header">
      <h1>Work Unit Migration Management</h1>
      <p class="demo-description">
        This demo shows the work unit migration management interface for transitioning from legacy unit strings to unit_id foreign keys.
      </p>
    </div>

    <!-- Migration Panel -->
    <WorkMigrationPanel 
      :auto-refresh="true"
      :refresh-interval="30000"
    />

    <!-- Enhanced Work List Demo -->
    <div class="demo-section">
      <h2>Enhanced Work List</h2>
      <p>The work list now supports different hierarchy display modes and shows proper unit information.</p>
      
      <div class="demo-controls">
        <button 
          class="btn btn-primary"
          @click="showWorkList = true"
        >
          Open Enhanced Work List
        </button>
      </div>

      <WorkListForm
        :is-open="showWorkList"
        title="Enhanced Work List Demo"
        :show-hierarchy-controls="true"
        :hierarchy-mode="'flat'"
        @close="showWorkList = false"
        @select="handleWorkSelect"
      />
    </div>

    <!-- Work Form Demo -->
    <div class="demo-section">
      <h2>Updated Work Form</h2>
      <p>Work forms now use unit selectors instead of text inputs and validate unit_id foreign keys.</p>
      
      <div class="demo-controls">
        <button 
          class="btn btn-primary"
          @click="showWorkForm = true"
        >
          Open Work Form Demo
        </button>
      </div>

      <!-- Simple Work Form Modal -->
      <div v-if="showWorkForm" class="modal-overlay" @click="closeWorkForm">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Work Form Demo</h3>
            <button class="modal-close" @click="closeWorkForm">✕</button>
          </div>
          <div class="modal-body">
            <WorkBasicInfo
              :work="demoWork"
              :units="units"
              :works="works"
              @update:work="handleWorkUpdate"
            />
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeWorkForm">Close</button>
            <button class="btn btn-primary" @click="saveWork">Save Demo Work</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected Work Display -->
    <div v-if="selectedWork" class="demo-section">
      <h2>Selected Work</h2>
      <div class="work-display">
        <div class="work-info">
          <h3>{{ selectedWork.name }}</h3>
          <p><strong>Code:</strong> {{ selectedWork.code || 'N/A' }}</p>
          <p><strong>Unit:</strong> {{ (selectedWork as any).unit_display || selectedWork.unit_name || 'N/A' }}</p>
          <p><strong>Price:</strong> {{ selectedWork.price || 0 }}</p>
          <p><strong>Is Group:</strong> {{ selectedWork.is_group ? 'Yes' : 'No' }}</p>
          <p v-if="(selectedWork as any).hierarchy_path"><strong>Path:</strong> {{ (selectedWork as any).hierarchy_path.join(' > ') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import WorkMigrationPanel from '@/components/common/WorkMigrationPanel.vue'
import WorkListForm from '@/components/common/WorkListForm.vue'
import WorkBasicInfo from '@/components/work/WorkBasicInfo.vue'
import { useReferencesStore } from '@/stores/references'
import { useToast } from '@/composables/useToast'
import type { Work, Unit } from '@/types/models'

// State
const showWorkList = ref(false)
const showWorkForm = ref(false)
const selectedWork = ref<Work | null>(null)
const demoWork = ref<Partial<Work>>({
  name: 'Demo Work',
  code: 'DEMO-001',
  unit_id: undefined,
  unit: '',
  price: 100.50,
  labor_rate: 2.5,
  is_group: false,
  parent_id: null
})

// References
const referencesStore = useReferencesStore()
const toast = useToast()

// Computed
const units = computed(() => referencesStore.units)
const works = computed(() => referencesStore.works)

// Methods
function handleWorkSelect(work: Work) {
  selectedWork.value = work
  showWorkList.value = false
  toast.success(`Selected work: ${work.name}`)
}

function handleWorkUpdate(updatedWork: Partial<Work>) {
  demoWork.value = { ...updatedWork }
}

function closeWorkForm() {
  showWorkForm.value = false
}

function saveWork() {
  toast.success('Demo work saved (not actually saved to database)')
  console.log('Demo work data:', demoWork.value)
  closeWorkForm()
}

// Lifecycle
onMounted(async () => {
  try {
    // Load reference data
    await Promise.all([
      referencesStore.fetchUnits(),
      referencesStore.fetchWorks()
    ])
  } catch (error) {
    console.error('Failed to load reference data:', error)
    toast.error('Failed to load reference data')
  }
})
</script>

<style scoped>
.migration-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.demo-header {
  text-align: center;
  margin-bottom: 3rem;
}

.demo-header h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.demo-description {
  color: #6c757d;
  font-size: 1.125rem;
  max-width: 600px;
  margin: 0 auto;
}

.demo-section {
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.demo-section h2 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.demo-section p {
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.demo-controls {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.work-display {
  background: #f8f9fa;
  border-radius: 0.375rem;
  padding: 1.5rem;
  border: 1px solid #e9ecef;
}

.work-info h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.work-info p {
  margin-bottom: 0.5rem;
  color: #495057;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
</style>