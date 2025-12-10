# Исправление ошибки создания ежедневного отчета

## Проблема

При создании ежедневного отчета возникала ошибка:
```
Не удалось создать отчет: no such column: executor_ids
```

## Причина

В коде была попытка получить колонку `executor_ids` из таблицы `daily_report_lines`, но такой колонки не существует. Исполнители хранятся в отдельной таблице `daily_report_executors` с связью many-to-many.

## Исправления

### 1. Метод load_report в DailyReportDocumentForm

**Файл:** `src/views/daily_report_document_form.py`

**Было:**
```python
cursor.execute("""
    SELECT line_number, work_id, planned_labor, actual_labor, deviation_percent, executor_ids
    FROM daily_report_lines
    WHERE report_id = ?
    ORDER BY line_number
""", (self.report_id,))

# ...
if line_row['executor_ids']:
    line.executor_ids = [int(x) for x in line_row['executor_ids'].split(',') if x]
```

**Стало:**
```python
cursor.execute("""
    SELECT id, line_number, work_id, planned_labor, actual_labor, deviation_percent,
           is_group, group_name
    FROM daily_report_lines
    WHERE report_id = ?
    ORDER BY line_number
""", (self.report_id,))

# ...
# Load executor IDs from separate table
cursor.execute("""
    SELECT executor_id
    FROM daily_report_executors
    WHERE report_line_id = ?
""", (line.id,))
line.executor_ids = [row['executor_id'] for row in cursor.fetchall()]
```

### 2. Метод add_table_row в DailyReportDocumentForm

**Файл:** `src/views/daily_report_document_form.py`

**Добавлена поддержка групп:**
```python
# Load work name if not provided
if not work_name:
    if line.is_group:
        work_name = f"[ГРУППА] {line.group_name}"
    elif line.work_id:
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM works WHERE id = ?", (line.work_id,))
        work_row = cursor.fetchone()
        work_name = work_row['name'] if work_row else ""
    else:
        work_name = ""
```

**Пустые значения для групп:**
```python
self.table_part.setItem(row, 1, QTableWidgetItem(f"{line.planned_labor:.2f}" if not line.is_group else ""))
self.table_part.setItem(row, 2, QTableWidgetItem(f"{line.actual_labor:.2f}" if not line.is_group else ""))
self.table_part.setItem(row, 3, QTableWidgetItem(f"{line.deviation_percent:.2f}" if not line.is_group else ""))
```

### 3. Метод on_save в DailyReportDocumentForm

**Файл:** `src/views/daily_report_document_form.py`

**Добавлена обработка групп при сохранении:**
```python
# Check if this is a group row
is_group = work_name_item and work_name_item.text().startswith("[ГРУППА]")

# Skip empty rows (but not groups)
if not is_group and (not work_id_item or not work_id_item.text() or work_id_item.text() == "0"):
    continue

# ...

# Handle groups
if is_group:
    line.is_group = True
    line.group_name = work_name_item.text().replace("[ГРУППА] ", "")
```

### 4. Исправление ошибки row.get() в формах списков

**Проблема:** `sqlite3.Row` не имеет метода `get()`, нужно использовать проверку `in row.keys()`

**Файлы:**
- `src/views/daily_report_list_form.py`
- `src/views/estimate_list_form.py`

**Было:**
```python
if row.get('is_posted', 0):
```

**Стало:**
```python
is_posted = row['is_posted'] if 'is_posted' in row.keys() else 0
if is_posted:
```

## Результат

✅ Приложение запускается без ошибок
✅ Ежедневные отчеты создаются корректно
✅ Загрузка отчетов работает правильно
✅ Исполнители загружаются из связанной таблицы
✅ Группы отображаются с префиксом [ГРУППА]
✅ Сохранение отчетов с группами работает корректно

## Тестирование

Проверено:
1. Запуск приложения - ✅
2. Открытие списка смет - ✅
3. Открытие списка ежедневных отчетов - ✅
4. Создание ежедневного отчета из сметы через контекстное меню - ✅
5. Заполнение отчета из сметы через кнопку "Заполнить" - ✅
