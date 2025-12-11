# Следующие шаги - Руководство по реализации

## Текущий статус

✅ **Завершено:**
- Все 6 форм списков обновлены (100%)
- Созданы базовые компоненты (DataTable, DateRangePicker, useFilters)
- Написана полная документация (9 документов)

⏳ **Требуется:**
- Расширение API для поддержки фильтрации
- Контекстное меню
- Экспорт данных

---

## Приоритет 1: Расширение API (3 дня)

### Задача 1.1: Добавить параметры фильтрации

**Файлы для изменения:**
- `api/endpoints/documents.py`
- `api/endpoints/references.py`

**Что делать:**

1. **Estimates** - добавить параметры:
```python
@router.get("/estimates")
async def list_estimates(
    # ... существующие параметры
    customer_id: Optional[int] = None,
    is_posted: Optional[bool] = None,
    sum_from: Optional[float] = None,
    sum_to: Optional[float] = None,
    # ...
):
    # Добавить в where_clauses:
    if customer_id:
        where_clauses.append("e.customer_id = ?")
        params.append(customer_id)
    
    if is_posted is not None:
        where_clauses.append("e.is_posted = ?")
        params.append(1 if is_posted else 0)
    
    if sum_from is not None:
        where_clauses.append("e.total_sum >= ?")
        params.append(sum_from)
    
    if sum_to is not None:
        where_clauses.append("e.total_sum <= ?")
        params.append(sum_to)
```

2. **Timesheets** - добавить параметры:
```python
date_from, date_to, period_from, period_to, object_id, estimate_id, is_posted
```

3. **Counterparties** - добавить параметры:
```python
type, is_deleted
```

4. **Objects** - добавить параметры:
```python
status, customer_id, start_date_from, start_date_to, is_deleted
```

5. **Persons** - добавить параметры:
```python
position, specialty, status, is_deleted
```

6. **Works** - добавить параметры:
```python
category, unit, price_from, price_to, is_deleted
```

### Задача 1.2: Добавить колонки в ответы

**Документы:**
```python
# В SELECT добавить JOIN с users
SELECT 
    e.*,
    u.username as author
FROM estimates e
LEFT JOIN users u ON e.created_by = u.id
```

**Справочники:**
- Убедиться, что все поля из БД возвращаются в ответе
- Добавить JOIN для связанных таблиц (например, customer_name для objects)

### Задача 1.3: Массовые операции

**Добавить endpoints:**
```python
@router.post("/counterparties/bulk-delete")
async def bulk_delete_counterparties(
    ids: List[int],
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    cursor = db.cursor()
    success_count = 0
    errors = []
    
    for id in ids:
        try:
            cursor.execute(
                "UPDATE counterparties SET is_deleted = 1 WHERE id = ?",
                (id,)
            )
            success_count += 1
        except Exception as e:
            errors.append(f"ID {id}: {str(e)}")
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Удалено {success_count} из {len(ids)}",
        "errors": errors
    }
```

Создать аналогичные endpoints для: objects, persons, works

---

## Приоритет 2: Контекстное меню (1-2 дня)

### Задача 2.1: Создать компонент ContextMenu.vue

**Файл:** `web-client/src/components/common/ContextMenu.vue`

```vue
<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      ref="menuRef"
      :style="{ top: `${position.y}px`, left: `${position.x}px` }"
      class="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[160px]"
      @click.stop
    >
      <slot :close="close"></slot>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

interface Props {
  isOpen: boolean
  position: { x: number; y: number }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:isOpen': [value: boolean]
  'close': []
}>()

const menuRef = ref<HTMLElement>()

function close() {
  emit('update:isOpen', false)
  emit('close')
}

function handleClickOutside(event: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    close()
  }
}

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
```

### Задача 2.2: Создать composable useContextMenu.ts

**Файл:** `web-client/src/composables/useContextMenu.ts`

```typescript
import { ref } from 'vue'

export function useContextMenu() {
  const isOpen = ref(false)
  const position = ref({ x: 0, y: 0 })
  const targetRow = ref<any>(null)

  function open(event: MouseEvent, row: any) {
    event.preventDefault()
    
    targetRow.value = row
    position.value = {
      x: event.clientX,
      y: event.clientY
    }
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
    targetRow.value = null
  }

  return {
    isOpen,
    position,
    targetRow,
    open,
    close
  }
}
```

### Задача 2.3: Добавить в DataTable

**Обновить:** `web-client/src/components/common/DataTable.vue`

