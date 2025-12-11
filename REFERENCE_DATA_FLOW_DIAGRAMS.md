# Диаграммы связей и потоков данных справочников

## 1. Общая архитектура репозиториев

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND REPOSITORIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │ WorkRepository   │      │ UnitRepository   │                │
│  │                  │      │                  │                │
│  │ - get_all()      │      │ - get_all()      │                │
│  │ - get_by_id()    │      │ - get_by_id()    │                │
│  │ - create()       │      │ - create()       │                │
│  │ - update()       │      │ - update()       │                │
│  └────────┬─────────┘      └────────┬─────────┘                │
│           │                         │                            │
│           │  references             │                            │
│           └─────────────────────────┘                            │
│                                                                   │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │ CostItemRepo     │      │ MaterialRepo     │                │
│  │                  │      │                  │                │
│  │ - get_all()      │      │ - get_all()      │                │
│  │ - get_by_id()    │      │ - get_by_id()    │                │
│  │ - create()       │      │ - create()       │                │
│  │ - update()       │      │ - update()       │                │
│  └────────┬─────────┘      └────────┬─────────┘                │
│           │                         │                            │
│           │  references             │                            │
│           └─────────────────────────┘                            │
│                                                                   │
│  ┌──────────────────────────────────────────┐                   │
│  │ CostItemMaterialRepository               │                   │
│  │                                          │                   │
│  │ - get_composition(work_id)               │                   │
│  │ - add_cost_item(work_id, cost_item_id)   │                   │
│  │ - add_material(work_id, data)            │                   │
│  │ - update_material_quantity()             │                   │
│  │ - remove_cost_item()                     │                   │
│  │ - remove_material()                      │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Структура данных и связи между таблицами

```
┌─────────────────┐
│     Units       │
│─────────────────│
│ id (PK)         │
│ name            │
│ abbreviation    │
└────────┬────────┘
         │
         │ referenced by
         ├──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
┌─────────────────┐              ┌─────────────────┐
│     Works       │              │   CostItems     │
│─────────────────│              │─────────────────│
│ id (PK)         │              │ id (PK)         │
│ code            │              │ code            │
│ name            │              │ description     │
│ unit_id (FK)    │◄─┐           │ price           │
│ price           │  │           │ unit_id (FK)    │
│ labor_rate      │  │           │ is_folder       │
│ parent_id (FK)  │──┘           │ parent_id (FK)  │◄─┐
│ is_group        │              └────────┬────────┘  │
└────────┬────────┘                       └───────────┘
         │                                  │
         │                                  │
         │         referenced by            │
         │              ┌───────────────────┘
         │              │
         ▼              ▼
┌──────────────────────────────────┐
│    CostItemMaterial              │
│──────────────────────────────────│
│ id (PK)                          │
│ work_id (FK) ────────────────────┼──► Work
│ cost_item_id (FK) ───────────────┼──► CostItem
│ material_id (FK, nullable) ──────┼──► Material
│ quantity_per_unit                │
└──────────────────────────────────┘
         │
         │ references (when material_id IS NOT NULL)
         ▼
┌─────────────────┐
│   Materials     │
│─────────────────│
│ id (PK)         │
│ code            │
│ description     │
│ price           │
│ unit_id (FK)    │──► Unit
└─────────────────┘
```

## 3. Поток данных при загрузке формы работы

```
USER OPENS WORK FORM
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ WorkForm.vue - onMounted()                                   │
└─────────────────────────────────────────────────────────────┘
        │
        ├──► 1. Load Reference Data (parallel)
        │    │
        │    ├──► GET /units
        │    │    └──► UnitRepository.get_all()
        │    │         └──► Cache in useReferenceCache
        │    │
        │    └──► GET /works
        │         └──► WorkRepository.get_all()
        │              └──► Cache in useReferenceCache
        │
        └──► 2. Load Work Composition
             │
             ├──► GET /works/{id}
             │    └──► WorkRepository.get_by_id()
             │         └──► Returns: Work basic info
             │
             └──► GET /works/{id}/composition
                  └──► CostItemMaterialRepository.get_composition()
                       │
                       ├──► Query CostItemMaterial WHERE work_id = {id}
                       │    │
                       │    ├──► JOIN CostItem (for cost item details)
                       │    │    └──► JOIN Unit (for cost item unit name)
                       │    │
                       │    └──► JOIN Material (for material details)
                       │         └──► JOIN Unit (for material unit name)
                       │
                       └──► Returns:
                            ├─ cost_items[] (material_id IS NULL)
                            └─ materials[] (material_id IS NOT NULL)

┌─────────────────────────────────────────────────────────────┐
│ RESULT: Form populated with:                                 │
│ - Work basic info (name, code, unit, price, etc.)           │
│ - List of cost items associated with work                   │
│ - List of materials associated with work                    │
│ - Reference data cached for dropdowns                       │
└─────────────────────────────────────────────────────────────┘
```

