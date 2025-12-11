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

#### 1. Создать SQLAlchemy модель (src/data/models/sqlalchemy_models.py)

```python
from sqlalchemy import Column, Integer, String, Boolean
from src.data.sqlalchemy_base import Base

class Unit(Base):
    __tablename__ = 'units'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    short_name = Column(String(50))
    marked_for_deletion = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Unit(id={self.id}, name='{self.name}')>"
```

#### 2. Создать миграцию (автоматически)

```bash
# Alembic автоматически создаст таблицу на основе модели
alembic revision --autogenerate -m "Add units table"
alembic upgrade head
```

#### 3. Создать репозиторий (src/data/repositories/unit_repository.py)

```python
from typing import List, Optional
from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Unit

class UnitRepository:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def find_all(self) -> List[Unit]:
        """Получить все единицы измерения"""
        with self.db_manager.session_scope() as session:
            return session.query(Unit)\
                .filter_by(marked_for_deletion=False)\
                .order_by(Unit.name)\
                .all()
    
    def find_by_id(self, unit_id: int) -> Optional[Unit]:
        """Найти единицу измерения по ID"""
        with self.db_manager.session_scope() as session:
            return session.query(Unit).filter_by(id=unit_id).first()
    
    def save(self, unit: Unit) -> bool:
        """Сохранить единицу измерения"""
        try:
            with self.db_manager.session_scope() as session:
                session.add(unit)
                return True
        except Exception as e:
            logger.error(f"Failed to save unit: {e}")
            return False
    
    def delete(self, unit_id: int) -> bool:
        """Пометить единицу измерения для удаления"""
        try:
            with self.db_manager.session_scope() as session:
                unit = session.query(Unit).filter_by(id=unit_id).first()
                if unit:
                    unit.marked_for_deletion = True
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete unit: {e}")
            return False
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

### SQLAlchemy ORM

Система использует SQLAlchemy ORM для работы с базой данных. Это обеспечивает поддержку нескольких СУБД (SQLite, PostgreSQL, MSSQL).

### Получение сессии

```python
from src.data.database_manager import DatabaseManager

db_manager = DatabaseManager()

# Использование context manager (рекомендуется)
with db_manager.session_scope() as session:
    # Работа с базой данных
    user = session.query(User).filter_by(username='admin').first()
    # Автоматический commit при успехе, rollback при ошибке
```

### CRUD операции

**Create (создание):**

```python
from src.data.models.sqlalchemy_models import Person

with db_manager.session_scope() as session:
    person = Person(
        full_name="Иван Иванов",
        position="Инженер",
        phone="+7 999 123-45-67",
        hourly_rate=500.0
    )
    session.add(person)
    # Commit происходит автоматически при выходе из context manager
    # person.id будет доступен после commit
```

**Read (чтение):**

```python
from src.data.models.sqlalchemy_models import Estimate

with db_manager.session_scope() as session:
    # Получить по ID
    estimate = session.query(Estimate).filter_by(id=1).first()
    
    # Получить все записи
    all_estimates = session.query(Estimate).all()
    
    # Фильтрация
    recent_estimates = session.query(Estimate)\
        .filter(Estimate.date >= '2024-01-01')\
        .order_by(Estimate.date.desc())\
        .all()
    
    # С join
    estimates_with_customer = session.query(Estimate)\
        .join(Counterparty, Estimate.customer_id == Counterparty.id)\
        .filter(Counterparty.name.like('%ООО%'))\
        .all()
```

**Update (обновление):**

```python
with db_manager.session_scope() as session:
    person = session.query(Person).filter_by(id=1).first()
    if person:
        person.phone = "+7 999 999-99-99"
        person.hourly_rate = 600.0
        # Изменения сохраняются автоматически при commit
```

**Delete (удаление):**

```python
with db_manager.session_scope() as session:
    person = session.query(Person).filter_by(id=1).first()
    if person:
        session.delete(person)
        # Удаление происходит при commit
```

### Работа с отношениями

**One-to-Many (один ко многим):**

```python
from src.data.models.sqlalchemy_models import Estimate, EstimateLine

with db_manager.session_scope() as session:
    # Создание estimate с lines
    estimate = Estimate(
        number="СМ-001",
        date=datetime.date.today(),
        customer_id=1
    )
    
    # Добавление строк
    line1 = EstimateLine(
        work_id=1,
        quantity=100.0,
        unit_price=50.0
    )
    line2 = EstimateLine(
        work_id=2,
        quantity=200.0,
        unit_price=75.0
    )
    
    estimate.lines.append(line1)
    estimate.lines.append(line2)
    
    session.add(estimate)
    # Все lines сохранятся автоматически благодаря cascade
