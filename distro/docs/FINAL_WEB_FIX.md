# Финальные исправления веб-клиента

## Исправленные проблемы

### 1. Ошибка PersonUpdate - AttributeError: 'full_name'
**Причина:** Модели Person и Object в API не соответствовали структуре БД
- Person в БД имеет `full_name` и `position`, но модель использовала `name`
- Object в БД имеет `address` и `owner_id`, но модель не включала эти поля

**Исправление:**
- Обновлены модели в `api/models/references.py`:
  - `PersonBase` теперь использует `full_name` и `position`
  - `ObjectBase` теперь включает `address` и `owner_id`

### 2. Несоответствие TypeScript типов
**Исправление:**
- Обновлены типы в `web-client/src/types/models.ts`:
  - `Person` теперь использует `full_name` вместо `name`
  - `Object` теперь включает `address` и `owner_id`

### 3. Отображение имен в компонентах
**Проблема:** Компонент Picker по умолчанию использует `displayKey="name"`, но для Person нужно `full_name`

**Исправление:** Добавлен `display-key="full_name"` в компонентах:
- `web-client/src/views/documents/EstimateFormView.vue` (поле "Ответственный")
- `web-client/src/views/documents/DailyReportFormView.vue` (поле "Бригадир")
- `web-client/src/components/documents/DailyReportLines.vue` (поле "Исполнители", 2 места)

### 4. Ошибка печати 401/403
**Статус:** Endpoint печати требует аутентификации. Убедитесь, что:
- Пользователь авторизован
- Токен действителен
- Токен передается в заголовке Authorization

## Структура БД

### Таблица persons
```sql
- id (INTEGER)
- full_name (TEXT)
- position (TEXT)
- phone (TEXT)
- user_id (INTEGER)
- parent_id (INTEGER)
- marked_for_deletion (INTEGER)
```

### Таблица objects
```sql
- id (INTEGER)
- name (TEXT)
- owner_id (INTEGER)
- address (TEXT)
- parent_id (INTEGER)
- marked_for_deletion (INTEGER)
- is_group (INTEGER)
```

## Тестирование

### API
```bash
python test_references_api.py
```

Все справочники должны загружаться корректно:
- ✅ Counterparties: 4 items
- ✅ Objects: 2 items
- ✅ Works: 16 items
- ✅ Persons: 4 items
- ✅ Organizations: 2 items

### Веб-клиент
1. Перезагрузите страницу (F5)
2. Войдите в систему (admin/admin)
3. Проверьте формы:
   - Создание сметы - все поля должны заполняться
   - Создание акта - все поля должны заполняться
   - Выбор ответственного/бригадира - должны отображаться полные имена
   - Выбор исполнителей - должны отображаться полные имена

## Статус
✅ Модели API исправлены
✅ TypeScript типы обновлены
✅ Компоненты обновлены для корректного отображения
✅ API сервер работает
✅ Все справочники загружаются

Перезагрузите веб-клиент для применения изменений.