```vue
<template>
  <!-- В строке таблицы добавить -->
  <tr @contextmenu="handleContextMenu($event, row)">
    <!-- ... -->
  </tr>
  
  <!-- После таблицы -->
  <ContextMenu
    v-model:isOpen="contextMenu.isOpen.value"
    :position="contextMenu.position.value"
    @close="contextMenu.close"
  >
    <slot name="context-menu" :row="contextMenu.targetRow.value" :close="contextMenu.close"></slot>
  </ContextMenu>
</template>

<script setup lang="ts">
import { useContextMenu } from '@/composables/useContextMenu'
import ContextMenu from './ContextMenu.vue'

const contextMenu = useContextMenu()

function handleContextMenu(event: MouseEvent, row: any) {
  contextMenu.open(event, row)
  emit('context-menu', row)
}
</script>
```

### Задача 2.4: Использовать в формах

```vue
<DataTable>
  <template #context-menu="{ row, close }">
    <button @click="handleEdit(row); close()">Открыть</button>
    <button @click="handleCopy(row); close()">Копировать</button>
    <button @click="handleDelete(row); close()">Удалить</button>
    <hr />
    <button v-if="!row.is_posted" @click="handlePost(row); close()">
      Провести
    </button>
  </template>
</DataTable>
```

---

## Приоритет 3: Экспорт данных (1-2 дня)

### Задача 3.1: Создать composable useExport.ts

**Файл:** `web-client/src/composables/useExport.ts`

```typescript
export function useExport() {
  async function exportToExcel(data: any[], filename: string) {
    // Использовать библиотеку xlsx
    const XLSX = await import('xlsx')
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
    XLSX.writeFile(wb, `${filename}.xlsx`)
  }

  async function exportToCSV(data: any[], filename: string) {
    const csv = convertToCSV(data)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${filename}.csv`
    link.click()
  }

  function convertToCSV(data: any[]): string {
    if (data.length === 0) return ''
    
    const headers = Object.keys(data[0])
    const rows = data.map(row => 
      headers.map(header => JSON.stringify(row[header] ?? '')).join(',')
    )
    
    return [headers.join(','), ...rows].join('\n')
  }

  return {
    exportToExcel,
    exportToCSV
  }
}
```

### Задача 3.2: Создать компонент ExportButton.vue

**Файл:** `web-client/src/components/common/ExportButton.vue`

```vue
<template>
  <div class="relative">
    <button
      @click="toggleMenu"
      class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
    >
      <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Экспорт
    </button>
    
    <div
      v-if="showMenu"
      class="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-10"
    >
      <button
        @click="handleExport('excel')"
        class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
      >
        Excel (.xlsx)
      </button>
      <button
        @click="handleExport('csv')"
        class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
      >
        CSV (.csv)
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  'export': [format: 'excel' | 'csv']
}>()

const showMenu = ref(false)

function toggleMenu() {
  showMenu.value = !showMenu.value
}

function handleExport(format: 'excel' | 'csv') {
  emit('export', format)
  showMenu.value = false
}
</script>
```

### Задача 3.3: Добавить в формы

```vue
<template>
  <DataTable>
    <template #header-actions>
      <ExportButton @export="handleExport" />
      <button @click="handleCreate">Создать</button>
    </template>
  </DataTable>
</template>

<script setup lang="ts">
import { useExport } from '@/composables/useExport'
import ExportButton from '@/components/common/ExportButton.vue'

const { exportToExcel, exportToCSV } = useExport()

