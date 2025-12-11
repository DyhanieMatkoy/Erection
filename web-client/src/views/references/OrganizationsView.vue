<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Организации</h2>
        <p class="mt-1 text-sm text-gray-600">Управление справочником организаций</p>
      </div>

      <DataTable
        :columns="columns"
        :data="view.table.data.value"
        :loading="view.table.loading.value"
        :pagination="view.table.pagination.value"
        @row-click="view.handleEdit"
        @page-change="view.handlePageChange"
        @search="view.handleSearch"
        @sort="view.handleSort"
      >
        <template #header-actions>
          <button
            @click="view.handleCreate"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Создать
          </button>
        </template>

        <template #cell-is_deleted="{ value }">
          <span
            :class="[
              'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
              value ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
            ]"
          >
            {{ value ? 'Удален' : 'Активен' }}
          </span>
        </template>

        <template #actions="{ row }">
          <button @click.stop="view.handleEdit(row)" class="text-blue-600 hover:text-blue-900 mr-4">
            Изменить
          </button>
          <button @click.stop="view.handleDelete(row)" class="text-red-600 hover:text-red-900">
            Удалить
          </button>
        </template>
      </DataTable>

      <Modal
        :open="view.modalOpen.value"
        :title="view.editingItem.value ? 'Редактирование организации' : 'Создание организации'"
        size="md"
        @close="view.handleCloseModal"
      >
        <form @submit.prevent="view.handleSubmit" class="space-y-4">
          <FormField
            v-model="view.formData.value.name"
            label="Наименование"
            type="text"
            required
            :error="view.errors.value.name"
          />

          <div v-if="view.submitError.value" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ view.submitError.value }}</p>
          </div>
        </form>

        <template #footer>
          <button
            @click="view.handleCloseModal"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
          >
            Отмена
          </button>
          <button
            @click="view.handleSubmit"
            type="button"
            :disabled="view.submitting.value"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
          >
            {{ view.submitting.value ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </template>
      </Modal>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useReferenceView } from '@/composables/useReferenceView'
import { useReferencesStore } from '@/stores/references'
import * as referencesApi from '@/api/references'
import type { Organization } from '@/types/models'
import AppLayout from '@/components/layout/AppLayout.vue'
import DataTable from '@/components/common/DataTable.vue'
import Modal from '@/components/common/Modal.vue'
import FormField from '@/components/common/FormField.vue'

const referencesStore = useReferencesStore()

const view = useReferenceView<Organization>(
  {
    getAll: referencesApi.getOrganizations,
    create: referencesApi.createOrganization,
    update: referencesApi.updateOrganization,
    delete: referencesApi.deleteOrganization,
  },
  () => referencesStore.fetchOrganizations(true)
)

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Наименование' },
  { key: 'is_deleted', label: 'Статус' },
]

onMounted(() => {
  view.loadData()
})
</script>
