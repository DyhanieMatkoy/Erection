# Design Document

## Overview

The Work Composition Form is a comprehensive interface for defining the complete composition of construction work types. It enables users to specify both cost items (трудозатраты в нормочасах - labor requirements) and materials (нормы расхода материалов - material consumption rates) in a single unified editing experience.

The form implements a three-tier relationship model:
- **Work** (e.g., "Штукатурка стен" - Wall Plastering)
- **CostItem** (e.g., "Труд рабочих" - Labor, "Аренда оборудования" - Equipment rental)
- **Material** (e.g., "Цемент" - Cement, "Песок" - Sand)

This design enables accurate cost estimation and material planning by establishing standard consumption rates at the work catalog level, which can then be automatically applied when works are added to estimates.

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Work Composition Form                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Basic      │  │  Cost Items  │  │  Materials   │     │
│  │   Info       │  │    Table     │  │    Table     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
├─────────────────────────────────────────────────────────────┤
│  /api/works/{id}                                            │
│  /api/works/{id}/cost-items                                 │
│  /api/works/{id}/materials                                  │
│  /api/cost-items (selector)                                 │
│  /api/materials (selector)                                  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                        Database                              │
├─────────────────────────────────────────────────────────────┤
│  works                                                       │
│  cost_items                                                  │
│  materials                                                   │
│  cost_item_materials (association table)                    │
│  units                                                       │
└─────────────────────────────────────────────────────────────┘
```


### Component Architecture

The frontend follows a composable architecture pattern:

```
WorkForm (Main Container)
├── WorkBasicInfo (Basic fields component)
│   ├── TextInput (code, name)
│   ├── UnitListForm (unit_id selection from full list)
│   ├── NumberInput (price, labor_rate)
│   ├── Checkbox (is_group)
│   └── WorkListForm (parent_id selection from full hierarchical list)
├── CostItemsTable (Cost items management)
│   ├── TableHeader
│   ├── CostItemRow[] (repeating rows)
│   │   └── ActionButtons (delete)
│   ├── AddButton
│   └── CostItemListForm (Full-scale list form)
│       ├── SearchInput
│       ├── FilterControls
│       ├── HierarchicalTable (all cost items)
│       ├── Pagination
│       └── SelectionActions (OK/Cancel)
└── MaterialsTable (Materials management)
    ├── TableHeader
    ├── MaterialRow[] (repeating rows)
    │   ├── CostItemListForm (full list for reassignment)
    │   ├── EditableQuantityCell
    │   └── ActionButtons (delete)
    ├── AddButton
    └── MaterialListForm (Full-scale list form)
        ├── CostItemListForm (step 1: select from full list)
        ├── MaterialSearchAndList (step 2: full list with search)
        │   ├── SearchInput
        │   ├── FilterControls
        │   ├── MaterialsTable (all materials)
        │   └── Pagination
        ├── QuantityInput (step 3)
        └── SelectionActions (OK/Cancel)
