# Шаги по устранению проблемы "Смета открылась 1 раз, затем перестала"

## Текущий статус

✅ Все автоматические тесты проходят успешно:
- `test_forms.py` - 9/9 тестов пройдено
- `test_estimate_open.py` - множественное открытие работает
- `test_main_window_flow.py` - поток главного окна работает

✅ Все `row.get()` исправлены на правильный синтаксис

## Для воспроизведения проблемы

1. **Запустите приложение с логированием:**
   ```bash
   run_with_logging.bat
   ```

2. **Выполните следующие действия:**
   - Откройте список смет (меню "Документы" → "Сметы")
   - Дважды кликните на любую смету (или нажмите Enter)
   - Закройте форму сметы
   - Попробуйте открыть ту же смету снова
   
3. **Если возникает ошибка:**
   - Скопируйте текст ошибки из консоли
   - Сделайте скриншот окна с ошибкой
   - Запишите точную последовательность действий

## Возможные сценарии

### Сценарий 1: Ошибка "row.get()"

**Симптомы:**
```
AttributeError: 'sqlite3.Row' object has no attribute 'get'
```

**Решение:**
```bash
# Очистить кэш
clear_cache.bat

# Запустить тест
python test_forms.py

# Если тест проходит, но приложение не работает:
python -B main.py
```

### Сценарий 2: Ошибка "database is locked"

**Симптомы:**
```
sqlite3.OperationalError: database is locked
```

**Решение:**
- Закройте все окна приложения
- Перезапустите приложение
- Если не помогает, перезагрузите компьютер

### Сценарий 3: Форма "зависает"

**Симптомы:**
- Форма открывается, но не отвечает
- Кнопки не нажимаются
- Окно белое/пустое

**Решение:**
- Закройте приложение через диспетчер задач
- Очистите кэш: `clear_cache.bat`
- Запустите снова

### Сценарий 4: Ошибка импорта

**Симптомы:**
```
ImportError: cannot import name 'EstimateDocumentForm'
```

**Решение:**
```bash
# Проверить импорт
python -c "from src.views.estimate_document_form import EstimateDocumentForm; print('OK')"

# Если ошибка, очистить кэш
clear_cache.bat
```

## Диагностические команды

### 1. Проверка БД
```bash
python -c "from src.data.database_manager import DatabaseManager; db = DatabaseManager(); db.initialize('construction.db'); print('DB OK')"
```

### 2. Проверка формы
```bash
python -c "from PyQt6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); from src.views.estimate_document_form import EstimateDocumentForm; form = EstimateDocumentForm(0); print('Form OK')"
```

### 3. Проверка данных
```bash
python -c "from src.data.database_manager import DatabaseManager; db = DatabaseManager(); db.initialize('construction.db'); cursor = db.get_connection().cursor(); cursor.execute('SELECT COUNT(*) FROM estimates'); print(f'Estimates: {cursor.fetchone()[0]}')"
```

## Если ничего не помогает

### Полный сброс (ВНИМАНИЕ: потеря данных!)

```bash
# 1. Закрыть приложение
# 2. Удалить БД
del construction.db

# 3. Очистить кэш
clear_cache.bat

# 4. Запустить заново
python main.py
```

### Создание отчета об ошибке

Соберите следующую информацию:

1. **Точная ошибка из консоли**
2. **Скриншот окна с ошибкой**
3. **Последовательность действий для воспроизведения**
4. **Результаты тестов:**
   ```bash
   python test_forms.py > test_results.txt 2>&1
   ```
5. **Версия Python:**
   ```bash
   python --version > version.txt
   ```

## Контакты для помощи

Если проблема не решается, предоставьте:
- Файл `test_results.txt`
- Файл `version.txt`
- Текст ошибки из консоли
- Описание действий для воспроизведения

## Быстрая проверка

Выполните эти команды по порядку:

```bash
# 1. Очистить кэш
clear_cache.bat

# 2. Запустить тесты
python test_forms.py

# 3. Если тесты OK, запустить приложение
python main.py
```

Если тесты проходят, но приложение не работает - проблема в окружении или кэше.
Если тесты не проходят - проблема в коде, смотрите вывод теста.
