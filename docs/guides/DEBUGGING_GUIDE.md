# Руководство по отладке проблем с открытием форм

## Проблема

Форма сметы открывается 1 раз, затем перестает открываться.

## Диагностика

### 1. Запуск с логированием

```bash
run_with_logging.bat
```

Или напрямую:
```bash
python main.py 2>&1 | tee output.log
```

### 2. Запуск тестов

**Тест множественного открытия:**
```bash
python test_estimate_open.py
```

**Тест потока главного окна:**
```bash
python test_main_window_flow.py
```

**Полный тест всех форм:**
```bash
python test_forms.py
```

### 3. Проверка кэша

Очистите кэш Python:
```bash
clear_cache.bat
```

Или запустите без кэша:
```bash
python -B main.py
```

## Возможные причины

### 1. Кэш Python (.pyc файлы)

**Симптомы:**
- Код выглядит правильным, но ошибка остается
- После перезапуска работает, потом снова ломается

**Решение:**
```bash
clear_cache.bat
python main.py
```

### 2. Ошибка в коде (row.get())

**Симптомы:**
- Ошибка `'sqlite3.Row' object has no attribute 'get'`
- Появляется при загрузке документа

**Решение:**
Проверьте, что все `row.get()` заменены на:
```python
value = row['column'] if 'column' in row.keys() else default
```

**Файлы для проверки:**
- `src/views/estimate_list_form.py`
- `src/views/estimate_document_form.py`
- `src/views/daily_report_list_form.py`
- `src/views/daily_report_document_form.py`

### 3. Проблема с подключением к БД

**Симптомы:**
- Первое открытие работает
- Последующие открытия не работают
- Ошибки типа "database is locked"

**Решение:**
Проверьте, что соединение с БД правильно закрывается:
```python
# В конце операций
cursor.close()
```

### 4. Утечка памяти / незакрытые формы

**Симптомы:**
- Формы не закрываются полностью
- Память растет при каждом открытии

**Решение:**
Убедитесь, что формы имеют атрибут `WA_DeleteOnClose`:
```python
form.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
```

## Отладочные команды

### Проверка структуры БД

```python
python -c "from src.data.database_manager import DatabaseManager; db = DatabaseManager(); db.initialize('construction.db'); cursor = db.get_connection().cursor(); cursor.execute('PRAGMA table_info(estimate_lines)'); print([row[1] for row in cursor.fetchall()])"
```

### Проверка наличия данных

```python
python -c "from src.data.database_manager import DatabaseManager; db = DatabaseManager(); db.initialize('construction.db'); cursor = db.get_connection().cursor(); cursor.execute('SELECT COUNT(*) FROM estimates'); print(f'Estimates: {cursor.fetchone()[0]}')"
```

### Проверка импортов

```python
python -c "from src.views.estimate_document_form import EstimateDocumentForm; print('Import OK')"
```

## Сбор информации для отчета об ошибке

Если проблема не решается, соберите следующую информацию:

1. **Вывод консоли:**
   ```bash
   python main.py > output.log 2>&1
   ```

2. **Результаты тестов:**
   ```bash
   python test_forms.py > test_results.log 2>&1
   ```

3. **Версия Python:**
   ```bash
   python --version
   ```

4. **Установленные пакеты:**
   ```bash
   pip list > packages.txt
   ```

5. **Структура БД:**
   ```bash
   python -c "from src.data.database_manager import DatabaseManager; db = DatabaseManager(); db.initialize('construction.db'); cursor = db.get_connection().cursor(); cursor.execute('SELECT sql FROM sqlite_master WHERE type=\"table\" AND name=\"estimate_lines\"'); print(cursor.fetchone()[0])" > db_structure.txt
   ```

## Быстрые исправления

### Полная переустановка

```bash
# 1. Очистить кэш
clear_cache.bat

# 2. Удалить БД (ВНИМАНИЕ: потеря данных!)
del construction.db

# 3. Запустить заново
python main.py
```

### Проверка конкретной формы

```python
# test_single_form.py
import sys
from PyQt6.QtWidgets import QApplication
from src.data.database_manager import DatabaseManager
from src.views.estimate_document_form import EstimateDocumentForm

app = QApplication(sys.argv)
db = DatabaseManager()
db.initialize('construction.db')

# Попробуйте открыть форму
try:
    form = EstimateDocumentForm(1)  # ID существующей сметы
    form.show()
    print("✓ Form opened successfully")
    app.exec()
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
```

## Контрольный список

- [ ] Очищен кэш Python
- [ ] Проверены все `row.get()` заменены
- [ ] Тесты проходят успешно
- [ ] БД инициализирована корректно
- [ ] Поля `is_group`, `group_name` существуют в БД
- [ ] Нет ошибок в консоли при запуске
- [ ] Формы имеют `WA_DeleteOnClose`
- [ ] Логирование включено

## Получение помощи

Если проблема не решается:

1. Запустите все тесты и сохраните результаты
2. Соберите логи с помощью `run_with_logging.bat`
3. Проверьте консоль на наличие ошибок
4. Опишите точную последовательность действий для воспроизведения
