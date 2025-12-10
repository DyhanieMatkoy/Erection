# Архитектура системы управления рабочим временем строительных бригад

## Обзор

Система представляет собой десктопное приложение на PyQt6 с архитектурой Model-View-ViewModel (MVVM), имитирующее поведение 1С 8.3. Приложение использует SQLite для хранения данных и предоставляет интерфейс для управления сметами, учета трудозатрат и формирования отчетности.

## Архитектура

### Общая структура

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ List Forms   │  │Document Forms│  │Report Forms  │  │
│  │ (QML/Widgets)│  │ (QML/Widgets)│  │ (QML/Widgets)│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                   ViewModel Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ListViewModel │  │ DocViewModel │  │ReportViewModel│ │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                    Business Logic Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Services     │  │ Validators   │  │ Calculators  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Repositories │  │ Models       │  │ Database     │  │
│  │              │  │              │  │ (SQLite)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Технологический стек

- **Frontend**: PyQt6 (Qt Widgets)
- **Backend**: Python 3.10+
- **База данных**: SQLite3 (встроенный модуль Python)
- **Отчеты**: ReportLab (PDF), QPrinter
- **Импорт/Экспорт**: openpyxl (для работы с Excel)
- **Хеширование**: hashlib (встроенный модуль Python)

## Компоненты и интерфейсы

### 1. Presentation Layer (Слой представления)

#### 1.1 Базовые формы

**BaseListForm** - базовый класс для форм списков
- Методы:
  - `void onInsertPressed()` - создание нового элемента (Insert/F9)
  - `void onEnterPressed()` - открытие выбранного элемента
  - `void onDeletePressed()` - пометка на удаление
  - `void onSearchActivated(QString text)` - быстрый поиск (Ctrl+F)
  - `void onCopyPressed()` - копирование элемента (Ctrl+D)
  - `void saveColumnSettings()` - сохранение настроек колонок
  - `void loadColumnSettings()` - загрузка настроек колонок

**BaseDocumentForm** - базовый класс для форм документов
- Методы:
  - `void onSave()` - сохранение (Ctrl+S)
  - `void onSaveAndClose()` - сохранение и закрытие (Ctrl+Shift+S)
  - `void onClose()` - закрытие с проверкой изменений (Esc)
  - `void onPrint()` - печать (Ctrl+P)
  - `bool hasUnsavedChanges()` - проверка несохраненных изменений
  - `void showConfirmationDialog()` - диалог подтверждения

**BaseTablePart** - базовый компонент для табличных частей
- Методы:
  - `void onInsertRow()` - добавление строки (Insert, Ctrl+Plus)
  - `void onInsertGroup()` - добавление строки группы (Ctrl+Shift+G)
  - `void onDeleteRow()` - удаление строки (Delete, Ctrl+Minus)
  - `void onToggleGroup(int rowIndex)` - свернуть/развернуть группу
  - `void onF4Pressed()` - открытие формы выбора справочника
  - `void onCopyRows()` - копирование строк (Ctrl+C)
  - `void onPasteRows()` - вставка строк (Ctrl+V)
  - `void recalculateRow(int rowIndex)` - пересчет строки
  - `void recalculateTotals()` - пересчет итогов
  - `QList<int> getGroupChildren(int groupRowIndex)` - получение дочерних строк группы
  - `void hideGroupChildren(int groupRowIndex)` - скрыть дочерние строки группы
  - `void showGroupChildren(int groupRowIndex)` - показать дочерние строки группы

#### 1.2 Специализированные формы

**EstimateListForm** - форма списка смет
- Наследует: BaseListForm
- Дополнительные методы:
  - `void onImportFromExcel()` - импорт из Excel

**EstimateDocumentForm** - форма документа сметы
- Наследует: BaseDocumentForm
- Компоненты:
  - Реквизиты: Номер, Дата, Заказчик, Объект, Подрядчик, Ответственный
  - Табличная часть: Работа, Количество, Единица измерения, Цена, Норма трудозатрат, Сумма, Плановые трудозатраты
  - Итоги: Итого сумма, Итого трудозатраты

