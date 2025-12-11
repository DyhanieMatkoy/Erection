# Анализ фильтрации смет в форме табеля

## Проблема
Администратор и пользователь '1' не видят документы в отфильтрованном списке смет при выборе из формы табеля.

## Текущая реализация

### 1. Бизнес-процесс (как должно работать)
1. Пользователь выбирает **Объект** (стройплощадка)
2. Система фильтрует **Сметы**, показывая только те, которые относятся к выбранному объекту
3. Пользователь выбирает **Смету** из отфильтрованного списка
4. Табель привязывается к объекту и смете

### 2. Код фронтенда

**Файл:** `web-client/src/views/documents/TimesheetFormView.vue`

**Загрузка смет (строки 253-259):**
```typescript
onMounted(async () => {
  // Load ALL estimates (no filtering)
  try {
    const response = await documentsApi.getEstimates({ page: 1, page_size: 10000 })
    estimatesData.value = response.data.filter((e) => !e.marked_for_deletion)
    console.log(`Loaded ${estimatesData.value.length} estimates`)
  } catch (error) {
    console.error('Failed to load estimates:', error)
  }
})
```

**Фильтрация на клиенте (строки 71-88):**
```typescript
const filteredEstimates = computed(() => {
  let estimates = estimatesData.value
  if (formData.value.object_id) {
    // Фильтруем сметы по выбранному объекту
    estimates = estimates.filter((e) => e.object_id === formData.value.object_id)
  }
  return estimates.map((e) => ({
    id: e.id!,
    name: `${e.number} от ${formatDate(e.date)}`,
  }))
})

const estimatesForPicker = computed(() => {
  const filtered = filteredEstimates.value
  // ПРОБЛЕМА: Если фильтрация дает 0 результатов, показываем ВСЕ сметы
  if (filtered.length === 0 && formData.value.object_id) {
    return estimatesData.value.map((e) => ({
      id: e.id!,
      name: `${e.number} от ${formatDate(e.date)} (${getObjectName(e.object_id)})`,
    }))
  }
  return filtered
})
```

**Сброс сметы при смене объекта (строки 109-112):**
```typescript
function handleObjectChange() {
  // Reset estimate when object changes
  formData.value.estimate_id = 0
}
```

### 3. Код бэкенда

**Файл:** `api/endpoints/documents.py`

**Эндпоинт списка смет (строки 93-165):**
```python
@router.get("/documents/estimates")
async def list_estimates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    object_id: Optional[int] = None,  # ← Параметр фильтрации СУЩЕСТВУЕТ
    responsible_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = Query("date", regex="^(date|number|id)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Get list of estimates with pagination and filtering"""
    offset = (page - 1) * page_size
    
    # Build query
    where_clauses = ["e.marked_for_deletion = 0"]
    params = []
    
    if search:
        where_clauses.append("(e.number LIKE ? OR c.name LIKE ? OR o.name LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    if object_id:  # ← Фильтрация по объекту РЕАЛИЗОВАНА
        where_clauses.append("e.object_id = ?")
        params.append(object_id)
    
    # ... остальной код запроса
```

**API клиент:** `web-client/src/api/documents.ts`
```typescript
export async function getEstimates(params?: PaginationParams): Promise<ApiResponse<Estimate[]>> {
  const response = await apiClient.get<ApiResponse<Estimate[]>>('/documents/estimates', { params })
  return response.data
}
```

### 4. Данные в базе

**Сметы (не удаленные):**
```
ID: 1,   Number: 295,              Date: 2025-11-19, Object: 4, Deleted: 0
ID: 2,   Number: 295,              Date: 2025-11-20, Object: 4, Deleted: 0
ID: 6,   Number: TEST-001,         Date: 2025-11-20, Object: 3, Deleted: 0
ID: 7,   Number: TEST-GROUPS,      Date: 2025-11-20, Object: 3, Deleted: 0
ID: 158, Number: TEST-001,         Date: 2025-11-30, Object: 1, Deleted: 0
ID: 159, Number: TEST-001,         Date: 2025-11-30, Object: 1, Deleted: 0
ID: 160, Number: TEST-001-UPDATED, Date: 2025-11-30, Object: 1, Deleted: 0
ID: 162, Number: TEST-002,         Date: 2025-11-30, Object: 1, Deleted: 0
```

**Объекты:**
```
ID: 3, Name: Жилой комплекс "Солнечный"
ID: 4, Name: Торговый центр "Центральный"
ID: 1, Name: (множество тестовых объектов)
```

