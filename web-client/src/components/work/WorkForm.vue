<template>
  <div class="work-form">
    <!-- Loading State with Skeleton -->
    <div v-if="loading" class="loading-overlay">
      <LoadingSkeleton type="form" :rows="5" />
      <div class="mt-4">
        <LoadingSkeleton type="table" :rows="3" :columns="6" />
      </div>
      <div class="mt-4">
        <LoadingSkeleton type="table" :rows="3" :columns="8" />
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error && !loading" class="error-banner">
      <span class="error-icon">⚠️</span>
      <span class="error-message">{{ error }}</span>
      <button @click="error = null" class="close-error">&times;</button>
    </div>

    <!-- Form Content -->
    <div v-if="!loading" class="form-content">
      <!-- Work Basic Info Section -->
      <WorkBasicInfo
        ref="basicInfoRef"
        :work="localWork"
        :units="units"
        :works="works"
        @update:work="handleWorkUpdate"
        @validate="validateForm"
      />

      <!-- Cost Items Section -->
      <div class="section">
        <CostItemsTable
          :cost-items="costItems"
          :has-materials="costItemHasMaterials"
          @add-cost-item="handleAddCostItem"
          @delete-cost-item="handleDeleteCostItem"
        />
      </div>

      <!-- Materials Section -->
      <div class="section">
        <MaterialsTable
          :materials="materials"
          :cost-items="costItems"
          @add-material="handleAddMaterial"
          @update-quantity="handleUpdateQuantity"
          @change-cost-item="handleChangeCostItem"
          @delete-material="handleDeleteMaterial"
        />
      </div>

      <!-- Total Cost Display -->
      <div class="total-cost-section">
        <div class="total-cost-card">
          <div class="total-cost-label">Total Work Cost</div>
          <div class="total-cost-value">{{ formatCurrency(totalCost) }}</div>
          <div class="total-cost-breakdown">
            <div class="breakdown-item">
              <span class="breakdown-label">Cost Items:</span>
              <span class="breakdown-value">{{ formatCurrency(costItemsTotal) }}</span>
            </div>
            <div class="breakdown-item">
              <span class="breakdown-label">Materials:</span>
              <span class="breakdown-value">{{ formatCurrency(materialsTotal) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="form-actions">
        <button
          @click="handleCancel"
          class="btn btn-secondary"
          :disabled="saving"
          title="Cancel and discard changes"
        >
          Cancel
        </button>
        <button
          @click="handleSave"
          class="btn btn-primary"
          :disabled="saving || !isFormValid"
          :title="!isFormValid ? 'Please fix validation errors before saving' : 'Save work and all associations'"
        >
          <span v-if="saving" class="spinner-small"></span>
          <span v-else>Save</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import WorkBasicInfo from './WorkBasicInfo.vue'
import CostItemsTable from './CostItemsTable.vue'
import MaterialsTable from './MaterialsTable.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { useWorkComposition } from '@/composables/useWorkComposition'
import { useToast } from '@/composables/useToast'
import { useReferenceCache } from '@/composables/useCache'
import { unitsApi } from '@/api/costs-materials'
import { getWorks } from '@/api/references'
import type { Work, Unit, CostItem } from '@/types/models'

interface Props {
  workId: number
}

interface Emits {
  (e: 'saved', work: Work): void
  (e: 'cancelled'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Composables
const {
  work,
  costItems,
  materials,
  loading: composableLoading,
  error: composableError,
  totalCost,
  loadWork,
  saveWork,
  addCostItem,
  removeCostItem,
  addMaterial,
  updateMaterialQuantity,
  changeMaterialCostItem,
  removeMaterial,
  costItemHasMaterials
} = useWorkComposition(props.workId)

const toast = useToast()
const referenceCache = useReferenceCache()

// Local state
const localWork = ref<Partial<Work>>({})
const units = ref<Unit[]>([])
const works = ref<Work[]>([])
const saving = ref(false)
const error = ref<string | null>(null)
const isFormValid = ref(true)
const basicInfoRef = ref<InstanceType<typeof WorkBasicInfo> | null>(null)
const loadingReferenceData = ref(false)

// Computed
const loading = computed(() => composableLoading.value || saving.value)

const costItemsTotal = computed(() => {
  return costItems.value.reduce((sum, item) => {
    return sum + (item.cost_item?.price || 0)
  }, 0)
})

const materialsTotal = computed(() => {
  return materials.value.reduce((sum, item) => {
    const price = item.material?.price || 0
    const quantity = item.quantity_per_unit || 0
    return sum + (price * quantity)
  }, 0)
})

// Watch for work changes from composable
watch(work, (newWork) => {
  if (newWork) {
    localWork.value = { ...newWork }
  }
}, { immediate: true })

// Watch for composable errors
watch(composableError, (newError) => {
  if (newError) {
    error.value = newError
  }
})

// Methods
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function handleWorkUpdate(updatedWork: Partial<Work>) {
  localWork.value = { ...updatedWork }
  validateForm()
}

function validateForm() {
  // Validate basic info
  if (basicInfoRef.value) {
    isFormValid.value = basicInfoRef.value.validate()
  }
  
  // Additional validation
  if (!localWork.value.name || localWork.value.name.trim() === '') {
    isFormValid.value = false
  }
  
  // Validate group work constraints
  if (localWork.value.is_group) {
    if ((localWork.value.price && localWork.value.price > 0) ||
        (localWork.value.labor_rate && localWork.value.labor_rate > 0)) {
      isFormValid.value = false
    }
  }
  
  // Validate materials have valid quantities
  for (const material of materials.value) {
    if (material.quantity_per_unit <= 0) {
      isFormValid.value = false
      break
    }
  }
}

async function handleSave() {
  // Validate form
  validateForm()
  
  if (!isFormValid.value) {
    error.value = 'Please fix validation errors before saving'
    toast.error('Please fix validation errors before saving')
    return
  }
  
  saving.value = true
  error.value = null
  
  try {
    // Save work basic info
    const success = await saveWork(localWork.value)
    
    if (success && work.value) {
      // Show success message
      toast.success('Work saved successfully')
      
      // Emit saved event
      emit('saved', work.value)
    } else {
      error.value = 'Failed to save work'
      toast.error('Failed to save work')
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Failed to save work'
    error.value = errorMessage
    toast.error(errorMessage)
    console.error('Error saving work:', err)
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  if (hasUnsavedChanges()) {
    if (confirm('You have unsaved changes. Are you sure you want to cancel?')) {
      emit('cancelled')
    }
  } else {
    emit('cancelled')
  }
}

function hasUnsavedChanges(): boolean {
  if (!work.value) return false
  
  // Check if basic info has changed
  return (
    localWork.value.name !== work.value.name ||
    localWork.value.code !== work.value.code ||
    localWork.value.unit_id !== work.value.unit_id ||
    localWork.value.price !== work.value.price ||
    localWork.value.labor_rate !== work.value.labor_rate ||
    localWork.value.parent_id !== work.value.parent_id ||
    localWork.value.is_group !== work.value.is_group
  )
}

async function handleAddCostItem(costItem: CostItem) {
  error.value = null
  
  try {
    const success = await addCostItem(costItem.id)
    if (success) {
      toast.success('Cost item added successfully')
    } else {
      const errorMsg = 'Failed to add cost item'
      error.value = errorMsg
      toast.error(errorMsg)
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to add cost item'
    error.value = errorMsg
    toast.error(errorMsg)
    console.error('Error adding cost item:', err)
  }
}

async function handleDeleteCostItem(costItemId: number) {
  error.value = null
  
  try {
    const success = await removeCostItem(costItemId)
    if (success) {
      toast.success('Cost item removed successfully')
    } else {
      const errorMsg = 'Failed to remove cost item'
      error.value = errorMsg
      toast.error(errorMsg)
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to remove cost item'
    error.value = errorMsg
    toast.error(errorMsg)
    console.error('Error removing cost item:', err)
  }
}

async function handleAddMaterial(data: { costItemId: number; materialId: number; quantity: number }) {
  error.value = null
  
  try {
    const success = await addMaterial(data.costItemId, data.materialId, data.quantity)
    if (success) {
      toast.success('Material added successfully')
    } else {
      const errorMsg = 'Failed to add material'
      error.value = errorMsg
      toast.error(errorMsg)
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to add material'
    error.value = errorMsg
    toast.error(errorMsg)
    console.error('Error adding material:', err)
  }
}

async function handleUpdateQuantity(data: { id: number; quantity: number }) {
  error.value = null
  
  try {
    const success = await updateMaterialQuantity(data.id, data.quantity)
    if (success) {
      toast.success('Quantity updated successfully')
    } else {
      const errorMsg = 'Failed to update quantity'
      error.value = errorMsg
      toast.error(errorMsg)
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to update quantity'
    error.value = errorMsg
    toast.error(errorMsg)
    console.error('Error updating quantity:', err)
  }
}

async function handleChangeCostItem(data: { id: number; newCostItemId: number }) {
  error.value = null
  
  try {
    const success = await changeMaterialCostItem(data.id, data.newCostItemId)
    if (success) {
      toast.success('Cost item changed successfully')
    } else {
      const errorMsg = 'Failed to change cost item'
      error.value = errorMsg
      toast.error(errorMsg)
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to change cost item'
    error.value = errorMsg
    toast.error(errorMsg)
    console.error('Error changing cost item:', err)
  }
}

async function handleDeleteMaterial(id: number) {
  error.value = null
  
  try {
    const success = await removeMaterial(id)
    if (success) {
      toast.success('Material removed successfully')
    } else {
      const errorMsg = 'Failed to remove material'
      error.value = errorMsg
      toast.error(errorMsg)
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to remove material'
    error.value = errorMsg
    toast.error(errorMsg)
    console.error('Error removing material:', err)
  }
}

function showSuccessMessage(message: string) {
  toast.success(message)
}

async function loadReferenceData() {
  loadingReferenceData.value = true
  try {
    // Load units with caching
    units.value = await referenceCache.units.getOrFetch('all', async () => {
      return await unitsApi.getAll()
    })
    
    // Load works for parent selection with caching
    works.value = await referenceCache.works.getOrFetch('all', async () => {
      const response = await getWorks()
      return response.data || []
    })
  } catch (err) {
    console.error('Error loading reference data:', err)
    const errorMsg = 'Failed to load reference data'
    error.value = errorMsg
    toast.error(errorMsg)
  } finally {
    loadingReferenceData.value = false
  }
}

// Lifecycle
onMounted(async () => {
  try {
    // Load reference data
    await loadReferenceData()
    
    // Load work composition
    await loadWork()
  } catch (err) {
    console.error('Error initializing form:', err)
    const errorMsg = 'Failed to initialize form'
    error.value = errorMsg
    toast.error(errorMsg)
  }
})
</script>

<style scoped>
.work-form {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  position: relative;
}

/* Loading State */
.loading-overlay {
  padding: 2rem;
  min-height: 400px;
}

.mt-4 {
  margin-top: 2rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.spinner-small {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid #ffffff;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error Banner */
.error-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background-color: #f8d7da;
  border: 1px solid #f5c2c7;
  border-radius: 0.5rem;
  color: #842029;
  margin-bottom: 2rem;
}

.error-icon {
  font-size: 1.5rem;
}

.error-message {
  flex: 1;
  font-weight: 500;
}

.close-error {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #842029;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-error:hover {
  opacity: 0.7;
}

/* Form Content */
.form-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Total Cost Section */
.total-cost-section {
  display: flex;
  justify-content: flex-end;
}

.total-cost-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 0.5rem;
  padding: 1.5rem 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  min-width: 350px;
}

.total-cost-label {
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.9;
  margin-bottom: 0.5rem;
}

.total-cost-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.total-cost-breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
}

.breakdown-label {
  opacity: 0.9;
}

.breakdown-value {
  font-weight: 600;
}

/* Form Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 2rem;
  border-top: 2px solid #e9ecef;
}

/* Button Styles */
.btn {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  font-weight: 500;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-width: 120px;
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
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  transform: translateY(-1px);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
  box-shadow: 0 4px 8px rgba(108, 117, 125, 0.3);
  transform: translateY(-1px);
}

.btn-secondary:active:not(:disabled) {
  transform: translateY(0);
}

/* Responsive Design */
@media (max-width: 768px) {
  .work-form {
    padding: 1rem;
  }
  
  .total-cost-card {
    min-width: 100%;
  }
  
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
