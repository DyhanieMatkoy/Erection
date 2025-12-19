<template>
  <div :class="containerClasses">
    <!-- Two-column layout -->
    <div v-if="layoutConfig && layoutType === 'two_column'" class="form-grid">
      <!-- Left column -->
      <div class="form-column form-column--left">
        <div
          v-for="field in layoutConfig.leftColumn"
          :key="field.name"
          class="form-field"
        >
          <label :for="field.name" class="form-label">
            {{ field.label }}
            <span v-if="field.isRequired" class="required-marker">*</span>
          </label>
          <component
            :is="getFieldComponent(field)"
            :id="field.name"
            :name="field.name"
            v-bind="field.props"
            class="form-input"
          />
        </div>
      </div>

      <!-- Right column -->
      <div class="form-column form-column--right">
        <div
          v-for="field in layoutConfig.rightColumn"
          :key="field.name"
          class="form-field"
        >
          <label :for="field.name" class="form-label">
            {{ field.label }}
            <span v-if="field.isRequired" class="required-marker">*</span>
          </label>
          <component
            :is="getFieldComponent(field)"
            :id="field.name"
            :name="field.name"
            v-bind="field.props"
            class="form-input"
          />
        </div>
      </div>
    </div>

    <!-- Full-width fields (for two-column layout) or all fields (for single-column) -->
    <div class="form-full-width">
      <div
        v-for="field in fullWidthFields"
        :key="field.name"
        class="form-field form-field--full-width"
      >
        <label :for="field.name" class="form-label">
          {{ field.label }}
          <span v-if="field.isRequired" class="required-marker">*</span>
        </label>
        <component
          :is="getFieldComponent(field)"
          :id="field.name"
          :name="field.name"
          v-bind="field.props"
          class="form-input"
        />
      </div>
    </div>

    <!-- Debug info (only in development) -->
    <div v-if="showDebugInfo" class="debug-info">
      <p><strong>Layout Type:</strong> {{ layoutType }}</p>
      <p><strong>Breakpoint:</strong> {{ breakpoint }}</p>
      <p><strong>Window Size:</strong> {{ windowSize?.width }}x{{ windowSize?.height }}</p>
      <p><strong>Fields:</strong> {{ fields.length }} total</p>
      <p v-if="layoutConfig">
        <strong>Distribution:</strong> 
        Left: {{ layoutConfig.leftColumn.length }}, 
        Right: {{ layoutConfig.rightColumn.length }}, 
        Full: {{ layoutConfig.fullWidthFields.length }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'
import { useResponsiveFormLayout } from '@/services/responsiveLayoutAdapter'
import type { FormField, FieldType } from '@/services/formLayoutManager'

const props = defineProps({
  fields: {
    type: Array as PropType<FormField[]>,
    required: true
  },
  showDebugInfo: {
    type: Boolean,
    default: false
  }
})

// Use responsive layout composable
const fieldsRef = computed(() => props.fields)
const {
  layoutConfig,
  layoutType,
  windowSize,
  breakpoint,
  containerClasses
} = useResponsiveFormLayout(fieldsRef)

// Compute full-width fields based on layout type
const fullWidthFields = computed(() => {
  if (layoutType.value === 'two_column' && layoutConfig.value) {
    return layoutConfig.value.fullWidthFields
  } else {
    // Single column - all fields are full width
    return props.fields
  }
})

// Get appropriate component for field type
function getFieldComponent(field: FormField) {
  if (field.component) {
    return field.component
  }

  // Default components based on field type
  switch (field.fieldType) {
    case 'long_text':
      return 'textarea'
    case 'numeric':
      return 'input'
    case 'date':
      return 'input'
    case 'boolean':
      return 'input'
    case 'reference':
      return 'select'
    default:
      return 'input'
  }
}
</script>

<style scoped>
.form-container {
  width: 100%;
  padding: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 1rem;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-field--full-width {
  margin-bottom: 1rem;
}

.form-label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.required-marker {
  color: #ef4444;
  margin-left: 0.25rem;
}

.form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input[type="textarea"] {
  min-height: 4rem;
  resize: vertical;
}

.form-full-width {
  width: 100%;
}

/* Responsive breakpoints */
.form-container--mobile .form-grid {
  grid-template-columns: 1fr;
  gap: 1rem;
}

.form-container--tablet .form-grid {
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.form-container--desktop .form-grid {
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.form-container--wide .form-grid {
  grid-template-columns: 2fr 3fr;
  gap: 2.5rem;
}

/* Single column layout */
.form-container--single-column .form-grid {
  display: none;
}

.form-container--single-column .form-full-width {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Debug info */
.debug-info {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f3f4f6;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.debug-info p {
  margin: 0.25rem 0;
}

/* Ensure proper spacing on smaller screens */
@media (max-width: 768px) {
  .form-container {
    padding: 0.5rem;
  }
  
  .form-grid {
    grid-template-columns: 1fr !important;
    gap: 1rem !important;
  }
}
</style>