**DailyReportForm** - форма ежедневного отчета
- Наследует: BaseDocumentForm
- Компоненты:
  - Реквизиты: Дата, ДокументОснование (Смета), Бригадир
  - Табличная часть: Работа, Плановые трудозатраты, Фактические трудозатраты, Отклонение %, Исполнители
  - Кнопка "Заполнить" - открывает диалог выбора строк сметы
- Дополнительные методы:
  - `void onFillFromEstimate()` - заполнение из сметы

**EstimateLinePickerDialog** - диалог выбора строк сметы
- Компоненты:
  - Таблица со строками сметы с флажками для отметки
  - Возможность выделения диапазона мышью
  - Кнопки "Выбрать", "Отмена"
- Методы:
  - `QList<int> getSelectedLineIds()` - получение ID выбранных строк

**AnalyticsReportForm** - форма аналитических отчетов
- Компоненты:
  - Фильтры: Период, Смета, Объект, Ответственный
  - Сводная таблица с группировками
  - Кнопки экспорта (PDF, Excel, CSV)

### 2. ViewModel Layer

**ListViewModel** - базовая модель представления для списков
- Свойства:
  - `QAbstractItemModel* model` - модель данных
  - `QString searchText` - текст поиска
  - `QMap<QString, QVariant> columnSettings` - настройки колонок
- Методы:
  - `void loadData()` - загрузка данных
  - `void filterData(QString text)` - фильтрация данных
  - `void createNew()` - создание нового элемента
  - `void deleteSelected()` - удаление выбранного

**DocumentViewModel** - базовая модель представления для документов
- Свойства:
  - `QObject* document` - объект документа
  - `bool isModified` - флаг изменений
  - `QList<QObject*> tablePart` - табличная часть
- Методы:
  - `void save()` - сохранение документа
  - `void load(int id)` - загрузка документа
  - `void addTableRow()` - добавление строки в табличную часть
  - `void removeTableRow(int index)` - удаление строки
  - `void recalculate()` - пересчет документа

**EstimateViewModel** - модель представления сметы
- Наследует: DocumentViewModel
- Дополнительные методы:
  - `void onWorkSelected(int rowIndex, int workId)` - обработка выбора работы
  - `void onQuantityChanged(int rowIndex, double quantity)` - изменение количества
  - `void onPriceChanged(int rowIndex, double price)` - изменение цены
  - `void calculateRowSum(int rowIndex)` - расчет суммы строки
  - `void calculateRowLabor(int rowIndex)` - расчет трудозатрат строки

### 3. Business Logic Layer

**EstimateService** - сервис работы со сметами
- Методы:
  - `Estimate* create()` - создание новой сметы
  - `Estimate* load(int id)` - загрузка сметы
  - `bool save(Estimate* estimate)` - сохранение сметы
  - `bool validate(Estimate* estimate)` - валидация сметы
  - `Estimate* importFromExcel(QString filePath)` - импорт из Excel
  - `QByteArray generatePrintForm(int estimateId)` - генерация печатной формы

**DailyReportService** - сервис работы с ежедневными отчетами
- Методы:
  - `DailyReport* create(int estimateId)` - создание отчета
  - `bool save(DailyReport* report)` - сохранение отчета
  - `bool validate(DailyReport* report)` - валидация отчета
  - `QList<Estimate*> getUnfinishedEstimates()` - получение незавершенных смет
  - `QList<EstimateLine*> getEstimateLines(int estimateId)` - получение строк сметы для выбора
  - `bool fillFromEstimate(DailyReport* report, QList<int> selectedLineIds)` - заполнение отчета из выбранных строк сметы

**AnalyticsService** - сервис аналитики
- Методы:
  - `QList<AnalyticsRow*> getAnalytics(QDate from, QDate to)` - получение аналитики
  - `QList<AnalyticsDetail*> getDetails(int estimateId)` - детализация по смете
  - `QByteArray exportToPdf(QList<AnalyticsRow*> data)` - экспорт в PDF
  - `QByteArray exportToExcel(QList<AnalyticsRow*> data)` - экспорт в Excel
  - `QByteArray exportToCsv(QList<AnalyticsRow*> data)` - экспорт в CSV