```

### List Form Pattern

Instead of dropdown selectors, the system uses full-scale list forms for selecting cost items, materials, units, and parent works. This provides better usability for large catalogs:

**List Form Features:**
- Full table/list view of all available items
- Search and filter capabilities
- **Substring entry**: Type code or name fragment to quickly filter
- Pagination for large datasets
- Hierarchical display (for cost items and works)
- Multi-column sorting
- Clear selection state
- OK/Cancel actions

**Substring Entry Feature:**
Reference type fields (cost items, materials, units, parent works) support quick entry by substring:
- User can type directly in the field
- System searches by code OR name as user types
- Shows matching results in real-time
- User can select from filtered results or press Enter to select first match
- Example: Typing "цем" instantly filters to "Цемент М400" and similar items
- Example: Typing "M001" filters to materials with code "M001"

**List Form vs Dropdown:**
- Dropdowns: Limited to small datasets, poor search, no context
- List Forms: Handle thousands of items, rich filtering, full context, substring entry

**Example: Cost Item List Form**
```
┌─────────────────────────────────────────────────────────────┐
│  Select Cost Item                                      [X]  │
├─────────────────────────────────────────────────────────────┤
│  Search: [____________]  [🔍]  Filters: [All] [Items Only] │
├─────────────────────────────────────────────────────────────┤
│  Code    │ Description              │ Unit │ Price │ Labor │
├──────────┼──────────────────────────┼──────┼───────┼───────┤
│  1.01    │ Труд рабочих             │ час  │ 500   │ 2.5   │
│  1.02    │ Аренда оборудования      │ час  │ 200   │ 0.5   │
│  1.03    │ Материалы                │ руб  │ 0     │ 0     │
│  ...     │ ...                      │ ...  │ ...   │ ...   │
├─────────────────────────────────────────────────────────────┤
│  Page 1 of 45                    [< Previous] [Next >]     │
├─────────────────────────────────────────────────────────────┤
│                                          [Cancel]  [Select] │
└─────────────────────────────────────────────────────────────┘
```

**Example: Material List Form**
```
┌─────────────────────────────────────────────────────────────┐
│  Select Material                                       [X]  │
├─────────────────────────────────────────────────────────────┤
│  Search: [____________]  [🔍]  Unit: [All ▼]               │
├─────────────────────────────────────────────────────────────┤
│  Code    │ Description              │ Unit │ Price         │
├──────────┼──────────────────────────┼──────┼───────────────┤
│  M001    │ Цемент М400              │ т    │ 5,000.00      │
│  M002    │ Песок речной             │ т    │ 800.00        │
│  M003    │ Щебень фракция 5-20      │ т    │ 1,200.00      │
│  ...     │ ...                      │ ...  │ ...           │
├─────────────────────────────────────────────────────────────┤
│  Page 1 of 120                   [< Previous] [Next >]     │
├─────────────────────────────────────────────────────────────┤
│                                          [Cancel]  [Select] │
└─────────────────────────────────────────────────────────────┘
```

### State Management

The form uses a composable pattern for state management:

```typescript
// useWorkComposition.ts
const workComposition = {
  work: ref<Work | null>(null),
  costItems: ref<CostItemMaterial[]>([]),
  materials: ref<CostItemMaterial[]>([]),
  totalCost: computed(() => calculateTotalCost()),
  
  // Actions
  loadWork: async (workId: number) => {...},
  saveWork: async () => {...},
  addCostItem: async (costItemId: number) => {...},
  removeCostItem: async (costItemId: number) => {...},
  addMaterial: async (costItemId: number, materialId: number, quantity: number) => {...},
  updateMaterialQuantity: async (id: number, quantity: number) => {...},
  changeMaterialCostItem: async (id: number, newCostItemId: number) => {...},
  removeMaterial: async (id: number) => {...}
}
```

## Components and Interfaces

### Backend Models

```python
# SQLAlchemy Models
class Work(Base):
    __tablename__ = "works"
    id = Column(Integer, primary_key=True)
    code = Column(String(50))
    name = Column(String(500), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"))
    price = Column(Float, default=0.0)
    labor_rate = Column(Float, default=0.0)
    parent_id = Column(Integer, ForeignKey("works.id"))
    is_group = Column(Boolean, default=False)
    marked_for_deletion = Column(Boolean, default=False)
    
    # Relationships
    unit = relationship("Unit")
    parent = relationship("Work", remote_side=[id])
    cost_items = relationship("CostItemMaterial", 
                             foreign_keys="CostItemMaterial.work_id",
                             primaryjoin="and_(Work.id==CostItemMaterial.work_id, "
                                        "CostItemMaterial.material_id==None)")
    materials = relationship("CostItemMaterial",
                           foreign_keys="CostItemMaterial.work_id",
                           primaryjoin="and_(Work.id==CostItemMaterial.work_id, "
                                      "CostItemMaterial.material_id!=None)")

class CostItemMaterial(Base):
    __tablename__ = "cost_item_materials"
    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    cost_item_id = Column(Integer, ForeignKey("cost_items.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"))
    quantity_per_unit = Column(Float, default=0.0)
    
    # Relationships
    work = relationship("Work")
    cost_item = relationship("CostItem")
    material = relationship("Material")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('work_id', 'cost_item_id', 'material_id', 
                        name='uq_work_cost_item_material'),
    )
