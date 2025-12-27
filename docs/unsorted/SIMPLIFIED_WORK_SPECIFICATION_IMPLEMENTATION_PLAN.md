# План реализации упрощенной спецификации работ

## Обзор изменений

Данный план описывает изменения во всех компонентах системы для реализации упрощенной спецификации работ, которая заменяет сложную систему cost_item_materials на прямое добавление строк спецификации.

## 1. Изменения в базе данных

### Новая таблица work_specifications
```sql
CREATE TABLE work_specifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    component_type VARCHAR(20) NOT NULL, -- 'Material', 'Labor', 'Equipment', 'Other'
    component_name VARCHAR(500) NOT NULL,
    unit_id INTEGER,
    consumption_rate DECIMAL(15,6) NOT NULL DEFAULT 0,
    unit_price DECIMAL(15,2) NOT NULL DEFAULT 0,
    total_cost DECIMAL(15,2) GENERATED ALWAYS AS (consumption_rate * unit_price) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    marked_for_deletion BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES units(id)
);
```

### Миграция данных
1. Создать новую таблицу work_specifications
2. Мигрировать данные из cost_item_materials:
   - Cost items (где material_id IS NULL) → component_type = 'Labor'
   - Materials (где material_id IS NOT NULL) → component_type = 'Material'
3. Сохранить старую таблицу для совместимости
4. Добавить feature flag для переключения между системами

## 2. Изменения в Desktop приложении (Python/Qt)

### Файлы для изменения:

#### `src/data/repositories/work_specification_repository.py` (новый файл)
```python
class WorkSpecificationRepository:
    def get_by_work_id(self, work_id: int) -> List[WorkSpecification]
    def create(self, specification: WorkSpecification) -> int
    def update(self, specification: WorkSpecification) -> bool
    def delete(self, specification_id: int) -> bool
    def copy_from_work(self, target_work_id: int, source_work_id: int) -> bool
    def get_totals_by_type(self, work_id: int) -> Dict[str, Decimal]
```

#### `src/views/widgets/work_specification_widget.py` (новый файл)
- Заменяет cost_items_table.py и materials_table.py
- QTableWidget с колонками: Тип, Наименование, Ед.изм, Норма, Цена, Сумма
- Inline редактирование для норм расхода и цен
- Контекстное меню для дублирования и удаления

#### `src/views/dialogs/specification_entry_dialog.py` (новый файл)
- Диалог для добавления/редактирования записей спецификации
- Выбор типа компонента (Material, Labor, Equipment, Other)
- Автодополнение для единиц измерения

#### Изменения в `src/views/work_form.py`
```python
# Заменить:
self.cost_items_table = CostItemsTable()
self.materials_table = MaterialsTable()

# На:
self.specification_widget = WorkSpecificationWidget()

# Добавить вкладки:
tab_widget = QTabWidget()
tab_widget.addTab(basic_info_widget, "Основные данные")
tab_widget.addTab(self.specification_widget, "Спецификация")
```

### Новые функции:
1. **Прямое добавление компонентов** без выбора из справочников
2. **Группировка по типам** с подсчетом итогов
3. **Импорт/экспорт Excel** для спецификаций
4. **Копирование спецификации** между работами
5. **Шаблоны спецификаций** для типовых работ

## 3. Изменения в Web клиенте (Vue 3 + TypeScript)

### Новые файлы:

#### `web-client/src/types/work-specification.ts`
```typescript
export interface WorkSpecification {
  id?: number
  work_id: number
  component_type: ComponentType
  component_name: string
  unit_id?: number
  unit_name?: string
  consumption_rate: number
  unit_price: number
  total_cost: number
}

export enum ComponentType {
  Material = 'Material',
  Labor = 'Labor',
  Equipment = 'Equipment',
  Other = 'Other'
}
```