**CalculatorService** - сервис расчетов
- Методы:
  - `double calculateSum(double quantity, double price)` - расчет суммы
  - `double calculateLabor(double quantity, double laborRate)` - расчет трудозатрат
  - `double calculateDeviation(double planned, double actual)` - расчет отклонения
  - `void recalculateDocument(Document* doc)` - пересчет документа

**ValidationService** - сервис валидации
- Методы:
  - `ValidationResult validateEstimate(Estimate* estimate)` - валидация сметы
  - `ValidationResult validateDailyReport(DailyReport* report)` - валидация отчета
  - `bool checkReferenceUsage(int refId, QString refType)` - проверка использования справочника

**AuthService** - сервис аутентификации и авторизации
- Методы:
  - `User* login(QString username, QString password)` - вход в систему
  - `void logout()` - выход из системы
  - `bool hasPermission(User* user, QString action)` - проверка прав
  - `QList<Document*> filterByPermissions(User* user, QList<Document*> docs)` - фильтрация по правам

### 4. Data Layer

#### 4.1 Models (Модели данных)

**Estimate** - модель сметы
```cpp
class Estimate {
    int id;
    QString number;
    QDate date;
    int customerId;        // FK -> Counterparty
    int objectId;          // FK -> Object
    int contractorId;      // FK -> Organization
    int responsibleId;     // FK -> Person
    double totalSum;
    double totalLabor;
    QList<EstimateLine*> lines;
};
```

**EstimateLine** - строка сметы
```cpp
class EstimateLine {
    int id;
    int estimateId;        // FK -> Estimate
    int workId;            // FK -> Work
    double quantity;
    QString unit;
    double price;
    double laborRate;
    double sum;
    double plannedLabor;
    bool isGroup;          // Признак группы
    QString groupName;     // Наименование группы
    int parentGroupId;     // FK -> EstimateLine (родительская группа)
    bool isCollapsed;      // Признак свернутой группы
};
```

**DailyReport** - модель ежедневного отчета
```cpp
class DailyReport {
    int id;
    QDate date;
    int estimateId;        // FK -> Estimate (ДокументОснование)
    int foremanId;         // FK -> Person
    QList<DailyReportLine*> lines;
};
```

**DailyReportLine** - строка ежедневного отчета
```cpp
class DailyReportLine {
    int id;
    int reportId;          // FK -> DailyReport
    int workId;            // FK -> Work
    double plannedLabor;
    double actualLabor;
    double deviationPercent;
    QList<int> executorIds; // FK -> Person
    bool isGroup;          // Признак группы (копируется из сметы)
    QString groupName;     // Наименование группы
    int parentGroupId;     // FK -> DailyReportLine (родительская группа)
    bool isCollapsed;      // Признак свернутой группы
};
```

**Counterparty** - справочник контрагентов
```cpp
class Counterparty {
    int id;
    QString name;
    QString inn;
    QString contactPerson;
    QString phone;
    bool markedForDeletion;
};
```

**Object** - справочник объектов
```cpp
class Object {
    int id;
    QString name;
    int ownerId;           // FK -> Counterparty
    QString address;
    bool markedForDeletion;
};
```

**Work** - справочник работ
```cpp
class Work {
    int id;
    QString name;
    QString unit;
    double price;
    double laborRate;
    bool markedForDeletion;
};
```

**Person** - справочник физических лиц
```cpp
class Person {
    int id;
    QString fullName;
    QString position;
    QString phone;
    int userId;            // FK -> User
    bool markedForDeletion;
};
```

**Organization** - справочник организаций
```cpp
class Organization {
    int id;
    QString name;
    QString inn;
    int defaultResponsibleId; // FK -> Person
    bool markedForDeletion;
};
```

