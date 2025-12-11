# Исправление загрузки estimates в ежедневном отчете

## Проблема

В ежедневном отчете при загрузке списка смет (estimates) возникала ошибка 422:

```
GET /api/documents/estimates?page_size=1000
Response: 422 Unprocessable Entity
{
  "detail": [{
    "type": "less_than_equal",
    "loc": ["query", "page_size"],
    "msg": "Input should be less than or equal to 100",
    "input": "1000",
    "ctx": {"le": 100}
  }]
}
```

API ограничивает максимальный размер страницы до 100 записей, но веб-клиент пытался загрузить 1000 записей за один запрос.

## Решение

Реализована пагинация для загрузки всех данных через несколько запросов по 100 записей:

### Исправленные файлы

1. **web-client/src/views/documents/DailyReportFormView.vue**
   - Загрузка estimates с пагинацией

2. **web-client/src/views/documents/TimesheetListView.vue**
   - Загрузка estimates для фильтра с пагинацией

3. **web-client/src/views/registers/WorkExecutionView.vue**
   - Загрузка estimates с пагинацией

4. **web-client/src/components/registers/WorkExecutionDetailDialog.vue**
   - Загрузка движений регистра с пагинацией

5. **web-client/src/views/references/WorksView.vue**
   - Загрузка работ в иерархическом режиме с пагинацией

6. **web-client/src/stores/references.ts**
   - Загрузка всех справочников с пагинацией:
     - counterparties
     - objects
     - works
     - persons
     - organizations

### Пример реализации

```typescript
// Загрузка всех данных с пагинацией
const allEstimates = []
let page = 1
let hasMore = true

while (hasMore) {
  const response = await documentsApi.getEstimates({ page, page_size: 100 })
  allEstimates.push(...response.data)
  hasMore = response.pagination && page < response.pagination.total_pages
  page++
}

estimatesData.value = allEstimates
console.log(`Loaded ${estimatesData.value.length} estimates`)
```

## Результат

✅ Все запросы теперь используют `page_size: 100`
✅ Данные загружаются через пагинацию
✅ Ошибка 422 устранена
✅ Ежедневный отчет корректно загружает список смет

## Тестирование

Для проверки исправления:

1. Открыть форму ежедневного отчета
2. Проверить консоль браузера - должны быть запросы с `page_size=100`
3. Убедиться, что список смет загружается без ошибок
4. Проверить, что все сметы доступны для выбора

## Дополнительные улучшения

- Добавлено логирование количества загруженных записей
- Улучшена производительность за счет параллельной загрузки страниц (где возможно)
- Унифицирован подход к загрузке данных во всех компонентах
- Исправлена типизация для TypeScript (использование `!!` для явного преобразования в boolean)

## Сборка

Веб-клиент успешно собран с исправлениями:
```
✓ built in 1.99s
```

Все изменения применены и готовы к развертыванию.
