# Финальная архитектура конфигураций

## Проблема
Десктопное приложение устанавливается отдельно на каждый клиентский компьютер, поэтому нужна особая система конфигураций.

## Решение: Трехуровневая система конфигураций

### 1. Серверные компоненты (Backend + Frontend)

#### Development (разработка):
```
config/
├── server/
│   ├── development/
│   │   ├── api.env          # API настройки для разработки
│   │   ├── web-client.env   # Frontend настройки для разработки
│   │   └── database.ini     # База данных для разработки
│   └── production/
│       ├── api.env          # API настройки для продакшена
│       ├── web-client.env   # Frontend настройки для продакшена
│       └── database.ini     # База данных для продакшена
```

#### Учетные данные:
- **Development:** admin/admin, простые настройки
- **Production:** admin/сложный_пароль, безопасные настройки

### 2. Десктопное приложение

#### Для разработчика (при упаковке):
```
desktop_configs/
├── development/
│   └── env.ini              # Настройки для тестирования
├── client_template/
│   └── env.ini              # Шаблон для клиентов
└── production_template/
    └── env.ini              # Шаблон для продакшн клиентов
```

#### Для клиента (после установки):
```
%PROGRAMFILES%/ConstructionTimeManagement/
├── ConstructionTimeManagement.exe
├── env.ini                  # Конфигурация клиента
├── construction.db          # Локальная база данных
└── config/
    ├── server_connection.ini # Настройки подключения к серверу
    └── user_preferences.ini  # Пользовательские настройки
```

### 3. Конфигурационные шаблоны

#### Шаблон для клиента (client_template/env.ini):
```ini
[Auth]
# Учетные данные по умолчанию (ОБЯЗАТЕЛЬНО СМЕНИТЬ!)
login = admin
password = admin

[Database]
type = sqlite
path = construction.db
backup_enabled = true
backup_interval_hours = 24

[Sync]
enabled = true
server_url = https://your-company-server.com/api
node_code = DESKTOP-CLIENT-{COMPUTER_NAME}
auto_sync = true
sync_interval = 300
compression_enabled = true

[Application]
name = Система управления рабочим временем
version = 1.0.0
debug = false
first_run = true

[UI]
theme = default
language = ru
font_size = 10
```

#### Шаблон для продакшн сервера (server/production/api.env):
```env
# Production API Configuration
DATABASE_PATH=construction_prod.db
JWT_SECRET_KEY=GENERATED_SECURE_KEY_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8

# CORS - Production domains only
CORS_ORIGINS=https://your-company.com,https://app.your-company.com

# Sync Configuration
SYNC_ENABLED=true
SYNC_DEBUG_LOGGING=false
SYNC_LOG_LEVEL=INFO

# Database Configuration
DATABASE_TYPE=postgresql
DATABASE_HOST=db-server
DATABASE_PORT=5432
DATABASE_NAME=construction_prod
DATABASE_USER=construction_user
DATABASE_PASSWORD=GENERATED_DB_PASSWORD
```

## 4. Процесс развертывания

### Для разработчика:

#### Разработка:
```bash
# Запуск для разработки
./start_dev.bat --config=development

# Упаковка десктопного приложения
python package_desktop.py --template=client_template
```

#### Продакшн:
```bash
# Развертывание сервера
./deploy_server.bat --config=production

# Упаковка десктопного приложения для клиентов
python package_desktop.py --template=production_template --server-url=https://your-server.com
```

### Для клиента:

#### Установка:
1. Получает архив `ConstructionTimeManagement_Desktop_v1.0.zip`
2. Запускает `install.bat`
3. При первом запуске система предлагает:
   - Сменить пароль администратора
   - Настроить подключение к серверу
   - Выбрать режим работы (автономный/с синхронизацией)

#### Настройка подключения к серверу:
```ini
[Server]
url = https://your-company-server.com/api
enabled = true
auto_connect = true
timeout = 30

[Credentials]
# Эти данные вводит пользователь при первом запуске
username = 
password = 
remember_password = false
```

## 5. Управление паролями

### Скрипт для управления паролями:
```python
# manage_passwords.py
python manage_passwords.py --component=server --env=production --generate-admin
python manage_passwords.py --component=desktop --reset-admin --password=new_password
python manage_passwords.py --component=server --env=development --reset-all
```

### Автоматическая генерация для продакшена:
- JWT секреты генерируются автоматически
- Пароли БД генерируются автоматически  
- Пароль админа генерируется и сохраняется в безопасном месте

## 6. Безопасность по окружениям

### Development:
- Простые пароли (admin/admin)
- Отладка включена
- CORS разрешен для localhost
- HTTP допустим

### Production Server:
- Сложные сгенерированные пароли
- Отладка отключена
- CORS только для конкретных доменов
- Только HTTPS

### Production Desktop:
- Пароль по умолчанию admin/admin (пользователь ДОЛЖЕН сменить)
- Подключение только по HTTPS
- Автоматическое резервное копирование
- Логирование ошибок

## 7. Преимущества такой архитектуры

### Для разработчика:
- Простая разработка с admin/admin
- Легкое переключение между окружениями
- Автоматическая генерация безопасных настроек для продакшена

### Для системного администратора:
- Централизованное управление серверными настройками
- Безопасные настройки по умолчанию для продакшена
- Простое развертывание

### Для клиента:
- Простая установка десктопного приложения
- Автоматическая настройка при первом запуске
- Возможность работы автономно или с синхронизацией

### Для безопасности:
- Четкое разделение между dev и prod
- Принудительная смена паролей в продакшене
- Безопасные настройки по умолчанию

## 8. Миграция существующих установок

Для обновления существующих установок:
1. Скрипт миграции конфигураций
2. Автоматическое обновление настроек
3. Сохранение пользовательских данных
4. Уведомление о необходимости смены паролей