**User** - пользователи системы
```cpp
class User {
    int id;
    QString username;
    QString passwordHash;
    QString role;          // Администратор, Руководитель, Бригадир, Сотрудник
    bool isActive;
};
```

#### 4.2 Repositories (Репозитории)

**BaseRepository<T>** - базовый репозиторий
- Методы:
  - `T* findById(int id)` - поиск по ID
  - `QList<T*> findAll()` - получение всех записей
  - `QList<T*> findByFilter(QMap<QString, QVariant> filter)` - поиск с фильтром
  - `bool save(T* entity)` - сохранение
  - `bool remove(int id)` - удаление
  - `bool markForDeletion(int id)` - пометка на удаление

**EstimateRepository** - репозиторий смет
- Наследует: BaseRepository<Estimate>
- Дополнительные методы:
  - `QList<Estimate*> findByResponsible(int personId)` - поиск по ответственному
  - `QList<Estimate*> findUnfinished()` - незавершенные сметы

**DailyReportRepository** - репозиторий ежедневных отчетов
- Наследует: BaseRepository<DailyReport>
- Дополнительные методы:
  - `QList<DailyReport*> findByEstimate(int estimateId)` - поиск по смете
  - `QList<DailyReport*> findByPeriod(QDate from, QDate to)` - поиск по периоду
  - `QList<DailyReport*> findByExecutor(int personId)` - поиск по исполнителю

**ReferenceRepository<T>** - репозиторий справочников
- Наследует: BaseRepository<T>
- Дополнительные методы:
  - `QList<int> findUsages(int id)` - поиск использований
  - `bool canDelete(int id)` - проверка возможности удаления

#### 4.3 Database Schema

```sql
-- Справочники
CREATE TABLE counterparties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    inn TEXT,
    contact_person TEXT,
    phone TEXT,
    marked_for_deletion INTEGER DEFAULT 0
);

CREATE TABLE objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_id INTEGER REFERENCES counterparties(id),
    address TEXT,
    marked_for_deletion INTEGER DEFAULT 0
);

CREATE TABLE organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    inn TEXT,
    default_responsible_id INTEGER REFERENCES persons(id),
    marked_for_deletion INTEGER DEFAULT 0
);

CREATE TABLE persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    position TEXT,
    phone TEXT,
    user_id INTEGER REFERENCES users(id),
    marked_for_deletion INTEGER DEFAULT 0
);

CREATE TABLE works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT,
    price REAL,
    labor_rate REAL,
    marked_for_deletion INTEGER DEFAULT 0
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);

-- Документы
CREATE TABLE estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    date DATE NOT NULL,
    customer_id INTEGER REFERENCES counterparties(id),
    object_id INTEGER REFERENCES objects(id),
    contractor_id INTEGER REFERENCES organizations(id),
    responsible_id INTEGER REFERENCES persons(id),
    total_sum REAL DEFAULT 0,
    total_labor REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE estimate_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER REFERENCES estimates(id) ON DELETE CASCADE,
    line_number INTEGER,
    work_id INTEGER REFERENCES works(id),
    quantity REAL,
    unit TEXT,
    price REAL,
    labor_rate REAL,
    sum REAL,
    planned_labor REAL,
    is_group INTEGER DEFAULT 0,
    group_name TEXT,
    parent_group_id INTEGER REFERENCES estimate_lines(id),
    is_collapsed INTEGER DEFAULT 0
);

CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    estimate_id INTEGER REFERENCES estimates(id),
    foreman_id INTEGER REFERENCES persons(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_report_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE,
    line_number INTEGER,
    work_id INTEGER REFERENCES works(id),
    planned_labor REAL,
    actual_labor REAL,
    deviation_percent REAL,
    is_group INTEGER DEFAULT 0,
    group_name TEXT,
    parent_group_id INTEGER REFERENCES daily_report_lines(id),
    is_collapsed INTEGER DEFAULT 0
);

CREATE TABLE daily_report_executors (
    report_line_id INTEGER REFERENCES daily_report_lines(id) ON DELETE CASCADE,
    executor_id INTEGER REFERENCES persons(id),
    PRIMARY KEY (report_line_id, executor_id)
);

-- Настройки пользователя
CREATE TABLE user_settings (
    user_id INTEGER REFERENCES users(id),
    form_name TEXT,
    setting_key TEXT,
    setting_value TEXT,
    PRIMARY KEY (user_id, form_name, setting_key)
);

-- Константы
CREATE TABLE constants (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Индексы
CREATE INDEX idx_estimates_date ON estimates(date);
CREATE INDEX idx_estimates_responsible ON estimates(responsible_id);
CREATE INDEX idx_daily_reports_date ON daily_reports(date);
CREATE INDEX idx_daily_reports_estimate ON daily_reports(estimate_id);
```

