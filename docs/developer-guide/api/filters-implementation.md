# Расширение API для поддержки фильтрации

## План реализации

### Фаза 1: Расширение параметров фильтрации

#### 1.1 Документы - Estimates (api/endpoints/documents.py)

**Текущие параметры:**
- page, page_size, search
- object_id, responsible_id
- date_from, date_to
- sort_by, sort_order

**Добавить:**
```python
@router.get("/estimates")
async def list_estimates(
    # Существующие
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    object_id: Optional[int] = None,
    responsible_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = Query("date", regex="^(date|number|id)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    
    # НОВЫЕ параметры
    customer_id: Optional[int] = None,  # Заказчик
    is_posted: Optional[bool] = None,   # Статус проведения
    sum_from: Optional[float] = None,   # Сумма от
    sum_to: Optional[float] = None,     # Сумма до
    
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
```

**Логика фильтрации:**
```python
if customer_id:
    where_clauses.append("e.customer_id = ?")
    params.append(customer_id)

if is_posted is not None:
    where_clauses.append("e.is_posted = ?")
    params.append(1 if is_posted else 0)

if sum_from is not None:
    where_clauses.append("e.total_sum >= ?")
    params.append(sum_from)

if sum_to is not None:
    where_clauses.append("e.total_sum <= ?")
    params.append(sum_to)
```

#### 1.2 Документы - Timesheets

**Добавить параметры:**
```python
@router.get("/timesheets")
async def list_timesheets(
    # Существующие
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("date", regex="^(date|number|id)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    
    # НОВЫЕ параметры
    date_from: Optional[date] = None,      # Период документа (с)
    date_to: Optional[date] = None,        # Период документа (по)
    period_from: Optional[str] = None,     # Табельный период (с) YYYY-MM
    period_to: Optional[str] = None,       # Табельный период (по) YYYY-MM
    object_id: Optional[int] = None,       # Объект
    estimate_id: Optional[int] = None,     # Смета
    is_posted: Optional[bool] = None,      # Статус проведения
    
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
```

#### 1.3 Справочники - Counterparties (api/endpoints/references.py)

**Добавить параметры:**
```python
@router.get("/counterparties")
async def list_counterparties(
    # Существующие
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    
    # НОВЫЕ параметры
    type: Optional[str] = None,            # Тип (customer/contractor/supplier)
    is_deleted: Optional[bool] = None,     # Статус (активен/удален)
    
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
```

#### 1.4 Справочники - Objects

**Добавить параметры:**
```python
@router.get("/objects")
async def list_objects(
    # Существующие
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    
    # НОВЫЕ параметры
    status: Optional[str] = None,          # Статус (planning/in_progress/completed)
    customer_id: Optional[int] = None,     # Заказчик
    start_date_from: Optional[date] = None,# Дата начала (с)
    start_date_to: Optional[date] = None,  # Дата начала (по)
    is_deleted: Optional[bool] = None,     # Статус (активен/удален)
    
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
```

#### 1.5 Справочники - Persons

**Добавить параметры:**
```python
@router.get("/persons")
async def list_persons(
    # Существующие
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    
    # НОВЫЕ параметры
    position: Optional[str] = None,        # Должность
    specialty: Optional[str] = None,       # Специальность
    status: Optional[str] = None,          # Статус (active/dismissed)
    is_deleted: Optional[bool] = None,     # Статус (активен/удален)
    
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
```

#### 1.6 Справочники - Works

**Добавить параметры:**
```python
@router.get("/works")
async def list_works(
    # Существующие
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|id)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    
    # НОВЫЕ параметры
    category: Optional[str] = None,        # Категория
    unit: Optional[str] = None,            # Единица измерения (по unit_id foreign key)
    price_from: Optional[float] = None,    # Стоимость от
    price_to: Optional[float] = None,      # Стоимость до
    is_deleted: Optional[bool] = None,     # Статус (активен/удален)
    
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
```

---

### Фаза 2: Добавление колонок в ответы

#### 2.1 Документы

**Estimates - добавить:**
- `author` - имя пользователя, создавшего документ

**Timesheets - добавить:**
- `author` - имя пользователя, создавшего документ
- `total_hours` - общее количество часов

**Реализация:**
```python
# В SELECT добавить JOIN с users
SELECT 
    e.*,
    c.name as customer_name,
    o.name as object_name,
    u.username as author  -- НОВОЕ
FROM estimates e
LEFT JOIN counterparties c ON e.customer_id = c.id
LEFT JOIN objects o ON e.object_id = o.id
LEFT JOIN users u ON e.created_by = u.id  -- НОВОЕ
```