## 4. Поток добавления статьи затрат (Cost Item)

```
USER CLICKS "Add Cost Item"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ CostItemsTable.vue - showAddDialog = true                   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ CostItemListForm.vue - Dialog Opens                         │
└─────────────────────────────────────────────────────────────┘
        │
        ├──► 1. Load Cost Items (if not cached)
        │    │
        │    └──► GET /cost-items?page=1&limit=50
        │         └──► CostItemRepository.get_all()
        │              │
        │              ├──► Query: SELECT * FROM cost_items
        │              │           WHERE marked_for_deletion = false
        │              │           AND is_folder = false
        │              │           ORDER BY code
        │              │
        │              └──► Returns: Paginated list of cost items
        │
        ├──► 2. User searches/filters
        │    │
        │    └──► GET /cost-items?search={query}
        │         └──► Filter by code or description
        │
        └──► 3. User selects cost item
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ WorkForm.vue - handleAddCostItem(costItem)                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ useWorkComposition.ts - addCostItem(costItemId)             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ API: POST /works/{work_id}/cost-items                       │
│ Body: { "cost_item_id": 123 }                               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: add_cost_item_to_work()                            │
│                                                              │
│ 1. Validate work exists                                     │
│    └──► WorkRepository.get_by_id(work_id)                   │
│                                                              │
│ 2. Validate cost item exists                                │
│    └──► CostItemRepository.get_by_id(cost_item_id)          │
│                                                              │
│ 3. Check for duplicates                                     │
│    └──► Query: SELECT * FROM cost_item_material             │
│              WHERE work_id = {id}                            │
│              AND cost_item_id = {cost_item_id}              │
│              AND material_id IS NULL                         │
│                                                              │
│ 4. Create association                                       │
│    └──► INSERT INTO cost_item_material                      │
│         (work_id, cost_item_id, material_id, quantity)      │
│         VALUES ({work_id}, {cost_item_id}, NULL, 0.0)       │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ RESULT: Cost item added to work                             │
│ - New row in CostItemMaterial table                         │
│ - Frontend updates costItems[] array                        │
│ - Table re-renders with new cost item                       │
└─────────────────────────────────────────────────────────────┘
```

## 5. Поток добавления материала (Material)

```
USER CLICKS "Add Material"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ MaterialsTable.vue - showAddDialog = true                   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ MaterialSelectorDialog.vue - Dialog Opens                   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Select Cost Item                                    │
│ - Shows dropdown with cost items already added to work      │
│ - Source: costItems[] from useWorkComposition               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Select Material                                     │
│                                                              │
│ Load Materials:                                              │
│ GET /materials?page=1&limit=50                              │
│ └──► MaterialRepository.get_all()                           │
│      │                                                       │
│      ├──► Query: SELECT * FROM materials                    │
│      │           WHERE marked_for_deletion = false          │
│      │           ORDER BY code                               │
│      │                                                       │
│      └──► Returns: Paginated list of materials              │
│                                                              │
│ User searches/filters:                                       │
│ GET /materials?search={query}                               │
│ └──► Filter by code or description                          │
│                                                              │
│ Validation:                                                  │
│ - Check if material already added to selected cost item     │
│ - Disable already added materials                           │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Enter Quantity                                      │
│ - User enters quantity_per_unit                             │
│ - Validation: must be > 0                                   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ WorkForm.vue - handleAddMaterial(data)                      │
│ data = {                                                     │
│   costItemId: 123,                                          │
│   materialId: 456,                                          │
│   quantity: 2.5                                             │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ useWorkComposition.ts - addMaterial()                       │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ API: POST /works/{work_id}/materials                        │
│ Body: {                                                      │
│   "work_id": 1,                                             │
│   "cost_item_id": 123,                                      │
│   "material_id": 456,                                       │
│   "quantity_per_unit": 2.5                                  │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: add_material_to_work()                             │
│                                                              │
│ 1. Validate quantity > 0                                    │
│                                                              │
│ 2. Validate work exists                                     │
│    └──► WorkRepository.get_by_id(work_id)                   │
│                                                              │
│ 3. Verify cost item is added to work                        │
│    └──► Query: SELECT * FROM cost_item_material             │
│              WHERE work_id = {id}                            │
│              AND cost_item_id = {cost_item_id}              │
│              AND material_id IS NULL                         │
│    └──► If not found: Error "Cost item must be added first" │
│                                                              │
│ 4. Validate material exists                                 │
│    └──► MaterialRepository.get_by_id(material_id)           │
│                                                              │
│ 5. Check for duplicates                                     │
│    └──► Query: SELECT * FROM cost_item_material             │
│              WHERE work_id = {id}                            │
│              AND cost_item_id = {cost_item_id}              │
│              AND material_id = {material_id}                │
│                                                              │
│ 6. Create association                                       │
│    └──► INSERT INTO cost_item_material                      │
│         (work_id, cost_item_id, material_id, quantity)      │
│         VALUES ({work_id}, {cost_item_id},                  │
│                 {material_id}, {quantity})                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ RESULT: Material added to work                              │
│ - New row in CostItemMaterial table                         │
│ - Frontend updates materials[] array                        │
│ - Table re-renders with new material                        │
│ - Total cost recalculated                                   │
└─────────────────────────────────────────────────────────────┘
```

