# Руководство по настройке синхронизации для администраторов

## 📋 Обзор

Данное руководство предназначено для системных администраторов, которые настраивают и поддерживают систему синхронизации между десктопными клиентами и сервером CTM.

## 🎯 Архитектура синхронизации

### Компоненты системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop       │    │     Server      │    │   Desktop       │
│   Client 1      │◄──►│   (FastAPI)     │◄──►│   Client 2      │
│                 │    │                 │    │                 │
│ • Local SQLite  │    │ • Central DB    │    │ • Local SQLite  │
│ • Sync Service  │    │ • Sync API      │    │ • Sync Service  │
│ • Conflict UI   │    │ • Node Registry │    │ • Conflict UI   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Принципы работы

1. **Offline-First**: Клиенты работают автономно с локальной базой данных
2. **Периодическая синхронизация**: Автоматическая отправка изменений на сервер
3. **Конфликт-резолюция**: Автоматическое и ручное разрешение конфликтов
4. **Пакетная передача**: Эффективная передача данных с сжатием

## 🔧 Настройка сервера

### 1. Требования к серверу

**Минимальные требования:**
- OS: Windows Server 2016+ / Linux Ubuntu 18.04+
- RAM: 4GB (рекомендуется 8GB+)
- CPU: 2 ядра (рекомендуется 4+)
- Диск: 20GB свободного места
- Сеть: 100Mbps+ (рекомендуется 1Gbps)

**База данных:**
- SQLite: для тестирования и малых развертываний (<10 клиентов)
- MS SQL Server: для production (10+ клиентов)
- PostgreSQL: альтернатива для Linux-серверов

### 2. Установка серверной части

#### Шаг 1: Подготовка окружения

```bash
# Клонирование репозитория
git clone <repository-url>
cd construction-time-management

# Установка зависимостей
pip install -r requirements.txt

# Создание базы данных
python -c "from src.data.database_manager import DatabaseManager; dm = DatabaseManager(); dm.initialize('construction.db')"
```

#### Шаг 2: Настройка конфигурации

Создайте файл `env.ini`:

```ini
[Database]
type = sqlite
path = construction.db
# Для MS SQL Server:
# type = mssql
# server = localhost
# database = construction_db
# username = ctm_user
# password = secure_password

[Server]
host = 0.0.0.0
port = 8000
debug = false

[Sync]
enabled = true
max_packet_size = 1048576  # 1MB
compression_enabled = true
conflict_retention_days = 30
node_timeout_minutes = 60
```

#### Шаг 3: Запуск сервера

```bash
# Для разработки
python api/main.py

# Для production (с Gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000
```

### 3. Настройка базы данных для синхронизации

#### Создание пользователя синхронизации (MS SQL Server)

```sql
-- Создание логина и пользователя
CREATE LOGIN ctm_sync_user WITH PASSWORD = 'SecurePassword123!';
USE construction_db;
CREATE USER ctm_sync_user FOR LOGIN ctm_sync_user;

-- Предоставление необходимых прав
ALTER ROLE db_datareader ADD MEMBER ctm_sync_user;
ALTER ROLE db_datawriter ADD MEMBER ctm_sync_user;
ALTER ROLE db_ddladmin ADD MEMBER ctm_sync_user;

-- Права на выполнение процедур синхронизации
GRANT EXECUTE ON SCHEMA::dbo TO ctm_sync_user;
```

#### Настройка индексов для производительности

```sql
-- Индексы для таблиц синхронизации
CREATE INDEX IX_sync_changes_node_timestamp ON sync_changes (target_node_id, timestamp);
CREATE INDEX IX_sync_changes_entity ON sync_changes (entity_type, entity_uuid);
CREATE INDEX IX_sync_conflicts_status ON sync_conflicts (status, arrival_time);
CREATE INDEX IX_sync_nodes_last_seen ON sync_nodes (last_seen_at);

-- Индексы для основных таблиц
CREATE INDEX IX_estimates_updated_at ON estimates (updated_at);
CREATE INDEX IX_daily_reports_updated_at ON daily_reports (updated_at);
CREATE INDEX IX_timesheets_updated_at ON timesheets (updated_at);
```

## 🖥️ Настройка клиентов