```


### API Endpoints

```python
# Work CRUD
GET    /api/works/{id}                    # Get work basic info
POST   /api/works                         # Create new work
PUT    /api/works/{id}                    # Update work basic info
DELETE /api/works/{id}                    # Soft delete work

# Work Composition
GET    /api/works/{id}/composition        # Get complete composition
POST   /api/works/{id}/cost-items         # Add cost item to work
DELETE /api/works/{id}/cost-items/{cost_item_id}  # Remove cost item
POST   /api/works/{id}/materials          # Add material to work
PUT    /api/works/{id}/materials/{id}     # Update material quantity/cost item
DELETE /api/works/{id}/materials/{id}     # Remove material

# List Forms (Full catalog access)
GET    /api/cost-items                    # Get all cost items (paginated, filterable)
  ?page={n}&limit={n}                     # Pagination
  &search={term}                          # Search by code or description
  &parent_id={id}                         # Filter by parent (hierarchical)
  &is_folder={bool}                       # Filter folders vs items
  
GET    /api/materials                     # Get all materials (paginated, filterable)
  ?page={n}&limit={n}                     # Pagination
  &search={term}                          # Search by code or description
  &unit_id={id}                           # Filter by unit
  
GET    /api/units                         # Get all units (full list)
GET    /api/works                         # Get all works (hierarchical, for parent selection)
  ?is_group={bool}                        # Filter to show only groups
```

### Frontend Models

```typescript
export interface Work {
  id: number
  code?: string
  name: string
  unit_id?: number
  unit_name?: string
  price: number
  labor_rate: number
  parent_id: number | null
  is_group: boolean
  marked_for_deletion: boolean
}

export interface CostItem {
  id: number
  parent_id: number | null
  code?: string
  description: string
  is_folder: boolean
  price: number
  unit_id?: number
  unit_name?: string
  labor_coefficient: number
  marked_for_deletion: boolean
}

export interface Material {
  id: number
  code?: string
  description: string
  price: number
  unit_id?: number
  unit_name?: string
  marked_for_deletion: boolean
}

export interface CostItemMaterial {
  id: number
  work_id: number
  cost_item_id: number
  material_id: number | null
  quantity_per_unit: number
  
  // Populated when joined
  cost_item?: CostItem
  material?: Material
}

export interface WorkComposition {
  work: Work
  cost_items: CostItemMaterial[]  // Where material_id is null
  materials: CostItemMaterial[]   // Where material_id is not null
  total_cost: number
}
```

## Data Models

### Database Schema

```sql
-- Works table (existing)
CREATE TABLE works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50),
    name VARCHAR(500) NOT NULL,
    unit_id INTEGER,
    price FLOAT DEFAULT 0.0,
    labor_rate FLOAT DEFAULT 0.0,
    parent_id INTEGER,
    is_group BOOLEAN DEFAULT FALSE,
    marked_for_deletion BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (unit_id) REFERENCES units(id),
    FOREIGN KEY (parent_id) REFERENCES works(id),
    
    INDEX idx_work_parent (parent_id),
    INDEX idx_work_name (name),
    INDEX idx_work_code (code)
);

-- Cost Item Materials association table (existing, with work_id added)
CREATE TABLE cost_item_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    cost_item_id INTEGER NOT NULL,
    material_id INTEGER,
    quantity_per_unit FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_item_id) REFERENCES cost_items(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
    
    INDEX idx_cost_item_material_work (work_id),
    INDEX idx_cost_item_material_cost_item (cost_item_id),
    INDEX idx_cost_item_material_material (material_id),
    UNIQUE (work_id, cost_item_id, material_id)
);
```

### Data Relationships

```
Work (1) ──────────────────> (N) CostItemMaterial
                                      │
                                      ├──> (1) CostItem
                                      └──> (0..1) Material

