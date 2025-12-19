# Функциональность печати смет с ресурсной ведомостью

## Обзор

Добавлен второй вариант печатной формы для смет с отдельной таблицей ресурсной ведомости в формате: номер строки, материал, количество, цена, сумма с итогом внизу.

## Новые возможности

### 1. Варианты печати смет

- **STANDARD** - стандартный формат сметы (как было ранее)
- **RESOURCE** - смета + отдельная ресурсная ведомость

### 2. Поддержка форматов

- **PDF** - PDF документ с разрывом страницы между сметой и ресурсной ведомостью
- **Excel** - Excel файл с двумя листами: "Смета" и "Ресурсная ведомость"

### 3. Конфигурация

Настройки сохраняются в файле `env.ini`:

```ini
[PrintForms]
format = EXCEL
estimate_variant = RESOURCE
```

## Структура ресурсной ведомости

| № п/п | Материал | Количество | Цена | Сумма |
|-------|----------|------------|------|-------|
| 1 | 01.001 - Цемент М400 | 2.500 т | 5000.00 | 12500.00 |
| 2 | 02.015 - Арматура А500С | 150.000 кг | 45.00 | 6750.00 |
| ... | ... | ... | ... | ... |
| | | | **ИТОГО:** | **19250.00** |

## Использование

### Программный интерфейс

```python
from src.services.print_form_service import PrintFormService
from src.services.estimate_service import EstimateService

# Через сервис печати
print_service = PrintFormService()

# Генерация стандартной сметы
result = print_service.generate_estimate(estimate_id, 'STANDARD')

# Генерация сметы с ресурсной ведомостью
result = print_service.generate_estimate(estimate_id, 'RESOURCE')

# Через сервис смет
estimate_service = EstimateService()

# Использование конфигурации по умолчанию
result = estimate_service.generate_print_form(estimate_id)

# Явное указание варианта
result = estimate_service.generate_print_form(estimate_id, 'RESOURCE')
```

### Настройка конфигурации

```python
print_service = PrintFormService()

# Установка формата печати
print_service.set_print_format('PDF')  # или 'EXCEL'

# Установка варианта сметы
print_service.set_estimate_print_variant('RESOURCE')  # или 'STANDARD'

# Получение текущих настроек
format_type = print_service.get_print_format()
variant = print_service.get_estimate_print_variant()
```

## Технические детали

### Новые классы

1. **EstimateResourcePrintForm** - генератор PDF с ресурсной ведомостью
2. **ExcelEstimateResourcePrintForm** - генератор Excel с ресурсной ведомостью

### Алгоритм формирования ресурсной ведомости

1. Получение всех работ из сметы (исключая группы)
2. Для каждой работы получение связанных материалов из таблицы `cost_item_materials`
3. Группировка материалов по коду и описанию
4. Суммирование количества: `quantity_per_unit * estimate_line_quantity`
5. Расчет общей стоимости: `total_quantity * material_price`
6. Сортировка по коду материала

### SQL запрос для получения ресурсов

```sql
SELECT DISTINCT
    m.id,
    m.code,
    m.description,
    m.price,
    m.unit,
    SUM(cim.quantity_per_unit * el.quantity) as total_quantity,
    SUM(cim.quantity_per_unit * el.quantity * m.price) as total_sum
FROM estimate_lines el
JOIN works w ON el.work_id = w.id
JOIN cost_item_materials cim ON cim.work_id = w.id
JOIN materials m ON cim.material_id = m.id
WHERE el.estimate_id = ? 
    AND el.work_id != -1  -- Исключить группы
    AND cim.material_id IS NOT NULL
GROUP BY m.id, m.code, m.description, m.price, m.unit
ORDER BY m.code
```

## Файлы и структура

### Новые файлы

- `src/services/estimate_resource_print_form.py` - PDF генератор с ресурсной ведомостью
- `src/services/excel_estimate_resource_print_form.py` - Excel генератор с ресурсной ведомостью
- `test_estimate_resource_print.py` - тесты новой функциональности
- `examples/estimate_resource_print_example.py` - пример использования

### Обновленные файлы

- `src/services/print_form_service.py` - добавлена поддержка вариантов печати
- `src/services/estimate_service.py` - обновлен для работы с новыми вариантами
- `src/services/estimate_print_form.py` - обновлен для работы с новой системой БД
- `src/services/excel_estimate_print_form.py` - обновлен для работы с новой системой БД

### Шаблоны

- `PrnForms/estimate_resource_template.xlsx` - шаблон Excel для сметы с ресурсной ведомостью

## Тестирование

Запуск тестов:

```bash
python test_estimate_resource_print.py
```

Запуск примера:

```bash
python examples/estimate_resource_print_example.py
```

## Конфигурация по умолчанию

- **Формат печати**: PDF
- **Вариант сметы**: STANDARD

## Совместимость

- Полная обратная совместимость с существующими сметами
- Работает с текущей структурой базы данных
- Поддерживает все существующие функции печати

## Ограничения

- Ресурсная ведомость формируется только для материалов, связанных с работами через таблицу `cost_item_materials`
- Если у работ нет связанных материалов, ресурсная ведомость будет пустой
- Группировка материалов происходит по коду и описанию (одинаковые материалы объединяются)

## Примеры использования

### Генерация PDF с ресурсной ведомостью

```python
from src.services.estimate_resource_print_form import EstimateResourcePrintForm

generator = EstimateResourcePrintForm()
pdf_content = generator.generate(estimate_id)

with open('estimate_with_resources.pdf', 'wb') as f:
    f.write(pdf_content)
```

### Генерация Excel с ресурсной ведомостью

```python
from src.services.excel_estimate_resource_print_form import ExcelEstimateResourcePrintForm

generator = ExcelEstimateResourcePrintForm()
excel_content = generator.generate(estimate_id)

with open('estimate_with_resources.xlsx', 'wb') as f:
    f.write(excel_content)
```

### Создание шаблонов

```python
from src.services.print_form_service import PrintFormService

service = PrintFormService()
success, message = service.create_templates()
print(message)
```

## Заключение

Новая функциональность предоставляет гибкие возможности для печати смет с детализированной ресурсной ведомостью, что особенно полезно для:

- Планирования закупок материалов
- Контроля расхода ресурсов
- Детального анализа стоимости проекта
- Подготовки документации для заказчиков