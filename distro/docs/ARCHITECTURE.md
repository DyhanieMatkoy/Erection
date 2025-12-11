# Архитектура системы

## Обзор

Система управления строительством построена на многоуровневой архитектуре с разделением на слои данных, бизнес-логики и представления.

## Архитектурная диаграмма

```mermaid
graph TB
    subgraph "Клиентский слой"
        Desktop["PyQt6 Desktop<br/>Приложение"]
        WebClient["Vue.js Web<br/>Клиент"]
    end
    
    subgraph "API слой"
        FastAPI["FastAPI<br/>REST API"]
        Auth["Аутентификация<br/>JWT"]
        Middleware["Middleware<br/>(CORS, Auth)"]
    end
    
    subgraph "Бизнес-логика"
        Services["Сервисы"]
        DocPosting["Проведение<br/>документов"]
        PrintForms["Печатные<br/>формы"]
        Reports["Отчеты"]
    end
    
    subgraph "Слой данных"
        Repositories["Репозитории"]
        Models["Модели данных"]
        DBManager["Database<br/>Manager"]
    end
    
    subgraph "База данных"
        SQLite["SQLite<br/>Database"]
    end
    
    Desktop --> Services
    WebClient --> FastAPI
    FastAPI --> Auth
    FastAPI --> Middleware
    FastAPI --> Services
    Services --> DocPosting
    Services --> PrintForms
    Services --> Reports
    Services --> Repositories
    Repositories --> Models
    Repositories --> DBManager
    DBManager --> SQLite
    
    style Desktop fill:#e1f5ff
    style WebClient fill:#e1f5ff
    style FastAPI fill:#fff4e1
    style Services fill:#f0e1ff
    style Repositories fill:#e1ffe1
    style SQLite fill:#ffe1e1
```

## Компоненты системы

### 1. Клиентский слой

#### PyQt6 Desktop приложение
- Нативное десктопное приложение на Python
- Использует PyQt6 для UI
- Прямой доступ к бизнес-логике через сервисы
- Поддержка горячих клавиш в стиле 1С

#### Vue.js Web клиент
- SPA приложение на Vue 3 + TypeScript
- Использует Tailwind CSS для стилизации
- Взаимодействует с backend через REST API
- Адаптивный дизайн

### 2. API слой (FastAPI)

```mermaid
graph LR
    Client[Клиент] --> Router[Роутеры]
    Router --> Auth[Аутентификация]
    Router --> Endpoints[Endpoints]
    Endpoints --> Services[Сервисы]
    
    subgraph "Endpoints"
        RefEndpoints[References]
        DocEndpoints[Documents]
        RegEndpoints[Registers]
    end
```

Основные эндпоинты:
- `/api/auth/*` - аутентификация и авторизация
- `/api/references/*` - справочники
- `/api/documents/*` - документы (сметы, отчеты)
- `/api/registers/*` - регистры

### 3. Бизнес-логика

```mermaid
graph TB
    subgraph "Сервисы"
        AuthService[Auth Service]
        DocService[Document Service]
        PostingService[Posting Service]
        PrintService[Print Service]
        ReportService[Report Service]
    end
    
    subgraph "Функциональность"
        PostingService --> Register[Регистр<br/>накопления]
        PrintService --> PDF[PDF формы]
        PrintService --> Excel[Excel формы]
        ReportService --> Analytics[Аналитика]
    end
```

#### Ключевые сервисы:

1. **AuthService** - управление пользователями и правами доступа
2. **DocumentPostingService** - проведение документов
3. **PrintFormService** - генерация печатных форм
4. **ExcelImportService** - импорт из Excel
5. **DailyReportService** - работа с ежедневными отчетами

### 4. Слой данных

```mermaid
graph TB
    subgraph "Репозитории"
        RefRepo[Reference<br/>Repository]
        EstRepo[Estimate<br/>Repository]
        ReportRepo[Daily Report<br/>Repository]
        RegRepo[Register<br/>Repository]
    end
    
    subgraph "Database Manager"
        DBM[Database<br/>Manager]
        Connection[Connection<br/>Pool]
        Migrations[Миграции]
    end
    
    RefRepo --> DBM
    EstRepo --> DBM
    ReportRepo --> DBM
    RegRepo --> DBM
    DBM --> Connection
    DBM --> Migrations
```

## Поток данных

### Создание документа (Desktop)

```mermaid
sequenceDiagram
    participant User
    participant View
    participant Service
    participant Repository
    participant DB
    
    User->>View: Создать смету
    View->>Service: create_estimate(data)
    Service->>Service: Валидация
    Service->>Repository: save(estimate)
    Repository->>DB: INSERT
    DB-->>Repository: id
    Repository-->>Service: estimate
    Service-->>View: result
    View-->>User: Показать смету
```

### Проведение документа