### 1. Развертывание десктопного клиента

#### Автоматическое развертывание

Создайте скрипт `deploy_client.bat`:

```batch
@echo off
echo Развертывание CTM Desktop Client...

REM Копирование файлов
xcopy /E /I /Y "\\server\ctm_dist\*" "C:\CTM\"

REM Создание конфигурации синхронизации
echo [Sync] > "C:\CTM\env.ini"
echo enabled=true >> "C:\CTM\env.ini"
echo server_url=http://your-server:8000 >> "C:\CTM\env.ini"
echo node_code=%COMPUTERNAME%-CLIENT >> "C:\CTM\env.ini"
echo auto_sync=true >> "C:\CTM\env.ini"
echo sync_interval=300 >> "C:\CTM\env.ini"

REM Создание ярлыка
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\CTM.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "C:\CTM\main.exe" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo Развертывание завершено!
pause
```

#### Ручная настройка

1. **Установка приложения** на рабочую станцию
2. **Первый запуск** - вход под admin/admin
3. **Настройка синхронизации:**
   - Меню "Настройки" → "Настройки синхронизации"
   - URL сервера: `http://your-server:8000`
   - Код узла: уникальный для каждого клиента (например: `OFFICE-PC-01`)
   - Нажать "Зарегистрировать узел"
   - Включить автоматическую синхронизацию

### 2. Конфигурация по умолчанию для клиентов

Создайте шаблон `env.ini` для клиентов:

```ini
[Sync]
enabled = true
server_url = http://your-server.company.com:8000
node_code = %COMPUTERNAME%-CLIENT
auto_sync = true
sync_interval = 300
compression_enabled = true
conflict_resolution = server_wins
version_history = true
debug_logging = false
batch_size = 100
log_level = INFO

[Auth]
# Оставьте пустым для ручного ввода при первом запуске
login = 
password = 

[PrintForms]
template_path = PrnForms
output_path = %USERPROFILE%\Documents\CTM_Reports
```

## 🔐 Управление узлами и безопасность

### 1. Регистрация и управление узлами

#### Просмотр зарегистрированных узлов

```python
# Скрипт для администратора: list_nodes.py
from src.data.database_manager import DatabaseManager
from src.data.sync_manager import get_sync_manager

db_manager = DatabaseManager()
db_manager.initialize("construction.db")
sync_manager = get_sync_manager(db_manager)

nodes = sync_manager.get_all_nodes()
print("Зарегистрированные узлы:")
print("-" * 50)
for node in nodes:
    print(f"ID: {node.id}")
    print(f"Код: {node.code}")
    print(f"Название: {node.name}")
    print(f"Последняя активность: {node.last_seen_at}")
    print(f"Статус: {'Активен' if node.is_active else 'Неактивен'}")
    print("-" * 50)
```

#### Деактивация узла

```python
# Скрипт: deactivate_node.py
import sys
from src.data.database_manager import DatabaseManager
from src.data.sync_manager import get_sync_manager

if len(sys.argv) != 2:
    print("Использование: python deactivate_node.py <node_code>")
    sys.exit(1)

node_code = sys.argv[1]

db_manager = DatabaseManager()
db_manager.initialize("construction.db")
sync_manager = get_sync_manager(db_manager)

success = sync_manager.deactivate_node(node_code)
if success:
    print(f"Узел {node_code} деактивирован")
else:
    print(f"Не удалось деактивировать узел {node_code}")
```

### 2. Мониторинг синхронизации

#### Скрипт мониторинга

