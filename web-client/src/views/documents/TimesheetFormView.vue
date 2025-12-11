<template>
  <AppLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">
            {{ isNew ? 'Новый табель' : `Табель ${formData.number}` }}
          </h2>
          <p class="mt-1 text-sm text-gray-600">
            {{ isNew ? 'Создание нового табеля' : 'Редактирование табеля' }}
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
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <FormField
            v-model="formData.number"
            label="Номер"
            required
            :disabled="formData.is_posted"
            :error="errors.number"
          />

          <FormField
            v-model="formData.date"
            label="Дата"
            type="date"
            required
            :disabled="formData.is_posted"
            :error="errors.date"
            @update:model-value="handleDateChange"
          />

          <Picker
            v-model="formData.object_id"
            label="Объект"
            :items="objects"
            required
            :disabled="formData.is_posted"
            :error="errors.object_id"
            @update:model-value="handleObjectChange"
          />

          <div>
            <Picker
              v-model="formData.estimate_id"
              label="Смета"
              :items="estimatesForPicker"
              :disabled="formData.is_posted || !formData.object_id"
              :error="errors.estimate_id"
              :placeholder="estimatePickerPlaceholder"
            />
            <p
              v-if="formData.object_id && filteredEstimates.length === 0"
              class="mt-1 text-sm text-amber-600"
            >
              ⚠️ Для выбранного объекта нет смет. Создайте смету в разделе "Документы → Сметы".
            </p>
          </div>
        </div>

        <div class="text-sm text-gray-600">
          <strong>Период:</strong> {{ formatMonthYear(formData.month_year) }}
        </div>
      </div>

      <!-- Lines -->
      <TimesheetLines
        v-if="formData.lines"
        v-model="formData.lines"
        :persons="persons"
        :month-year="formData.month_year"
        :disabled="formData.is_posted"
      />

      <!-- Actions -->
      <div class="flex justify-between items-center">
        <div>
          <button
            v-if="!isNew && !formData.is_posted && formData.object_id && formData.estimate_id"
            @click="handleAutoFill"
            :disabled="submitting"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Заполнить из ежедневных отчетов
          </button>
        </div>
        <div class="flex items-center space-x-3">
          <div v-if="submitError" class="text-sm text-red-600">{{ submitError }}</div>
          <button
            v-if="!isNew"
            @click="printDialogOpen = true"
            class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
              />
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
      v-if="formData.id"
      :open="printDialogOpen"
      document-type="timesheet"
      :document-id="formData.id"
      :document-name="`Табель_${formData.number}`"
      @close="printDialogOpen = false"
      @print="handlePrint"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useReferencesStore } from '@/stores/references'
import { useAuth } from '@/composables/useAuth'
import { usePrint } from '@/composables/usePrint'
import * as documentsApi from '@/api/documents'
import type { Timesheet, Estimate } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import FormField from '@/components/common/FormField.vue'
import Picker from '@/components/common/Picker.vue'
import TimesheetLines from '@/components/documents/TimesheetLines.vue'
import PrintDialog from '@/components/documents/PrintDialog.vue'

const router = useRouter()
const route = useRoute()
const referencesStore = useReferencesStore()
const { isAdmin } = useAuth()
const { printTimesheet } = usePrint()

const isNew = computed(() => route.params.id === 'new')
const printDialogOpen = ref(false)

const formData = ref<Timesheet>({
  number: '',
  date: new Date().toISOString().split('T')[0] || "",
  object_id: 0,
  estimate_id: 0,
  foreman_id: 0,
  month_year: new Date().toISOString().slice(0, 7), // "YYYY-MM"
  is_posted: false,
  posted_at: null,
  marked_for_deletion: false,
  lines: [],
})

const errors = ref<Record<string, string>>({})
const submitError = ref('')
const submitting = ref(false)
const estimatesData = ref<Estimate[]>([])

const objects = computed(() =>
  referencesStore.objects
    .filter((o) => !o.is_deleted)
    .map((o) => ({ id: o.id, name: o.name }))
)

const filteredEstimates = computed(() => {
  let estimates = estimatesData.value
  if (formData.value.object_id) {
    estimates = estimates.filter((e) => e.object_id === formData.value.object_id)
  }
  return estimates.map((e) => ({
    id: e.id!,
    name: `${e.number} от ${formatDate(e.date)}`,
  }))
})

const estimatesForPicker = computed(() => {
  return filteredEstimates.value
})