Key Points:
- work_id is required (NOT NULL)
- cost_item_id is required (NOT NULL)
- material_id is optional (can be NULL for cost item associations)
- When material_id is NULL: represents a cost item added to the work
- When material_id is NOT NULL: represents a material linked to a cost item for this work
- UNIQUE constraint prevents duplicate associations
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Work name validation
*For any* work submission, if the name is empty or contains only whitespace, the system should reject the submission with a validation error.
**Validates: Requirements 1.2, 11.1**

### Property 2: Work persistence round trip
*For any* valid work data, saving the work then retrieving it by ID should return equivalent data (same name, code, unit_id, price, labor_rate, is_group, parent_id).
**Validates: Requirements 1.5**

### Property 3: Group works cannot have price or labor rate
*For any* work where is_group is true, attempting to save with non-zero price or labor_rate should result in a validation error.
**Validates: Requirements 1.3, 11.2**

### Property 4: Parent work circular reference prevention
*For any* work, the parent_id cannot reference itself or any of its descendants in the hierarchy.
**Validates: Requirements 1.4, 15.3**

### Property 5: Cost item search filtering
*For any* search term and set of cost items, all returned results should contain the search term in either the code or description field (case-insensitive).
**Validates: Requirements 2.2, 14.2**

### Property 6: Cost item association creation
*For any* valid work and cost item, adding the cost item to the work should create a CostItemMaterial record with work_id, cost_item_id, and material_id=NULL.
**Validates: Requirements 2.3**

### Property 7: Cost item display completeness
*For any* cost item added to a work, the cost items table should display all required fields: code, description, unit_name, price, and labor_coefficient.
**Validates: Requirements 2.4, 9.1**

### Property 8: Duplicate cost item prevention
*For any* work with existing cost items, attempting to add a cost item that is already associated should be rejected with an error.
**Validates: Requirements 2.5**

### Property 9: Cost item deletion with materials check
*For any* cost item in a work, if it has associated materials (CostItemMaterial records where material_id is NOT NULL), deletion should be prevented with a warning message.
**Validates: Requirements 3.1, 3.2**

### Property 10: Cost item deletion without materials
*For any* cost item in a work with no associated materials, confirming deletion should remove all CostItemMaterial records where work_id matches and cost_item_id matches and material_id is NULL.
**Validates: Requirements 3.4**

### Property 11: Cost item deletion UI update
*For any* cost item deletion, after successful removal, the cost item should no longer appear in the cost items table.
**Validates: Requirements 3.5**

### Property 12: Material selector cost item filtering
*For any* work, the material selector dialog should only display cost items that are already associated with the work (exist in CostItemMaterial with this work_id).
**Validates: Requirements 4.2**

### Property 13: Material search filtering
*For any* search term and set of materials, all returned results should contain the search term in either the code or description field (case-insensitive).
**Validates: Requirements 4.3, 14.4**

### Property 14: Material quantity validation
*For any* material addition or quantity update, values that are zero, negative, or non-numeric should be rejected with a validation error.
**Validates: Requirements 4.4, 5.2, 11.3**

### Property 15: Material association creation
*For any* valid work, cost item, material, and quantity > 0, adding the material should create a CostItemMaterial record with all four values correctly set.
**Validates: Requirements 4.5**

### Property 16: Material quantity update
*For any* material in a work, updating the quantity_per_unit should persist the new value to the database while preserving work_id, cost_item_id, and material_id.
**Validates: Requirements 5.3**

### Property 17: Material total cost calculation
*For any* material, the total cost should equal material.price × quantity_per_unit.
**Validates: Requirements 5.4, 8.2, 10.5**

### Property 18: Material quantity validation revert
*For any* invalid quantity input (non-numeric or <= 0), the system should revert to the previous valid value and display an error message.
**Validates: Requirements 5.5**

### Property 19: Material cost item change preserves other fields
*For any* material, changing the cost_item_id should update only that field while maintaining the same work_id, material_id, and quantity_per_unit values.
**Validates: Requirements 6.3, 6.4**