```mermaid
sequenceDiagram
    participant User
    participant Service
    participant PostingService
    participant Repository
    participant Register
    participant DB
    
    User->>Service: post_document(id)
    Service->>PostingService: post(document)
    PostingService->>PostingService: Создать движения
    PostingService->>Register: write_records()
    Register->>DB: INSERT movements
    PostingService->>Repository: mark_posted()
    Repository->>DB: UPDATE is_posted
    DB-->>Service: success
    Service-->>User: Документ проведен
```

### API запрос (Web)

```mermaid
sequenceDiagram
    participant WebClient
    participant FastAPI
    participant Auth
    participant Service
    participant Repository
    participant DB
    
    WebClient->>FastAPI: GET /api/documents/estimates
    FastAPI->>Auth: verify_token()
    Auth-->>FastAPI: user
    FastAPI->>Service: get_estimates(user)
    Service->>Service: Фильтрация по правам
    Service->>Repository: find_all()
    Repository->>DB: SELECT
    DB-->>Repository: rows
    Repository-->>Service: estimates
    Service-->>FastAPI: filtered_estimates
    FastAPI-->>WebClient: JSON response
```

## Модель данных

### Иерархия сущностей

```mermaid
graph TB
    subgraph "Справочники"
        Persons[Физлица]
        Orgs[Организации]
        Counter[Контрагенты]
        Objects[Объекты]
        Works[Работы]
    end
    
    subgraph "Документы"
        Estimate[Смета]
        DailyReport[Ежедневный<br/>отчет]
    end
    
    subgraph "Регистры"
        WorkExec[Регистр<br/>выполнения работ]
    end
    
    Counter --> Estimate
    Objects --> Estimate
    Orgs --> Estimate
    Persons --> Estimate
    Works --> Estimate
    
    Estimate --> DailyReport
    Persons --> DailyReport
    Works --> DailyReport
    
    Estimate --> WorkExec
    DailyReport --> WorkExec
    Objects --> WorkExec
    Works --> WorkExec
```

## Паттерны проектирования

### 1. Repository Pattern
Абстракция доступа к данным через репозитории

### 2. Service Layer
Бизнес-логика инкапсулирована в сервисах

### 3. Singleton
DatabaseManager использует паттерн Singleton

### 4. Factory
Создание печатных форм через фабрику

### 5. Strategy
Различные стратегии печати (PDF, Excel)

## Безопасность

```mermaid
graph LR
    subgraph "Аутентификация"
        Login[Логин] --> JWT[JWT Token]
        JWT --> Verify[Проверка токена]
    end
    
    subgraph "Авторизация"
        Verify --> Role[Проверка роли]
        Role --> Filter[Фильтрация данных]
    end
    
    subgraph "Роли"
        Admin[Admin<br/>Полный доступ]
        Foreman[Foreman<br/>Свои отчеты]
        Executor[Executor<br/>Назначенные отчеты]
    end
```

### Уровни доступа:

1. **Admin** - полный доступ ко всем данным
2. **Foreman** - доступ к своим ежедневным отчетам
3. **Executor** - доступ к отчетам, где назначен исполнителем

## Масштабируемость

### Текущая архитектура
- Однопользовательская SQLite база (Desktop)
- Многопользовательский API (Web)

### Возможности расширения
- Миграция на PostgreSQL/MySQL
- Кэширование (Redis)
- Очереди задач (Celery)
- Микросервисная архитектура

## Технологический стек

### Backend
- Python 3.8+
- FastAPI (Web API)
- PyQt6 (Desktop UI)
- SQLite (Database)
- Pydantic (Validation)
- JWT (Authentication)

### Frontend
- Vue 3 (Framework)
- TypeScript (Language)
- Tailwind CSS (Styling)
- Vite (Build tool)

### Печатные формы
- ReportLab (PDF)
- OpenPyXL (Excel)

## Диаграмма развертывания

```mermaid
graph TB
    subgraph "Пользовательская машина"
        DesktopApp[Desktop<br/>Приложение]
        Browser[Web<br/>Браузер]
    end
    
    subgraph "Сервер приложений"
        WebServer[Web Server<br/>Nginx/Apache]
        APIServer[FastAPI<br/>Server]
        StaticFiles[Static Files<br/>Vue Build]
    end
    
    subgraph "База данных"
        LocalDB[SQLite<br/>Local]
        ServerDB[SQLite<br/>Server]
    end
    
    DesktopApp --> LocalDB
    Browser --> WebServer
    WebServer --> StaticFiles
    WebServer --> APIServer
    APIServer --> ServerDB
```

## Производительность

### Оптимизации:
- Индексы на часто используемых полях
- Ленивая загрузка связанных данных
- Пагинация списков
- Кэширование справочников
- Batch операции для массовых изменений

### Метрики:
- Время загрузки списка документов: < 100ms
- Время создания документа: < 50ms
- Время проведения документа: < 200ms
- Время генерации печатной формы: < 1s
