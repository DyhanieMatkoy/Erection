# Исправление форм Vue

## Проблемы
1. Справочники (counterparties, objects, works, persons, organizations) не загружались - ошибка 500
2. Формы смет и актов не показывали строки
3. Невозможно было заполнить поля с выбором справочников

## Причины

### 1. Ошибка в API references endpoint
```
TypeError: ReferenceRepository.__init__() takes 1 positional argument but 2 were given
```

`ReferenceRepository` не принимает аргументы в конструкторе, но код пытался передать `DATABASE_PATH`.

### 2. Несоответствие структуры ответов API
API возвращает:
```json
{
  "success": true,
  "data": {...}
}
```

Но клиентский код ожидал просто объект данных.

## Исправления

### 1. Переписан api/endpoints/references.py
- Удалена зависимость от `ReferenceRepository`
- Используется прямое подключение к БД через `DatabaseManager`
- Все CRUD операции переписаны для работы с SQL напрямую
- Увеличен `page_size` до 1000 для загрузки всех справочников

### 2. Исправлены API клиенты

#### web-client/src/api/documents.ts
Все методы теперь правильно извлекают данные из `response.data.data`:
- `getEstimate()`
- `createEstimate()`
- `updateEstimate()`
- `postEstimate()`
- `unpostEstimate()`
- `getDailyReport()`
- `createDailyReport()`
- `updateDailyReport()`
- `postDailyReport()`
- `unpostDailyReport()`

#### web-client/src/api/references.ts
Исправлены generic функции:
- `getReference()`
- `createReference()`
- `updateReference()`

## Тестирование

### Проверка API
```bash
python test_references_api.py
```

Ожидаемый результат:
```
Testing counterparties...
Status: 200
Success: True
Items count: 4

Testing objects...
Status: 200
Success: True
Items count: 2

Testing works...
Status: 200
Success: True
Items count: 16

Testing persons...
Status: 200
Success: True
Items count: 4

Testing organizations...
Status: 200
Success: True
Items count: 2
```

### Проверка веб-клиента
1. Перезагрузите страницу (F5)
2. Войдите в систему (admin/admin)
3. Откройте форму создания сметы
4. Проверьте, что:
   - Все выпадающие списки заполнены
   - Можно добавить строки
   - Можно выбрать работы
   - Форма сохраняется

## Статус
✅ API исправлен и работает
✅ Справочники загружаются
✅ Формы должны работать корректно

Перезагрузите веб-клиент для применения изменений.