## 6. Расчет стоимости работы

```
┌─────────────────────────────────────────────────────────────┐
│ useWorkComposition.ts - totalCost (computed)                │
└─────────────────────────────────────────────────────────────┘
        │
        ├──► Calculate Cost Items Total
        │    │
        │    └──► For each item in costItems[]:
        │         └──► sum += item.cost_item.price
        │
        ├──► Calculate Materials Total
        │    │
        │    └──► For each item in materials[]:
        │         └──► sum += item.material.price * item.quantity_per_unit
        │
        └──► Total Cost = Cost Items Total + Materials Total

┌─────────────────────────────────────────────────────────────┐
│ Example Calculation:                                         │
│                                                              │
│ Work: "Кладка кирпича"                                      │
│                                                              │
│ Cost Items:                                                  │
│ - Работа каменщика: 500.00 руб                             │
│ - Работа подсобника: 300.00 руб                            │
│ Subtotal: 800.00 руб                                        │
│                                                              │
│ Materials:                                                   │
│ - Кирпич: 15.00 руб × 400 шт = 6,000.00 руб               │
│ - Раствор: 250.00 руб × 0.5 м³ = 125.00 руб               │
│ Subtotal: 6,125.00 руб                                      │
│                                                              │
│ TOTAL: 6,925.00 руб                                         │
└─────────────────────────────────────────────────────────────┘
```

## 7. Кэширование справочных данных

```
┌─────────────────────────────────────────────────────────────┐
│ useReferenceCache.ts - Caching Strategy                     │
└─────────────────────────────────────────────────────────────┘
        │
        ├──► Units Cache
        │    │
        │    ├──► Key: 'all'
        │    ├──► TTL: 5 minutes
        │    └──► Invalidate on: create/update/delete unit
        │
        ├──► Works Cache
        │    │
        │    ├──► Key: 'all'
        │    ├──► TTL: 5 minutes
        │    └──► Invalidate on: create/update/delete work
        │
        ├──► Cost Items Cache
        │    │
        │    ├──► Key: 'page_{page}_search_{query}'
        │    ├──► TTL: 5 minutes
        │    └──► Invalidate on: create/update/delete cost item
        │
        └──► Materials Cache
             │
             ├──► Key: 'page_{page}_search_{query}'
             ├──► TTL: 5 minutes
             └──► Invalidate on: create/update/delete material

┌─────────────────────────────────────────────────────────────┐
│ Cache Flow:                                                  │
│                                                              │
│ 1. Component requests data                                  │
│    └──► Check cache                                         │
│         ├──► If found and not expired: return cached data   │
│         └──► If not found or expired:                       │
│              ├──► Fetch from API                            │
│              ├──► Store in cache                            │
│              └──► Return data                               │
│                                                              │
│ 2. User modifies data                                       │
│    └──► Invalidate related cache entries                    │
│         └──► Next request will fetch fresh data             │
└─────────────────────────────────────────────────────────────┘
```

## 8. Валидация и бизнес-правила

