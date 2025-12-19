<template>
  <div class="calculation-engine-demo">
    <div class="demo-header">
      <h1>Automatic Calculation Engine Demo</h1>
      <p>This demo shows the automatic calculation capabilities for table parts.</p>
    </div>

    <div class="demo-controls">
      <button 
        v-for="demo in demos" 
        :key="demo.id"
        class="demo-button"
        :class="{ active: activeDemo === demo.id }"
        @click="runDemo(demo.id)"
      >
        {{ demo.name }}
      </button>
    </div>

    <div class="demo-results">
      <h3>Results:</h3>
      <pre class="results-display">{{ results }}</pre>
    </div>

    <!-- Performance Monitor -->
    <CalculationPerformanceMonitor
      v-if="showPerformanceMonitor"
      :metrics="calculationMetrics"
      @status-changed="onPerformanceStatusChanged"
      @threshold-exceeded="onThresholdExceeded"
    />

    <div class="demo-controls">
      <button 
        class="toggle-button"
        @click="showPerformanceMonitor = !showPerformanceMonitor"
      >
        {{ showPerformanceMonitor ? 'Hide' : 'Show' }} Performance Monitor
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  useCalculationEngine, 
  CalculationType,
  createQuantityPriceRule,
  createSumTotalRule,
  type CalculationRule,
  type TotalCalculationRule
} from '../services/tablePartCalculationEngine'
import CalculationPerformanceMonitor from '../components/common/CalculationPerformanceMonitor.vue'

// State
const activeDemo = ref<string | null>(null)
const results = ref('Click a demo button to see results...')
const showPerformanceMonitor = ref(false)

// Calculation engine
const { 
  engine: calculationEngine, 
  metrics: calculationMetrics, 
  initializeEngine, 
  calculateField, 
  calculateTotals 
} = useCalculationEngine()

// Demo configuration
const demos = [
  { id: 'basic', name: 'Demo 1: Basic Quantity × Price' },
  { id: 'totals', name: 'Demo 2: Document Totals' },
  { id: 'custom', name: 'Demo 3: Custom Rules' },
  { id: 'performance', name: 'Demo 4: Performance Monitoring' },
  { id: 'errors', name: 'Demo 5: Error Handling' }
]

// Demo functions
async function runDemo(demoId: string) {
  activeDemo.value = demoId
  
  switch (demoId) {
    case 'basic':
      await demoBasicCalculation()
      break
    case 'totals':
      await demoTotalsCalculation()
      break
    case 'custom':
      await demoCustomCalculation()
      break
    case 'performance':
      await demoPerformanceMonitoring()
      break
    case 'errors':
      await demoErrorHandling()
      break
  }
}

async function demoBasicCalculation() {
  results.value = 'Demo 1: Basic Quantity × Price Calculation\n\n'
  
  const testCases = [
    { quantity: 10, price: 25.50, sum: 0 },
    { quantity: 5, price: 12.75, sum: 0 },
    { quantity: 20, price: 8.00, sum: 0 }
  ]
  
  let resultsText = 'Demo 1: Basic Quantity × Price Calculation\n\n'
  
  for (let i = 0; i < testCases.length; i++) {
    const rowData = { ...testCases[i] }
    const originalData = { ...rowData }
    
    try {
      const result = await calculateField(rowData, 'quantity')
      
      resultsText += `Test Case ${i + 1}:\n`
      resultsText += `  Input: Quantity=${originalData.quantity}, Price=${originalData.price}\n`
      resultsText += `  Result: Sum=${rowData.sum}\n`
      resultsText += `  Success: ${result.success}\n`
      resultsText += `  Execution Time: ${result.executionTimeMs.toFixed(2)}ms\n\n`
    } catch (error) {
      resultsText += `Test Case ${i + 1}: Error - ${error}\n\n`
    }
  }
  
  results.value = resultsText
}

async function demoTotalsCalculation() {
  const allData = [
    { quantity: 10, price: 5.00, sum: 50.00 },
    { quantity: 20, price: 3.50, sum: 70.00 },
    { quantity: 5, price: 8.00, sum: 40.00 },
    { quantity: 15, price: 6.00, sum: 90.00 }
  ]
  
  try {
    const totals = await calculateTotals(allData)
    
    let resultsText = 'Demo 2: Document Totals Calculation\n\n'
    resultsText += 'Input Data:\n'
    
    allData.forEach((row, i) => {
      resultsText += `  Row ${i + 1}: Qty=${row.quantity}, Price=${row.price}, Sum=${row.sum}\n`
    })
    
    resultsText += '\nCalculated Totals:\n'
    Object.entries(totals).forEach(([column, totalInfo]) => {
      resultsText += `  ${column}: ${totalInfo.formatted} (Rule: ${totalInfo.ruleId})\n`
    })
    
    results.value = resultsText
  } catch (error) {
    results.value = `Demo 2 Error: ${error}`
  }
}