#### 2.2 Справочники

**Counterparties - добавить:**
- `code` - код контрагента
- `inn` - ИНН
- `phone` - телефон
- `email` - email
- `type` - тип контрагента

**Objects - добавить:**
- `code` - код объекта
- `address` - адрес
- `customer_name` - имя заказчика (JOIN)
- `status` - статус объекта
- `start_date` - дата начала
- `end_date` - дата окончания

**Persons - добавить:**
- `personnel_number` - табельный номер
- `position` - должность
- `specialty` - специальность
- `phone` - телефон
- `hire_date` - дата приема
- `status` - статус (active/dismissed)

**Works - добавить:**
- `code` - код работы
- `category` - категория
- `standard_price` - нормативная стоимость

---

### Фаза 3: Массовые операции для справочников

**Добавить endpoints:**

```python
# api/endpoints/references.py

@router.post("/counterparties/bulk-delete")
async def bulk_delete_counterparties(
    ids: List[int],
    current_user: UserInfo = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """Bulk delete counterparties"""
    cursor = db.cursor()
    success_count = 0
    errors = []
    
    for id in ids:
        try:
            cursor.execute(
                "UPDATE counterparties SET is_deleted = 1 WHERE id = ?",
                (id,)
            )
            success_count += 1
        except Exception as e:
            errors.append(f"ID {id}: {str(e)}")
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Удалено {success_count} из {len(ids)}",
        "errors": errors
    }

# Аналогично для objects, persons, works
```

---

## Порядок реализации

### День 1: Документы
1. ✅ Расширить `/estimates` - добавить параметры фильтрации
2. ✅ Добавить колонку `author` в ответ
3. ✅ Расширить `/timesheets` - добавить параметры фильтрации
4. ✅ Добавить колонки `author`, `total_hours` в ответ
5. ✅ Тестирование

### День 2: Справочники (часть 1)
1. ✅ Расширить `/counterparties` - параметры + колонки
2. ✅ Добавить `/counterparties/bulk-delete`
3. ✅ Расширить `/objects` - параметры + колонки
4. ✅ Добавить `/objects/bulk-delete`
5. ✅ Тестирование

### День 3: Справочники (часть 2)
1. ✅ Расширить `/persons` - параметры + колонки
2. ✅ Добавить `/persons/bulk-delete`
3. ✅ Расширить `/works` - параметры + колонки
4. ✅ Добавить `/works/bulk-delete`
5. ✅ Тестирование

---

## Примеры запросов

### Estimates с фильтрами
```
GET /api/documents/estimates?
  page=1&
  page_size=25&
  date_from=2024-01-01&
  date_to=2024-12-31&
  object_id=5&
  customer_id=3&
  is_posted=true&
  sum_from=10000&
  sum_to=50000
```

### Counterparties с фильтрами
```
GET /api/references/counterparties?
  page=1&
  page_size=25&
  type=customer&
  is_deleted=false
```

### Bulk delete
```
POST /api/references/counterparties/bulk-delete
Body: {
  "ids": [1, 2, 3, 4, 5]
}

Response: {
  "success": true,
  "message": "Удалено 5 из 5",
  "errors": []
}
```

---

## Тестирование

### Ручное тестирование
1. Проверить каждый endpoint с разными комбинациями фильтров
2. Проверить граничные случаи (пустые результаты, большие диапазоны)
3. Проверить массовые операции

### Автоматическое тестирование
```python
# test_api_filters.py

def test_estimates_with_filters():
    response = client.get(
        "/api/documents/estimates",
        params={
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "is_posted": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
```

---

## Статус реализации

- [ ] Estimates - параметры фильтрации
- [ ] Estimates - колонка author
- [ ] Timesheets - параметры фильтрации
- [ ] Timesheets - колонки author, total_hours
- [ ] Counterparties - параметры + колонки
- [ ] Counterparties - bulk-delete
- [ ] Objects - параметры + колонки
- [ ] Objects - bulk-delete
- [ ] Persons - параметры + колонки
- [ ] Persons - bulk-delete
- [ ] Works - параметры + колонки
- [ ] Works - bulk-delete
- [ ] Тестирование
- [ ] Документация

**Ожидаемое время:** 3 дня
