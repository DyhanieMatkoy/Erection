# План реализации (TODO)

## Phase 1: Подготовка Базы Данных (Database Migration) ✅
Эти задачи критичны и должны быть выполнены первыми.

- [x] **Добавить UUID и Audit поля:** Создать миграцию (Alembic) для добавления колонок `uuid` (UUID, unique), `updated_at` (Datetime), `is_deleted` (Bool) во все таблицы:
    - [x] `daily_reports`
    - [x] `daily_report_lines`
    - [x] `estimates`
    - [x] `estimate_lines`
    - [x] `timesheets`
    - [x] `timesheet_lines`
    - [x] `work_specifications`
    - [x] `users` (если синхронизируются)
    - [x] `persons`
    - [x] `organizations`
    - [x] `counterparties`
    - [x] `objects`
    - [x] `works`
    - [x] `materials`
    - [x] `cost_items`
    - [x] `units`
- [x] **Заполнить UUID:** Написать скрипт миграции данных, который сгенерирует UUID для существующих записей.
- [x] **Создать таблицы синхронизации:**
    - [x] `sync_nodes` (Справочник узлов)
    - [x] `sync_changes` (Очередь изменений)
    - [x] `object_version_history` (История версий для конфликтов)

## Phase 2: Ядро синхронизации (Core Logic) ✅
Реализация на уровне Python (Shared code для Web и Desktop).

- [x] **Модель `SyncManager`:** Класс, управляющий логикой регистрации изменений.
- [x] **Event Listeners (SQLAlchemy):**
    - [x] `after_insert`: Добавлять запись в `sync_changes`.
    - [x] `after_update`: Добавлять запись в `sync_changes`.
    - [x] `after_delete`: Помечать `is_deleted=True` и добавлять запись в `sync_changes` (вместо реального удаления).
- [x] **Сериализатор:** Реализовать универсальный `JsonSerializer`, который умеет превращать SQLAlchemy модели в dict и обратно, учитывая вложенные списки (например, строки сметы).
- [x] **ConflictResolver:** Класс для разрешения конфликтов с различными стратегиями.
- [x] **PacketManager:** Класс для пакетной передачи с сжатием и подтверждениями.

## Phase 3: Серверная часть (Web API) ✅
Реализация API эндпоинтов на FastAPI.

- [x] **Endpoint `/api/sync/register`:** Регистрация нового десктоп-клиента, выдача ему `node_id`.
- [x] **Endpoint `/api/sync/exchange`:** Основной метод POST.
    - [x] Логика проверки токена.
    - [x] Логика обработки входящего пакета (Apply changes).
    - [x] Логика генерации исходящего пакета (Collect changes).
    - [x] Обработка квитанций (Purge queue).
- [x] **Endpoint `/api/sync/status/{node_id}`:** Получение статуса синхронизации узла.
- [x] **Endpoint `/api/sync/nodes`:** Список всех зарегистрированных узлов.
- [x] **Endpoint `/api/sync/conflicts`:** История конфликтов и их разрешение.
- [x] **Endpoint `/api/sync/statistics`:** Статистика синхронизации.

## Phase 4: Клиентская часть (Desktop) ✅
Интеграция в PyQt приложение.

- [x] **Настройки:** UI для ввода адреса сервера и токена.
- [x] **Фоновый поток:** `SyncService` с автоматической синхронизацией и retry логикой.
- [x] **Индикатор статуса:** Сигналы для отображения статуса (Онлайн/Офлайн/Синхронизация).
- [x] **Обработка конфликтов:** Диалог настроек синхронизации с управлением конфликтами.
- [x] **SyncSettingsDialog:** Полноценный диалог для настройки и мониторинга синхронизации.
- [x] **Offline Transfer:** Экспорт/импорт изменений для офлайн передачи.

## Phase 5: Тестирование и Отладка ✅

- [x] **Unit Tests:** Тесты сериализации/десериализации, SyncManager, PacketManager, ConflictResolver.
- [x] **Integration Tests:** Эмуляция обмена между двумя базами (в памяти).
- [x] **Property-Based Tests:** Тесты корректности с использованием Hypothesis.
- [x] **Load Tests:** Проверка работы с большими пакетами (1000+ записей).
- [x] **Comprehensive Documentation:** Полное руководство по системе синхронизации.

## Реализованные файлы:

### Миграции базы данных:
- `migrations/versions/20251213_003500_add_sync_fields.py` - Добавление UUID и audit полей
- `migrations/versions/20251213_003600_create_sync_tables.py` - Создание таблиц синхронизации
- `migrations/versions/20251213_003700_populate_uuids.py` - Заполнение UUID для существующих записей

### Модели данных:
- `src/data/models/sync_models.py` - Модели синхронизации (SyncNode, SyncChange, ObjectVersionHistory)
- Обновлены все основные модели в `src/data/models/sqlalchemy_models.py` с добавлением полей синхронизации

### Основная логика:
- `src/data/sync_manager.py` - SyncManager с отслеживанием изменений и сериализацией
- `src/data/packet_manager.py` - PacketManager для пакетной передачи с сжатием
- `src/data/conflict_resolver.py` - ConflictResolver со стратегиями разрешения конфликтов

### API эндпоинты:
- `api/endpoints/sync.py` - Полноценный REST API для синхронизации
- Интегрирован в `api/main.py`

### Клиентская часть:
- `src/services/sync_service.py` - SyncService для десктоп клиента с PyQt интеграцией
- `src/views/sync_settings_dialog.py` - Диалог настроек синхронизации

### Тестирование:
- `test/test_sync_system.py` - Комплексный набор тестов (unit, integration, property-based)

### Документация:
- `docs/SYNC_SYSTEM_GUIDE.md` - Полное руководство по системе синхронизации

## Статус: ЗАВЕРШЕНО ✅

Все фазы реализации успешно завершены. Система синхронизации готова к развертыванию и тестированию.
