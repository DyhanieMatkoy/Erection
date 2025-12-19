<template>
  <div class="compact-reference-example">
    <h2>Compact Reference Field Examples</h2>
    
    <div class="examples-grid">
      <!-- Works Reference -->
      <div class="example-section">
        <h3>Works Reference</h3>
        <CompactReferenceField
          v-model="worksValue"
          reference-type="works"
          placeholder="Выберите работу"
          :allow-edit="true"
          :related-fields="['unit', 'price']"
          @open-reference="onOpenWorks"
          @select-reference="onSelectWorks"
          @fill-related-fields="onFillRelatedFields"
        />
        <p class="field-info">
          Selected: {{ worksValue ? `${worksValue.name} (ID: ${worksValue.id})` : 'None' }}
        </p>
      </div>
      
      <!-- Counterparty Reference -->
      <div class="example-section">
        <h3>Counterparty Reference</h3>
        <CompactReferenceField
          v-model="counterpartyValue"
          reference-type="counterparties"
          placeholder="Выберите контрагента"
          :allow-edit="true"
          @open-reference="onOpenCounterparty"
          @select-reference="onSelectCounterparty"
        />
        <p class="field-info">
          Selected: {{ counterpartyValue ? `${counterpartyValue.name} (ID: ${counterpartyValue.id})` : 'None' }}
        </p>
      </div>
      
      <!-- Object Reference -->
      <div class="example-section">
        <h3>Object Reference</h3>
        <CompactReferenceField
          v-model="objectValue"
          reference-type="objects"
          placeholder="Выберите объект"
          :allow-edit="true"
          @open-reference="onOpenObject"
          @select-reference="onSelectObject"
        />
        <p class="field-info">
          Selected: {{ objectValue ? `${objectValue.name} (ID: ${objectValue.id})` : 'None' }}
        </p>
      </div>
      
      <!-- Person Reference (Read-only) -->
      <div class="example-section">
        <h3>Person Reference (Read-only)</h3>
        <CompactReferenceField
          v-model="personValue"
          reference-type="persons"
          placeholder="Выберите сотрудника"
          :allow-edit="false"
          @select-reference="onSelectPerson"
        />
        <p class="field-info">
          Selected: {{ personValue ? `${personValue.name} (ID: ${personValue.id})` : 'None' }}
        </p>
      </div>
      
      <!-- Disabled Reference -->
      <div class="example-section">
        <h3>Disabled Reference</h3>
        <CompactReferenceField
          v-model="disabledValue"
          reference-type="units"
          placeholder="Поле отключено"
          :disabled="true"
        />
        <p class="field-info">This field is disabled</p>
      </div>
    </div>
    
    <!-- Status Display -->
    <div class="status-section">
      <h3>Status</h3>
      <div class="status-display">
        {{ statusMessage }}
      </div>
    </div>
    
    <!-- Instructions -->
    <div class="instructions">
      <h3>Instructions</h3>
      <ul>
        <li>Click the 'o' button to open the selected element (when available)</li>
        <li>Click the '▼' button to select from list</li>
        <li>Use F4 to open selector</li>
        <li>Use Enter to select from list</li>
        <li>Auto-completion will appear when typing (3+ characters)</li>
      </ul>
    </div>
    
    <!-- Test Actions -->
    <div class="test-actions">
      <h3>Test Actions</h3>
      <div class="button-group">
        <button @click="setTestValues" class="btn btn-primary">
          Set Test Values
        </button>
        <button @click="clearAllValues" class="btn btn-secondary">
          Clear All Values
        </button>
        <button @click="toggleDisabled" class="btn btn-info">
          Toggle Disabled State
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CompactReferenceField from '@/components/common/CompactReferenceField.vue'
import type { ReferenceValue } from '@/types/table-parts'

// Reactive data
const worksValue = ref<ReferenceValue | null>(null)
const counterpartyValue = ref<ReferenceValue | null>(null)
const objectValue = ref<ReferenceValue | null>(null)
const personValue = ref<ReferenceValue | null>(null)
const disabledValue = ref<ReferenceValue | null>({ id: 1, name: 'Disabled Item', code: 'DIS' })

const statusMessage = ref('Ready - Click buttons to interact with reference fields')

// Event handlers
function onOpenWorks(value: ReferenceValue) {
  statusMessage.value = `Opening works: ${value.name} (ID: ${value.id})`
  console.log('Open works:', value)
}

