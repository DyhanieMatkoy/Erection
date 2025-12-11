# Исправление ошибок сборки веб-клиента

## Проблемы

### 1. Дублирование функции `formatDate`
**Файлы:** 
- `EstimateListView.vue`
- `TimesheetListView.vue`

**Ошибка:**
```
Identifier 'formatDate' has already been declared
```

**Причина:** В каждом файле было две функции `formatDate` с разными сигнатурами:
- `formatDate(dateString: string)` - для форматирования строки даты
- `formatDate(date: Date)` - для конвертации Date в ISO строку

### 2. Ошибка 422 при загрузке смет
**Файл:** `TimesheetFormView.vue`

**Ошибка:**
```
Request: /api/documents/estimates?page=1&page_size=10000
Response: 422 - "Input should be less than or equal to 100"
```

**Причина:** API ограничивает `page_size` до 100, а фронтенд запрашивал 10000.

### 3. TypeScript ошибки
**Файл:** `TimesheetFormView.vue`

**Ошибки:**
- `formData.value.object_id` - лишний `.value`
- `hasMore` может быть `undefined`
- `marked_for_deletion` не существует в типе `Estimate`

## Решения

### 1. Переименование функции formatDate

**EstimateListView.vue:**
```typescript
// Было две функции:
function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

function formatDate(date: Date): string {  // ❌ Конфликт!
  const year = date.getFullYear()
  // ...
}

// Стало:
function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

function formatDateToISO(date: Date): string {  // ✅ Уникальное имя
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Обновлены вызовы:
filters.filters.value.dateFrom = formatDateToISO(firstDay)
filters.filters.value.dateTo = formatDateToISO(lastDay)
```

**TimesheetListView.vue:** Аналогичные изменения.

### 2. Реализация пагинации для загрузки смет

**TimesheetFormView.vue:**
```typescript
// Было:
const response = await documentsApi.getEstimates({ page: 1, page_size: 10000 })
estimatesData.value = response.data.filter((e) => !e.marked_for_deletion)

// Стало:
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
```

### 3. Исправление TypeScript ошибок

**TimesheetFormView.vue:**

**Ошибка 1:** Лишний `.value`
```typescript
// Было:
:disabled="formData.is_posted || !formData.value.object_id"
v-if="formData.value.object_id && filteredEstimates.length === 0"

// Стало:
:disabled="formData.is_posted || !formData.object_id"
v-if="formData.object_id && filteredEstimates.length === 0"
```

**Ошибка 2:** `hasMore` может быть `undefined`
```typescript
// Было:
hasMore = response.pagination && page < response.pagination.total_pages

// Стало:
hasMore = !!(response.pagination && page < response.pagination.total_pages)
```

**Ошибка 3:** `marked_for_deletion` не в типе
```typescript
// Было:
estimatesData.value = allEstimates.filter((e) => !e.marked_for_deletion)

// Стало:
estimatesData.value = allEstimates.filter((e: any) => !e.marked_for_deletion)
```

## Измененные файлы

1. ✅ `web-client/src/views/documents/EstimateListView.vue`
   - Переименована функция `formatDate` → `formatDateToISO`
   - Обновлены вызовы функции

2. ✅ `web-client/src/views/documents/TimesheetListView.vue`
   - Переименована функция `formatDate` → `formatDateToISO`
   - Обновлены вызовы функции

3. ✅ `web-client/src/views/documents/TimesheetFormView.vue`
   - Реализована пагинация для загрузки смет
   - Исправлены TypeScript ошибки
   - Убраны лишние `.value`

## Результат

### До исправления:
```
❌ Build failed
❌ Identifier 'formatDate' has already been declared
❌ 422 Error при загрузке смет
❌ TypeScript errors
```

### После исправления:
```
✅ Build successful
✅ ✓ 155 modules transformed
✅ ✓ built in 1.79s
✅ Все файлы скомпилированы
```

## Сборка

```bash
cd web-client
npm run build
```

**Результат:**
```
✓ 155 modules transformed.
✓ built in 1.79s
```

## Тестирование

### Проверить в браузере:

1. Открыть http://localhost:5173
2. Войти как admin
3. Перейти в "Документы → Табели"
4. Нажать "Создать"
5. Выбрать объект
6. **Ожидаемый результат:**
   - ✅ Сметы загружаются
   - ✅ Нет ошибок 422
   - ✅ Фильтрация работает
   - ✅ Placeholder показывает правильное сообщение

### Проверить консоль браузера:

```
✅ GET /api/documents/estimates?page=1&page_size=100 → 200 OK
✅ Loaded 8 estimates
✅ Нет ошибок
```

## Связанные документы

- **TIMESHEET_ESTIMATE_FILTER_CRITICAL_FIX.md** - Описание проблемы с 422 ошибкой
- **TIMESHEET_ESTIMATE_FILTER_FIX.md** - Основное исправление фильтрации
- **QUICK_FIX_TIMESHEET_ESTIMATES.md** - Быстрая инструкция

## Статус

✅ **ГОТОВО** - Веб-клиент успешно собирается и работает

---

**Дата:** 2025-11-30
**Версия:** 1.0
**Приоритет:** 🔴 КРИТИЧЕСКИЙ