```

**Загрузка связанных данных:**

```python
from sqlalchemy.orm import joinedload

with db_manager.session_scope() as session:
    # Eager loading - загружает связанные данные одним запросом
    estimate = session.query(Estimate)\
        .options(joinedload(Estimate.lines))\
        .filter_by(id=1)\
        .first()
    
    # Теперь можно использовать estimate.lines без дополнительных запросов
    for line in estimate.lines:
        print(f"Work: {line.work_id}, Quantity: {line.quantity}")
```

### Транзакции

```python
# Автоматическое управление транзакциями
with db_manager.session_scope() as session:
    try:
        # Несколько операций в одной транзакции
        person = Person(full_name="Тест")
        session.add(person)
        session.flush()  # Получить person.id без commit
        
        estimate = Estimate(responsible_id=person.id)
        session.add(estimate)
        
        # Commit происходит автоматически
    except Exception as e:
        # Rollback происходит автоматически при ошибке
        raise
```

### Запросы с агрегацией

```python
from sqlalchemy import func

with db_manager.session_scope() as session:
    # Подсчет
    count = session.query(func.count(Estimate.id)).scalar()
    
    # Сумма
    total = session.query(func.sum(EstimateLine.quantity * EstimateLine.unit_price))\
        .filter(EstimateLine.estimate_id == 1)\
        .scalar()
    
    # Группировка
    results = session.query(
        Estimate.responsible_id,
        func.count(Estimate.id).label('count')
    ).group_by(Estimate.responsible_id).all()
```

### Пагинация

```python
def get_estimates_page(page=1, per_page=20):
    with db_manager.session_scope() as session:
        estimates = session.query(Estimate)\
            .order_by(Estimate.date.desc())\
            .limit(per_page)\
            .offset((page - 1) * per_page)\
            .all()
        
        total = session.query(func.count(Estimate.id)).scalar()
        
        return estimates, total
```

### Параметризованные запросы

SQLAlchemy автоматически параметризует запросы, защищая от SQL injection:

```python
# ✅ Правильно - SQLAlchemy автоматически параметризует
username = request.get('username')
user = session.query(User).filter_by(username=username).first()

# ✅ Также правильно
user = session.query(User).filter(User.username == username).first()

# ❌ Неправильно - никогда не используйте f-strings в SQL
# session.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### Работа с датами и временем

```python
from datetime import date, datetime
from src.data.datetime_utils import ensure_date, ensure_datetime

with db_manager.session_scope() as session:
    # Использование date
    estimate = Estimate(
        date=date.today(),
        number="СМ-001"
    )
    
    # Использование datetime
    daily_report = DailyReport(
        date=date.today(),
        created_at=datetime.now()
    )
    
    # Фильтрация по дате
    estimates = session.query(Estimate)\
        .filter(Estimate.date >= date(2024, 1, 1))\
        .filter(Estimate.date <= date(2024, 12, 31))\
        .all()
    
    # Использование утилит для конвертации
    date_value = ensure_date("2024-01-01")  # Конвертирует строку в date
```

### Обработка ошибок

```python
from src.data.exceptions import DatabaseConnectionError, DatabaseOperationError

try:
    with db_manager.session_scope() as session:
        person = Person(full_name="Тест")
        session.add(person)
except DatabaseOperationError as e:
    # Ошибка операции с БД (constraint violation, etc.)
    logger.error(f"Database operation failed: {e}")
    # Показать сообщение пользователю
except DatabaseConnectionError as e:
    # Ошибка подключения к БД
    logger.error(f"Database connection failed: {e}")
    # Показать сообщение о проблемах с подключением
except Exception as e:
    # Другие ошибки
    logger.error(f"Unexpected error: {e}")
```

### Миграции базы данных

Система использует Alembic для управления схемой базы данных:

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Add new column"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Посмотреть историю
alembic history
```

### Поддержка нескольких СУБД

Система поддерживает SQLite, PostgreSQL и MSSQL. Конфигурация в `env.ini`:

```ini
[Database]
# SQLite (по умолчанию)
type = sqlite
sqlite_path = construction.db

# PostgreSQL
# type = postgresql
# postgres_host = localhost
# postgres_port = 5432
# postgres_database = construction
# postgres_user = postgres
# postgres_password = password

# MSSQL
# type = mssql
# mssql_host = localhost
# mssql_port = 1433
# mssql_database = construction
# mssql_user = sa
# mssql_password = password
# mssql_driver = ODBC Driver 17 for SQL Server
```

См. [DATABASE_CONFIGURATION.md](DATABASE_CONFIGURATION.md) для подробной информации о конфигурации.

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