async function demoCustomCalculation() {
  // Add custom discount rule
  if (calculationEngine.value) {
    const discountRule: CalculationRule = {
      id: 'discount_calculation',
      name: '10% Discount Calculation',
      sourceColumns: ['sum'],
      targetColumn: 'discounted_sum',
      calculationType: CalculationType.CUSTOM,
      customFunction: (rowData) => {
        const sum = parseFloat(rowData.sum) || 0
        return sum * 0.9
      },
      triggerOnChange: true,
      precision: 2,
      enabled: true
    }
    
    calculationEngine.value.addCalculationRule(discountRule)
    
    const discountTotal: TotalCalculationRule = {
      column: 'discounted_sum',
      calculationType: CalculationType.SUM,
      precision: 2,
      enabled: true
    }
    
    calculationEngine.value.addTotalRule('discount_total', discountTotal)
  }
  
  const rowData = { quantity: 10, price: 15.00, sum: 0, discounted_sum: 0 }
  
  let resultsText = 'Demo 3: Custom Calculation Rules\n\n'
  resultsText += `Input: Quantity=${rowData.quantity}, Price=${rowData.price}\n\n`
  
  try {
    // Calculate sum first
    const result1 = await calculateField(rowData, 'quantity')
    resultsText += `Step 1 - Calculate Sum:\n`
    resultsText += `  Sum = ${rowData.sum}\n`
    resultsText += `  Execution Time: ${result1.executionTimeMs.toFixed(2)}ms\n\n`
    
    // Calculate discount
    const result2 = await calculateField(rowData, 'sum')
    resultsText += `Step 2 - Calculate 10% Discount:\n`
    resultsText += `  Discounted Sum = ${rowData.discounted_sum}\n`
    resultsText += `  Execution Time: ${result2.executionTimeMs.toFixed(2)}ms\n\n`
    
    // Calculate totals
    const totals = await calculateTotals([rowData])
    resultsText += 'Totals with Custom Rules:\n'
    Object.entries(totals).forEach(([column, totalInfo]) => {
      resultsText += `  ${column}: ${totalInfo.formatted}\n`
    })
    
    results.value = resultsText
  } catch (error) {
    results.value = `Demo 3 Error: ${error}`
  }
}

async function demoPerformanceMonitoring() {
  let resultsText = 'Demo 4: Performance Monitoring\n\n'
  
  // Generate test data
  const testData = Array.from({ length: 10 }, (_, i) => ({
    quantity: i + 1,
    price: (i + 1) * 2.5,
    sum: 0
  }))
  
  resultsText += 'Performing 10 calculations...\n\n'
  
  try {
    // Perform calculations
    for (const rowData of testData) {
      await calculateField(rowData, 'quantity')
    }
    
    // Show metrics
    const metrics = calculationMetrics.value
    resultsText += 'Performance Metrics:\n'
    resultsText += `  Individual Calculation Time: ${metrics.individualCalculationTimeMs.toFixed(2)}ms\n`
    resultsText += `  Total Calculation Time: ${metrics.totalCalculationTimeMs.toFixed(2)}ms\n`
    resultsText += `  Calculations Per Second: ${metrics.calculationsPerSecond.toFixed(2)}\n`
    resultsText += `  Error Count: ${metrics.errorCount}\n`
    resultsText += `  Memory Usage: ${metrics.memoryUsageMb.toFixed(2)}MB\n\n`
    
    resultsText += 'Performance monitoring is active. Check the performance monitor below for real-time data.'
    
    // Show performance monitor
    showPerformanceMonitor.value = true
    
    results.value = resultsText
  } catch (error) {
    results.value = `Demo 4 Error: ${error}`
  }
}

async function demoErrorHandling() {
  let resultsText = 'Demo 5: Error Handling\n\n'
  
  const errorCases = [
    { data: { quantity: 'invalid', price: 10.00, sum: 0 }, description: 'Invalid quantity' },
    { data: { quantity: null, price: 15.00, sum: 0 }, description: 'Null quantity' },
    { data: { quantity: 5, price: 'not_a_number', sum: 0 }, description: 'Invalid price' },
    { data: { quantity: '', price: 20.00, sum: 0 }, description: 'Empty quantity' }
  ]
  
  for (let i = 0; i < errorCases.length; i++) {
    const { data, description } = errorCases[i]
    
    try {
      const result = await calculateField(data, 'quantity')
      
      resultsText += `Error Test ${i + 1} - ${description}:\n`
      resultsText += `  Input: Quantity=${data.quantity}, Price=${data.price}\n`
      resultsText += `  Success: ${result.success}\n`
      resultsText += `  Result: Sum=${data.sum}\n`
      resultsText += `  Execution Time: ${result.executionTimeMs.toFixed(2)}ms\n\n`
    } catch (error) {
      resultsText += `Error Test ${i + 1} - ${description}:\n`
      resultsText += `  Input: Quantity=${data.quantity}, Price=${data.price}\n`
      resultsText += `  Success: false\n`
      resultsText += `  Error: ${error}\n\n`
    }
  }
  
  results.value = resultsText
}

function onPerformanceStatusChanged(status: string) {
  console.log(`Performance status changed to: ${status}`)
}

function onThresholdExceeded(metricName: string, value: number) {
  console.warn(`Performance threshold exceeded - ${metricName}: ${value}`)
}

// Lifecycle
onMounted(() => {
  initializeEngine()
})
</script>

<style scoped>
.calculation-engine-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.demo-header {
  text-align: center;
  margin-bottom: 2rem;
}

.demo-header h1 {
  color: #333;
  margin-bottom: 0.5rem;
}

.demo-header p {
  color: #666;
  font-size: 1.1rem;
}

.demo-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.demo-button {
  padding: 0.75rem 1.5rem;
  border: 2px solid #007bff;
  background: white;
  color: #007bff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.demo-button:hover {
  background: #007bff;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.demo-button.active {
  background: #007bff;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

.toggle-button {
  padding: 0.5rem 1rem;
  border: 1px solid #6c757d;
  background: white;
  color: #6c757d;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.toggle-button:hover {
  background: #6c757d;
  color: white;
}

.demo-results {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.demo-results h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.2rem;
}

.results-display {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .calculation-engine-demo {
    padding: 1rem;
  }
  
  .demo-controls {
    flex-direction: column;
    align-items: center;
  }
  
  .demo-button {
    width: 100%;
    max-width: 300px;
  }
}
</style>