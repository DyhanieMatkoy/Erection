<template>
  <div class="migration-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        <span class="icon">🔄</span>
        Work Unit Migration
      </h3>
      <button 
        v-if="!isExpanded"
        class="expand-btn"
        @click="isExpanded = true"
        title="Expand migration panel"
      >
        <span>📊</span>
        View Details
      </button>
      <button 
        v-else
        class="collapse-btn"
        @click="isExpanded = false"
        title="Collapse migration panel"
      >
        ✕
      </button>
    </div>

    <!-- Migration Status Summary -->
    <div class="status-summary">
      <div v-if="loading.status" class="loading-indicator">
        Loading migration status...
      </div>
      <div v-else-if="migrationStatus" class="status-grid">
        <div class="status-card">
          <div class="status-value">{{ migrationStatus.total_works }}</div>
          <div class="status-label">Total Works</div>
        </div>
        <div class="status-card success">
          <div class="status-value">{{ migrationStatus.migrated_count }}</div>
          <div class="status-label">Migrated</div>
        </div>
        <div class="status-card warning">
          <div class="status-value">{{ migrationStatus.pending_count }}</div>
          <div class="status-label">Pending</div>
        </div>
        <div class="status-card info">
          <div class="status-value">{{ migrationStatus.manual_review_count }}</div>
          <div class="status-label">Manual Review</div>
        </div>
      </div>
      
      <!-- Progress Bar -->
      <div v-if="migrationStatus" class="progress-container">
        <div class="progress-bar">
          <div 
            class="progress-fill"
            :style="{ width: `${migrationStatus.completion_percentage}%` }"
          ></div>
        </div>
        <div class="progress-text">
          {{ migrationStatus.completion_percentage.toFixed(1) }}% Complete
        </div>
      </div>
    </div>

    <!-- Expanded Panel -->
    <div v-if="isExpanded" class="expanded-content">
      <!-- Migration Controls -->
      <div class="migration-controls">
        <h4>Migration Controls</h4>
        <div class="control-row">
          <div class="control-group">
            <label for="threshold">Auto-apply threshold:</label>
            <input 
              id="threshold"
              v-model.number="migrationSettings.auto_apply_threshold"
              type="number"
              min="0"
              max="1"
              step="0.1"
              class="threshold-input"
            />
            <span class="help-text">Confidence level for automatic matching (0.0 - 1.0)</span>
          </div>
          <div class="control-group">
            <label for="batch-size">Batch size:</label>
            <input 
              id="batch-size"
              v-model.number="migrationSettings.batch_size"
              type="number"
              min="10"
              max="1000"
              class="batch-input"
            />
            <span class="help-text">Number of works to process per batch</span>
          </div>
        </div>
        <div class="action-buttons">
          <button 
            class="btn btn-primary"
            @click="startMigration"
            :disabled="loading.migration"
          >
            <span v-if="loading.migration">🔄 Processing...</span>
            <span v-else>🚀 Start Migration</span>
          </button>
          <button 
            class="btn btn-secondary"
            @click="refreshStatus"
            :disabled="loading.status"
          >
            <span v-if="loading.status">🔄</span>
            <span v-else>🔄 Refresh Status</span>
          </button>
        </div>
      </div>

      <!-- Manual Review Section -->
      <div v-if="migrationStatus && migrationStatus.manual_review_count > 0" class="manual-review">
        <h4>Manual Review Required</h4>
        <div v-if="loading.pending" class="loading-indicator">
          Loading pending migrations...
        </div>
        <div v-else-if="pendingMigrations.length > 0" class="review-list">
          <div 
            v-for="entry in pendingMigrations" 
            :key="entry.work_id"
            class="review-item"
          >
            <div class="item-info">
              <div class="work-name">{{ entry.work_name }}</div>
              <div class="legacy-unit">Legacy unit: <strong>{{ entry.legacy_unit }}</strong></div>
              <div v-if="entry.matched_unit_name" class="suggested-match">
                Suggested: <strong>{{ entry.matched_unit_name }}</strong>
                <span v-if="entry.confidence_score" class="confidence">
                  ({{ (entry.confidence_score * 100).toFixed(1) }}% confidence)
                </span>
              </div>
              <div v-if="entry.manual_review_reason" class="review-reason">
                Reason: {{ entry.manual_review_reason }}
              </div>
            </div>
            <div class="item-actions">
              <button 
                v-if="entry.matched_unit_id"
                class="btn btn-success btn-sm"
                @click="reviewMigration(entry.work_id, 'approve')"
                :disabled="loading.review"
              >
                ✓ Approve
              </button>
              <button 
                class="btn btn-warning btn-sm"
                @click="showUnitSelector(entry)"
              >
                🔧 Assign Unit
              </button>
              <button 
                class="btn btn-danger btn-sm"
                @click="reviewMigration(entry.work_id, 'reject')"
                :disabled="loading.review"
              >
                ✗ Reject
              </button>
            </div>
          </div>
        </div>
        <div v-else class="no-pending">
          No pending migrations found.
        </div>
      </div>

      <!-- Migration Log -->
      <div v-if="migrationLog.length > 0" class="migration-log">
        <h4>Migration Log</h4>
        <div class="log-entries">
          <div 
            v-for="(entry, index) in migrationLog" 
            :key="index"
            :class="['log-entry', entry.type]"
          >
            <span class="log-time">{{ formatTime(entry.timestamp) }}</span>
            <span class="log-message">{{ entry.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Unit Selector Modal -->
    <div v-if="showUnitSelectorModal" class="modal-overlay" @click="closeUnitSelector">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>Select Unit for {{ selectedEntry?.work_name }}</h4>
          <button class="modal-close" @click="closeUnitSelector">✕</button>
        </div>
        <div class="modal-body">
          <div class="unit-search">
            <input 
              v-model="unitSearchQuery"
              type="text"
              placeholder="Search units..."
              class="search-input"
            />
          </div>
          <div class="unit-list">
            <div 
              v-for="unit in filteredUnits" 
              :key="unit.id"
              class="unit-item"
              @click="selectUnit(unit.id)"
            >
              <div class="unit-name">{{ unit.name }}</div>
              <div v-if="unit.description" class="unit-description">{{ unit.description }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeUnitSelector">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, beforeUnmount, watch } from 'vue'
import { useReferencesStore } from '@/stores/references'
import * as migrationApi from '@/api/references'
import type { MigrationStatus, MigrationEntry } from '@/api/references'

interface Props {
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 30000 // 30 seconds
})

// State
const isExpanded = ref(false)
const migrationStatus = ref<MigrationStatus | null>(null)
const pendingMigrations = ref<MigrationEntry[]>([])
const migrationSettings = ref({
  auto_apply_threshold: 0.8,
  batch_size: 100
})

const loading = ref({
  status: false,
  migration: false,
  pending: false,
  review: false
})

const migrationLog = ref<Array<{
  timestamp: Date
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}>>([])

// Unit selector modal
const showUnitSelectorModal = ref(false)
const selectedEntry = ref<MigrationEntry | null>(null)
const unitSearchQuery = ref('')

// References store
const referencesStore = useReferencesStore()

// Computed
const filteredUnits = computed(() => {
  const query = unitSearchQuery.value.toLowerCase()
  return referencesStore.units.filter(unit => 
    unit.name.toLowerCase().includes(query) ||
    (unit.description && unit.description.toLowerCase().includes(query))
  )
})

// Methods
async function loadMigrationStatus() {
  loading.value.status = true
  try {
    migrationStatus.value = await migrationApi.getMigrationStatus()
    addLogEntry('Migration status updated', 'info')
  } catch (error) {
    console.error('Failed to load migration status:', error)
    addLogEntry('Failed to load migration status', 'error')
  } finally {
    loading.value.status = false
  }
}

async function loadPendingMigrations() {
  loading.value.pending = true
  try {
    pendingMigrations.value = await migrationApi.getPendingMigrations(50)
    addLogEntry(`Loaded ${pendingMigrations.value.length} pending migrations`, 'info')
  } catch (error) {
    console.error('Failed to load pending migrations:', error)
    addLogEntry('Failed to load pending migrations', 'error')
  } finally {
    loading.value.pending = false
  }
}

async function startMigration() {
  loading.value.migration = true
  try {
    const result = await migrationApi.startMigration(migrationSettings.value)
    addLogEntry(`Migration started: ${result.message}`, 'success')
    
    // Refresh status after starting migration
    setTimeout(() => {
      loadMigrationStatus()
      loadPendingMigrations()
    }, 2000)
  } catch (error) {
    console.error('Failed to start migration:', error)
    addLogEntry('Failed to start migration', 'error')
  } finally {
    loading.value.migration = false
  }
}

async function reviewMigration(workId: number, action: 'approve' | 'reject' | 'assign', unitId?: number) {
  loading.value.review = true
  try {
    const result = await migrationApi.reviewMigration({
      work_id: workId,
      action,
      unit_id: unitId
    })
    
    addLogEntry(`Migration ${action} completed for work ${workId}`, 'success')
    
    // Remove from pending list
    pendingMigrations.value = pendingMigrations.value.filter(entry => entry.work_id !== workId)
    
    // Refresh status
    loadMigrationStatus()
  } catch (error) {
    console.error('Failed to review migration:', error)
    addLogEntry(`Failed to ${action} migration for work ${workId}`, 'error')
  } finally {
    loading.value.review = false
  }
}

function showUnitSelector(entry: MigrationEntry) {
  selectedEntry.value = entry
  unitSearchQuery.value = ''
  showUnitSelectorModal.value = true
  
  // Load units if not already loaded
  if (referencesStore.units.length === 0) {
    referencesStore.fetchUnits()
  }
}

function closeUnitSelector() {
  showUnitSelectorModal.value = false
  selectedEntry.value = null
  unitSearchQuery.value = ''
}

async function selectUnit(unitId: number) {
  if (selectedEntry.value) {
    await reviewMigration(selectedEntry.value.work_id, 'assign', unitId)
    closeUnitSelector()
  }
}

function refreshStatus() {
  loadMigrationStatus()
  loadPendingMigrations()
}

function addLogEntry(message: string, type: 'info' | 'success' | 'warning' | 'error') {
  migrationLog.value.unshift({
    timestamp: new Date(),
    message,
    type
  })
  
  // Keep only last 50 entries
  if (migrationLog.value.length > 50) {
    migrationLog.value = migrationLog.value.slice(0, 50)
  }
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString()
}

// Watch for expansion to load data
watch(isExpanded, (expanded) => {
  if (expanded) {
    loadPendingMigrations()
  }
})

// Auto-refresh
let refreshTimer: NodeJS.Timeout | null = null

function startAutoRefresh() {
  if (props.autoRefresh && !refreshTimer) {
    refreshTimer = setInterval(() => {
      loadMigrationStatus()
      if (isExpanded.value) {
        loadPendingMigrations()
      }
    }, props.refreshInterval)
  }
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// Lifecycle
onMounted(() => {
  loadMigrationStatus()
  startAutoRefresh()
})

// Cleanup
beforeUnmount(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.migration-panel {
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
  border-radius: 0.5rem 0.5rem 0 0;
}

.panel-title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: #495057;
}

.icon {
  font-size: 1.25rem;
}

.expand-btn, .collapse-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #007bff;
  background: #007bff;
  color: white;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.expand-btn:hover, .collapse-btn:hover {
  background: #0056b3;
}

.status-summary {
  padding: 1rem;
}

.loading-indicator {
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.status-card {
  text-align: center;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e9ecef;
  background: #f8f9fa;
}

.status-card.success {
  background: #d4edda;
  border-color: #c3e6cb;
}

.status-card.warning {
  background: #fff3cd;
  border-color: #ffeaa7;
}

.status-card.info {
  background: #d1ecf1;
  border-color: #bee5eb;
}

.status-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #495057;
}

.status-label {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.progress-container {
  margin-top: 1rem;
}

.progress-bar {
  width: 100%;
  height: 1rem;
  background: #e9ecef;
  border-radius: 0.5rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  margin-top: 0.5rem;
  font-weight: 600;
  color: #495057;
}

.expanded-content {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
}

.migration-controls h4,
.manual-review h4,
.migration-log h4 {
  margin: 0 0 1rem 0;
  color: #495057;
  font-size: 1rem;
  font-weight: 600;
}

.control-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.control-group label {
  font-weight: 500;
  color: #495057;
  font-size: 0.875rem;
}

.threshold-input, .batch-input, .search-input {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.help-text {
  font-size: 0.75rem;
  color: #6c757d;
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  border-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-success {
  background: #28a745;
  border-color: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #1e7e34;
}

.btn-warning {
  background: #ffc107;
  border-color: #ffc107;
  color: #212529;
}

.btn-warning:hover:not(:disabled) {
  background: #e0a800;
}

.btn-danger {
  background: #dc3545;
  border-color: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.manual-review {
  margin-top: 2rem;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.review-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  background: #f8f9fa;
}

.item-info {
  flex: 1;
}

.work-name {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.25rem;
}

.legacy-unit, .suggested-match, .review-reason {
  font-size: 0.875rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.confidence {
  color: #28a745;
  font-weight: 500;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.no-pending {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 2rem;
}

.migration-log {
  margin-top: 2rem;
}

.log-entries {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
}

.log-entry {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  border-bottom: 1px solid #f8f9fa;
  font-size: 0.875rem;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-entry.success {
  background: #d4edda;
}

.log-entry.warning {
  background: #fff3cd;
}

.log-entry.error {
  background: #f8d7da;
}

.log-time {
  font-weight: 500;
  color: #6c757d;
  white-space: nowrap;
}

.log-message {
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
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h4 {
  margin: 0;
  color: #495057;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #6c757d;
}

.modal-body {
  padding: 1rem;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.unit-search {
  margin-bottom: 1rem;
}

.unit-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
}

.unit-item {
  padding: 0.75rem;
  border-bottom: 1px solid #f8f9fa;
  cursor: pointer;
  transition: background-color 0.2s;
}

.unit-item:hover {
  background: #f8f9fa;
}

.unit-item:last-child {
  border-bottom: none;
}

.unit-name {
  font-weight: 500;
  color: #495057;
}

.unit-description {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
}
</style>