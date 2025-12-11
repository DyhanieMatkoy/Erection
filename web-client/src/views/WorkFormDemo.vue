<template>
  <div class="work-form-demo">
    <div class="demo-header">
      <h1>Work Form Demo</h1>
      <p class="subtitle">Complete work composition editing interface</p>
    </div>

    <div class="demo-controls">
      <div class="control-group">
        <label for="work-select">Select Work:</label>
        <select
          id="work-select"
          v-model="selectedWorkId"
          class="form-control"
          @change="handleWorkChange"
        >
          <option :value="null">-- Select a work --</option>
          <option v-for="work in availableWorks" :key="work.id" :value="work.id">
            {{ work.code ? `${work.code} - ` : '' }}{{ work.name }}
          </option>
        </select>
      </div>

      <button
        v-if="!showForm"
        @click="createNewWork"
        class="btn btn-primary"
      >
        Create New Work
      </button>
    </div>

    <!-- Work Form -->
    <div v-if="showForm && selectedWorkId" class="form-container">
      <WorkForm
        :key="selectedWorkId"
        :work-id="selectedWorkId"
        @saved="handleSaved"
        @cancelled="handleCancelled"
      />
    </div>

    <!-- Empty State -->
    <div v-else-if="!showForm" class="empty-state">
      <p>Select a work from the dropdown above or create a new work to get started.</p>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="success-toast">
      {{ successMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import WorkForm from '@/components/work/WorkForm.vue'
import { getWorks, createWork } from '@/api/references'
import type { Work } from '@/types/models'

// State
const selectedWorkId = ref<number | null>(null)
const availableWorks = ref<Work[]>([])
const showForm = ref(false)
const successMessage = ref<string | null>(null)

// Methods
async function loadWorks() {
  try {
    const response = await getWorks()
    availableWorks.value = response.data || []
    
    // If we have works, select the first one
    if (availableWorks.value.length > 0 && !selectedWorkId.value) {
      const firstWork = availableWorks.value[0]
      if (firstWork) {
        selectedWorkId.value = firstWork.id
        showForm.value = true
      }
    }
  } catch (error) {
    console.error('Error loading works:', error)
    alert('Failed to load works')
  }
}

async function createNewWork() {
  try {
    const newWork = await createWork({
      name: 'New Work',
      code: '',
      is_group: false,
      price: 0,
      labor_rate: 0,
      parent_id: null
    })
    
    // Add to list
    availableWorks.value.push(newWork)
    
    // Select the new work
    selectedWorkId.value = newWork.id
    showForm.value = true
  } catch (error) {
    console.error('Error creating work:', error)
    alert('Failed to create new work')
  }
}

function handleWorkChange() {
  if (selectedWorkId.value) {
    showForm.value = true
  } else {
    showForm.value = false
  }
}

function handleSaved(work: Work) {
  showSuccessMessage(`Work "${work.name}" saved successfully!`)
  
  // Update the work in the list
  const index = availableWorks.value.findIndex(w => w.id === work.id)
  if (index !== -1) {
    availableWorks.value[index] = work
  }
}

function handleCancelled() {
  showSuccessMessage('Changes cancelled')
}

function showSuccessMessage(message: string) {
  successMessage.value = message
  setTimeout(() => {
    successMessage.value = null
  }, 3000)
}

// Lifecycle
onMounted(() => {
  loadWorks()
})
</script>

<style scoped>
.work-form-demo {
  min-height: 100vh;
  background-color: #f8f9fa;
  padding: 2rem;
}

.demo-header {
  text-align: center;
  margin-bottom: 2rem;
}

.demo-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: #212529;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.125rem;
  color: #6c757d;
  margin: 0;
}

.demo-controls {
  max-width: 1400px;
  margin: 0 auto 2rem;
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  background: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.control-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  font-weight: 500;
  color: #495057;
  font-size: 0.875rem;
}

.form-control {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus {
  border-color: #80bdff;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.btn {
  padding: 0.5rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

.form-container {
  max-width: 1400px;
  margin: 0 auto;
}

.empty-state {
  max-width: 1400px;
  margin: 0 auto;
  padding: 4rem 2rem;
  text-align: center;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  color: #6c757d;
}

.empty-state p {
  font-size: 1.125rem;
  margin: 0;
}

/* Success Toast */
.success-toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background-color: #28a745;
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  animation: slideIn 0.3s ease-out;
  z-index: 1000;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .work-form-demo {
    padding: 1rem;
  }
  
  .demo-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .btn {
    width: 100%;
  }
  
  .success-toast {
    left: 1rem;
    right: 1rem;
    bottom: 1rem;
  }
}
</style>
