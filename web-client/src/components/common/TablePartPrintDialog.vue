<template>
  <div class="table-part-print-dialog">
    <!-- Print Dialog Modal -->
    <div v-if="isVisible" class="modal-overlay" @click="closeDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Печать: {{ tableName }}</h3>
          <button class="close-button" @click="closeDialog">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="print-settings-panel">
            <!-- Page Setup -->
            <div class="settings-group">
              <h4>Настройки страницы</h4>
              
              <div class="setting-row">
                <label>Ориентация:</label>
                <div class="radio-group">
                  <label>
                    <input 
                      type="radio" 
                      v-model="printConfig.orientation" 
                      value="portrait"
                      @change="updatePreview"
                    />
                    Книжная
                  </label>
                  <label>
                    <input 
                      type="radio" 
                      v-model="printConfig.orientation" 
                      value="landscape"
                      @change="updatePreview"
                    />
                    Альбомная
                  </label>
                </div>
              </div>
              
              <div class="setting-row">
                <label>Масштаб:</label>
                <input 
                  type="range" 
                  v-model="printConfig.scale" 
                  min="25" 
                  max="200" 
                  step="5"
                  @input="updatePreview"
                />
                <span>{{ printConfig.scale }}%</span>
              </div>
              
              <div class="margins-grid">
                <div class="margin-input">
                  <label>Верх (мм):</label>
                  <input 
                    type="number" 
                    v-model="printConfig.topMargin" 
                    min="0" 
                    max="50"
                    @input="updatePreview"
                  />
                </div>
                <div class="margin-input">
                  <label>Низ (мм):</label>
                  <input 
                    type="number" 
                    v-model="printConfig.bottomMargin" 
                    min="0" 
                    max="50"
                    @input="updatePreview"
                  />
                </div>
                <div class="margin-input">
                  <label>Лево (мм):</label>
                  <input 
                    type="number" 
                    v-model="printConfig.leftMargin" 
                    min="0" 
                    max="50"
                    @input="updatePreview"
                  />
                </div>
                <div class="margin-input">
                  <label>Право (мм):</label>
                  <input 
                    type="number" 
                    v-model="printConfig.rightMargin" 
                    min="0" 
                    max="50"
                    @input="updatePreview"
                  />
                </div>
              </div>
            </div>
            
            <!-- Table Options -->
            <div class="settings-group">
              <h4>Настройки таблицы</h4>
              
              <div class="checkbox-group">
                <label>
                  <input 
                    type="checkbox" 
                    v-model="printConfig.repeatHeaders"
                    @change="updatePreview"
                  />
                  Повторять заголовки на каждой странице
                </label>
                
                <label>
                  <input 
                    type="checkbox" 
                    v-model="printConfig.showGrid"
                    @change="updatePreview"
                  />
                  Показывать линии сетки
                </label>
                
                <label>
                  <input 
                    type="checkbox" 
                    v-model="printConfig.fitToWidth"
                    @change="updatePreview"
                  />
                  Подогнать по ширине страницы
                </label>
              </div>
            </div>
            
            <!-- Output Format -->
            <div class="settings-group">
              <h4>Формат вывода</h4>
              
              <div class="radio-group">
                <label>
                  <input 
                    type="radio" 
                    v-model="printConfig.format" 
                    value="print"
                  />
                  Принтер
                </label>
                <label>
                  <input 
                    type="radio" 
                    v-model="printConfig.format" 
                    value="pdf"
                  />
                  PDF файл
                </label>
              </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="button-group">
              <button 
                class="btn btn-secondary" 
                @click="updatePreview"
                :disabled="isGeneratingPreview"
              >
                {{ isGeneratingPreview ? 'Обновление...' : 'Обновить просмотр' }}
              </button>
              
              <button 
                class="btn btn-primary" 
                @click="printDocument"
                :disabled="isPrinting"
              >
                {{ isPrinting ? 'Печать...' : 'Печать' }}
              </button>
              
              <button class="btn btn-secondary" @click="closeDialog">
                Отмена
              </button>
            </div>
          </div>
          
          <!-- Print Preview -->
          <div class="print-preview-panel">
            <h4>Предварительный просмотр</h4>
            
            <div class="preview-container">
              <div 
                v-if="isGeneratingPreview" 
                class="preview-loading"
              >
                <div class="loading-spinner"></div>
                <p>Генерация просмотра...</p>
              </div>
              
              <div 
                v-else-if="previewError" 
                class="preview-error"
              >
                <p>Ошибка генерации просмотра: {{ previewError }}</p>
              </div>
              
              <div 
                v-else 
                class="preview-content"
                v-html="previewHtml"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, nextTick } from 'vue'
import { useTablePartPrint } from '@/composables/useTablePartPrint'

interface TableRow {
  [key: string]: any
}

interface PrintConfiguration {
  orientation: 'portrait' | 'landscape'
  scale: number
  topMargin: number
  bottomMargin: number
  leftMargin: number
  rightMargin: number
  repeatHeaders: boolean
  showGrid: boolean
  fitToWidth: boolean
  format: 'print' | 'pdf'
  maxRowsPerPage: number
}