#### `web-client/src/api/work-specification.ts`
```typescript
export const workSpecificationApi = {
  getByWorkId: (workId: number) => Promise<WorkSpecification[]>
  create: (spec: WorkSpecificationCreate) => Promise<WorkSpecification>
  update: (id: number, spec: WorkSpecificationUpdate) => Promise<WorkSpecification>
  delete: (id: number) => Promise<void>
  copyFromWork: (targetWorkId: number, sourceWorkId: number) => Promise<void>
  exportToExcel: (workId: number) => Promise<Blob>
  importFromExcel: (workId: number, file: File) => Promise<void>
}
```

#### `web-client/src/components/work/WorkSpecificationPanel.vue`
- Основной компонент для управления спецификацией
- Таблица с inline редактированием
- Кнопки добавления, удаления, копирования
- Отображение итогов по типам компонентов

#### `web-client/src/components/work/SpecificationEntryForm.vue`
- Форма для добавления/редактирования записей
- Выбор типа компонента
- Валидация полей

#### `web-client/src/composables/useWorkSpecification.ts`
```typescript
export function useWorkSpecification(workId: Ref<number>) {
  const specifications = ref<WorkSpecification[]>([])
  const totalsByType = computed(() => calculateTotalsByType(specifications.value))
  const grandTotal = computed(() => calculateGrandTotal(specifications.value))
  
  const addSpecification = async (spec: WorkSpecificationCreate) => { ... }
  const updateSpecification = async (id: number, spec: WorkSpecificationUpdate) => { ... }
  const deleteSpecification = async (id: number) => { ... }
  
  return {
    specifications,
    totalsByType,
    grandTotal,
    addSpecification,
    updateSpecification,
    deleteSpecification
  }
}
```

### Изменения в существующих файлах:

#### `web-client/src/components/work/WorkForm.vue`
```vue
<template>
  <div class="work-form">
    <q-tabs v-model="activeTab">
      <q-tab name="basic" label="Основные данные" />
      <q-tab name="specification" label="Спецификация" />
    </q-tabs>
    
    <q-tab-panels v-model="activeTab">
      <q-tab-panel name="basic">
        <WorkBasicInfo v-model="work" />
      </q-tab-panel>
      <q-tab-panel name="specification">
        <WorkSpecificationPanel :work-id="work.id" />
      </q-tab-panel>
    </q-tab-panels>
  </div>
</template>
```

## 4. Изменения в API (FastAPI)

### Новые файлы:

#### `api/models/work_specification.py`
```python
class WorkSpecificationBase(BaseModel):
    work_id: int
    component_type: str
    component_name: str
    unit_id: Optional[int] = None
    consumption_rate: float = Field(gt=0)
    unit_price: float = Field(ge=0)

class WorkSpecificationCreate(WorkSpecificationBase):
    pass

class WorkSpecification(WorkSpecificationBase):
    id: int
    total_cost: float
    unit_name: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
```

#### `api/endpoints/work_specifications.py`
```python
@router.get("/works/{work_id}/specifications")
async def get_work_specifications(work_id: int) -> List[WorkSpecification]:
    ...

@router.post("/works/{work_id}/specifications")
async def create_specification(work_id: int, spec: WorkSpecificationCreate) -> WorkSpecification:
    ...

@router.put("/works/{work_id}/specifications/{spec_id}")
async def update_specification(work_id: int, spec_id: int, spec: WorkSpecificationUpdate) -> WorkSpecification:
    ...

@router.delete("/works/{work_id}/specifications/{spec_id}")
async def delete_specification(work_id: int, spec_id: int):
    ...

@router.post("/works/{work_id}/specifications/copy-from/{source_work_id}")
async def copy_specifications(work_id: int, source_work_id: int):
    ...
```

### Изменения в `api/main.py`
```python
from api.endpoints import work_specifications

app.include_router(work_specifications.router, prefix="/api", tags=["work-specifications"])
```

## 5. Изменения в DBF Importer

### Файлы для изменения:

#### `dbf_importer/core/importer.py`
```python
def import_work_specifications(self, dbf_path: str):
    """Импорт спецификаций работ из DBF файлов"""
    # Чтение данных о составе работ из DBF
    # Определение типа компонента по данным
    # Создание записей work_specifications
    
def detect_component_type(self, dbf_record) -> str:
    """Определение типа компонента по данным DBF"""
    # Логика определения: Material, Labor, Equipment, Other
    
def map_dbf_units(self, dbf_unit: str) -> int:
    """Сопоставление единиц измерения DBF с системными"""
```

#### Новые поля для импорта:
- Состав работ → work_specifications
- Нормы расхода материалов → consumption_rate
- Расценки → unit_price
- Типы компонентов → component_type

## 6. Миграция и совместимость

### Этапы миграции:
1. **Этап 1**: Создание новой таблицы work_specifications
2. **Этап 2**: Миграция данных из cost_item_materials
3. **Этап 3**: Реализация новой функциональности с feature flag
4. **Этап 4**: Тестирование и отладка
5. **Этап 5**: Переключение на новую систему по умолчанию
6. **Этап 6**: Удаление старого кода (опционально)

### Feature Flag
```python
# В конфигурации
USE_SIMPLIFIED_SPECIFICATIONS = True

# В коде
if settings.USE_SIMPLIFIED_SPECIFICATIONS:
    return work_specification_repository.get_by_work_id(work_id)
else:
    return cost_item_materials_repository.get_by_work_id(work_id)
```

### Обратная совместимость
- Создать представления (views) для эмуляции старых таблиц
- Поддержать старые API endpoints в режиме совместимости
- Обеспечить работу существующих отчетов

## 7. Преимущества новой системы

### Для пользователей:
1. **Простота использования** - прямое добавление компонентов без выбора из справочников
2. **Понятный workflow** - добавление строки = добавление компонента в спецификацию
3. **Гибкость** - возможность создавать любые компоненты без предварительного создания в справочниках
4. **Наглядность** - четкое разделение по типам компонентов с итогами

### Для разработчиков:
1. **Упрощенная модель данных** - одна таблица вместо сложных связей
2. **Лучшая производительность** - меньше JOIN операций
3. **Проще поддержка** - понятная структура данных
4. **Легче тестирование** - простые CRUD операции

### Для системы:
1. **Меньше сложности** - убираем искусственные ограничения
2. **Лучшая масштабируемость** - простая структура данных
3. **Проще миграция** - прямое сопоставление данных
4. **Меньше багов** - простая логика работы

## 8. Риски и митигация

### Риски:
1. **Потеря данных при миграции** - тщательное тестирование миграционных скриптов
2. **Нарушение существующих интеграций** - поддержка обратной совместимости
3. **Сопротивление пользователей** - постепенное внедрение с обучением

### Митигация:
1. **Поэтапное внедрение** с feature flags
2. **Тщательное тестирование** на копиях продуктивных данных
3. **Документация** и обучение пользователей
4. **Rollback план** для возврата к старой системе

## 9. План внедрения

### Неделя 1-2: Подготовка
- Создание новой схемы БД
- Разработка миграционных скриптов
- Настройка feature flags

### Неделя 3-4: Backend
- Реализация API endpoints
- Создание repository слоя
- Unit тесты

### Неделя 5-6: Desktop приложение
- Новые виджеты для спецификации
- Интеграция в WorkForm
- Тестирование UI

### Неделя 7-8: Web клиент
- Vue компоненты
- Composables
- Интеграция в WorkForm

### Неделя 9-10: DBF Importer
- Обновление логики импорта
- Тестирование с реальными данными
- Валидация результатов

### Неделя 11-12: Тестирование и внедрение
- Интеграционное тестирование
- Пользовательское тестирование
- Постепенное внедрение в продакшн

Этот план обеспечивает плавный переход от сложной системы cost_item_materials к простой и понятной системе work_specifications, решая основную проблему с непонятным use case выбора готовых cost items из справочника.