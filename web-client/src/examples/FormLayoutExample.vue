<template>
  <div class="form-layout-example">
    <h2>Form Layout Manager Example</h2>
    <p>This example demonstrates the responsive form layout with different field types and counts.</p>

    <!-- Controls -->
    <div class="controls">
      <button @click="toggleFieldCount" class="btn btn-primary">
        {{ showAllFields ? 'Show Few Fields (< 6)' : 'Show Many Fields (≥ 6)' }}
      </button>
      <button @click="toggleDebugInfo" class="btn btn-secondary">
        {{ showDebugInfo ? 'Hide Debug Info' : 'Show Debug Info' }}
      </button>
      <button @click="addLongTextField" class="btn btn-secondary">
        Add Long Text Field
      </button>
    </div>

    <!-- Form Layout Component -->
    <ResponsiveFormLayout 
      :fields="currentFields" 
      :show-debug-info="showDebugInfo"
    />

    <!-- Field Configuration -->
    <div class="field-config">
      <h3>Field Configuration</h3>
      <div class="field-list">
        <div 
          v-for="field in currentFields" 
          :key="field.name"
          class="field-item"
          :class="{
            'field-item--long': isLongField(field),
            'field-item--short': !isLongField(field)
          }"
        >
          <span class="field-name">{{ field.name }}</span>
          <span class="field-type">{{ field.fieldType }}</span>
          <span class="field-width">{{ isLongField(field) ? 'Full Width' : 'Column' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ResponsiveFormLayout from '@/components/common/ResponsiveFormLayout.vue'
import { FormLayoutManager, FieldType, type FormField } from '@/services/formLayoutManager'

const layoutManager = new FormLayoutManager()
const showDebugInfo = ref(true)
const showAllFields = ref(true)
const longFieldCounter = ref(0)

// Define field sets
const fewFields: FormField[] = [
  {
    name: 'name',
    label: 'Name',
    fieldType: FieldType.SHORT_TEXT,
    isRequired: true,
    props: { type: 'text', placeholder: 'Enter name' }
  },
  {
    name: 'email',
    label: 'Email',
    fieldType: FieldType.SHORT_TEXT,
    isRequired: true,
    props: { type: 'email', placeholder: 'Enter email' }
  },
  {
    name: 'phone',
    label: 'Phone',
    fieldType: FieldType.SHORT_TEXT,
    props: { type: 'tel', placeholder: 'Enter phone' }
  },
  {
    name: 'birthdate',
    label: 'Birth Date',
    fieldType: FieldType.DATE,
    props: { type: 'date' }
  }
]

const manyFields: FormField[] = [
  ...fewFields,
  {
    name: 'address',
    label: 'Address',
    fieldType: FieldType.LONG_TEXT,
    isMultiline: true,
    props: { placeholder: 'Enter full address' }
  },
  {
    name: 'city',
    label: 'City',
    fieldType: FieldType.SHORT_TEXT,
    isRequired: true,
    props: { type: 'text', placeholder: 'Enter city' }
  },
  {
    name: 'state',
    label: 'State',
    fieldType: FieldType.REFERENCE,
    props: {}
  },
  {
    name: 'zipcode',
    label: 'ZIP Code',
    fieldType: FieldType.SHORT_TEXT,
    maxLength: 10,
    props: { type: 'text', placeholder: 'Enter ZIP' }
  },
  {
    name: 'salary',
    label: 'Salary',
    fieldType: FieldType.NUMERIC,
    props: { type: 'number', min: 0, step: 1000 }
  },
  {
    name: 'startDate',
    label: 'Start Date',
    fieldType: FieldType.DATE,
    isRequired: true,
    props: { type: 'date' }
  },
  {
    name: 'isActive',
    label: 'Active Employee',
    fieldType: FieldType.BOOLEAN,
    props: { type: 'checkbox' }
  }
]

// Additional long fields that can be added dynamically
const additionalLongFields = ref<FormField[]>([])

// Current fields based on toggle
const currentFields = computed(() => {
  const baseFields = showAllFields.value ? manyFields : fewFields
  return [...baseFields, ...additionalLongFields.value]
})

function toggleFieldCount() {
  showAllFields.value = !showAllFields.value
}

function toggleDebugInfo() {
  showDebugInfo.value = !showDebugInfo.value
}

function addLongTextField() {
  longFieldCounter.value++
  const newField: FormField = {
    name: `longText${longFieldCounter.value}`,
    label: `Long Text Field ${longFieldCounter.value}`,
    fieldType: FieldType.LONG_TEXT,
    isMultiline: true,
    maxLength: 500,
    props: { 
      placeholder: `Enter long text for field ${longFieldCounter.value}`,
      rows: 4
    }
  }
  additionalLongFields.value.push(newField)
}

function isLongField(field: FormField): boolean {
  return layoutManager.isLongStringField(field)
}
</script>

<style scoped>
.form-layout-example {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.form-layout-example h2 {
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.form-layout-example p {
  color: #6b7280;
  margin-bottom: 2rem;
}

.controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background-color: #2563eb;
}

.btn-secondary {
  background-color: #6b7280;
  color: white;
}

.btn-secondary:hover {
  background-color: #4b5563;
}

.field-config {
  margin-top: 2rem;
  padding: 1.5rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
}

.field-config h3 {
  margin: 0 0 1rem 0;
  color: #1f2937;
}

.field-list {
  display: grid;
  gap: 0.5rem;
}

.field-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 1rem;
  padding: 0.75rem;
  background-color: white;
  border-radius: 0.375rem;
  border-left: 4px solid #e5e7eb;
}

.field-item--long {
  border-left-color: #f59e0b;
}

.field-item--short {
  border-left-color: #10b981;
}

.field-name {
  font-weight: 500;
  color: #1f2937;
}

.field-type {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-width {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.field-item--long .field-width {
  background-color: #fef3c7;
  color: #92400e;
}

.field-item--short .field-width {
  background-color: #d1fae5;
  color: #065f46;
}

@media (max-width: 768px) {
  .form-layout-example {
    padding: 1rem;
  }
  
  .controls {
    flex-direction: column;
  }
  
  .field-item {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}
</style>