```python
# monitor_sync.py
import time
from datetime import datetime, timedelta
from src.data.database_manager import DatabaseManager
from src.data.sync_manager import get_sync_manager

def monitor_sync_status():
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    sync_manager = get_sync_manager(db_manager)
    
    print(f"Мониторинг синхронизации - {datetime.now()}")
    print("=" * 60)
    
    # Активные узлы
    nodes = sync_manager.get_all_nodes()
    active_nodes = [n for n in nodes if n.is_active]
    
    print(f"Активных узлов: {len(active_nodes)}")
    
    # Узлы без активности более 1 часа
    inactive_threshold = datetime.now() - timedelta(hours=1)
    inactive_nodes = [n for n in active_nodes 
                     if n.last_seen_at < inactive_threshold]
    
    if inactive_nodes:
        print(f"⚠️ Узлы без активности более 1 часа:")
        for node in inactive_nodes:
            print(f"   - {node.code} (последняя активность: {node.last_seen_at})")
    
    # Неразрешенные конфликты
    conflicts = sync_manager.get_unresolved_conflicts()
    if conflicts:
        print(f"⚠️ Неразрешенных конфликтов: {len(conflicts)}")
    
    # Ошибки синхронизации за последние 24 часа
    error_threshold = datetime.now() - timedelta(hours=24)
    # Здесь можно добавить запрос к логам ошибок
    
    print("=" * 60)

if __name__ == "__main__":
    monitor_sync_status()
```

### 3. Резервное копирование данных синхронизации

#### Скрипт резервного копирования

```python
# backup_sync_data.py
import os
import shutil
import json
from datetime import datetime
from src.data.database_manager import DatabaseManager
from src.data.sync_manager import get_sync_manager

def backup_sync_data():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"sync_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    sync_manager = get_sync_manager(db_manager)
    
    # Экспорт узлов
    nodes = sync_manager.get_all_nodes()
    nodes_data = []
    for node in nodes:
        nodes_data.append({
            'id': node.id,
            'code': node.code,
            'name': node.name,
            'description': node.description,
            'is_active': node.is_active,
            'last_seen_at': node.last_seen_at.isoformat() if node.last_seen_at else None
        })
    
    with open(os.path.join(backup_dir, "nodes.json"), 'w', encoding='utf-8') as f:
        json.dump(nodes_data, f, indent=2, ensure_ascii=False)
    
    # Копирование базы данных
    shutil.copy2("construction.db", os.path.join(backup_dir, "construction.db"))
    
    # Копирование конфигурации
    if os.path.exists("env.ini"):
        shutil.copy2("env.ini", os.path.join(backup_dir, "env.ini"))
    
    print(f"Резервная копия создана: {backup_dir}")
    return backup_dir

if __name__ == "__main__":
    backup_sync_data()
```

## 📊 Мониторинг и диагностика

### 1. Ключевые метрики для мониторинга

#### Метрики производительности
- **Время отклика API синхронизации** (< 1 сек)
- **Размер очереди синхронизации** (< 1000 записей)
- **Частота конфликтов** (< 5% от операций)
- **Время разрешения конфликтов** (< 24 часа)

#### Метрики доступности
- **Активность узлов** (последняя активность < 1 часа)
- **Успешность синхронизации** (> 95%)
- **Доступность сервера** (> 99.5%)

### 2. Настройка логирования

#### Конфигурация логирования сервера

```python
# logging_config.py
import logging
import logging.handlers
import os

def setup_sync_logging():
    # Создание директории для логов
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Настройка форматирования
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Основной лог синхронизации
    sync_logger = logging.getLogger('sync')
    sync_logger.setLevel(logging.INFO)
    
    # Ротация логов (10MB, 5 файлов)
    sync_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'sync.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    sync_handler.setFormatter(formatter)
    sync_logger.addHandler(sync_handler)
    
    # Лог ошибок
    error_logger = logging.getLogger('sync.errors')
    error_logger.setLevel(logging.ERROR)
    
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'sync_errors.log'),
        maxBytes=5*1024*1024,
        backupCount=3
    )
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    
    return sync_logger, error_logger
```

### 3. Диагностические скрипты

#### Проверка состояния синхронизации

