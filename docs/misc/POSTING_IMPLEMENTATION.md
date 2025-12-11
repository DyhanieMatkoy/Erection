# Реализация проведения документов и регистра накопления

## Выполнено

### 1. База данных ✅
- Создана таблица `work_execution_register` для хранения движений
- Добавлены поля `is_posted` и `posted_at` в таблицы `estimates` и `daily_reports`
- Созданы индексы для быстрого поиска по регистратору и измерениям

### 2. Репозиторий регистра ✅
Создан `WorkExecutionRegisterRepository` с методами:
- `get_movements()` - получение движений документа
- `delete_movements()` - удаление движений документа
- `create_movement()` - создание движения
- `get_balance()` - получение остатков с группировкой
- `get_turnovers()` - получение оборотов за период

### 3. Сервис проведения ✅
Создан `DocumentPostingService` с методами:
- `post_estimate()` - проведение сметы (создает приход +)
- `unpost_estimate()` - отмена проведения сметы
- `post_daily_report()` - проведение отчета (создает расход -)
- `unpost_daily_report()` - отмена проведения отчета

### 4. Обновлены требования и задачи ✅
- Добавлено Требование 8 о проведении документов
- Создан файл tasks_registers.md с детальными задачами

## Требуется доделать

### 1. Формы документов
Добавить в `EstimateDocumentForm` и `DailyReportDocumentForm`:

```python
# В __init__:
self.is_posted = False
from ..services.document_posting_service import DocumentPostingService
self.posting_service = DocumentPostingService()

# В setup_ui добавить кнопки:
self.post_button = QPushButton("Провести (Ctrl+K)")
self.post_button.clicked.connect(self.on_post)

self.unpost_button = QPushButton("Отменить проведение")
self.unpost_button.clicked.connect(self.on_unpost)

# Методы:
def on_post(self):
    if not self.save_data():
        return
    
    success, error = self.posting_service.post_estimate(self.estimate_id)
    if success:
        QMessageBox.information(self, "Успех", "Документ проведен")
        self.load_estimate()
        self.update_posting_state()
    else:
        QMessageBox.critical(self, "Ошибка", error)

def on_unpost(self):
    success, error = self.posting_service.unpost_estimate(self.estimate_id)
    if success:
        QMessageBox.information(self, "Успех", "Проведение отменено")
        self.load_estimate()
        self.update_posting_state()
    else:
        QMessageBox.critical(self, "Ошибка", error)

def update_posting_state(self):
    # Блокировать/разблокировать поля
    is_editable = not self.is_posted
    self.number_edit.setReadOnly(not is_editable)
    self.table_part.setEnabled(is_editable)
    # ... для всех полей
    
    # Обновить кнопки
    self.post_button.setEnabled(not self.is_posted)
    self.unpost_button.setEnabled(self.is_posted)
    
    # Обновить заголовок
    status = " [ПРОВЕДЕН]" if self.is_posted else ""
    self.setWindowTitle(f"Смета {self.number_edit.text()}{status}")

# В load_estimate добавить:
self.is_posted = row['is_posted'] == 1
self.update_posting_state()
```

### 2. Списки документов
Добавить колонку "Проведен" в `EstimateListForm` и `DailyReportListForm`:

```python
# В setup_ui:
self.table_view.setColumnCount(8)  # +1 колонка
self.table_view.setHorizontalHeaderLabels([
    "ID", "Номер", "Дата", "Заказчик", "Объект", 
    "Ответственный", "Итого сумма", "Проведен"
])

# В load_data:
posted_item = QTableWidgetItem("✓" if row['is_posted'] else "")
if row['is_posted']:
    # Выделить жирным
    font = posted_item.font()
    font.setBold(True)
    posted_item.setFont(font)
self.table_view.setItem(row_idx, 7, posted_item)
```

### 3. Отчет по выполнению работ
Создать `src/views/work_execution_report_form.py`:

```python
class WorkExecutionReportForm(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager().get_connection()
        self.register_repo = WorkExecutionRegisterRepository()
        self.setup_ui()
    
    def setup_ui(self):
        # Параметры отчета
        # - Период (дата начала, дата окончания)
        # - Объект (ComboBox)
        # - Смета (ComboBox)
        # - Работа (ComboBox)
        # - Группировка (ComboBox: по объектам, по сметам, по работам)
        
        # Таблица результатов
        # Колонки: Группировка, План кол-во, Факт кол-во, Остаток кол-во,
        #          План сумма, Факт сумма, Остаток сумма, % выполнения
        
        # Кнопки: Сформировать, Экспорт в Excel
        pass
    
    def generate_report(self):
        # Получить параметры
        # Вызвать register_repo.get_balance() или get_turnovers()
        # Заполнить таблицу
        # Рассчитать % выполнения
        pass
```

### 4. Добавить в меню
В `src/views/main_window.py`:

```python
# В setup_ui:
work_execution_action = QAction("Выполнение работ", self)
work_execution_action.triggered.connect(self.open_work_execution_report)
reports_menu.addAction(work_execution_action)

def open_work_execution_report(self):
    from .work_execution_report_form import WorkExecutionReportForm
    
    for window in self.mdi_area.subWindowList():
        if isinstance(window.widget(), WorkExecutionReportForm):
            self.mdi_area.setActiveSubWindow(window)
            return
    
    form = WorkExecutionReportForm()
    sub_window = self.mdi_area.addSubWindow(form)
    sub_window.show()
```

## Тестирование

После доработки протестировать:

1. Создать смету с несколькими работами
2. Провести смету
3. Проверить движения в регистре:
   ```sql
   SELECT * FROM work_execution_register WHERE recorder_type='estimate';
   ```
4. Создать ежедневный отчет по смете
5. Провести отчет
6. Проверить движения в регистре
7. Открыть отчет по выполнению работ
8. Проверить остатки (план - факт)
9. Отменить проведение документов
10. Проверить, что движения удалены

## Структура регистра

```
work_execution_register:
- recorder_type: 'estimate' | 'daily_report'
- recorder_id: ID документа
- period: дата движения
- object_id: объект (измерение)
- estimate_id: смета (измерение)
- work_id: работа (измерение)
- quantity_income: приход количества (+)
- quantity_expense: расход количества (-)
- sum_income: приход суммы (+)
- sum_expense: расход суммы (-)
```

## Логика проведения

### Смета (приход +):
- Для каждой строки табличной части создается движение
- quantity_income = количество из строки
- sum_income = сумма из строки
- period = дата сметы
- object_id = объект из сметы

### Ежедневный отчет (расход -):
- Для каждой строки табличной части создается движение
- quantity_expense = фактические трудозатраты
- sum_expense = фактические трудозатраты × цена работы
- period = дата отчета
- object_id = объект из сметы
- estimate_id = смета из отчета

## Отчет по выполнению

Показывает:
- План = SUM(quantity_income)
- Факт = SUM(quantity_expense)
- Остаток = План - Факт
- % выполнения = (Факт / План) × 100

С группировкой по объектам, сметам, работам или датам.
