# Руководство по автоматической очистке тестовых данных

## Обзор

Система автоматической очистки тестовых данных предназначена для удаления временных файлов и папок, создаваемых во время выполнения тестов, включая папки с Unicode символами, которые могут создаваться property-based тестами (Hypothesis).

## Что очищается

### 1. Папки с Unicode символами
- Папки с именами, содержащими не-ASCII символы
- Короткие папки с цифровыми именами (например, "0", "1")
- Вложенные структуры таких папок

### 2. Временные файлы
- Файлы с расширениями: `.db`, `.tmp`, `.temp`, `.cache`, `.log`
- Файлы с паттернами: `tmp*`, `test_*.db`, `*_test.db`
- Временные файлы Hypothesis в `.hypothesis/tmp/`

### 3. Кэш файлы
- Папки `__pycache__` во всех директориях
- Кэш pytest (`.pytest_cache`)
- Кэш Hypothesis (`.hypothesis`)

## Автоматическая очистка

### Настройка
Автоматическая очистка настроена в файле `conftest.py` и выполняется:

1. **После каждого теста** - удаление временных файлов
2. **После всех тестов** - полная очистка всех тестовых данных

### Использование
Автоматическая очистка работает автоматически при запуске pytest:

```bash
# Обычный запуск тестов с автоматической очисткой
python -m pytest

# Запуск конкретного теста
python -m pytest test_config_validator.py -v
```

## Ручная очистка

### Основные команды

```bash
# Предварительный просмотр (что будет удалено)
python test_cleanup_manager.py --dry-run

# Выполнить очистку
python test_cleanup_manager.py

# Настроить автоматическую очистку
python test_cleanup_manager.py --setup-auto
```

### Программное использование

```python
from test_cleanup_manager import TestCleanupManager

# Создание менеджера очистки
cleanup_manager = TestCleanupManager()

# Поиск тестовых данных
unicode_dirs = cleanup_manager.find_unicode_test_dirs()
temp_files = cleanup_manager.find_temp_files()

# Выполнение очистки
results = cleanup_manager.cleanup_all()

# Предварительный просмотр
results = cleanup_manager.cleanup_all(dry_run=True)
```

## Защищенные директории

Следующие директории **НЕ** удаляются системой очистки:

- `.git`, `.kiro`, `.vscode`, `.trae`
- `alembic`, `api`, `archives`, `config`
- `dbf_importer`, `deploy-to-prod`, `desktop_package`
- `dist`, `docs`, `examples`, `fonts`
- `migration_backups`, `migration_results`, `migrations`
- `node_modules`, `password_fix_deployment`
- `PrnForms`, `run`, `scripts`, `src`, `test`, `web-client`
- `test_configs`, `test_databases`, `test_logs`
- `test_migrations`, `test_reports`, `validation_results`
- `api_test_results`

## Конфигурация .gitignore

В файл `.gitignore` добавлены правила для исключения тестовых данных:

```gitignore
# Test cleanup - Unicode test directories and temporary files
[^a-zA-Z0-9._-]*
*[^\x00-\x7F]*
tmp*
*.tmp
*.temp
test_*.db
*_test.db

# Hypothesis temporary files
.hypothesis/tmp/
.hypothesis/examples/

# Temporary test databases and files
test_databases/tmp*
test_logs/tmp*
test_reports/tmp*
```

## Логирование

Система очистки ведет подробные логи:

```
2026-01-26 21:46:38,186 - TestCleanupManager - INFO - Начинаем очистку тестовых данных...
2026-01-26 21:46:38,189 - TestCleanupManager - INFO - Найдена тестовая директория: æģĺĘę
2026-01-26 21:46:59,585 - TestCleanupManager - INFO - Удалена директория: æģĺĘę
2026-01-26 21:47:00,335 - TestCleanupManager - INFO - Очистка завершена!
```

## Безопасность

### Проверки безопасности
- Система проверяет защищенные директории перед удалением
- Используется белый список для предотвращения случайного удаления важных файлов
- Все операции логируются для отслеживания

