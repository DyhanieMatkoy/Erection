# Импорт смет из Excel и печатные формы в веб-версии

## Реализованный функционал

### 1. Импорт смет из Excel

#### API Endpoint
- **POST** `/documents/estimates/import-excel`
- Принимает файл Excel (.xlsx, .xls)
- Возвращает созданную смету с ID

#### Веб-интерфейс
- Кнопка "Импорт из Excel" в списке смет (`EstimateListView.vue`)
- Автоматическое открытие импортированной сметы после успешного импорта
- Обработка ошибок с понятными сообщениями

#### Логика импорта
Используется существующий сервис `ExcelImportService` из десктопной версии:
- Парсинг заголовка документа (заказчик, подрядчик, объект)
- Автоматическое создание справочников при необходимости
- Импорт строк сметы с работами
- Расчет итоговых сумм и трудозатрат

### 2. Печатные формы

#### API Endpoints
- **GET** `/documents/estimates/{id}/print?format=pdf|excel`
- **GET** `/documents/daily-reports/{id}/print?format=pdf|excel`
- **GET** `/documents/timesheets/{id}/print?format=pdf|excel`

#### Форматы печати
1. **PDF** - формат АРСД (используется ReportLab)
2. **Excel** - формат XLSX (используется openpyxl)

#### Веб-интерфейс

##### В списке смет
- Кнопки "Excel" и "PDF" для каждой сметы
- Прямое скачивание без диалога

##### В форме редактирования сметы
- Кнопка "Печать" открывает диалог выбора формата
- Опции:
  - Скачать PDF
  - Открыть PDF в новой вкладке
  - Скачать Excel

#### Используемые сервисы
- `ExcelEstimatePrintForm` - генерация Excel для смет
- `EstimatePrintForm` - генерация PDF для смет
- `ExcelDailyReportPrintForm` - генерация Excel для ежедневных отчетов
- `DailyReportPrintForm` - генерация PDF для ежедневных отчетов
- `ExcelTimesheetPrintForm` - генерация Excel для табелей

### 3. Структура файлов

#### Backend (API)
```
api/endpoints/documents.py
  - import_estimate_from_excel()  # Новый endpoint
  - print_estimate()              # Существующий
  - print_daily_report()          # Существующий
  - print_timesheet()             # Существующий

src/services/
  - excel_import_service.py       # Сервис импорта
  - excel_estimate_print_form.py  # Печать смет в Excel
  - excel_daily_report_print_form.py
  - excel_timesheet_print_form.py
  - excel_print_form_generator.py # Базовый класс
```

#### Frontend (Web)
```
web-client/src/
  api/documents.ts
    - importEstimateFromExcel()   # Новая функция
    - printEstimate()             # Существующая
    - printDailyReport()
    - printTimesheet()
  
  views/documents/
    - EstimateListView.vue        # Добавлены кнопки импорта и печати
    - EstimateFormView.vue        # Уже была кнопка печати
  
  components/documents/
    - PrintDialog.vue             # Диалог выбора формата
  
  composables/
    - usePrint.ts                 # Composable для печати
```

### 4. Шаблоны печатных форм

Шаблоны хранятся в папке `PrnForms/`:
- `estimate_template.xlsx` - шаблон для смет
- `daily_report_template.xlsx` - шаблон для ежедневных отчетов

Если шаблон не найден, документ создается программно.

### 5. Использование

#### Импорт сметы
1. Открыть список смет
2. Нажать "Импорт из Excel"
3. Выбрать файл Excel со сметой
4. Смета автоматически импортируется и открывается для редактирования

#### Печать из списка
1. В списке смет нажать кнопку "Excel" или "PDF"
2. Файл автоматически скачивается

#### Печать из формы
1. Открыть смету
2. Нажать кнопку "Печать"
3. Выбрать формат (PDF или Excel)
4. Выбрать действие (Скачать или Открыть)

### 6. Требования

#### Python пакеты
- `openpyxl` - для работы с Excel
- `reportlab` - для генерации PDF
- `python-multipart` - для загрузки файлов в FastAPI

#### Настройки
В `env.ini` можно указать путь к шаблонам:
```ini
[PrintForms]
templates_path = PrnForms
```

### 7. Обработка ошибок

- Проверка формата файла при импорте
- Валидация структуры Excel документа
- Автоматическое создание справочников
- Понятные сообщения об ошибках для пользователя
- Очистка временных файлов

### 8. Безопасность

- Проверка прав доступа через `get_current_user`
- Валидация загружаемых файлов
- Использование временных файлов с автоматической очисткой
- Защита от SQL-инъекций через параметризованные запросы

## Следующие шаги

Функционал полностью реализован и готов к использованию. Для тестирования:

1. Запустить API сервер: `python -m uvicorn api.main:app --reload`
2. Запустить веб-клиент: `cd web-client && npm run dev`
3. Открыть список смет и протестировать импорт и печать
