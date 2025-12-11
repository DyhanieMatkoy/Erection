<template>
  <div class="work-composition-view">
    <!-- Header -->
    <div class="view-header">
      <div class="header-content">
        <button @click="handleBack" class="back-button" title="Back to works list">
          <span class="back-icon">←</span>
          <span>Back</span>
        </button>
        <h1 class="view-title">
          {{ isNewWork ? 'Create New Work' : 'Edit Work Composition' }}
        </h1>
      </div>
      <div class="header-actions">
        <button
          v-if="!isNewWork"
          @click="handleRefresh"
          class="btn btn-outline"
          :disabled="refreshing"
          title="Refresh work data"
        >
          <span v-if="refreshing" class="spinner-small"></span>
          <span v-else>🔄</span>
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Breadcrumb Navigation -->
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <ol class="breadcrumb-list">
        <li class="breadcrumb-item">
          <router-link to="/" class="breadcrumb-link">Home</router-link>
        </li>
        <li class="breadcrumb-item">
          <router-link to="/references/works" class="breadcrumb-link">Works</router-link>
        </li>
        <li class="breadcrumb-item active" aria-current="page">
          {{ isNewWork ? 'New Work' : `Work #${workId}` }}
        </li>
      </ol>
    </nav>

    <!-- Main Content -->
    <div class="view-content">
      <!-- Work Form -->
      <WorkForm
        v-if="workId"
        :work-id="workId"
        @saved="handleSaved"
        @cancelled="handleCancelled"
      />

      <!-- Empty State for New Work -->
      <div v-else class="empty-state">
        <div class="empty-state-icon">📝</div>
        <h2 class="empty-state-title">Create a New Work</h2>
        <p class="empty-state-description">
          Define a new work type with its cost items and material composition.
        </p>
        <button @click="handleCreateNew" class="btn btn-primary">
          Create New Work
        </button>
      </div>
    </div>

    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="modal-overlay" @click="closeSuccessModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2 class="modal-title">✓ Success</h2>
          <button @click="closeSuccessModal" class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <p>Work has been saved successfully!</p>
        </div>
        <div class="modal-footer">
          <button @click="handleViewList" class="btn btn-secondary">
            View Works List
          </button>
          <button @click="closeSuccessModal" class="btn btn-primary">
            Continue Editing
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import WorkForm from '@/components/work/WorkForm.vue'
import type { Work } from '@/types/models'

const router = useRouter()
const route = useRoute()

// State
const workId = ref<number | null>(null)
const refreshing = ref(false)
const showSuccessModal = ref(false)
const savedWork = ref<Work | null>(null)

// Computed
const isNewWork = computed(() => !workId.value || workId.value === 0)

// Methods
function handleBack() {
  router.push('/references/works')
}

function handleRefresh() {
  refreshing.value = true
  // Force component re-mount by changing key
  const currentId = workId.value
  workId.value = null
  setTimeout(() => {
    workId.value = currentId
    refreshing.value = false
  }, 100)
}

function handleSaved(work: Work) {
  savedWork.value = work
  showSuccessModal.value = true
}

function handleCancelled() {
  if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
    router.push('/references/works')
  }
}

function handleCreateNew() {
  // Navigate to create new work
  // This would typically create a new work record first
  console.log('Create new work - implementation needed')
}

function closeSuccessModal() {
  showSuccessModal.value = false
}

function handleViewList() {
  showSuccessModal.value = false
  router.push('/references/works')
}

// Lifecycle
onMounted(() => {
  // Get work ID from route params
  const id = route.params.id
  if (id && id !== 'new') {
    workId.value = parseInt(id as string, 10)
  }
})
</script>

<style scoped>
.work-composition-view {
  min-height: 100vh;
  background-color: #f8f9fa;
}

/* Header */
.view-header {
  background: white;
  border-bottom: 1px solid #e9ecef;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex: 1;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: none;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  color: #495057;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.back-button:hover {
  background-color: #f8f9fa;
  border-color: #adb5bd;
  color: #212529;
}

.back-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.view-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: #212529;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

/* Breadcrumb */
.breadcrumb {
  background: white;
  padding: 0.75rem 2rem;
  border-bottom: 1px solid #e9ecef;
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 0.875rem;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  color: #6c757d;
}

.breadcrumb-item:not(:last-child)::after {
  content: '/';
  margin-left: 0.5rem;
  color: #adb5bd;
}

.breadcrumb-link {
  color: #007bff;
  text-decoration: none;
  transition: color 0.2s;
}

.breadcrumb-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.breadcrumb-item.active {
  color: #495057;
  font-weight: 500;
}

/* Content */
.view-content {
  padding: 2rem;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: white;
  border-radius: 0.5rem;
  padding: 3rem;
  text-align: center;
}

.empty-state-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.empty-state-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #212529;
  margin: 0 0 1rem 0;
}

.empty-state-description {
  font-size: 1rem;
  color: #6c757d;
  margin: 0 0 2rem 0;
  max-width: 500px;
}

/* Button Styles */
.btn {
  padding: 0.5rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-outline {
  background-color: white;
  color: #495057;
  border: 1px solid #dee2e6;
}

.btn-outline:hover:not(:disabled) {
  background-color: #f8f9fa;
  border-color: #adb5bd;
}

/* Spinner */
.spinner-small {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid currentColor;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 100%;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #28a745;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #212529;
}

.modal-body {
  padding: 1.5rem;
  color: #495057;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e9ecef;
  background-color: #f8f9fa;
}

/* Responsive Design */
@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .header-content {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
  }

  .view-title {
    font-size: 1.5rem;
  }

  .breadcrumb {
    padding: 0.75rem 1rem;
  }

  .view-content {
    padding: 1rem;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-footer .btn {
    width: 100%;
  }
}
</style>