### Восстановление
Если случайно удалены важные файлы:
1. Проверьте логи системы очистки
2. Восстановите из системы контроля версий (git)
3. Восстановите из резервных копий

## Настройка для разработчиков

### Добавление новых паттернов очистки

```python
# В test_cleanup_manager.py
self.cleanup_extensions.add('.new_extension')
self.temp_patterns.append(r'^new_pattern_.*$')
```

### Добавление защищенных директорий

```python
# В test_cleanup_manager.py
self.protected_dirs.add('new_protected_dir')
```

### Настройка Hypothesis

В `conftest.py` настроены профили Hypothesis для ограничения генерации Unicode символов:

```python
settings.register_profile("dev", max_examples=10, deadline=None)
settings.load_profile("dev")
```

## Устранение неполадок

### Проблема: Файлы не удаляются
**Решение:** Проверьте права доступа и убедитесь, что файлы не используются другими процессами.

### Проблема: Важные файлы удалены
**Решение:** Проверьте настройки `protected_dirs` и восстановите из git.

### Проблема: Слишком много временных файлов
**Решение:** Запустите ручную очистку: `python test_cleanup_manager.py`

## Мониторинг

### Проверка эффективности очистки

```bash
# Проверка размера временных данных
du -sh test_databases/ test_logs/ test_reports/

# Поиск файлов с Unicode именами
find . -name "*[^[:ascii:]]*" -type d
```

### Автоматизация мониторинга

Можно добавить в CI/CD pipeline:

```bash
# В скрипте развертывания
python test_cleanup_manager.py --dry-run
if [ $? -eq 0 ]; then
    echo "Cleanup check passed"
else
    echo "Cleanup issues detected"
    exit 1
fi
```

## Заключение

Система автоматической очистки обеспечивает:
- Автоматическое удаление тестовых данных
- Защиту важных файлов и директорий
- Подробное логирование операций
- Гибкую настройку паттернов очистки
- Интеграцию с pytest и Hypothesis

Система работает автоматически и не требует вмешательства разработчика в обычных условиях.

## Обновления системы

### Версия 1.1 (26.01.2026):
- ✅ **ИСПРАВЛЕНА КРИТИЧЕСКАЯ ПРОБЛЕМА**: Система теперь правильно обнаруживает одиночные буквы (L, A, Z и т.д.)
- ✅ Улучшена логика определения тестовых папок в методе `is_unicode_test_dir()`
- ✅ Добавлена поддержка коротких случайных имен (AB, X1, 99 и т.д.)
- ✅ Расширен белый список защищенных папок
- ✅ Успешно удалена проблемная папка `L/` из корня проекта

### Что было исправлено:
**Проблема**: Папки с одиночными буквами (например, `L/`) не обнаруживались системой очистки.

**Причина**: Метод `is_unicode_test_dir()` проверял только цифровые папки (`dir_name.isdigit()`) и Unicode символы, но пропускал одиночные ASCII буквы.

**Решение**: Добавлена проверка для:
- Цифровых папок: `0`, `1`, `123`
- Одиночных букв: `A`, `B`, `L`, `Z`
- Коротких случайных имен: `AB`, `X1`, `99` (до 2 символов)

### Код исправления:
```python
def is_unicode_test_dir(self, dir_name: str) -> bool:
    try:
        dir_name.encode('ascii')
        if len(dir_name) <= 3:
            # Цифровые папки
            if dir_name.isdigit():
                return True
            # Одиночные буквы
            if len(dir_name) == 1 and dir_name.isalpha():
                return True
            # Короткие случайные имена
            if len(dir_name) <= 2 and dir_name.isalnum():
                return True
        return False
    except UnicodeEncodeError:
        return True
```

### Планируемые улучшения:
- Поддержка конфигурационных файлов для настройки
- Интеграция с системой мониторинга
- Статистика использования дискового пространства
- Более гибкие правила определения тестовых артефактов