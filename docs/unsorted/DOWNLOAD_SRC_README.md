# Скрипты для скачивания файлов src с GitHub

Два скрипта для скачивания файлов из папки `src` репозитория GitHub:
- `download_src_files.bat` - Windows batch скрипт
- `download_src_files.py` - Python скрипт (кроссплатформенный)

## Использование

### Windows Batch скрипт

**Скачать в текущую папку (создаст папку `src`):**
```cmd
download_src_files.bat
```

**Скачать в указанную папку:**
```cmd
download_src_files.bat C:\MyProject\src
```

**Требования:**
- Windows 10/11 (curl встроен)
- PowerShell

### Python скрипт

**Скачать в текущую папку (создаст папку `src`):**
```cmd
python download_src_files.py
```

**Скачать в указанную папку:**
```cmd
python download_src_files.py C:\MyProject\src
```

**Требования:**
- Python 3.6+
- Библиотека `requests`:
  ```cmd
  pip install requests
  ```

## Особенности

### Batch скрипт
- ✅ Не требует установки Python
- ✅ Использует встроенные инструменты Windows
- ✅ Простой и быстрый
- ❌ Скачивает только файлы из корня папки `src` (не рекурсивно)
- ❌ Только для Windows

### Python скрипт
- ✅ Кроссплатформенный (Windows, Linux, macOS)
- ✅ Рекурсивное скачивание (включая подпапки)
- ✅ Показывает прогресс и статистику
- ✅ Проверяет лимиты GitHub API
- ✅ Более надежная обработка ошибок
- ❌ Требует установки Python и библиотеки requests

## Настройка

Если нужно скачать из другого репозитория или ветки, отредактируйте переменные в начале скрипта:

**В batch скрипте:**
```batch
set REPO_OWNER=DyhanieMatkoy
set REPO_NAME=Erection
set BRANCH=main
set SOURCE_PATH=src
```

**В Python скрипте:**
```python
REPO_OWNER = "DyhanieMatkoy"
REPO_NAME = "Erection"
BRANCH = "main"
SOURCE_PATH = "src"
```

## Примеры использования

### Обновление локальных файлов src
```cmd
# Скачать в текущую папку src
download_src_files.bat

# Или с Python
python download_src_files.py
```

### Скачивание в другую папку
```cmd
# Batch
download_src_files.bat D:\Projects\Erection\src

# Python
python download_src_files.py D:\Projects\Erection\src
```

### Скачивание с последующей установкой
```cmd
# 1. Скачать файлы
python download_src_files.py

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить приложение
python main.py
```

## Устранение неполадок

### Ошибка "curl не найден" (Batch)
- Убедитесь что используете Windows 10/11
- Проверьте что curl доступен: `curl --version`

### Ошибка "requests не найден" (Python)
```cmd
pip install requests
```

### Ошибка "GitHub API rate limit"
- GitHub API имеет лимит 60 запросов в час для неавторизованных пользователей
- Подождите час или используйте GitHub токен для увеличения лимита

### Ошибка доступа к папке
- Запустите скрипт от имени администратора
- Или укажите папку в которой у вас есть права записи

## Рекомендации

- **Для быстрого скачивания без подпапок**: используйте batch скрипт
- **Для полного скачивания со всеми подпапками**: используйте Python скрипт
- **Для автоматизации**: используйте Python скрипт в CI/CD пайплайнах