function onSelectWorks(referenceType: string, currentValue?: ReferenceValue | null) {
  statusMessage.value = `Selecting from works reference (current: ${currentValue?.name || 'none'})`
  console.log('Select works:', referenceType, currentValue)
  
  // Mock selection for demo
  setTimeout(() => {
    worksValue.value = {
      id: Math.floor(Math.random() * 1000) + 1,
      name: `Test Work ${Math.floor(Math.random() * 100)}`,
      code: `W${Math.floor(Math.random() * 1000)}`
    }
    statusMessage.value = `Works selected: ${worksValue.value.name}`
  }, 500)
}

function onOpenCounterparty(value: ReferenceValue) {
  statusMessage.value = `Opening counterparty: ${value.name} (ID: ${value.id})`
  console.log('Open counterparty:', value)
}

function onSelectCounterparty(referenceType: string, currentValue?: ReferenceValue | null) {
  statusMessage.value = `Selecting from counterparties reference`
  console.log('Select counterparty:', referenceType, currentValue)
  
  // Mock selection for demo
  setTimeout(() => {
    counterpartyValue.value = {
      id: Math.floor(Math.random() * 1000) + 1,
      name: `Test Counterparty ${Math.floor(Math.random() * 100)}`,
      code: `CP${Math.floor(Math.random() * 1000)}`
    }
    statusMessage.value = `Counterparty selected: ${counterpartyValue.value.name}`
  }, 500)
}

function onOpenObject(value: ReferenceValue) {
  statusMessage.value = `Opening object: ${value.name} (ID: ${value.id})`
  console.log('Open object:', value)
}

function onSelectObject(referenceType: string, currentValue?: ReferenceValue | null) {
  statusMessage.value = `Selecting from objects reference`
  console.log('Select object:', referenceType, currentValue)
  
  // Mock selection for demo
  setTimeout(() => {
    objectValue.value = {
      id: Math.floor(Math.random() * 1000) + 1,
      name: `Test Object ${Math.floor(Math.random() * 100)}`,
      code: `OBJ${Math.floor(Math.random() * 1000)}`
    }
    statusMessage.value = `Object selected: ${objectValue.value.name}`
  }, 500)
}

function onSelectPerson(referenceType: string, currentValue?: ReferenceValue | null) {
  statusMessage.value = `Selecting from persons reference`
  console.log('Select person:', referenceType, currentValue)
  
  // Mock selection for demo
  setTimeout(() => {
    personValue.value = {
      id: Math.floor(Math.random() * 1000) + 1,
      name: `Test Person ${Math.floor(Math.random() * 100)}`,
      code: `P${Math.floor(Math.random() * 1000)}`
    }
    statusMessage.value = `Person selected: ${personValue.value.name}`
  }, 500)
}

function onFillRelatedFields(referenceValue: ReferenceValue, relatedFields: string[]) {
  statusMessage.value = `Filling related fields: ${relatedFields.join(', ')} for ${referenceValue.name}`
  console.log('Fill related fields:', referenceValue, relatedFields)
}

// Test actions
function setTestValues() {
  worksValue.value = { id: 1, name: 'Test Work Item', code: 'TW001' }
  counterpartyValue.value = { id: 2, name: 'Test Counterparty', code: 'TCP001' }
  objectValue.value = { id: 3, name: 'Test Object', code: 'TO001' }
  personValue.value = { id: 4, name: 'Test Person', code: 'TP001' }
  statusMessage.value = 'Test values set for all fields'
}

function clearAllValues() {
  worksValue.value = null
  counterpartyValue.value = null
  objectValue.value = null
  personValue.value = null
  statusMessage.value = 'All values cleared'
}

function toggleDisabled() {
  // This would toggle disabled state in a real implementation
  statusMessage.value = 'Disabled state toggled (demo only)'
}
</script>

<style scoped>
.compact-reference-example {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.example-section {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
  background: #f8f9fa;
}

.example-section h3 {
  margin: 0 0 12px 0;
  color: #495057;
  font-size: 16px;
}

.field-info {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
}

.status-section {
  margin: 30px 0;
  padding: 16px;
  background: #e3f2fd;
  border-radius: 8px;
}

.status-display {
  font-family: monospace;
  background: white;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
  min-height: 20px;
}

.instructions {
  margin: 20px 0;
  padding: 16px;
  background: #fff3cd;
  border-radius: 8px;
}

.instructions ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.instructions li {
  margin: 4px 0;
}

.test-actions {
  margin: 20px 0;
  padding: 16px;
  background: #d1ecf1;
  border-radius: 8px;
}

.button-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn-info:hover {
  background: #117a8b;
}
</style>