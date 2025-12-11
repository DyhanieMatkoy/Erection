<template>
  <div class="work-basic-info-demo">
    <div class="page-header">
      <h1>Work Basic Info Component Demo</h1>
      <p class="subtitle">Test the WorkBasicInfo component with validation</p>
    </div>

    <div class="demo-container">
      <WorkBasicInfo
        :work="currentWork"
        :units="units"
        :works="works"
        @update:work="handleWorkUpdate"
        @validate="handleValidate"
      />

      <div class="actions">
        <button class="btn btn-primary" @click="saveWork">
          Save Work
        </button>
        <button class="btn btn-secondary" @click="resetWork">
          Reset
        </button>
      </div>

      <div class="debug-panel">
        <h3>Current Work Data</h3>
        <pre>{{ JSON.stringify(currentWork, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import WorkBasicInfo from '@/components/work/WorkBasicInfo.vue'
import type { Work, Unit } from '@/types/models'

// Sample data
const units = ref<Unit[]>([
  { id: 1, name: 'м', description: 'Meter', marked_for_deletion: false },
  { id: 2, name: 'м²', description: 'Square meter', marked_for_deletion: false },
  { id: 3, name: 'м³', description: 'Cubic meter', marked_for_deletion: false },
  { id: 4, name: 'кг', description: 'Kilogram', marked_for_deletion: false },
  { id: 5, name: 'т', description: 'Ton', marked_for_deletion: false },
  { id: 6, name: 'шт', description: 'Piece', marked_for_deletion: false }
])

const works = ref<Work[]>([
  {
    id: 1,
    name: 'Construction Works',
    code: 'CW-001',
    unit: 'м²',
    unit_id: 2,
    price: 0,
    labor_rate: 0,
    parent_id: null,
    is_group: true,
    is_deleted: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01'
  },
  {
    id: 2,
    name: 'Masonry Works',
    code: 'MW-001',
    unit: 'м²',
    unit_id: 2,
    price: 0,
    labor_rate: 0,
    parent_id: 1,
    is_group: true,
    is_deleted: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01'
  },
  {
    id: 3,
    name: 'Brick Laying',
    code: 'BL-001',
    unit: 'м²',
    unit_id: 2,
    price: 1500,
    labor_rate: 2.5,
    parent_id: 2,
    is_group: false,
    is_deleted: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01'
  }
])

const initialWork: Partial<Work> = {
  name: '',
  code: '',
  unit_id: undefined,
  unit: undefined,
  price: 0,
  labor_rate: 0,
  parent_id: null,
  is_group: false
}

const currentWork = ref<Partial<Work>>({ ...initialWork })

function handleWorkUpdate(updatedWork: Partial<Work>) {
  currentWork.value = updatedWork
}

function handleValidate() {
  console.log('Validation triggered')
}

function saveWork() {
  console.log('Saving work:', currentWork.value)
  alert('Work saved! Check console for details.')
}

function resetWork() {
  currentWork.value = { ...initialWork }
}
</script>

<style scoped>
.work-basic-info-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 700;
  color: #212529;
}

.subtitle {
  margin: 0;
  font-size: 1.125rem;
  color: #6c757d;
}

.demo-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.actions {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.debug-panel {
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 0.5rem;
  border: 1px solid #dee2e6;
}

.debug-panel h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.125rem;
  color: #495057;
}

.debug-panel pre {
  margin: 0;
  padding: 1rem;
  background-color: #212529;
  color: #f8f9fa;
  border-radius: 0.25rem;
  overflow-x: auto;
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>