interface Props {
  tableData: TableRow[]
  tableName?: string
  visible?: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'print-requested', config: PrintConfiguration): void
}

const props = withDefaults(defineProps<Props>(), {
  tableName: 'Табличная часть',
  visible: false
})

const emit = defineEmits<Emits>()

// Reactive state
const isVisible = ref(props.visible)
const isGeneratingPreview = ref(false)
const isPrinting = ref(false)
const previewHtml = ref('')
const previewError = ref('')

// Print configuration
const printConfig = reactive<PrintConfiguration>({
  orientation: 'portrait',
  scale: 100,
  topMargin: 20,
  bottomMargin: 20,
  leftMargin: 15,
  rightMargin: 15,
  repeatHeaders: true,
  showGrid: true,
  fitToWidth: false,
  format: 'print',
  maxRowsPerPage: 50
})

// Composable for print functionality
const { generatePreview, printToPrinter, printToPdf } = useTablePartPrint()

// Watch for visibility changes
watch(() => props.visible, (newValue) => {
  isVisible.value = newValue
  if (newValue) {
    updatePreview()
  }
})

// Debounced preview update
let previewUpdateTimeout: number | null = null

const updatePreview = async () => {
  if (previewUpdateTimeout) {
    clearTimeout(previewUpdateTimeout)
  }
  
  previewUpdateTimeout = setTimeout(async () => {
    await generatePreviewContent()
  }, 500)
}

const generatePreviewContent = async () => {
  if (!props.tableData || props.tableData.length === 0) {
    previewHtml.value = '<p>Нет данных для предварительного просмотра</p>'
    return
  }
  
  isGeneratingPreview.value = true
  previewError.value = ''
  
  try {
    const html = await generatePreview(props.tableData, {
      ...printConfig,
      tableName: props.tableName
    })
    
    previewHtml.value = html
  } catch (error) {
    previewError.value = error instanceof Error ? error.message : 'Неизвестная ошибка'
  } finally {
    isGeneratingPreview.value = false
  }
}

const printDocument = async () => {
  if (!props.tableData || props.tableData.length === 0) {
    alert('Нет данных для печати')
    return
  }
  
  isPrinting.value = true
  
  try {
    const config = {
      ...printConfig,
      tableName: props.tableName
    }
    
    if (printConfig.format === 'pdf') {
      await printToPdf(props.tableData, config)
    } else {
      await printToPrinter(props.tableData, config)
    }
    
    emit('print-requested', config)
    closeDialog()
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Неизвестная ошибка'
    alert(`Ошибка печати: ${message}`)
  } finally {
    isPrinting.value = false
  }
}

const closeDialog = () => {
  isVisible.value = false
  emit('close')
}

// Initialize preview on mount
onMounted(() => {
  if (isVisible.value) {
    nextTick(() => {
      updatePreview()
    })
  }
})
</script>

<style scoped>
.table-part-print-dialog {
  position: relative;
}

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
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  max-height: 800px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-button:hover {
  background-color: #e9ecef;
}

.modal-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.print-settings-panel {
  width: 300px;
  padding: 1.5rem;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  background-color: #f8f9fa;
}

.print-preview-panel {
  flex: 1;
  padding: 1.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.settings-group {
  margin-bottom: 1.5rem;
}

.settings-group h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
}

.setting-row {
  margin-bottom: 1rem;
}

.setting-row label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
  font-size: 0.875rem;
}

.radio-group {
  display: flex;
  gap: 1rem;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 0;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0;
}

.margins-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.margin-input label {
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}

.margin-input input {
  width: 100%;
  padding: 0.25rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.875rem;
}

input[type="range"] {
  width: 100%;
  margin: 0.5rem 0;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.preview-container {
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: auto;
  background-color: white;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #6c757d;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e9ecef;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.preview-error {
  padding: 2rem;
  text-align: center;
  color: #dc3545;
}

.preview-content {
  padding: 1rem;
  font-family: Arial, sans-serif;
  font-size: 12px;
  line-height: 1.4;
}

/* Print preview styles */
.preview-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  border: 1px solid #ddd;
  padding: 4px 8px;
  text-align: left;
}

.preview-content :deep(th) {
  background-color: #f8f9fa;
  font-weight: bold;
}

.preview-content :deep(.table-title) {
  font-size: 16px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 1rem;
}

.preview-content :deep(.page-break) {
  border-top: 2px dashed #ccc;
  margin: 1rem 0;
  padding-top: 1rem;
}

.preview-content :deep(.table-continued) {
  font-style: italic;
  font-size: 10px;
  color: #666;
  text-align: right;
  margin-bottom: 0.5rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-content {
    width: 95vw;
    height: 90vh;
  }
  
  .modal-body {
    flex-direction: column;
  }
  
  .print-settings-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
    max-height: 300px;
  }
  
  .margins-grid {
    grid-template-columns: 1fr;
  }
}
</style>