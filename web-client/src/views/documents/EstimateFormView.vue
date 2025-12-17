<template>
  <AppLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">
            {{ isNew ? 'Новая смета' : `Смета ${formData.number}` }}
          </h2>
          <p class="mt-1 text-sm text-gray-600">
            {{ isNew ? 'Создание новой сметы' : 'Редактирование сметы' }}
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
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            v-model="formData.number"
            label="Номер"
            type="text"
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
          />

          <Picker
            v-model="formData.customer_id"
            label="Заказчик"
            :items="counterparties"
            required
            :disabled="formData.is_posted"
            :error="errors.customer_id"
          />

          <Picker
            v-model="formData.object_id"
            label="Объект"
            :items="objects"
            required
            :disabled="formData.is_posted"
            :error="errors.object_id"
          />

          <Picker
            v-model="formData.contractor_id"
            label="Подрядчик"
            :items="organizations"
            required
            :disabled="formData.is_posted"
            :error="errors.contractor_id"
          />

          <Picker
            v-model="formData.responsible_id"
            label="Ответственный"
            :items="persons"
            display-key="full_name"
            required
            :disabled="formData.is_posted"
            :error="errors.responsible_id"
          />
        </div>

        <!-- Totals -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <label class="block text-sm font-medium text-gray-700">Общая сумма</label>
            <div class="mt-1 text-lg font-semibold text-gray-900">
              {{ formatNumber(formData.total_sum) }}
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Общая трудоемкость</label>
            <div class="mt-1 text-lg font-semibold text-gray-900">
              {{ formatNumber(formData.total_labor) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Lines -->
      <EstimateLines
        v-model="formData.lines!"
        :works="works"
        :units="units"
        :disabled="formData.is_posted"
        @update:totals="handleTotalsUpdate"
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
      v-if="formData.id"
      :open="printDialogOpen"
      document-type="estimate"
      :document-id="formData.id"
      :document-name="`Смета_${formData.number}`"
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
import type { Estimate, EstimateLine } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import FormField from '@/components/common/FormField.vue'
import Picker from '@/components/common/Picker.vue'
import EstimateLines from '@/components/documents/EstimateLines.vue'
import PrintDialog from '@/components/documents/PrintDialog.vue'

const router = useRouter()
const route = useRoute()
const referencesStore = useReferencesStore()
const { isAdmin } = useAuth()
const { printEstimate } = usePrint()

const isNew = computed(() => route.params.id === 'new')
const printDialogOpen = ref(false)

const formData = ref<Estimate>({
  number: '',
  date: new Date().toISOString().split('T')[0] || "",
  customer_id: 0,
  object_id: 0,
  contractor_id: 0,
  responsible_id: 0,
  total_sum: 0,
  total_labor: 0,
  is_posted: false,
  posted_at: null,
  is_deleted: false,
  lines: [],
})

const errors = ref<Record<string, string>>({})
const submitError = ref('')
const submitting = ref(false)

const counterparties = computed(() =>
  referencesStore.counterparties.filter((c) => !c.is_deleted)
)
const objects = computed(() => referencesStore.objects.filter((o) => !o.is_deleted))
const organizations = computed(() => referencesStore.organizations.filter((o) => !o.is_deleted))
const persons = computed(() => referencesStore.persons.filter((p) => !p.is_deleted))
const works = computed(() => referencesStore.works.filter((w) => !w.is_deleted))
const units = computed(() => referencesStore.units.filter((u) => !u.marked_for_deletion))

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function handleTotalsUpdate(totals: { sum: number; labor: number }) {
  formData.value.total_sum = totals.sum
  formData.value.total_labor = totals.labor
}

async function loadData() {
  if (isNew.value) return

  try {
    const estimate = await documentsApi.getEstimate(Number(route.params.id))
    formData.value = estimate
  } catch (error) {
    console.error('Failed to load estimate:', error)
    alert('Ошибка загрузки сметы')
    router.push('/documents/estimates')
  }
}

async function loadFromTimesheet(timesheetId: number) {
  try {
    const timesheet = await documentsApi.getTimesheet(timesheetId)
    
    // Заполняем основные поля из ежедневного отчета
    formData.value.date = timesheet.date
    formData.value.object_id = timesheet.object_id
    
    // Если есть связанная смета, загружаем данные из нее
    if (timesheet.estimate_id) {
      try {
        const estimate = await documentsApi.getEstimate(timesheet.estimate_id)
        formData.value.customer_id = estimate.customer_id
        formData.value.contractor_id = estimate.contractor_id
        formData.value.responsible_id = estimate.responsible_id
      } catch (e) {
        console.error('Failed to load estimate:', e)
      }
    }
    
    // Генерируем номер сметы
    const today = new Date()
    const dateStr = (today.toISOString().split('T')[0] || '').replace(/-/g, '')
    formData.value.number = `СМ-${dateStr}-${Math.floor(Math.random() * 1000)}`
    
    // Копируем строки из ежедневного отчета (табеля)
    // В табеле нет строк работ, поэтому оставляем пустым
    // Пользователь должен добавить строки вручную
    formData.value.lines = []
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при загрузке ежедневного отчета')
  }
}

async function handleSave() {
  // Validate
  errors.value = {}
  if (!formData.value.number.trim()) errors.value.number = 'Обязательное поле'
  if (!formData.value.date) errors.value.date = 'Обязательное поле'
  if (!formData.value.customer_id) errors.value.customer_id = 'Обязательное поле'
  if (!formData.value.object_id) errors.value.object_id = 'Обязательное поле'
  if (!formData.value.contractor_id) errors.value.contractor_id = 'Обязательное поле'
  if (!formData.value.responsible_id) errors.value.responsible_id = 'Обязательное поле'

  if (Object.keys(errors.value).length > 0) return

  submitting.value = true
  submitError.value = ''

  try {
    if (isNew.value) {
      const created = await documentsApi.createEstimate(formData.value)
      router.push(`/documents/estimates/${created.id}`)
    } else {
      await documentsApi.updateEstimate(formData.value.id!, formData.value)
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
  if (!confirm('Провести смету?')) return

  submitting.value = true
  try {
    await documentsApi.postEstimate(formData.value.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при проведении')
  } finally {
    submitting.value = false
  }
}

async function handleUnpost() {
  if (!confirm('Отменить проведение сметы?')) return

  submitting.value = true
  try {
    await documentsApi.unpostEstimate(formData.value.id!)
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { detail?: string } } }
    alert(apiError.response?.data?.detail || 'Ошибка при отмене проведения')
  } finally {
    submitting.value = false
  }
}

function handleBack() {
  router.push('/documents/estimates')
}

async function handlePrint(format: 'pdf' | 'excel', action: 'download' | 'open') {
  try {
    await printEstimate(
      formData.value.id!,
      format,
      action,
      `Смета_${formData.value.number}`
    )
    printDialogOpen.value = false
  } catch (error) {
    console.error('Print failed:', error)
  }
}

onMounted(async () => {
  // Load references
  await Promise.all([
    referencesStore.fetchCounterparties(),
    referencesStore.fetchObjects(),
    referencesStore.fetchOrganizations(),
    referencesStore.fetchPersons(),
    referencesStore.fetchWorks(),
    referencesStore.fetchUnits(),
  ])

  // Load estimate if editing
  await loadData()
  
  // Load from timesheet if creating based on timesheet
  const timesheetId = route.query.timesheet_id
  if (isNew.value && timesheetId) {
    await loadFromTimesheet(Number(timesheetId))
  }
})
</script>