**Пользователи:**
```
ID: 4, Username: admin,    Role: Администратор
ID: 5, Username: manager,  Role: Руководитель
ID: 6, Username: foreman,  Role: Бригадир
ID: 7, Username: foreman_test, Role: Бригадир
```

## Причины проблемы

### 1. Неэффективная загрузка данных
- Фронтенд загружает **ВСЕ** сметы (page_size: 10000) при монтировании компонента
- Фильтрация происходит **на клиенте**, а не на сервере
- При большом количестве смет это приведет к проблемам производительности

### 2. Запутанный fallback механизм
```typescript
if (filtered.length === 0 && formData.value.object_id) {
  // Показываем ВСЕ сметы с названиями объектов
  return estimatesData.value.map((e) => ({
    id: e.id!,
    name: `${e.number} от ${formatDate(e.date)} (${getObjectName(e.object_id)})`,
  }))
}
```
- Когда для выбранного объекта нет смет, показываются **все** сметы
- Это сбивает с толку пользователя
- Пользователь может выбрать смету от другого объекта

### 3. Отсутствие обратной связи
- Нет сообщения "Для выбранного объекта нет смет"
- Пользователь не понимает, почему список пустой или показывает все сметы

### 4. Возможный сценарий проблемы
Если admin или user '1' выбирают объект, для которого нет смет:
- Список фильтруется и становится пустым
- Срабатывает fallback, показывающий все сметы
- Но если в базе вообще мало смет, может показаться, что фильтр не работает

## Решение

### Вариант 1: Улучшенная клиентская фильтрация (быстрое решение)

**Изменения в `TimesheetFormView.vue`:**

1. Убрать запутанный fallback
2. Добавить четкое сообщение, когда нет смет
3. Показать количество доступных смет

```typescript
const estimatesForPicker = computed(() => {
  const filtered = filteredEstimates.value
  return filtered
})

const estimatePickerPlaceholder = computed(() => {
  if (!formData.value.object_id) {
    return 'Сначала выберите объект'
  }
  if (filteredEstimates.value.length === 0) {
    return 'Нет смет для выбранного объекта'
  }
  return `Выберите смету (${filteredEstimates.value.length})`
})
```

### Вариант 2: Серверная фильтрация (оптимальное решение)

**Изменения в `TimesheetFormView.vue`:**

1. Загружать сметы только для выбранного объекта
2. Перезагружать при смене объекта

```typescript
async function handleObjectChange() {
  formData.value.estimate_id = 0
  await loadEstimatesForObject(formData.value.object_id)
}

async function loadEstimatesForObject(objectId: number) {
  if (!objectId) {
    estimatesData.value = []
    return
  }
  
  try {
    const response = await documentsApi.getEstimates({ 
      page: 1, 
      page_size: 1000,
      object_id: objectId  // ← Используем серверную фильтрацию
    })
    estimatesData.value = response.data.filter((e) => !e.marked_for_deletion)
  } catch (error) {
    console.error('Failed to load estimates:', error)
    estimatesData.value = []
  }
}
```

### Вариант 3: Комбинированный подход (рекомендуется)

1. Использовать серверную фильтрацию для уменьшения трафика
2. Добавить UI индикаторы для лучшего UX
3. Сохранить возможность работы без выбранного объекта

## Рекомендации

### Немедленные действия:
1. ✅ Убрать fallback, показывающий все сметы
2. ✅ Добавить информативное сообщение "Нет смет для выбранного объекта"
3. ✅ Показать количество доступных смет в placeholder

### Среднесрочные улучшения:
1. Использовать серверную фильтрацию для оптимизации
2. Добавить индикатор загрузки при смене объекта
3. Кэшировать загруженные сметы по объектам

### Долгосрочные улучшения:
1. Добавить возможность создать смету прямо из формы табеля
2. Показать предупреждение, если у объекта нет смет
3. Добавить фильтрацию по дате/статусу смет

## Ссылки на код

### Фронтенд:
- **Форма табеля:** `web-client/src/views/documents/TimesheetFormView.vue`
  - Загрузка смет: строки 253-259
  - Фильтрация: строки 71-88
  - Обработка смены объекта: строки 109-112

- **API клиент:** `web-client/src/api/documents.ts`
  - Функция getEstimates: строки 5-8

### Бэкенд:
- **Эндпоинт смет:** `api/endpoints/documents.py`
  - list_estimates: строки 93-165
  - Фильтрация по object_id: строки 119-121

### Модели:
- **Estimate модель:** `api/models/documents.py`
- **Timesheet модель:** `api/models/documents.py`