### Property 20: Material cost item dropdown filtering
*For any* material row, the cost item dropdown should only contain cost items that are associated with the current work.
**Validates: Requirements 6.1**

### Property 21: Material deletion
*For any* material in a work, confirming deletion should remove the CostItemMaterial record where work_id, cost_item_id, and material_id all match.
**Validates: Requirements 7.2**

### Property 22: Material deletion UI update
*For any* material deletion, after successful removal, the material should no longer appear in the materials table.
**Validates: Requirements 7.3**

### Property 23: Total cost recalculation on material deletion
*For any* material deletion, the total work cost should be recalculated to exclude the deleted material's cost.
**Validates: Requirements 7.4**

### Property 24: Total cost includes cost items
*For any* work, the total cost should include the sum of all associated cost item prices.
**Validates: Requirements 8.1**

### Property 25: Total cost includes materials
*For any* work, the total cost should include the sum of all material costs (price × quantity_per_unit for each material).
**Validates: Requirements 8.2**

### Property 26: Total cost automatic recalculation
*For any* change to work composition (adding/removing cost items or materials, changing quantities), the total cost should be automatically recalculated.
**Validates: Requirements 8.3**

### Property 27: Total cost currency formatting
*For any* total cost display, the value should be formatted with appropriate currency symbols and decimal precision.
**Validates: Requirements 8.4**

### Property 28: Unit name retrieval via join
*For any* cost item or material displayed, the unit_name should be retrieved by joining with the units table using unit_id.
**Validates: Requirements 9.2, 10.2**

### Property 29: Cost item catalog fields read-only
*For any* cost item in the table, attempting to edit code, description, unit, price, or labor_coefficient should be prevented (only deletion allowed).
**Validates: Requirements 9.3**

### Property 30: Numeric value formatting
*For any* numeric value displayed (price, labor_coefficient, quantity), the value should be formatted with appropriate decimal precision.
**Validates: Requirements 9.5**

### Property 31: Material catalog fields read-only except quantity
*For any* material in the table, only the quantity_per_unit field should be editable; all other fields (code, description, unit, price) should be read-only.
**Validates: Requirements 10.3, 10.4**

### Property 32: Work name required validation
*For any* work save attempt, if the name field is empty, the system should prevent saving and display a validation error.
**Validates: Requirements 11.1**

### Property 33: Material cost item linkage validation
*For any* work save attempt, if any material is not linked to a cost item (invalid cost_item_id), the system should prevent saving and display a validation error.
**Validates: Requirements 11.4**

### Property 34: Successful save persists all associations
*For any* valid work with cost items and materials, saving should persist the work record and all CostItemMaterial association records.
**Validates: Requirements 11.5**

### Property 35: Work referential integrity
*For any* CostItemMaterial record creation, the work_id must reference an existing work in the works table.
**Validates: Requirements 13.1**

### Property 36: Cost item referential integrity
*For any* CostItemMaterial record creation, the cost_item_id must reference an existing cost item in the cost_items table.
**Validates: Requirements 13.2**

### Property 37: Material referential integrity
*For any* CostItemMaterial record with a material, the material_id must reference an existing material in the materials table.
**Validates: Requirements 13.3**

### Property 38: Work deletion cascades to associations
*For any* work deletion, all associated CostItemMaterial records (where work_id matches) should be automatically deleted.
**Validates: Requirements 13.4**

### Property 39: Cost item deletion cascades to associations
*For any* cost item deletion, all CostItemMaterial records (where cost_item_id matches) should be automatically deleted.
**Validates: Requirements 13.5**

### Property 40: Material deletion cascades to associations
*For any* material deletion, all CostItemMaterial records (where material_id matches) should be automatically deleted.
**Validates: Requirements 13.5**

### Property 41: Hierarchical path display
*For any* work with a parent, the form should display the complete hierarchical path from root to current work.
**Validates: Requirements 15.1**

### Property 42: Groups can be parents
*For any* work marked as is_group=true, it should be available as a parent option for other works.
**Validates: Requirements 15.2**

