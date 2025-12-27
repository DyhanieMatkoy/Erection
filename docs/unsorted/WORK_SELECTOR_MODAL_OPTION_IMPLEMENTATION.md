# Реализация опции модального/немодального открытия селектора работ

## Обзор

Реализована возможность выбора режима открытия формы-селектора работ из сметы: модально (в диалоговом окне) или немодально (в отдельном окне).

## Реализованные компоненты

### Backend

#### 1. Сервис настроек пользователя (`src/services/user_settings_service.py`)
- Добавлены методы для работы с настройками селектора работ:
  - `get_work_selector_settings(user_id)` - получение настроек
  - `set_work_selector_settings(user_id, settings)` - сохранение настроек

#### 2. API endpoint (`api/endpoints/work_selector_settings.py`)
- `GET /api/work-selector-settings/{user_id}` - получение настроек
- `PUT /api/work-selector-settings/{user_id}` - обновление настроек

### Frontend

#### 1. Сервис настроек (`web-client/src/services/workSelectorSettingsService.ts`)
- `WorkSelectorSettingsService` - класс для работы с API настроек
- Методы `getUserSettings()` и `saveUserSettings()`

#### 2. Composable (`web-client/src/composables/useWorkSelectorSettings.ts`)
- `useWorkSelectorSettings()` - реактивное управление настройками
- Методы для переключения режимов и сохранения настроек

#### 3. Компонент настроек (`web-client/src/components/settings/WorkSelectorSettingsDialog.vue`)
- Диалог настроек селектора работ
- Переключение между модальным и немодальным режимами
- Настройки иерархии и отображения

#### 4. Обновленный компонент строк сметы (`web-client/src/components/documents/EstimateLines.vue`)
- Интеграция с настройками селектора работ
- Кнопка доступа к настройкам
- Условное отображение селектора в модальном или немодальном режиме

## Настройки

### Доступные опции:

1. **open_modal** (boolean) - режим открытия:
   - `true` - модальное окно (по умолчанию)
   - `false` - отдельное окно

2. **default_hierarchy_mode** (string) - режим отображения иерархии:
   - `'tree'` - дерево (по умолчанию)
   - `'flat'` - плоский список
   - `'breadcrumb'` - с путями

3. **show_hierarchy_controls** (boolean) - показывать элементы управления иерархией:
   - `true` - показывать (по умолчанию)
   - `false` - скрыть

4. **auto_expand_groups** (boolean) - автоматически разворачивать группы:
   - `true` - разворачивать (по умолчанию)
   - `false` - не разворачивать

## Использование

### Для пользователя:
1. В форме сметы нажать кнопку настроек (шестеренка) рядом с кнопкой "Добавить строку"
2. В диалоге настроек выбрать желаемый режим открытия
3. Настроить дополнительные параметры отображения
4. Настройки автоматически сохраняются

### Для разработчика:
```typescript
// Использование composable
const {
  isModalMode,
  hierarchyMode,
  showHierarchyControls,
  autoExpandGroups,
  toggleModalMode,
  setHierarchyMode
} = useWorkSelectorSettings()

// Проверка режима
if (isModalMode.value) {
  // Открыть модально
} else {
  // Открыть в окне
}
```

## Тестирование

### Backend тесты:
```bash
python test_work_selector_settings.py
```

### Frontend тесты:
```bash
cd web-client
npx vitest run src/composables/__tests__/useWorkSelectorSettings.spec.ts
```

## Структура файлов

```
├── src/services/user_settings_service.py          # Backend сервис настроек
├── api/endpoints/work_selector_settings.py        # API endpoints
├── web-client/src/
│   ├── services/workSelectorSettingsService.ts    # Frontend сервис
│   ├── composables/useWorkSelectorSettings.ts     # Composable
│   ├── components/
│   │   ├── settings/WorkSelectorSettingsDialog.vue # Диалог настроек
│   │   └── documents/EstimateLines.vue             # Обновленный компонент
│   └── __tests__/                                  # Тесты
├── test_work_selector_settings.py                 # Backend тесты
└── WORK_SELECTOR_MODAL_OPTION_IMPLEMENTATION.md   # Документация
```

## Особенности реализации

1. **Персистентность настроек** - настройки сохраняются в базе данных для каждого пользователя
2. **Реактивность** - изменения настроек мгновенно отражаются в интерфейсе
3. **Fallback** - при ошибках API используются настройки по умолчанию
4. **Типизация** - полная типизация TypeScript для всех компонентов
5. **Тестирование** - покрытие тестами основной функциональности

## Интеграция с существующим кодом

Изменения минимальны и обратно совместимы:
- Добавлена кнопка настроек в `EstimateLines`
- Селектор работ теперь учитывает пользовательские настройки
- API расширен новыми endpoints без изменения существующих

## Будущие улучшения

1. Добавление анимаций переходов между режимами
2. Расширение настроек фильтрации и сортировки
3. Экспорт/импорт настроек пользователя
4. Глобальные настройки для администраторов