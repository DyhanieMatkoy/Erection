# Быстрый старт: Desktop приложение по сети

## Для администратора (настройка сервера)

### 1. Установите PostgreSQL на сервере
```bash
# Скачайте и установите PostgreSQL с официального сайта
# https://www.postgresql.org/download/
```

### 2. Мигрируйте данные в PostgreSQL
```cmd
migrate_to_postgresql.bat
```

### 3. Настройте сетевой доступ
Отредактируйте файлы конфигурации PostgreSQL:

**postgresql.conf:**
```
listen_addresses = '*'
port = 5432
```

**pg_hba.conf:**
```
host    all    all    0.0.0.0/0    md5
```

### 4. Откройте порт в брандмауэре
```cmd
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=TCP localport=5432
```

### 5. Перезапустите PostgreSQL
```cmd
net stop postgresql-x64-14
net start postgresql-x64-14
```

## Для пользователя (настройка клиента)

### 1. Скопируйте файлы приложения
Скопируйте всю папку проекта на свой компьютер.

### 2. Установите зависимости
```cmd
pip install -r requirements.txt
```

### 3. Настройте подключение к базе данных
Запустите мастер настройки:
```cmd
setup_network_client.bat
```

Или создайте файл `env.ini` вручную:
```ini
[database]
type = postgresql
host = IP_АДРЕС_СЕРВЕРА
port = 5432
database = construction
username = postgres
password = ВАШ_ПАРОЛЬ
```

### 4. Запустите приложение
```cmd
start_desktop.bat
```

## Устранение проблем

### Ошибка подключения к базе данных
- Проверьте IP-адрес сервера
- Убедитесь, что PostgreSQL запущен на сервере
- Проверьте настройки брандмауэра
- Проверьте правильность логина и пароля

### Ошибки Python
- Установите зависимости: `pip install -r requirements.txt`
- Проверьте версию Python (требуется 3.8+)

### Медленная работа
- Используйте PostgreSQL вместо SQLite
- Проверьте качество сетевого соединения
- Рассмотрите использование VPN для стабильного соединения

## Контакты
Для получения помощи обратитесь к администратору системы.