### Property 43: Child count display
*For any* work that has child works, the system should display the count of children.
**Validates: Requirements 15.5**

### Property 44: Substring filtering by code or name
*For any* reference field and search substring, all returned results should contain the substring in either the code or name field (case-insensitive).
**Validates: Requirements 16.1, 16.2**

### Property 45: Enter key selects first match
*For any* reference field with filtered results, pressing Enter should select the first item in the filtered list.
**Validates: Requirements 16.3**

### Property 46: Multiple matches display
*For any* substring that matches multiple items, all matching items should be displayed with the matching text highlighted.
**Validates: Requirements 16.4**

### Property 47: Clear search shows full list
*For any* reference field, clearing the search input should display the complete unfiltered list of items.
**Validates: Requirements 16.5**


## Error Handling

### Validation Errors

```typescript
enum ValidationError {
  WORK_NAME_REQUIRED = "Work name is required",
  GROUP_CANNOT_HAVE_PRICE = "Group works cannot have price or labor rate",
  INVALID_QUANTITY = "Quantity must be greater than zero",
  DUPLICATE_COST_ITEM = "This cost item is already added to this work",
  DUPLICATE_MATERIAL = "This material is already added to this cost item",
  COST_ITEM_HAS_MATERIALS = "Cannot delete cost item with associated materials. Delete materials first.",
  MATERIAL_REQUIRES_COST_ITEM = "Material must be linked to a cost item",
  CIRCULAR_REFERENCE = "Cannot set parent: would create circular reference",
  INVALID_PARENT = "Invalid parent work selected",
  INVALID_WORK_ID = "Work ID does not exist",
  INVALID_COST_ITEM_ID = "Cost item ID does not exist",
  INVALID_MATERIAL_ID = "Material ID does not exist"
}
```

### Error Handling Strategy

**Client-Side Validation:**
- Validate required fields before submission
- Validate numeric ranges (quantity > 0)
- Validate uniqueness constraints (duplicate cost items/materials)
- Display inline error messages near invalid fields
- Prevent form submission until all errors are resolved

