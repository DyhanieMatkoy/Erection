<template>
  <AppLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">
            {{ isNew ? 'Новый ежедневный отчет' : `Отчет от ${formatDate(formData.date)}` }}
          </h2>
          <p class="mt-1 text-sm text-gray-600">
            {{ isNew ? 'Создание нового отчета' : 'Редактирование отчета' }}
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <span
            v-if="formData.is_posted"
            class="px-3 py-1 text-sm font-semibold rounded-full bg-green-100 text-green-800"
          >
            Проведен
          </span>
          <button
            @click="handleBack"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Назад
          </button>
        </div>
      </div>

      <!-- Form -->
      <div class="bg-white shadow rounded-lg p-6 space-y-6">
        <!-- Header fields -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormField
            v-model="formData.date"
            label="Дата"
            type="date"
            required
            :disabled="formData.is_posted"
            :error="errors.date"
          />

          <Picker
            v-model="formData.estimate_id"
            label="Смета"
            :items="estimates"
            required
            :disabled="formData.is_posted"
            :error="errors.estimate_id"
            @update:model-value="handleEstimateChange"
          />

          <Picker
            v-model="formData.foreman_id"
            label="Бригадир"
            :items="persons"
            display-key="full_name"
            required
            :disabled="formData.is_posted"
            :error="errors.foreman_id"
          />
        </div>
      </div>

      <!-- Lines -->
      <DailyReportLines
        v-model="formData.lines!"
        :persons="persons"
        :disabled="formData.is_posted"
      />

      <!-- Actions -->
      <div class="flex justify-between items-center">
        <div v-if="submitError" class="text-sm text-red-600">{{ submitError }}</div>
        <div class="flex space-x-3 ml-auto">
          <button
            v-if="!isNew"
            @click="printDialogOpen = true"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Печать
          </button>
          <button
            v-if="!isNew && isAdmin && !formData.is_posted"
            @click="handlePost"
            :disabled="submitting"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
          >
            Провести
          </button>
          <button
            v-if="!isNew && isAdmin && formData.is_posted"
            @click="handleUnpost"
            :disabled="submitting"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50"
          >
            Отменить проведение
          </button>
          <button
            v-if="!formData.is_posted"
            @click="handleSave"
            :disabled="submitting"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {{ submitting ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Print Dialog -->
    <PrintDialog
      :open="printDialogOpen"
      document-type="daily-report"
      :document-id="formData.id!"
      :document-name="`Отчет_${formatDate(formData.date)}`"
      @close="printDialogOpen = false"
      @print="handlePrint"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useReferencesStore } from '@/stores/references'
import { useAuth } from '@/composables/useAuth'
import { usePrint } from '@/composables/usePrint'
import * as documentsApi from '@/api/documents'
import type { DailyReport, DailyReportLine, Estimate } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import FormField from '@/components/common/FormField.vue'
import Picker from '@/components/common/Picker.vue'
import DailyReportLines from '@/components/documents/DailyReportLines.vue'
import PrintDialog from '@/components/documents/PrintDialog.vue'

const router = useRouter()
const route = useRoute()
const referencesStore = useReferencesStore()
const { isAdmin } = useAuth()
const { printDailyReport } = usePrint()

const isNew = computed(() => route.params.id === 'new')
const printDialogOpen = ref(false)

const formData = ref<DailyReport>({
  date: new Date().toISOString().split('T')[0]!,
  estimate_id: 0,
  foreman_id: 0,
  is_posted: false,
  posted_at: null,
  is_deleted: false,
  lines: [],
})

const errors = ref<Record<string, string>>({})
const submitError = ref('')
const submitting = ref(false)
const estimatesData = ref<Estimate[]>([])

const estimates = computed(() =>
  estimatesData.value.map((e) => ({
    id: e.id!,
    name: `${e.number} от ${formatDate(e.date)} (${e.object_name})`,
  }))
)

const persons = computed(() => referencesStore.persons.filter((p) => !p.is_deleted))

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

async function handleEstimateChange() {
  if (!formData.value.estimate_id) return

  try {
    const estimate = await documentsApi.getEstimate(formData.value.estimate_id)
    
    // Auto-fill lines from estimate
    formData.value.lines = (estimate.lines || [])
      .filter((line) => !line.is_group)
      .map((line, index) => {
        // Convert to number, handling non-numeric values
        const plannedLabor = parseFloat(String(line.labor)) || 0
        return {
          line_number: index + 1,
          estimate_line_id: line.id!,
          work_id: line.work_id || undefined,
          work_name: line.work_name,
          planned_labor: plannedLabor,
          actual_labor: 0,
          deviation: plannedLabor > 0 ? -100 : 0, // -100% deviation when actual is 0
          executors: [],
        }
      })
  } catch (error) {
    console.error('Failed to load estimate:', error)
  }
}

async function loadData() {
  if (isNew.value) return

  try {
    const report = await documentsApi.getDailyReport(Number(route.params.id))
    
    // Recalculate deviations for each line to ensure correct display
    if (report.lines) {
      report.lines = report.lines.map((line) => {
        const planned = parseFloat(String(line.planned_labor)) || 0
        const actual = parseFloat(String(line.actual_labor)) || 0
        
        let deviation = 0
        if (planned > 0) {
          deviation = ((actual - planned) / planned) * 100
        }
        
        return {
          ...line,
          deviation: deviation,
        }
      })
    }
    
    formData.value = report
  } catch (error) {
    console.error('Failed to load daily report:', error)
    alert('Ошибка загрузки отчета')
    router.push('/documents/daily-reports')
  }
}

async function handleSave() {
  // Validate
  errors.value = {}
  if (!formData.value.date) errors.value.date = 'Обязательное поле'
  if (!formData.value.estimate_id) errors.value.estimate_id = 'Обязательное поле'
  if (!formData.value.foreman_id) errors.value.foreman_id = 'Обязательное поле'

  if (Object.keys(errors.value).length > 0) return

  submitting.value = true
  submitError.value = ''

  try {
    if (isNew.value) {
      const created = await documentsApi.createDailyReport(formData.value)
      router.push(`/documents/daily-reports/${created.id}`)
    } else {
      await documentsApi.updateDailyReport(formData.value.id!, formData.value)
      await loadData()
    }
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    submitError.value = apiError.response?.data?.detail || 'Ошибка при сохранении'
  } finally {
    submitting.value = false
  }
}

async function handlePost() {
  if (!confirm('Провести отчет?')) return

  submitting.value = true
  try {
    await documentsApi.postDailyReport(formData.value.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при проведении')
  } finally {
    submitting.value = false
  }
}

async function handleUnpost() {
  if (!confirm('Отменить проведение отчета?')) return

  submitting.value = true
  try {
    await documentsApi.unpostDailyReport(formData.value.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при отмене проведения')
  } finally {
    submitting.value = false
  }
}

function handleBack() {
  router.push('/documents/daily-reports')
}

async function handlePrint(format: 'pdf' | 'excel', action: 'download' | 'open') {
  try {
    await printDailyReport(
      formData.value.id!,
      format,
      action,
      `Отчет_${formatDate(formData.value.date)}`
    )
    printDialogOpen.value = false
  } catch (error) {
    console.error('Print failed:', error)
  }
}

onMounted(async () => {
  // Load references
  await referencesStore.fetchPersons()

  // Load estimates with pagination
  try {
    const allEstimates = []
    let page = 1
    let hasMore = true
    
    while (hasMore) {
      const response = await documentsApi.getEstimates({ page, page_size: 100 })
      allEstimates.push(...response.data)
      hasMore = !!(response.pagination && page < response.pagination.total_pages)
      page++
    }
    
    estimatesData.value = allEstimates
    console.log(`Loaded ${estimatesData.value.length} estimates`)
  } catch (error) {
    console.error('Failed to load estimates:', error)
  }

  // Load report if editing
  await loadData()
})
</script>
