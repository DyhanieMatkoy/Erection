<template>
  <div class="performance-monitor">
    <!-- Status Header -->
    <div class="status-header">
      <div class="status-indicator" :class="statusClass">
        <div class="status-dot"></div>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div class="toggle-controls">
        <button 
          class="btn btn-sm btn-outline-secondary"
          @click="isExpanded = !isExpanded"
        >
          {{ isExpanded ? 'Свернуть' : 'Развернуть' }}
        </button>
      </div>
    </div>

    <!-- Expanded Monitoring Panel -->
    <div v-if="isExpanded" class="monitoring-panel">
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['tab-button', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.name }}
        </button>
      </div>

      <!-- Real-time Metrics Tab -->
      <div v-if="activeTab === 'realtime'" class="tab-content">
        <div class="metrics-grid">
          <!-- Individual Calculation Time -->
          <div class="metric-item">
            <label>Время расчета поля:</label>
            <div class="metric-value">
              <span class="value">{{ individualTimeMs.toFixed(1) }} мс</span>
              <div class="progress-bar">
                <div 
                  class="progress-fill individual-progress"
                  :style="{ width: `${individualTimePercentage}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Total Calculation Time -->
          <div class="metric-item">
            <label>Время расчета итогов:</label>
            <div class="metric-value">
              <span class="value">{{ totalTimeMs.toFixed(1) }} мс</span>
              <div class="progress-bar">
                <div 
                  class="progress-fill total-progress"
                  :style="{ width: `${totalTimePercentage}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Calculations per Second -->
          <div class="metric-item">
            <label>Расчетов в секунду:</label>
            <div class="metric-value">
              <span class="value">{{ calculationsPerSecond.toFixed(1) }}</span>
            </div>
          </div>

          <!-- Error Count -->
          <div class="metric-item">
            <label>Количество ошибок:</label>
            <div class="metric-value">
              <span class="value error-count" :class="{ 'has-errors': errorCount > 0 }">
                {{ errorCount }}
              </span>
            </div>
          </div>

          <!-- Memory Usage -->
          <div class="metric-item">
            <label>Использование памяти:</label>
            <div class="metric-value">
              <span class="value">{{ memoryUsageMb.toFixed(2) }} МБ</span>
            </div>
          </div>
        </div>

        <!-- Activity Indicators -->
        <div class="activity-indicators">
          <div class="indicator-group">
            <span class="indicator-label">Расчеты:</span>
            <div 
              class="activity-dot calculation-dot"
              :class="{ active: isCalculating }"
            ></div>
          </div>
          <div class="indicator-group">
            <span class="indicator-label">Ошибки:</span>
            <div 
              class="activity-dot error-dot"
              :class="{ active: hasRecentError }"
            ></div>
          </div>
        </div>
      </div>

      <!-- History Tab -->
      <div v-if="activeTab === 'history'" class="tab-content">
        <div class="history-controls">
          <button 
            class="btn btn-sm btn-secondary"
            @click="clearHistory"
          >
            Очистить историю
          </button>
          <button 
            class="btn btn-sm btn-secondary"
            @click="exportHistory"
          >
            Экспорт данных
          </button>
        </div>
        
        <div class="history-display">
          <div class="history-header">
            <span>Время</span>
            <span>Статус</span>
            <span>Длительность</span>
            <span>Ошибка</span>
          </div>
          <div class="history-items">
            <div 
              v-for="(item, index) in recentHistory" 
              :key="index"
              class="history-item"
              :class="{ error: !item.success }"
            >
              <span class="timestamp">{{ formatTimestamp(item.timestamp) }}</span>
              <span class="status">{{ item.success ? '✓' : '✗' }}</span>
              <span class="duration">{{ item.executionTimeMs.toFixed(1) }}мс</span>
              <span class="error">{{ item.error || '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Settings Tab -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <div class="settings-grid">
          <div class="settings-group">
            <h4>Пороговые значения</h4>
            
            <div class="setting-item">
              <label>Расчет поля - Отлично (мс):</label>
              <span class="setting-value">{{ thresholds.excellentIndividualMs }}</span>
            </div>
            
            <div class="setting-item">
              <label>Расчет поля - Хорошо (мс):</label>
              <span class="setting-value">{{ thresholds.goodIndividualMs }}</span>
            </div>
            
            <div class="setting-item">
              <label>Расчет поля - Предупреждение (мс):</label>
              <span class="setting-value">{{ thresholds.warningIndividualMs }}</span>
            </div>
            
            <div class="setting-item">
              <label>Расчет итогов - Отлично (мс):</label>
              <span class="setting-value">{{ thresholds.excellentTotalMs }}</span>
            </div>
            
            <div class="setting-item">
              <label>Расчет итогов - Хорошо (мс):</label>
              <span class="setting-value">{{ thresholds.goodTotalMs }}</span>
            </div>
            
            <div class="setting-item">
              <label>Расчет итогов - Предупреждение (мс):</label>
              <span class="setting-value">{{ thresholds.warningTotalMs }}</span>
            </div>
          </div>
          
          <div class="settings-group">
            <h4>Настройки мониторинга</h4>
            
            <div class="setting-item">
              <label>Размер истории:</label>
              <span class="setting-value">{{ maxHistorySize }}</span>
            </div>
            
            <div class="setting-item">
              <label>Интервал обновления:</label>
              <span class="setting-value">{{ updateIntervalMs }} мс</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { PerformanceMetrics, CalculationResult } from '../../services/tablePartCalculationEngine'

// Types
enum PerformanceStatus {
  EXCELLENT = 'excellent',
  GOOD = 'good',
  WARNING = 'warning',
  CRITICAL = 'critical'
}

interface PerformanceThresholds {
  excellentIndividualMs: number
  goodIndividualMs: number
  warningIndividualMs: number
  excellentTotalMs: number
  goodTotalMs: number
  warningTotalMs: number
  maxErrorRate: number
}

interface HistoryItem extends CalculationResult {
  timestamp: number
}

interface Tab {
  id: string
  name: string
}

// Props
interface Props {
  metrics?: PerformanceMetrics
  autoUpdate?: boolean
  updateInterval?: number
  maxHistorySize?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoUpdate: true,
  updateInterval: 1000,
  maxHistorySize: 1000
})

// Emits
interface Emits {
  (e: 'status-changed', status: PerformanceStatus): void
  (e: 'threshold-exceeded', metricName: string, value: number): void
}

const emit = defineEmits<Emits>()

// State
const isExpanded = ref(false)
const activeTab = ref('realtime')
const isCalculating = ref(false)
const hasRecentError = ref(false)

const individualTimeMs = ref(0)
const totalTimeMs = ref(0)
const calculationsPerSecond = ref(0)
const errorCount = ref(0)
const memoryUsageMb = ref(0)

const calculationHistory = ref<HistoryItem[]>([])
const currentStatus = ref<PerformanceStatus>(PerformanceStatus.EXCELLENT)

// Configuration
const thresholds = ref<PerformanceThresholds>({
  excellentIndividualMs: 50,
  goodIndividualMs: 80,
  warningIndividualMs: 100,
  excellentTotalMs: 100,
  goodTotalMs: 150,
  warningTotalMs: 200,
  maxErrorRate: 0.05
})

const updateIntervalMs = ref(props.updateInterval)
const maxHistorySize = ref(props.maxHistorySize)

// Tabs configuration
const tabs: Tab[] = [
  { id: 'realtime', name: 'Реальное время' },
  { id: 'history', name: 'История' },
  { id: 'settings', name: 'Настройки' }
]

// Timers
let updateTimer: number | null = null
let calculationIndicatorTimer: number | null = null
let errorIndicatorTimer: number | null = null

// Computed properties
const statusClass = computed(() => {
  return `status-${currentStatus.value}`
})

const statusText = computed(() => {
  const statusTexts = {
    [PerformanceStatus.EXCELLENT]: 'Отлично',
    [PerformanceStatus.GOOD]: 'Хорошо',
    [PerformanceStatus.WARNING]: 'Предупреждение',
    [PerformanceStatus.CRITICAL]: 'Критично'
  }
  return statusTexts[currentStatus.value]
})

const individualTimePercentage = computed(() => {
  return Math.min(100, (individualTimeMs.value / thresholds.value.warningIndividualMs) * 100)
})

const totalTimePercentage = computed(() => {
  return Math.min(100, (totalTimeMs.value / thresholds.value.warningTotalMs) * 100)
})

const recentHistory = computed(() => {
  return calculationHistory.value.slice(-20).reverse() // Show last 20 items, newest first
})

// Methods
function updateMetrics(metrics: PerformanceMetrics) {
  individualTimeMs.value = metrics.individualCalculationTimeMs
  totalTimeMs.value = metrics.totalCalculationTimeMs
  calculationsPerSecond.value = metrics.calculationsPerSecond
  errorCount.value = metrics.errorCount
  memoryUsageMb.value = metrics.memoryUsageMb

  // Update status
  const newStatus = calculatePerformanceStatus(metrics)
  if (newStatus !== currentStatus.value) {
    currentStatus.value = newStatus
    emit('status-changed', newStatus)
  }

  // Check thresholds
  checkThresholds(metrics)
}

function addCalculationResult(result: CalculationResult) {
  const historyItem: HistoryItem = {
    ...result,
    timestamp: Date.now()
  }

  calculationHistory.value.push(historyItem)

  // Limit history size
  if (calculationHistory.value.length > maxHistorySize.value) {
    calculationHistory.value.shift()
  }

  // Show activity indicators
  showCalculationActivity()
  
  if (!result.success) {
    showErrorActivity()
  }
}

function calculatePerformanceStatus(metrics: PerformanceMetrics): PerformanceStatus {
  const { individualCalculationTimeMs, totalCalculationTimeMs } = metrics

  // Check for critical performance issues
  if (individualCalculationTimeMs > thresholds.value.warningIndividualMs ||
      totalCalculationTimeMs > thresholds.value.warningTotalMs) {
    return PerformanceStatus.CRITICAL
  }

  // Check for warning conditions
  if (individualCalculationTimeMs > thresholds.value.goodIndividualMs ||
      totalCalculationTimeMs > thresholds.value.goodTotalMs) {
    return PerformanceStatus.WARNING
  }

  // Check for good performance
  if (individualCalculationTimeMs > thresholds.value.excellentIndividualMs ||
      totalCalculationTimeMs > thresholds.value.excellentTotalMs) {
    return PerformanceStatus.GOOD
  }

  return PerformanceStatus.EXCELLENT
}

function checkThresholds(metrics: PerformanceMetrics) {
  if (metrics.individualCalculationTimeMs > thresholds.value.warningIndividualMs) {
    emit('threshold-exceeded', 'individual_calculation_timeout', metrics.individualCalculationTimeMs)
  }

  if (metrics.totalCalculationTimeMs > thresholds.value.warningTotalMs) {
    emit('threshold-exceeded', 'total_calculation_timeout', metrics.totalCalculationTimeMs)
  }
}

function showCalculationActivity(duration = 500) {
  isCalculating.value = true
  
  if (calculationIndicatorTimer) {
    clearTimeout(calculationIndicatorTimer)
  }
  
  calculationIndicatorTimer = setTimeout(() => {
    isCalculating.value = false
  }, duration)
}

function showErrorActivity(duration = 2000) {
  hasRecentError.value = true
  
  if (errorIndicatorTimer) {
    clearTimeout(errorIndicatorTimer)
  }
  
  errorIndicatorTimer = setTimeout(() => {
    hasRecentError.value = false
  }, duration)
}

function clearHistory() {
  calculationHistory.value = []
}

function exportHistory() {
  const data = calculationHistory.value.map(item => ({
    timestamp: new Date(item.timestamp).toISOString(),
    success: item.success,
    executionTimeMs: item.executionTimeMs,
    error: item.error || '',
    ruleId: item.ruleId || ''
  }))

  const csv = [
    'Timestamp,Success,ExecutionTimeMs,Error,RuleId',
    ...data.map(row => 
      `${row.timestamp},${row.success},${row.executionTimeMs},"${row.error}","${row.ruleId}"`
    )
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `calculation-history-${new Date().toISOString().split('T')[0]}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString()
}

function startAutoUpdate() {
  if (props.autoUpdate && !updateTimer) {
    updateTimer = setInterval(() => {
      // This would typically get metrics from the calculation engine
      // For now, we'll just emit an event to request updated metrics
    }, updateIntervalMs.value)
  }
}

function stopAutoUpdate() {
  if (updateTimer) {
    clearInterval(updateTimer)
    updateTimer = null
  }
}

// Lifecycle
onMounted(() => {
  startAutoUpdate()
})

onUnmounted(() => {
  stopAutoUpdate()
  
  if (calculationIndicatorTimer) {
    clearTimeout(calculationIndicatorTimer)
  }
  
  if (errorIndicatorTimer) {
    clearTimeout(errorIndicatorTimer)
  }
})

// Expose methods for parent components
defineExpose({
  updateMetrics,
  addCalculationResult,
  showCalculationActivity,
  showErrorActivity,
  clearHistory,
  exportHistory
})
</script>

<style scoped>
.performance-monitor {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  font-size: 0.875rem;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: background-color 0.3s ease;
}

.status-excellent .status-dot {
  background-color: #4CAF50;
}

.status-good .status-dot {
  background-color: #8BC34A;
}

.status-warning .status-dot {
  background-color: #FF9800;
}

.status-critical .status-dot {
  background-color: #F44336;
}

.status-text {
  font-weight: 600;
  transition: color 0.3s ease;
}

.status-excellent .status-text {
  color: #4CAF50;
}

.status-good .status-text {
  color: #8BC34A;
}

.status-warning .status-text {
  color: #FF9800;
}

.status-critical .status-text {
  color: #F44336;
}

.monitoring-panel {
  padding: 1rem;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 1rem;
}

.tab-button {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.tab-button:hover {
  background-color: #f5f5f5;
}

.tab-button.active {
  border-bottom-color: #007bff;
  color: #007bff;
  font-weight: 600;
}

.tab-content {
  min-height: 200px;
}

.metrics-grid {
  display: grid;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #fafafa;
}

.metric-item label {
  font-weight: 500;
  color: #555;
}

.metric-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.value {
  font-weight: 600;
  min-width: 80px;
  text-align: right;
}

.value.error-count.has-errors {
  color: #F44336;
}

.progress-bar {
  width: 100px;
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
  border-radius: 4px;
}

.individual-progress {
  background-color: #4CAF50;
}

.total-progress {
  background-color: #2196F3;
}

.activity-indicators {
  display: flex;
  gap: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.indicator-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.indicator-label {
  font-weight: 500;
  color: #666;
}

.activity-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #e0e0e0;
  transition: background-color 0.3s ease;
}

.calculation-dot.active {
  background-color: #4CAF50;
}

.error-dot.active {
  background-color: #F44336;
}

.history-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.history-display {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.history-header {
  display: grid;
  grid-template-columns: 1fr 60px 80px 2fr;
  gap: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  font-weight: 600;
  border-bottom: 1px solid #e0e0e0;
}

.history-items {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  display: grid;
  grid-template-columns: 1fr 60px 80px 2fr;
  gap: 1rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #f0f0f0;
  font-family: 'Consolas', monospace;
  font-size: 0.8rem;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item.error {
  background-color: #fff5f5;
  color: #d32f2f;
}

.timestamp {
  color: #666;
}

.status {
  text-align: center;
  font-weight: bold;
}

.duration {
  text-align: right;
}

.error {
  color: #d32f2f;
  font-size: 0.75rem;
}

.settings-grid {
  display: grid;
  gap: 2rem;
}

.settings-group h4 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1rem;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item label {
  color: #555;
}

.setting-value {
  font-weight: 600;
  color: #333;
}

.btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.btn:hover {
  background-color: #f5f5f5;
}

.btn-outline-secondary {
  color: #6c757d;
  border-color: #6c757d;
}

.btn-outline-secondary:hover {
  background-color: #6c757d;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background-color: #545b62;
  border-color: #4e555b;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}
</style>