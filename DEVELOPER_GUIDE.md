# Руководство разработчика

## Быстрый старт для разработки

### 1. Клонирование и настройка

```bash
# Установка окружения
setup.bat

# Загрузка тестовых данных
.\venv\Scripts\python.exe load_test_data.py

# Проверка статуса
.\venv\Scripts\python.exe check_status.py
```

### 2. Запуск в режиме разработки

```bash
# Активация виртуального окружения
.\venv\Scripts\activate

# Запуск приложения
python main.py
```

## Архитектура проекта

### MVVM Pattern

```
View (PyQt6 Widgets)
    ↕
ViewModel (QObject с сигналами)
    ↕
Service (Бизнес-логика)
    ↕
Repository (Доступ к данным)
    ↕
Model (Dataclasses)
    ↕
Database (SQLite)
```

## Добавление новой функциональности

### Пример: Добавление справочника "Единицы измерения"

#### 1. Создать модель (src/data/models/references.py)

```python
@dataclass
class Unit:
    id: int = 0
    name: str = ""
    short_name: str = ""
    marked_for_deletion: bool = False
```

#### 2. Создать таблицу (src/data/database_manager.py)

```python
"""CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    marked_for_deletion INTEGER DEFAULT 0
)"""
```

#### 3. Создать репозиторий (src/data/repositories/unit_repository.py)

```python
class UnitRepository:
    def __init__(self):
        self.db = DatabaseManager().get_connection()
    
    def find_all(self) -> List[Unit]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM units WHERE marked_for_deletion = 0")
        # ... реализация
```

#### 4. Создать сервис (src/services/unit_service.py)

```python
class UnitService:
    def __init__(self):
        self.repo = UnitRepository()
    
    def get_all(self) -> List[Unit]:
        return self.repo.find_all()
```

#### 5. Создать ViewModel (src/viewmodels/unit_view_model.py)

```python
class UnitViewModel(QObject):
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = UnitService()
        self.units = []
    
    def load_data(self):
        self.units = self.service.get_all()
        self.data_changed.emit()
```

#### 6. Создать форму (src/views/unit_list_form.py)

```python
class UnitListForm(BaseListForm):
    def __init__(self):
        super().__init__()
        self.view_model = UnitViewModel()
        self.setup_connections()
    
    def setup_connections(self):
        self.view_model.data_changed.connect(self.refresh_table)
```

## Соглашения о коде

### Python Style Guide (PEP 8)

- Отступы: 4 пробела
- Максимальная длина строки: 100 символов
- Имена классов: PascalCase
- Имена функций: snake_case
- Константы: UPPER_CASE

### Структура файлов

```python
"""Module docstring"""
import standard_library
import third_party
from local_module import something

# Constants
CONSTANT_NAME = "value"

# Classes
class ClassName:
    """Class docstring"""
    pass

# Functions
def function_name():
    """Function docstring"""
    pass
```

### Типизация

Используйте type hints:

```python
from typing import List, Optional

def get_items(filter_text: str) -> List[Item]:
    """Get filtered items"""
    pass

def find_by_id(item_id: int) -> Optional[Item]:
    """Find item by ID"""
    pass
```

## Работа с базой данных

### Транзакции

```python
conn = DatabaseManager().get_connection()
try:
    cursor = conn.cursor()
    cursor.execute("INSERT ...")
    cursor.execute("UPDATE ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
```

### Параметризованные запросы

```python
# ✅ Правильно
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

# ❌ Неправильно (SQL injection)
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

## Тестирование

### Ручное тестирование

```bash
# Запуск приложения
python main.py

# Проверка статуса
python check_status.py
```

### Тестовые данные

```bash
# Перезагрузка тестовых данных
python load_test_data.py
```

## Отладка

### Логирование

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### PyQt6 отладка

```python
# Включить отладку Qt
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'
```

## Горячие клавиши в коде

### Обработка в формах

```python
def keyPressEvent(self, event):
    if event.key() == Qt.Key.Key_F9:
        self.on_create_new()
    elif event.matches(Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_S:
        self.on_save()
    else:
        super().keyPressEvent(event)
```

## Сигналы и слоты PyQt6

### Определение сигнала

```python
from PyQt6.QtCore import QObject, pyqtSignal

class MyViewModel(QObject):
    data_changed = pyqtSignal()
    item_selected = pyqtSignal(int)  # с параметром
```

### Подключение слота

```python
# Метод класса
self.view_model.data_changed.connect(self.on_data_changed)

# Lambda
self.button.clicked.connect(lambda: self.on_button_clicked(param))
```

## Полезные команды

### Управление зависимостями

```bash
# Установка новой библиотеки
.\venv\Scripts\pip.exe install package_name

# Обновление requirements.txt
.\venv\Scripts\pip.exe freeze > requirements.txt

# Обновление всех пакетов
.\venv\Scripts\pip.exe list --outdated
.\venv\Scripts\pip.exe install --upgrade package_name
```

### Работа с БД

```bash
# Открыть БД в SQLite
sqlite3 construction.db

# Экспорт схемы
sqlite3 construction.db .schema > schema.sql

# Бэкап БД
copy construction.db construction_backup.db
```

## Производительность

### Оптимизация запросов

```python
# ✅ Используйте индексы
cursor.execute("CREATE INDEX idx_name ON table(column)")

# ✅ Используйте LIMIT
cursor.execute("SELECT * FROM table LIMIT 100")

# ✅ Используйте транзакции для массовых операций
conn.execute("BEGIN")
for item in items:
    cursor.execute("INSERT ...")
conn.commit()
```

### Оптимизация UI

```python
# ✅ Используйте setUpdatesEnabled
self.table.setUpdatesEnabled(False)
# ... массовые изменения
self.table.setUpdatesEnabled(True)

# ✅ Используйте QTimer для debounce
from PyQt6.QtCore import QTimer
self.timer = QTimer()
self.timer.setSingleShot(True)
self.timer.timeout.connect(self.on_search)
self.search_edit.textChanged.connect(lambda: self.timer.start(300))
```

## Ресурсы

### Документация

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt Documentation](https://doc.qt.io/)
- [Python Documentation](https://docs.python.org/3/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### Инструменты

- **IDE**: PyCharm, VS Code
- **DB Browser**: DB Browser for SQLite, DBeaver
- **Git**: Git Bash, GitHub Desktop

## Следующие шаги

1. Изучите существующий код в `src/`
2. Прочитайте спецификации в `.kiro/specs/`
3. Выберите задачу из `tasks_pyqt6.md`
4. Реализуйте функциональность
5. Протестируйте
6. Обновите документацию

## Контрольный список для новой функции

- [ ] Создана модель данных
- [ ] Создана таблица в БД
- [ ] Создан репозиторий
- [ ] Создан сервис
- [ ] Создан ViewModel
- [ ] Создана форма UI
- [ ] Добавлены горячие клавиши
- [ ] Протестирована функциональность
- [ ] Обновлена документация