async function handleExport(format: 'excel' | 'csv') {
  // Получить все данные (без пагинации)
  const allData = await api.getAllData(filters.getQueryParams())
  
  if (format === 'excel') {
    await exportToExcel(allData, 'estimates')
  } else {
    await exportToCSV(allData, 'estimates')
  }
}
</script>
```

### Задача 3.4: Добавить API endpoint для экспорта

```python
@router.get("/estimates/export")
async def export_estimates(
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    # ... все параметры фильтрации
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    # Получить все данные без пагинации
    # Вернуть файл
    pass
```

---

## Приоритет 4: Расширенные горячие клавиши (0.5 дня)

### Задача 4.1: Создать useKeyboardShortcuts.ts

**Файл:** `web-client/src/composables/useKeyboardShortcuts.ts`

```typescript
import { onMounted, onUnmounted } from 'vue'

export interface KeyboardShortcutHandlers {
  onInsert?: () => void
  onEnter?: () => void
  onF2?: () => void
  onDelete?: () => void
  onF5?: () => void
  onCtrlF?: () => void
  onCtrlA?: () => void
  onCtrlC?: () => void
  onCtrlP?: () => void
  onEscape?: () => void
}

export function useKeyboardShortcuts(handlers: KeyboardShortcutHandlers) {
  function handleKeyDown(event: KeyboardEvent) {
    // Insert
    if (event.key === 'Insert' && handlers.onInsert) {
      event.preventDefault()
      handlers.onInsert()
    }
    // Enter
    else if (event.key === 'Enter' && handlers.onEnter) {
      event.preventDefault()
      handlers.onEnter()
    }
    // F2
    else if (event.key === 'F2' && handlers.onF2) {
      event.preventDefault()
      handlers.onF2()
    }
    // Delete
    else if (event.key === 'Delete' && handlers.onDelete) {
      event.preventDefault()
      handlers.onDelete()
    }
    // F5
    else if (event.key === 'F5' && handlers.onF5) {
      event.preventDefault()
      handlers.onF5()
    }
    // Ctrl+F
    else if (event.ctrlKey && event.key === 'f' && handlers.onCtrlF) {
      event.preventDefault()
      handlers.onCtrlF()
    }
    // Ctrl+A
    else if (event.ctrlKey && event.key === 'a' && handlers.onCtrlA) {
      const activeElement = document.activeElement
      if (activeElement?.tagName !== 'INPUT' && activeElement?.tagName !== 'TEXTAREA') {
        event.preventDefault()
        handlers.onCtrlA()
      }
    }
    // Ctrl+C
    else if (event.ctrlKey && event.key === 'c' && handlers.onCtrlC) {
      const activeElement = document.activeElement
      if (activeElement?.tagName !== 'INPUT' && activeElement?.tagName !== 'TEXTAREA') {
        event.preventDefault()
        handlers.onCtrlC()
      }
    }
    // Ctrl+P
    else if (event.ctrlKey && event.key === 'p' && handlers.onCtrlP) {
      event.preventDefault()
      handlers.onCtrlP()
    }
    // Escape
    else if (event.key === 'Escape' && handlers.onEscape) {
      handlers.onEscape()
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })
}
```

### Задача 4.2: Использовать в формах

```vue
<script setup lang="ts">
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'

useKeyboardShortcuts({
  onInsert: handleCreate,
  onEnter: () => selectedItems.value[0] && handleEdit(selectedItems.value[0]),
  onF2: () => selectedItems.value[0] && handleEdit(selectedItems.value[0]),
  onDelete: () => selectedItems.value[0] && handleDelete(selectedItems.value[0]),
  onF5: loadData,
  onCtrlF: () => tableRef.value?.focusSearch(),
  onCtrlA: () => tableRef.value?.selectAll(),
  onCtrlC: () => selectedItems.value[0] && handleCopy(selectedItems.value[0]),
  onEscape: () => tableRef.value?.clearSelection()
})
</script>
```

---

## Чек-лист реализации

### API
- [ ] Estimates - параметры фильтрации
- [ ] Estimates - колонка author
- [ ] Timesheets - параметры фильтрации
- [ ] Timesheets - колонки author, total_hours
- [ ] Counterparties - параметры + колонки + bulk-delete
- [ ] Objects - параметры + колонки + bulk-delete
- [ ] Persons - параметры + колонки + bulk-delete
- [ ] Works - параметры + колонки + bulk-delete

### Контекстное меню
- [ ] ContextMenu.vue
- [ ] useContextMenu.ts
- [ ] Интеграция в DataTable
- [ ] Добавить во все формы

### Экспорт
- [ ] useExport.ts
- [ ] ExportButton.vue
- [ ] Установить библиотеку xlsx
- [ ] Добавить во все формы
- [ ] API endpoints для экспорта

### Горячие клавиши
- [ ] useKeyboardShortcuts.ts
- [ ] Добавить во все формы
- [ ] Документация

### Тестирование
- [ ] API - ручное тестирование
- [ ] API - автоматические тесты
- [ ] Контекстное меню - E2E тесты
- [ ] Экспорт - ручное тестирование
- [ ] Горячие клавиши - ручное тестирование

---

## Установка зависимостей

```bash
# Для экспорта в Excel
cd web-client
npm install xlsx
```

---

## Ожидаемое время

- API расширение: 3 дня
- Контекстное меню: 1-2 дня
- Экспорт данных: 1-2 дня
- Горячие клавиши: 0.5 дня
- Тестирование: 1-2 дня

**Итого:** 6.5-9.5 дней

---

## Полезные ссылки

- API план: `API_FILTERS_IMPLEMENTATION.md`
- Руководство разработчика: `web-client/DEVELOPER_FORMS_GUIDE.md`
- Итоги форм: `FORMS_ALL_COMPLETE.md`
- Быстрый старт: `FORMS_QUICK_START.md`