```
┌─────────────────────────────────────────────────────────────┐
│ VALIDATION RULES                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Adding Cost Item:                                            │
│ ✓ Work must exist                                           │
│ ✓ Cost item must exist                                      │
│ ✓ Cost item must not be a folder (is_folder = false)       │
│ ✓ No duplicate cost items per work                          │
│                                                              │
│ Removing Cost Item:                                          │
│ ✓ Cannot remove if has associated materials                 │
│ ✓ Must delete materials first                               │
│                                                              │
│ Adding Material:                                             │
│ ✓ Work must exist                                           │
│ ✓ Cost item must be added to work first                     │
│ ✓ Material must exist                                       │
│ ✓ Quantity must be > 0                                      │
│ ✓ No duplicate material-cost item combinations              │
│                                                              │
│ Updating Material Quantity:                                  │
│ ✓ Quantity must be > 0                                      │
│ ✓ Association must exist                                    │
│                                                              │
│ Changing Material Cost Item:                                 │
│ ✓ New cost item must be added to work                       │
│ ✓ No duplicate after change                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 9. Последовательность операций при сохранении

```
USER CLICKS "Save"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ WorkForm.vue - handleSave()                                  │
│                                                              │
│ 1. Validate form                                            │
│    ├──► Check required fields                               │
│    ├──► Validate group work constraints                     │
│    └──► Validate material quantities > 0                    │
│                                                              │
│ 2. If validation fails:                                     │
│    └──► Show error, stop                                    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ useWorkComposition.ts - saveWork()                          │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ API: PUT /works/{work_id}                                   │
│ Body: {                                                      │
│   "name": "...",                                            │
│   "code": "...",                                            │
│   "unit_id": 1,                                             │
│   "price": 100.00,                                          │
│   "labor_rate": 50.00,                                      │
│   "parent_id": null,                                        │
│   "is_group": false                                         │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: WorkRepository.update()                            │
│                                                              │
│ UPDATE works                                                 │
│ SET name = ?, code = ?, unit_id = ?, ...                   │
│ WHERE id = ?                                                 │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ RESULT: Work saved                                           │
│ - Database updated                                           │
│ - Cache invalidated                                          │
│ - Success message shown                                      │
│ - Form emits 'saved' event                                  │
└─────────────────────────────────────────────────────────────┘

NOTE: Cost items and materials are saved immediately when added,
      not on form save. This provides better UX and data integrity.
```

## 10. Диаграмма состояний компонента WorkForm

```

        ┌─────────────┐
        │   INITIAL   │
        └──────┬──────┘
               │
               │ onMounted()
               ▼
        ┌─────────────┐
        │   LOADING   │◄──────────────┐
        │             │               │
        │ - Loading   │               │
        │   reference │               │
        │   data      │               │
        │ - Loading   │               │
        │   work      │               │
        │   composition│              │
        └──────┬──────┘               │
               │                      │
               │ Success              │ Retry
               ▼                      │
        ┌─────────────┐               │
        │    READY    │               │
        │             │               │
        │ - Form      │               │
        │   editable  │               │
        │ - Can add   │               │
        │   items     │               │
        └──────┬──────┘               │
               │                      │
               ├──► Add Cost Item ────┤
               │                      │
               ├──► Add Material ─────┤
               │                      │
               ├──► Edit Quantity ────┤
               │                      │
               │ Save clicked         │
               ▼                      │
        ┌─────────────┐               │
        │   SAVING    │               │
        │             │               │
        │ - Disabled  │               │
        │   form      │               │
        │ - Spinner   │               │
        └──────┬──────┘               │
               │                      │
               ├──► Success ──────────┤
               │    (emit 'saved')    │
               │                      │
               └──► Error ────────────┘
                    (show error)

        ┌─────────────┐
        │    ERROR    │
        │             │
        │ - Show      │
        │   error     │
        │   banner    │
        │ - Allow     │
        │   retry     │
        └─────────────┘
```

## Резюме

### Ключевые моменты архитектуры:

1. **Разделение ответственности**
   - Репозитории отвечают за доступ к данным
   - API endpoints обрабатывают HTTP запросы и валидацию
   - Composables управляют состоянием на фронтенде
   - Компоненты отвечают за UI

2. **Связь данных**
   - CostItemMaterial - центральная таблица связей
   - Одна запись с material_id = NULL = статья затрат
   - Одна запись с material_id != NULL = материал
   - Все связано через work_id и cost_item_id

3. **Валидация на нескольких уровнях**
   - Frontend: немедленная обратная связь
   - API: бизнес-правила и целостность данных
   - Database: ограничения и внешние ключи

4. **Оптимизация производительности**
   - Кэширование справочных данных
   - Пагинация больших списков
   - Ленивая загрузка данных
   - Оптимистичные обновления UI

5. **Пользовательский опыт**
   - Немедленное сохранение изменений
   - Валидация в реальном времени
   - Понятные сообщения об ошибках
   - Предотвращение некорректных операций