const estimatePickerPlaceholder = computed(() => {
  if (!formData.value.object_id) {
    return 'Сначала выберите объект'
  }
  if (filteredEstimates.value.length === 0) {
    return 'Нет смет для выбранного объекта'
  }
  return `Выберите смету (доступно: ${filteredEstimates.value.length})`
})

function getObjectName(objectId: number): string {
  const obj = referencesStore.objects.find((o) => o.id === objectId)
  return obj?.name || 'Неизвестный объект'
}

const persons = computed(() => referencesStore.persons.filter((p) => !p.is_deleted))

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

function formatMonthYear(monthYear: string): string {
  if (!monthYear) return ''
  const [year, month] = monthYear.split('-')
  const date = new Date(parseInt(year), parseInt(month) - 1)
  return date.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long' })
}

function handleDateChange() {
  // Update month_year when date changes
  if (formData.value.date) {
    formData.value.month_year = formData.value.date.slice(0, 7)
  }
}

function handleObjectChange() {
  // Reset estimate when object changes
  formData.value.estimate_id = 0
}

async function handleAutoFill() {
  if (!formData.value.object_id || !formData.value.estimate_id) {
    alert('Выберите объект и смету')
    return
  }

  if (
    formData.value.lines &&
    formData.value.lines.length > 0 &&
    !confirm('Табличная часть содержит данные. Заменить их?')
  ) {
    return
  }

  submitting.value = true
  try {
    const result = await documentsApi.autofillTimesheet(
      formData.value.object_id,
      formData.value.estimate_id,
      formData.value.month_year
    )

    formData.value.lines = result.lines
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при автозаполнении')
  } finally {
    submitting.value = false
  }
}

async function loadData() {
  if (isNew.value) {
    // Generate number for new timesheet
    formData.value.number = `ТБ-${Date.now()}`
    return
  }

  try {
    const timesheet = await documentsApi.getTimesheet(Number(route.params.id))
    formData.value = timesheet
  } catch (error) {
    console.error('Failed to load timesheet:', error)
    alert('Ошибка загрузки табеля')
    router.push('/documents/timesheets')
  }
}

async function handleSave() {
  // Validate
  errors.value = {}
  if (!formData.value.number) errors.value.number = 'Обязательное поле'
  if (!formData.value.date) errors.value.date = 'Обязательное поле'
  if (!formData.value.object_id) errors.value.object_id = 'Обязательное поле'
  // Estimate is optional - allow saving without it

  if (Object.keys(errors.value).length > 0) return

  submitting.value = true
  submitError.value = ''

  try {
    // Prepare data - convert 0 to null for optional fields
    const dataToSave = {
      ...formData.value,
      estimate_id: formData.value.estimate_id || null,
      foreman_id: formData.value.foreman_id || null,
    }

    if (isNew.value) {
      const created = await documentsApi.createTimesheet(dataToSave)
      router.push(`/documents/timesheets/${created.id}`)
    } else {
      await documentsApi.updateTimesheet(formData.value.id!, dataToSave)
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
  if (!confirm('Провести табель?')) return

  submitting.value = true
  try {
    await documentsApi.postTimesheet(formData.value.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при проведении')
  } finally {
    submitting.value = false
  }
}

async function handleUnpost() {
  if (!confirm('Отменить проведение табеля?')) return

  submitting.value = true
  try {
    await documentsApi.unpostTimesheet(formData.value.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при отмене проведения')
  } finally {
    submitting.value = false
  }
}

function handleBack() {
  router.push('/documents/timesheets')
}

async function handlePrint(format: 'pdf' | 'excel', action: 'download' | 'open') {
  try {
    await printTimesheet(formData.value.id!, format, action, `Табель_${formData.value.number}`)
    printDialogOpen.value = false
  } catch (error) {
    console.error('Print failed:', error)
  }
}

onMounted(async () => {
  // Load references
  await referencesStore.fetchObjects()
  await referencesStore.fetchPersons()

  // Load ALL estimates with pagination
  try {
    const allEstimates = []
    let page = 1
    let hasMore = true
    
    while (hasMore) {
      const response = await documentsApi.getEstimates({ page, page_size: 100 })
      allEstimates.push(...response.data)
      
      // Check if there are more pages
      hasMore = !!(response.pagination && page < response.pagination.total_pages)
      page++
    }
    
    estimatesData.value = allEstimates.filter((e: any) => !e.marked_for_deletion)
    console.log(`Loaded ${estimatesData.value.length} estimates`)
  } catch (error) {
    console.error('Failed to load estimates:', error)
  }

  // Load timesheet if editing
  await loadData()
})
</script>