## Обработка ошибок

### Стратегия обработки ошибок

1. **Валидация на уровне UI**: Проверка обязательных полей, форматов данных
2. **Валидация на уровне бизнес-логики**: Проверка бизнес-правил
3. **Обработка ошибок БД**: Транзакции, откат изменений
4. **Логирование**: Запись всех ошибок в лог-файл

### Типы ошибок

```cpp
enum class ErrorType {
    ValidationError,      // Ошибка валидации
    DatabaseError,        // Ошибка БД
    PermissionError,      // Ошибка прав доступа
    NotFoundError,        // Объект не найден
    BusinessLogicError    // Ошибка бизнес-логики
};

class AppError {
    ErrorType type;
    QString message;
    QString details;
    QDateTime timestamp;
};
```

### Обработчики ошибок

- **ValidationErrorHandler**: Показывает сообщения валидации пользователю
- **DatabaseErrorHandler**: Логирует ошибки БД, показывает общее сообщение
- **PermissionErrorHandler**: Показывает сообщение о недостаточных правах
- **GlobalErrorHandler**: Централизованная обработка всех ошибок

## Стратегия тестирования

### Unit Tests (Модульные тесты)

- Тестирование моделей данных
- Тестирование сервисов (CalculatorService, ValidationService)
- Тестирование репозиториев (с использованием in-memory SQLite)
- Фреймворк: Qt Test

### Integration Tests (Интеграционные тесты)

- Тестирование взаимодействия слоев
- Тестирование работы с БД
- Тестирование импорта/экспорта

### UI Tests (Тесты интерфейса)

- Тестирование горячих клавиш
- Тестирование пересчетов в табличных частях
- Тестирование форм списков и документов
- Фреймворк: Qt Test + QTest::keyClick

### Performance Tests (Тесты производительности)

- Время пересчета табличных частей (< 100-200 мс)
- Время формирования отчетов (< 5-10 секунд)
- Время загрузки больших списков

## Производительность и оптимизация

### Оптимизация пересчетов

- Использование debounce для пересчетов (100 мс задержка)
- Пересчет только измененных строк
- Кэширование промежуточных результатов

### Оптимизация БД

- Индексы на часто используемых полях
- Использование транзакций для массовых операций
- Ленивая загрузка связанных данных

### Оптимизация UI

- Виртуализация списков (отображение только видимых строк)
- Асинхронная загрузка данных
- Кэширование настроек форм

## Безопасность

### Аутентификация

- Хеширование паролей (bcrypt)
- Сессии пользователей
- Автоматический выход при неактивности

### Авторизация

- Ролевая модель доступа (RBAC)
- Проверка прав на уровне сервисов
- Фильтрация данных по правам пользователя

### Защита данных

- Валидация всех входных данных
- Параметризованные SQL-запросы (защита от SQL-injection)
- Логирование всех операций изменения данных

## Расширяемость

### Плагинная архитектура

- Возможность добавления новых типов документов
- Возможность добавления новых отчетов
- Возможность добавления новых форматов экспорта

### Конфигурируемость

- Настройка форм через конфигурационные файлы
- Настройка прав доступа через БД
- Настройка печатных форм через шаблоны