```python
# diagnose_sync.py
from src.data.database_manager import DatabaseManager
from src.data.sync_manager import get_sync_manager
from datetime import datetime, timedelta

def diagnose_sync_health():
    print("🔍 Диагностика состояния синхронизации")
    print("=" * 50)
    
    db_manager = DatabaseManager()
    db_manager.initialize("construction.db")
    sync_manager = get_sync_manager(db_manager)
    
    # 1. Проверка узлов
    nodes = sync_manager.get_all_nodes()
    print(f"📊 Всего узлов: {len(nodes)}")
    
    active_nodes = [n for n in nodes if n.is_active]
    print(f"✅ Активных узлов: {len(active_nodes)}")
    
    # 2. Проверка конфликтов
    conflicts = sync_manager.get_unresolved_conflicts()
    print(f"⚠️ Неразрешенных конфликтов: {len(conflicts)}")
    
    if conflicts:
        print("   Типы конфликтов:")
        conflict_types = {}
        for conflict in conflicts:
            entity_type = conflict.entity_type
            conflict_types[entity_type] = conflict_types.get(entity_type, 0) + 1
        
        for entity_type, count in conflict_types.items():
            print(f"   - {entity_type}: {count}")
    
    # 3. Проверка очереди синхронизации
    total_pending = 0
    for node in active_nodes:
        pending = sync_manager.get_pending_changes(node.id, limit=10000)
        node_pending = len(pending)
        total_pending += node_pending
        
        if node_pending > 100:
            print(f"⚠️ Узел {node.code}: {node_pending} ожидающих изменений")
    
    print(f"📤 Всего ожидающих изменений: {total_pending}")
    
    # 4. Проверка производительности базы данных
    # Здесь можно добавить запросы для проверки производительности
    
    print("=" * 50)
    print("✅ Диагностика завершена")

if __name__ == "__main__":
    diagnose_sync_health()
```

## 🚨 Устранение неполадок

### Частые проблемы и решения

#### 1. Узел не может зарегистрироваться

**Симптомы:**
- Ошибка "Failed to register node" в логах клиента
- HTTP 500 или connection timeout

**Решения:**
1. Проверьте доступность сервера: `telnet server-ip 8000`
2. Проверьте firewall на сервере
3. Убедитесь, что сервис запущен: `ps aux | grep python`
4. Проверьте логи сервера на ошибки

#### 2. Синхронизация не работает

**Симптомы:**
- Изменения не передаются между узлами
- Статус "Офлайн" в клиенте

**Решения:**
1. Проверьте настройки синхронизации в `env.ini`
2. Убедитесь, что узел зарегистрирован
3. Проверьте токен аутентификации
4. Запустите диагностику сети в клиенте

#### 3. Множественные конфликты

**Симптомы:**
- Большое количество неразрешенных конфликтов
- Медленная синхронизация

**Решения:**
1. Проверьте синхронизацию времени на всех узлах
2. Настройте стратегию разрешения конфликтов
3. Обучите пользователей избегать одновременного редактирования
4. Используйте массовые операции для разрешения конфликтов

#### 4. Проблемы производительности

**Симптомы:**
- Медленная синхронизация
- Высокая нагрузка на сервер

**Решения:**
1. Увеличьте интервал синхронизации
2. Уменьшите размер пакета
3. Настройте индексы базы данных
4. Рассмотрите масштабирование сервера

## 📋 Чек-лист развертывания

### Подготовка к развертыванию

- [ ] Сервер настроен и протестирован
- [ ] База данных создана и проиндексирована
- [ ] Резервное копирование настроено
- [ ] Мониторинг настроен
- [ ] Логирование настроено
- [ ] Firewall настроен
- [ ] SSL-сертификаты установлены (для production)

### Развертывание клиентов

- [ ] Шаблон конфигурации подготовлен
- [ ] Скрипты развертывания протестированы
- [ ] Пользователи обучены
- [ ] Документация предоставлена
- [ ] Техническая поддержка настроена

### После развертывания

- [ ] Все узлы зарегистрированы
- [ ] Синхронизация работает
- [ ] Конфликты разрешаются
- [ ] Производительность в норме
- [ ] Мониторинг активен
- [ ] Резервные копии создаются

## 📞 Техническая поддержка

### Сбор информации для поддержки

При обращении в техническую поддержку предоставьте:

1. **Логи сервера** (`logs/sync.log`, `logs/sync_errors.log`)
2. **Конфигурацию** (`env.ini` без паролей)
3. **Результат диагностики** (запустите `diagnose_sync.py`)
4. **Описание проблемы** с шагами воспроизведения
5. **Информацию об окружении** (ОС, версия приложения)

### Контакты

- **Техническая поддержка:** [support@company.com]
- **Экстренная поддержка:** [emergency@company.com]
- **Документация:** [docs.company.com/ctm]

---

**Примечание:** Данное руководство предполагает базовые знания администрирования Windows/Linux серверов и работы с базами данных.