**Server-Side Validation:**
- Re-validate all client-side rules
- Validate referential integrity (foreign keys exist)
- Validate business rules (groups can't have prices, etc.)
- Return structured error responses with field-level details
- Use HTTP 400 for validation errors, 404 for not found, 409 for conflicts

**Error Response Format:**
```typescript
interface ErrorResponse {
  error: string
  message: string
  details?: {
    field: string
    error: string
  }[]
}
```

### Database Constraint Handling

**Foreign Key Violations:**
- Catch and translate to user-friendly messages
- Example: "Cannot delete cost item: it is referenced by materials"

**Unique Constraint Violations:**
- Catch duplicate key errors
- Display: "This combination already exists"

**Cascade Deletions:**
- Use ON DELETE CASCADE for CostItemMaterial associations
- Warn user before deleting works with compositions
- Provide option to view what will be deleted

## Testing Strategy

### Unit Testing

**Backend Unit Tests:**
- Test each API endpoint independently
- Mock database layer
- Test validation logic
- Test error handling
- Test calculation functions (total cost)

**Frontend Unit Tests:**
- Test individual components in isolation
- Mock API calls
- Test user interactions (button clicks, input changes)
- Test computed properties (total cost calculation)
- Test validation logic

**Example Unit Tests:**
```typescript
describe('WorkCompositionPanel', () => {
  it('should display work name', () => {
    const work = { id: 1, name: 'Test Work', ... }
    const wrapper = mount(WorkCompositionPanel, { props: { work } })
    expect(wrapper.text()).toContain('Test Work')
  })
  
  it('should calculate total cost correctly', () => {
    const costItems = [{ price: 100 }, { price: 200 }]
    const materials = [
      { price: 50, quantity_per_unit: 2 },  // 100
      { price: 30, quantity_per_unit: 3 }   // 90
    ]
    const total = calculateTotalCost(costItems, materials)
    expect(total).toBe(490)  // 100 + 200 + 100 + 90
  })
})
```

### Property-Based Testing

**Testing Framework:** fast-check (for TypeScript/JavaScript)

**Property Test Configuration:**
- Minimum 100 iterations per property
- Use appropriate generators for each data type
- Tag each test with the property number from design doc

**Example Property Tests:**

```typescript
import fc from 'fast-check'

describe('Work Composition Properties', () => {
  /**
   * Feature: work-composition-form, Property 1: Work name validation
   * For any work submission, if the name is empty or contains only whitespace,
   * the system should reject the submission with a validation error.
   */
  it('Property 1: rejects empty or whitespace-only work names', () => {
    fc.assert(
      fc.property(
        fc.string().filter(s => s.trim() === ''),  // Empty or whitespace strings
        async (name) => {
          const work = { name, code: 'TEST', price: 100 }
          const result = await validateWork(work)
          expect(result.isValid).toBe(false)
          expect(result.errors).toContain('Work name is required')
        }
      ),
      { numRuns: 100 }
    )
  })
  
  /**
   * Feature: work-composition-form, Property 2: Work persistence round trip
   * For any valid work data, saving then retrieving should return equivalent data.
   */
  it('Property 2: work persistence round trip', () => {
    fc.assert(
      fc.property(
        fc.record({
          name: fc.string().filter(s => s.trim().length > 0),
          code: fc.option(fc.string(), { nil: null }),
          price: fc.float({ min: 0, max: 1000000 }),
          labor_rate: fc.float({ min: 0, max: 100 }),
          is_group: fc.boolean()
        }),
        async (workData) => {
          const saved = await saveWork(workData)
          const retrieved = await getWork(saved.id)
          
          expect(retrieved.name).toBe(workData.name)
          expect(retrieved.code).toBe(workData.code)
          expect(retrieved.price).toBeCloseTo(workData.price, 2)
          expect(retrieved.labor_rate).toBeCloseTo(workData.labor_rate, 2)
          expect(retrieved.is_group).toBe(workData.is_group)
        }
      ),
      { numRuns: 100 }
    )
  })
  
  /**
   * Feature: work-composition-form, Property 14: Material quantity validation
   * For any material addition, values <= 0 should be rejected.
   */
  it('Property 14: rejects zero or negative material quantities', () => {
    fc.assert(
      fc.property(
        fc.float({ max: 0 }),  // Zero or negative values
        async (quantity) => {
          const result = await validateMaterialQuantity(quantity)
          expect(result.isValid).toBe(false)
          expect(result.error).toContain('greater than zero')
        }
      ),
      { numRuns: 100 }
    )
  })
  
  /**
   * Feature: work-composition-form, Property 17: Material total cost calculation
   * For any material, total cost should equal price × quantity_per_unit.
   */
  it('Property 17: material total cost equals price times quantity', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 100000 }),  // price
        fc.float({ min: 0.001, max: 1000 }), // quantity
        (price, quantity) => {
          const material = { price, quantity_per_unit: quantity }
          const totalCost = calculateMaterialCost(material)
          expect(totalCost).toBeCloseTo(price * quantity, 2)
        }
      ),
      { numRuns: 100 }
    )
  })
  
  /**
   * Feature: work-composition-form, Property 38: Work deletion cascades
   * For any work deletion, all associated CostItemMaterial records should be deleted.
   */
  it('Property 38: work deletion cascades to associations', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 10 }),  // number of associations
        async (numAssociations) => {
          // Create work with associations
          const work = await createWork({ name: 'Test Work' })
          const associations = []
          for (let i = 0; i < numAssociations; i++) {
            const assoc = await addCostItemToWork(work.id, i + 1)
            associations.push(assoc.id)
          }
          
          // Delete work
          await deleteWork(work.id)
          
          // Verify all associations are deleted
          for (const assocId of associations) {
            const exists = await associationExists(assocId)
            expect(exists).toBe(false)
          }
        }
      ),
      { numRuns: 100 }
    )
  })
  
  /**
   * Feature: work-composition-form, Property 44: Substring filtering by code or name
   * For any search substring, all results should contain the substring in code or name.
   */
  it('Property 44: substring filtering matches code or name', () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({
          code: fc.string({ minLength: 1, maxLength: 20 }),
          name: fc.string({ minLength: 1, maxLength: 100 })
        }), { minLength: 10, maxLength: 100 }),  // List of items
        fc.string({ minLength: 1, maxLength: 10 }),  // Search substring
        (items, searchTerm) => {
          const results = filterBySubstring(items, searchTerm)
          
          // Every result should contain the search term in code or name
          for (const result of results) {
            const codeMatch = result.code.toLowerCase().includes(searchTerm.toLowerCase())
            const nameMatch = result.name.toLowerCase().includes(searchTerm.toLowerCase())
            expect(codeMatch || nameMatch).toBe(true)
          }
        }
      ),
      { numRuns: 100 }
    )
  })
  
  /**
   * Feature: work-composition-form, Property 45: Enter key selects first match
   * For any filtered results, pressing Enter should select the first item.
   */
  it('Property 45: enter key selects first match', () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({
          id: fc.integer({ min: 1 }),
          code: fc.string(),
          name: fc.string()
        }), { minLength: 1, maxLength: 50 }),
        (items) => {
          const firstItem = items[0]
          const selected = selectFirstMatch(items)
          expect(selected.id).toBe(firstItem.id)
        }
      ),
      { numRuns: 100 }
    )
  })
  
  /**
   * Feature: work-composition-form, Property 47: Clear search shows full list
   * For any reference field, clearing search should show all items.
   */
  it('Property 47: clearing search shows full list', () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({
          id: fc.integer({ min: 1 }),
          code: fc.string(),
          name: fc.string()
        }), { minLength: 1, maxLength: 100 }),
        (allItems) => {
          // Filter then clear
          const filtered = filterBySubstring(allItems, 'test')
          const cleared = filterBySubstring(allItems, '')
          
          // Cleared should equal all items
          expect(cleared.length).toBe(allItems.length)
          expect(cleared).toEqual(allItems)
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

**Generator Strategies:**

```typescript
// Smart generators for domain objects
const workGenerator = fc.record({
  name: fc.string({ minLength: 1, maxLength: 500 }).filter(s => s.trim().length > 0),
  code: fc.option(fc.string({ maxLength: 50 }), { nil: null }),
  price: fc.float({ min: 0, max: 1000000, noNaN: true }),
  labor_rate: fc.float({ min: 0, max: 100, noNaN: true }),
  is_group: fc.boolean(),
  parent_id: fc.option(fc.integer({ min: 1, max: 1000 }), { nil: null })
})

const quantityGenerator = fc.float({ 
  min: 0.001,  // Minimum valid quantity
  max: 10000,  // Reasonable maximum
  noNaN: true,
  noDefaultInfinity: true
})

const searchTermGenerator = fc.oneof(
  fc.string({ minLength: 1, maxLength: 50 }),  // Normal search
  fc.constant(''),  // Empty search
  fc.string().map(s => s.toLowerCase()),  // Lowercase
  fc.string().map(s => s.toUpperCase())   // Uppercase
)
```

### Integration Testing

**End-to-End Scenarios:**
1. Create new work with complete composition
2. Edit existing work composition
3. Delete cost items and materials
4. Change material quantities
5. Reassign materials to different cost items
6. Validate error handling
7. Test hierarchical work structures

**Test Data Setup:**
- Create test database with sample units, cost items, materials
- Use factories to generate test data
- Clean up after each test

### Testing Checklist

**Backend:**
- [ ] API endpoint tests for all CRUD operations
- [ ] Validation logic tests
- [ ] Database constraint tests
- [ ] Cascade deletion tests
- [ ] Error handling tests
- [ ] Property-based tests for business logic

**Frontend:**
- [ ] Component rendering tests
- [ ] User interaction tests
- [ ] Form validation tests
- [ ] API integration tests
- [ ] Property-based tests for calculations
- [ ] E2E tests for complete workflows

