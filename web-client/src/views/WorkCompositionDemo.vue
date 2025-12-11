<template>
  <div class="work-composition-demo">
    <div class="page-header">
      <h1>Work Composition Demo</h1>
      <p class="subtitle">Manage cost items and materials for construction works</p>
    </div>

    <div class="demo-controls">
      <label for="work-select">Select Work:</label>
      <select id="work-select" v-model="selectedWorkId" class="work-select">
        <option :value="null">-- Select a work --</option>
        <option value="6">Кладка кирпича (ID: 6)</option>
        <option value="7">Штукатурка стен (ID: 7)</option>
        <option value="8">Покраска стен (ID: 8)</option>
        <option value="9">Монтаж окон (ID: 9)</option>
      </select>
    </div>

    <div v-if="selectedWorkId" class="composition-container">
      <WorkCompositionPanel :work-id="parseInt(selectedWorkId)" :key="selectedWorkId" />
    </div>

    <div v-else class="empty-state">
      <p>Please select a work from the dropdown above to view and manage its composition.</p>
    </div>

    <div class="info-panel">
      <h3>About This Feature</h3>
      <p>
        This demo showcases the Work Composition feature which allows you to:
      </p>
      <ul>
        <li><strong>Add Cost Items:</strong> Define labor, equipment, and overhead costs for each work type</li>
        <li><strong>Add Materials:</strong> Link materials to specific cost items with quantities</li>
        <li><strong>Edit Quantities:</strong> Double-click material quantities to edit them inline</li>
        <li><strong>Calculate Costs:</strong> Automatically calculate total work costs</li>
        <li><strong>Manage Relationships:</strong> Maintain the three-way Work → CostItem → Material relationship</li>
      </ul>
      
      <h4>Quick Tips:</h4>
      <ul>
        <li>You must add cost items before you can add materials</li>
        <li>Materials must be linked to a cost item</li>
        <li>You cannot delete a cost item that has associated materials</li>
        <li>Double-click a quantity to edit it, or click the edit button</li>
        <li><strong>Substring Search:</strong> Type any part of a code or name to filter items instantly</li>
        <li><strong>Quick Select:</strong> Press Enter to select the first matching item</li>
        <li>Matching text is highlighted in yellow for easy identification</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import WorkCompositionPanel from '@/components/common/WorkCompositionPanel.vue'

const selectedWorkId = ref<string | null>(null)
</script>

<style scoped>
.work-composition-demo {
  max-width: 1400px;
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

.demo-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.5rem;
}

.demo-controls label {
  font-weight: 600;
  color: #495057;
}

.work-select {
  flex: 1;
  max-width: 400px;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.work-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.composition-container {
  margin-bottom: 2rem;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  background-color: #f8f9fa;
  border-radius: 0.5rem;
  border: 2px dashed #dee2e6;
  margin-bottom: 2rem;
}

.empty-state p {
  margin: 0;
  font-size: 1.125rem;
  color: #6c757d;
}

.info-panel {
  padding: 1.5rem;
  background-color: #e7f3ff;
  border-left: 4px solid #007bff;
  border-radius: 0.25rem;
}

.info-panel h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.25rem;
  color: #004085;
}

.info-panel h4 {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-size: 1.125rem;
  color: #004085;
}

.info-panel p {
  margin-bottom: 0.75rem;
  color: #004085;
}

.info-panel ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
  color: #004085;
}

.info-panel li {
  margin-bottom: 0.5rem;
}

.info-panel strong {
  font-weight: 600;
}
</style>
